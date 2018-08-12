import sys
from blessings import Terminal
import requests, json
from pygments import highlight
from pygments.lexers import JsonLdLexer
from pygments.formatters import TerminalFormatter, TerminalTrueColorFormatter


def error(message):
    t = Terminal()
    print(t.red(message))
    sys.exit(101)


def success(message):
    t = Terminal()
    print(t.green(message))


def print_json(data, colorize=False):
    """
    Print a json payload.
    :param data: the json payload to print
    :param colorize: if true, colorize the output
    """
    json_str = json.dumps(data, indent=2)
    if colorize:
        sys.stdout.write(highlight(json_str, JsonLdLexer(), TerminalFormatter()))
        sys.stdout.flush()
    else:
        print(json_str)


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