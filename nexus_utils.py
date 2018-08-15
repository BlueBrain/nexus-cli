import requests, json
from blessings import Terminal
from http.client import responses
import os, sys
from distutils.version import LooseVersion

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


def get_selected_deployment_base_url():
    return config_utils.get_selected_deployment_config()[1]['url'] + "/v0"


def get_by_id(entity_url, authenticate=True, verbose=False, fail_if_not_found=True):
    """
    Retrieve an entity description from a given URL (ID).

    :param entity_url: the URL of the entity to retrieve
    :param authenticate: if True, attempts to use the token of the logged in user.
    :param verbose: if True, prints extra information
    :param fail_if_not_found: if True, calls sys.exit upon not finding entity, otherwise returns None.
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
        if fail_if_not_found:
            utils.error("Failed to get entity from URL: " + entity_url +
                        '\nRequest status: ' + str(r.status_code) + ' (' + responses[r.status_code] + ')')
        else:
            return None

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


def search(query, organization=None, domain=None, fetch_entities=True, max_results=None, authenticate=True, verbose=False):
    """
    Execute provided search query and return resulting entities.

    :param query: a dict
    :param organization: str
    :param domain: str
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

    filter = ''
    if organization is not None:
        filter = '/' + organization
        if domain is not None:
            filter += '/' + domain
    else:
        if domain is not None:
            utils.error("You cannot filter by domain without specifying an organization");

    search_url = config_utils.get_selected_deployment_config()[1]['url'] + "/v0/queries" + filter

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


def upload_file(instance_id, file_to_upload, authenticate=True, verbose=False):
    headers = {}
    if authenticate:
        add_authorization_to_headers(headers)

    payload = get_by_id(instance_id, authenticate=authenticate)

    if payload['nxv:deprecated']:
        utils.error("You cannot upload a file on a deprecated entity: " + instance_id)

    if 'distribution' in payload:
        utils.error("attachment already present, you cannot upload more than one: " + instance_id)

    revision = payload["nxv:rev"]

    url = "{}/attachment?rev={}".format(instance_id, revision)
    if verbose:
        print("URL: " + url)
    try:
        file = {'file': open(file_to_upload, 'rb')}
        r = requests.put(url, files=file, headers=headers)
        if r.status_code != 201:
            print(t.red("%d (%s)\n%s" % (r.status_code, r.reason, r.content)))
            utils.error("File upload failed")
    except Exception as error:
        print(error)


