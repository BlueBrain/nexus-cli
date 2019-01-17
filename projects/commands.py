import click
from prettytable import PrettyTable

import config_utils
import utils


@click.command()
@click.option('--organization', '-o', help='Organisation to work on')
@click.option('--create', '-a', help='Create a new organization')
@click.option('--update', '-u', help='Update an organization')
@click.option('_list', '--list', '-l', help='List organizations')
@click.option('--deprecate', '-d', help='Deprecate an organization')
@click.option('--select', '-s', help='Select an organization')
@click.option('--current', '-c', help='Show currently selected organization')
def projects(organization, create, update, _list, deprecate , select, current):
    """Management of projects."""
    utils.error("Not implemented yet")



