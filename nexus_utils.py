import requests, json
from blessings import Terminal
from http.client import responses
import os, sys

import config_utils
import utils


t = Terminal()


def add_authorization_to_headers(headers):
    if headers is None:
        headers = {}
    access_token = config_utils.get_access_token()
    if access_token is not None:
        headers["Authorization"] = "Bearer " + access_token
    return headers


def get_by_id(entity_url, authenticate=True, verbose=False):
    """
    Retrieve an entity description from a given URL (ID).

    :param entity_url: the URL of the entity to retrieve
    :param authenticate: if True, attempts to use the token of the logged in user.
    :return: the payload this URL points to
    :rtype: dict
    """

    headers = {}
    if authenticate:
        add_authorization_to_headers(headers)

    if verbose:
        print("Fetching: " + entity_url)
    r = requests.get(entity_url, headers=headers)
    if r.status_code != 200:
        utils.error("Failed to get entity from URL: " + entity_url +
              '\nRequest status: ' + str(r.status_code) + ' (' + responses[r.status_code] + ')')

    data = r.json()
    r.close()
    return data


def get_results_by_uri(data_url, first_page_only=False, max_results=None, authenticate=True):
    """
    From a given URL, query nexus and retrieve all results and return them as a 'list of dict'

    :param str data_url: the URL from which to get data from nexus
    :param bool first_page_only: if set to True, data will not be loaded beyond the first page returned by nexus (default: False).
    :param int max_results: if not None, constrains how many results are to be collected.
    :param bool authenticate: if set to False, no force no token to be passed along, even if the user is logged in (detault: True).
    :return the list of collected results
    :rtype: list
    """
    results = []

    headers = {}
    if authenticate:
        add_authorization_to_headers(headers)

    total = 0
    count = 0
    while data_url is not None:
        r = requests.get(data_url, headers=headers)
        if r.status_code != 200:
            utils.error("Failed to list results from URL: " + data_url +
                  '\nRequest status: ' + str(r.status_code) + ' (' + responses[r.status_code] + ')')

        payload = r.json()
        r.close()
        if 'results' not in payload:
            print(t.red(json.dumps(payload, indent=2)))
            utils.error('\nUnexpected payload return from Nexus URL: ' + data_url +
                  "\nCould not find attribute 'results'.")

        total = payload['total']
        for item in payload['results']:
            results.append(item)
            count += 1
            if max_results is not None and count >= int(max_results):
                return results, total

        if not first_page_only:
            if 'links' in payload and 'next' in payload['links']:
                data_url = payload['links']['next']
            else:
                data_url = None  # exit loop
        else:
            data_url = None  # exit loop

    return results, total


def search(query, fetch_entities=True, max_results=None, authenticate=True, verbose=False):
    """
    Execute provided search query and return resulting entities.

    :param query: a dict
    :param fetch_entities: bool
    :param max_results:
    :param authenticate:
    :param verbose:
    :return:
    """

    results = []

    headers = {}
    if authenticate:
        add_authorization_to_headers(headers)
    headers["Content-Type"] = "application/json"

    search_url = config_utils.get_selected_deployment_config()[1]['url'] + "/v0/queries"

    r = None
    try:
        if verbose:
            print("Issuing POST: " + search_url)
            print("Query:")
            utils.print_json(query, colorize=True)
        r = requests.post(search_url, data=json.dumps(query), headers=headers, allow_redirects=False)
    except Exception as e:
        utils.error("Failed: {0}".format(e))

    # expecting a redirect
    if 300 <= r.status_code < 400:
        location = r.headers['Location']
        if verbose:
            print("HTTP " + str(r.status_code) + " ("+r.reason+")")
            print("Following redirect: " + location)

        # now get the results
        entities, total = get_results_by_uri(location, max_results=max_results)
        if verbose:
            print("Total: " + format(total, ',d'))
            print("Collected: " + format(len(entities), ',d'))

        if fetch_entities:
            for e in entities:
                payload = get_by_id(e['resultId'], verbose=verbose)
                results.append(payload)
        else:
            for e in entities:
                results.append(e['resultId'])
    else:
        utils.error("Unexpected HTTP code: %d (%s)\nContent:\n%s" % (r.status_code, r.reason, r.content))

    return results


def pretty_filesize(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def download_file(distribution, local_dir, authenticate=True, verbose=False):
    if distribution is None:
        utils.error("You must give a non null distribution")
    abs_local_dir = os.path.abspath(local_dir)

    downloadURL = distribution['downloadURL']
    originalFileName = distribution['originalFileName']
    contentSize = distribution['contentSize']['value']

    local_file = abs_local_dir + '/' + originalFileName

    if os.path.isfile(local_file):
        print(originalFileName+" - file exists already, SKIPPING")
    else:
        headers = {}
        if authenticate:
            add_authorization_to_headers(headers)

        if verbose:
            sys.stdout.write("Downloading %s (%s)" % (originalFileName, pretty_filesize(contentSize)) + " ... ")
            sys.stdout.flush()

        r = requests.get(downloadURL, headers=headers, stream=True)
        if r.status_code != 200:
            utils.error("Download error, received HTTP %d (%s)" % (r.status_code, r.reasons))
        with open(local_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

        print("done")

    return local_file