def create_organization(organization_name, authenticate=True, verbose=False):

    if organization_name is None:
        utils.error("You must give a non empty organization name")
    organization_name = organization_name.strip()
    if len(organization_name) == 0:
        utils.error("You must give a non empty organization name")

    headers = {}
    if authenticate:
        add_authorization_to_headers(headers)
    headers['Content-Type'] = 'application/ld+json'

    url = config_utils.get_selected_deployment_config()[1]['url'] + "/v0/organizations/" + organization_name

    payload = {
        "@context": {
            "schema": "http://schema.org/"
        },
        "schema:name": organization_name
    }

    if verbose:
        print("Creating new organization '%s': %s" % (organization_name, url))
        utils.print_json(payload, colorize=True)

    r = requests.put(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 201:
        utils.error("Unexpected error occurred: HTTP %d (%s)\nDetails: %s" % (r.status_code, r.reason, r.content))
    else:
        print(t.green("Organisation created."))


def create_domain(domain_name, organization_name, authenticate=True, verbose=False):

    if domain_name is None:
        utils.error("You must give a non empty domain name")
    domain_name = domain_name.strip()
    if len(domain_name) == 0:
        utils.error("You must give a non empty domain name")

    headers = {}
    if authenticate:
        add_authorization_to_headers(headers)
    headers['Content-Type'] = 'application/ld+json'

    base_url = config_utils.get_selected_deployment_config()[1]['url']
    url = base_url + "/v0/domains/" + organization_name + "/" + domain_name

    payload = {
        "@context": {
            "schema": "http://schema.org/"
        },
        "schema:name": domain_name,
        "description": ""
    }

    if verbose:
        print("Creating new domain '%s' in organization '%s': %s" % (domain_name, organization_name, url))
        utils.print_json(payload, colorize=True)

    r = requests.put(url, data=json.dumps(payload), headers=headers)

    if r.status_code != 201:
        utils.error("Unexpected error occurred: HTTP %d (%s)\nDetails: %s" % (r.status_code, r.reason, r.content))
    else:
        print(t.green("Domain created."))


def deprecate_domain(domain_name, organization_name, authenticate=True, verbose=False):

    if domain_name is None:
        utils.error("You must give a non empty domain name")
    domain_name = domain_name.strip()
    if len(domain_name) == 0:
        utils.error("You must give a non empty domain name")

    headers = {}
    if authenticate:
        add_authorization_to_headers(headers)
    headers['Content-Type'] = 'application/ld+json'

    base_url = get_selected_deployment_base_url()
    url = base_url + "/domains/" + organization_name + "/" + domain_name

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(t.red("Unexpected error occurred: HTTP %d (%s)" % (r.status_code, r.reason)))
        print(t.red("URL: %s" % url))
        utils.error("Details: %s" % r.content)

    domain_json = r.json()
    revision = domain_json['nxv:rev']
    if verbose:
        print("current revision: %s" % revision)

    if verbose:
        print("Deprecating domain '%s' in organization '%s': %s" % (domain_name, organization_name, url))

    url = url + "?rev=" + str(revision)
    r2 = requests.delete(url, headers=headers)

    if r2.status_code != 200:
        utils.error("Unexpected error occurred: HTTP %d (%s)\nDetails: %s" % (r2.status_code, r2.reason, r2.content))
    else:
        print(t.green("Domain deprecated."))


DEPRECATED_URI = 'https://bbp-nexus.epfl.ch/vocabs/nexus/core/terms/v0.1.0/deprecated'


def is_deprecated(entity_id, authenticate=True, verbose=False):
    payload = get_by_id(entity_id + "?format=expanded", authenticate=authenticate, verbose=verbose)
    if DEPRECATED_URI in payload:
        deprecated = payload[DEPRECATED_URI]
        if type(deprecated) is bool:
            return deprecated
        elif type(deprecated) is list:
            e = deprecated[0]
            if type(e) is dict:
                if '@value' in e:
                    d = e['@value']
                    if type(d) is bool:
                        return d
                    else:
                        utils.print_json(deprecated, colorize=True)
                        utils.error("Unexpected payload")
                else:
                    utils.print_json(deprecated, colorize=True)
                    utils.error("Unexpected payload")
            else:
                utils.print_json(deprecated, colorize=True)
                utils.error("Unexpected payload")
        else:
            utils.print_json(deprecated, colorize=True)
            utils.error("Unexpected payload")


def publish_schema(schema_id, authenticate=True, verbose=False):
    payload = get_by_id(schema_id, authenticate=authenticate, verbose=verbose)
    if "nxv:published" in payload:
        if payload['nxv:published']:
            if verbose:
                print("Schema already published")
        else:
            headers = {'Content-Type': 'application/ld+json'}
            if authenticate:
                add_authorization_to_headers(headers)
            revision = payload['nxv:rev']
            url = schema_id + "/config?rev=" + str(revision)
            cfg = {"published": True}
            r = requests.patch(url, data=json.dumps(cfg), headers=headers)
            if r.status_code == 200:
                print(t.green("Schema published"))
            else:
                print(t.red("URL: %s\nHTTP %d (%s)\nDetails: %s" % (url, r.status_code, r.reason, r.content)))
                utils.error("Failed to publish schema.")
            r.close()


def find_latest_context(organization, domain, context):
    """
    Given an organization, domain and context name, find the most recent version and return its id.
    """
    base_url = get_selected_deployment_base_url()
    schemas_url = base_url + "/contexts"
    _contexts, total = get_results_by_uri(schemas_url)

    # look for instance schema and pick the highest version
    id = None
    current_version = None
    for c in _contexts:
        context_id = c['resultId']
        values = context_id.split("/")[-4:] # org / domain / context / version
        if organization != values[0] or domain != values[1] or context != values[2]:
            continue

        version = values[3]

        if current_version is None:
            current_version = LooseVersion(version[1:])
            id = context_id
        else:
            tmp = LooseVersion(version[1:])
            if tmp > current_version:
                current_version = tmp
                id = context_id

    return id
