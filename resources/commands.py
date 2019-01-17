import click
from prettytable import PrettyTable

import config_utils
import utils


@click.command()
@click.option('--organization', '-o', help='Organisation to work on')
@click.option('--project', '-p', help='Project to work on')
@click.option('--create', '-c', help='Create a new resource')
@click.option('--file', help='source file to create new resource')
@click.option('--data', help='source payload to create new resource')
@click.option('--update', '-u', help='Create a new resource')
@click.option('_list', '--list', '-l', help='List resources')
@click.option('--deprecate', '-d', help='Deprecate an resource')
@click.option('--fetch', '-f', help='Fetch a resource by id')
def resources(organization, project, create, file, data, update, _list, deprecate, fetch):
    """Management of resources."""
    utils.error("Not implemented yet")



