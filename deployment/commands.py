import click
import re
import requests
import json
from blessings import Terminal
from prettytable import PrettyTable

import cli
from utils import error

t = Terminal()


def is_valid_deployment_name(name, reg=re.compile('^[a-zA-Z0-9\.\-_]+$')):
    return bool(reg.match(name))


@click.command()
@click.option('--add', '-a', help='Name of the nexus deployment to be locally added')
@click.option('--remove', '-r', help='Name of the nexus deployment to be locally removed')
@click.option('--select', '-r', help='Name of the nexus deployment to be selected for subsequent CLI calls')
@click.option('--url', '-u', help='URL of a nexus deployment (for --add, --remove)')
@click.option('--list', '-l', is_flag=True, help='List all nexus deployment locally registered')
def deployment(add, remove, select, url, list):
    """Manage Nexus deployments."""
    # click.echo("deployment")
    if add is not None and remove is not None:
        error("You cannot add and remove on the same command line.")

    if add is not None:
        # print('add:' + add)
        if url is None:
            error("You must have a URL (--url) in order to add a deployment")
        config = cli.get_cli_config()
        if add in config and 'url' in config[add]:
            error("This deployment already exist (%s) with url: %s" % (add, config[add]))

        # Validate URL
        data_url = url.rstrip("/") + '/v0/data'
        r = requests.get(data_url)
        if r.status_code != 200:
            error("Failed to get entity count from URL: " + data_url +
                  '\nRequest status: ' + str(r.status_code))

        config[add] = {'url': url.rstrip("/")}
        cli.save_cli_config(config)

    if remove is not None:
        # print('remove:'+remove)
        if url is not None:
            error("--remove doesn't take a URL")

        config = cli.get_cli_config()
        if remove not in config:
            error("Could not find deployment '%s' in CLI config" % remove)

        config.pop(remove, None)
        cli.save_cli_config(config)

    if select is not None:
        # print('select')
        if select is None:
            error("No deployment name given")
        config = cli.get_cli_config()
        if select not in config:
            error("Unknown deployment: " + select)
        for key in config.keys():
            if 'selected' in config[key] and key != select:
                config[key].pop('selected', None)
                print("deployment '%s' was unselected" % key)
        config[select]['selected'] = True
        cli.save_cli_config(config)

    if list is True:
        # print('list:'+str(list))
        config = cli.get_cli_config()
        table = PrettyTable(['Deployment', 'Selected', 'URL', '#entities (public)'])
        table.align["Deployment"] = "l"
        table.align["URL"] = "l"
        for key in config.keys():
            selected = ""

            if 'selected' in config[key] and config[key]['selected'] is True:
                selected = "Yes"

            data_url = config[key]['url'] + '/v0/data'
            r = requests.get(data_url)
            if r.status_code != 200:
                error("Failed to get entity count from URL: " + data_url +
                      '\nRequest status: ' + str(r.status_code))
            payload = r.json()
            if 'total' not in payload:
                print(t.red(json.dumps(payload, indent=2)))
                error('Unexpected payload return from Nexus ' + key + ' URL: ' + data_url +
                      "\nCould not find attribute 'total'.")
            data_count = payload['total']

            # TODO this is only public data, if a token is available, we could also show private count
            table.add_row([key, selected, config[key]['url'], data_count])

        print(table)

