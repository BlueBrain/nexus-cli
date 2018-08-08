import click
import re
import requests
import json
from blessings import Terminal
from prettytable import PrettyTable
import typing

import cli
from utils import error

t = Terminal()

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


@click.command()
@click.option('--add', '-a', help='Name of the nexus organization to be locally added')
@click.option('--deprecate', '-r', help='Name of the nexus organization to be locally deprecated')
@click.option('--list', '-l', is_flag=True, help='List all nexus organization registered')
def organizations(add, deprecate, list):
    """Manage Nexus organizations."""
    if list is not None:
        c = cli.get_selected_deployment_config()
        if c is None:
            error("You must select a deployment using `deployment --select` prior to running this command.")
        active_deployment_cfg = c[1]

        url = active_deployment_cfg['url'] + "/v0/organizations"
        data = get_results_by_uri(url)
        total = data[1]
        results = data[0]

        columns = ["Organizations"]
        table = PrettyTable(columns)
        table.align[columns[0]] = "l"
        for item in results:
            table.add_row([item['resultId']])
        print(table)
        if( len(results) == total ):
            print(t.green('Total:' + str(total)))
        else:
            print(t.green('Total: %d of %d' % (str(len(results)), str(total))))


    if add is not None:
        error("--add not implemented yet")

    if deprecate is not None:
        error("--deprecate not implemented yet")

