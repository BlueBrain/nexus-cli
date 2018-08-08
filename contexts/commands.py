import click
import requests
import json
from blessings import Terminal
from prettytable import PrettyTable

import config_utils
import nexus_utils
import utils

t = Terminal()


@click.command()
@click.option('--list', '-l', is_flag=True, help='List all nexus registered contexts in selected deployment')
@click.option('--public-only', '-p', is_flag=True, default=False, help='List only public datasets (i.e. no authentication)')
@click.option('--search', '-s', help='Free text search through contexts')
def contexts(list, public_only, search):
    """Manage Nexus contexts."""
    c = config_utils.get_selected_deployment_config()
    if c is None:
        utils.error("You must select a deployment using `deployment --select` prior to running this command.")
    cfg_name = c[0]
    config = c[1]

    if list is True:
        column_name = 'Context (' + cfg_name + ')'
        table = PrettyTable([column_name]) # TODO add "Revision", "Published", "Deprecated"
        table.align[column_name] = "l"

        if public_only:
            print("Limiting results to publicly accessible records")
            authenticate = False
        else:
            authenticate = True

        data_url = config['url'] + '/v0/contexts'
        data = nexus_utils.get_results_by_uri(data_url, authenticate=authenticate)
        total = data[1]
        results = data[0]

        for item in results:
            table.add_row([item['resultId']])

        print(table)
        print(t.green('Total:'+str(total)))


    if search is not None:
        utils.error("--search not supported yet")
        data_url = config['url'] + '/v0/contexts'
        count = 0
        while data_url is not None:
            r = requests.get(data_url)
            if r.status_code != 200:
                utils.error("Failed to list contexts from URL: " + data_url +
                      '\nRequest status: ' + str(r.status_code))

            payload = r.json()
            if 'results' not in payload:
                print(t.red(json.dumps(payload, indent=2)))
                utils.error('\nUnexpected payload return from Nexus ' + cfg_name + ' URL: ' + data_url +
                            "\nCould not find attribute 'results'.")
            context_list = payload['results']

            for context in context_list:
                context_url = context['resultId']
                r2 = requests.get(context_url)
                if r.status_code != 200:
                    utils.error("Failed to get context: " + context_url +
                                '\nRequest status: ' + str(r.status_code))

                context_payload = r2.json()
                print(t.green(json.dumps(context_payload, indent=2)))
                if '@context' in context_payload:
                    for term in context_payload['@context']:
                        print(term)

            if 'links' in payload and 'next' in payload['links']:
                data_url = payload['links']['next']
            else:
                data_url = None  # exit loop

