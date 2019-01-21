import sys
from blessings import Terminal
import requests, json
from pygments import highlight
from pygments.lexers import JsonLdLexer
from pygments.formatters import TerminalFormatter, TerminalTrueColorFormatter
import time
from datetime import datetime


t = Terminal()


def error(message):
    print(t.red(message))
    sys.exit(101)


def success(message):
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


def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset


def print_time(seconds):
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s%dd %dh %dm %ds' % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return '%s%dh %dm %ds' % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return '%s%dm %ds' % (sign_string, minutes, seconds)
    else:
        return '%s%ds' % (sign_string, seconds)