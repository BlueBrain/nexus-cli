import click
import cli
import re
from blessings import Terminal
from prettytable import PrettyTable

from utils import error

t = Terminal()

def is_valid_deployment_name(name, reg=re.compile('^[a-zA-Z0-9\.\-_]+$')):
    return bool(reg.match(name))


@click.command()
@click.option('--add', '-a', help='Name of the nexus deployment to be locally added')
@click.option('--remove', '-r', help='Name of the nexus deployment to be locally removed')
@click.option('--select', '-r', help='Name of the nexus deployment to be selected for subsequent CLI calls')
@click.option('--url', '-u', help='URL of a nexus deployment (for --add, --remove)')
@click.option('--list', '-l', is_flag=True, help='List all nexus deployment registered')
def deployment(add, remove, select, url, list):
    """Manage Nexus deployment accessed by the CLI."""
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

        config[add] = {'url': url}
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
        table = PrettyTable(['Deployment', 'Selected', 'URL'])
        for key in config.keys():
            selected = ""
            if 'selected' in config[key] and config[key]['selected'] is True:
                selected = "Yes"
            table.add_row([key, selected, config[key]['url']])
        print(table)

