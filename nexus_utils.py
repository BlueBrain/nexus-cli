from utils import error
import config_utils
import requests, json
from http.client import responses


def get_by_id(entity_url, authenticate=True):
    """
    Retrieve an entity description from a given URL (ID).

    :param entity_url: the URL of the entity to retrieve
    :param authenticate: if True, attempts to use the token of the logged in user.
    :return: the payload this URL points to
    :rtype: dict
    """
    headers = {}
    if authenticate:
        access_token = config_utils.get_access_token()
        if access_token is not None:
            headers["Authorization"] = "Bearer " + access_token

    r = requests.get(entity_url, headers=headers)
    if r.status_code != 200:
        error("Failed to get entity from URL: " + entity_url +
              '\nRequest status: ' + str(r.status_code) + ' (' + responses[r.status_code] + ')')

    return r.json()


def get_results_by_uri(data_url, first_page_only=False, authenticate=True):
    """
    From a given URL, query nexus and retrieve all results and return them as a 'list of dict'

    :param str data_url: the URL from which to get data from nexus
    :param bool first_page_only: if set to True, data will not be loaded beyond the first page returned by nexus (default: False).
    :param bool authenticate: if set to False, no force no token to be passed along, even if the user is logged in (detault: True).
    :return the list of collected results
    :rtype: list
    """
    results = []

    headers = {}
    if authenticate:
        access_token = config_utils.get_access_token()
        if access_token is not None:
            headers["Authorization"] = "Bearer " + access_token

    total = 0
    while data_url is not None:
        r = requests.get(data_url, headers=headers)
        if r.status_code != 200:
            error("Failed to list results from URL: " + data_url +
                  '\nRequest status: ' + str(r.status_code) + ' (' + responses[r.status_code] + ')')

        payload = r.json()
        if 'results' not in payload:
            print(t.red(json.dumps(payload, indent=2)))
            error('\nUnexpected payload return from Nexus URL: ' + data_url +
                  "\nCould not find attribute 'results'.")

        total = payload['total']
        for item in payload['results']:
            results.append(item)

        if not first_page_only:
            if 'links' in payload and 'next' in payload['links']:
                data_url = payload['links']['next']
            else:
                data_url = None  # exit loop
        else:
            data_url = None  # exit loop

    return results, total

