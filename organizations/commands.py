import click
from prettytable import PrettyTable

import config_utils
import utils


@click.command()
@click.option('--create', '-a', help='Create a new organization')
@click.option('_list', '--list', '-l', help='List organizations')
@click.option('--deprecate', '-d', help='Deprecate an organization')
@click.option('--select', '-s', help='Select an organization')
@click.option('--current', '-c', help='Show currently selected organization')
def organizations(create, _list, deprecate, select, current):
    """Management of organizations."""
    utils.error("Not implemented yet")



