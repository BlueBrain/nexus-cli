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
@click.option('--no-format', '-n', is_flag=True, default=False, help='print without table formatting')
@click.option('--search', '-s', help='Free text search through contexts')
def contexts(list, public_only, no_format, search):
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
            s = item['resultId']
            if no_format:
                print(s)
            else:
                table.add_row([s])

        if not no_format:
            print(table)
            print(t.green('Total:'+str(total)))

    if search is not None:
        # utils.error("--search not supported yet")
        if public_only:
            print("Limiting results to publicly accessible records")
            authenticate = False
        else:
            authenticate = True

        data_url = config['url'] + '/v0/contexts'

        data = nexus_utils.get_results_by_uri(data_url, authenticate=authenticate)
        results = data[0]

        for item in results:
            context_id = item['resultId']
            print("Getting " + context_id + " ...")
            context_json = nexus_utils.get_by_id(context_id, authenticate=authenticate)
            if '@context' in context_json:
                for key in context_json['@context']:
                    if type(key) is str:
                        if search in key:
                            print(t.green(key))
                    elif type(key) is dict:
                        for k in key.keys():
                            if search in k:
                                print(t.green(k + ": " + str(key[k])))
            else:
                print("no @context found")




