import sys
from blessings import Terminal
import requests, json


def error(message):
    t = Terminal()
    print(t.red(message))
    sys.exit(101)


def success(message):
    t = Terminal()
    print(t.green(message))


def get_results_by_uri(data_url, first_page_only=False, token=None):
    """From a given URL, query nexus and retrieve all results and return them as a 'list of dict'"""
    results = []
    total = 0
    while data_url is not None:
        r = requests.get(data_url)
        if r.status_code != 200:
            error("Failed to list results from URL: " + data_url +
                  '\nRequest status: ' + str(r.status_code))

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