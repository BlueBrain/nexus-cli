import click

from nexuscli import utils
from nexuscli.nexus_utils import get_nexus_client

from nexuscli.cli import cli


@cli.group()
def orgs():
    """Organizations operations"""


@orgs.command(name='create', help='Create a new organization')
@click.argument('name')
def create(name):
    utils.error("Not implemented yet")


@orgs.command(name='update', help='Update an organization')
@click.argument('id')
@click.option('--data', '-d', help='Payload to replace it with')
def update(id, data):
    utils.error("Not implemented yet")


@orgs.command(name='list', help='List all organizations')
def _list():
    nxs = get_nexus_client()



@orgs.command(name='deprecate', help='Deprecate an organization')
@click.argument('name')
def deprecate(name):
    utils.error("Not implemented yet")


@orgs.command(name='select', help='Select an organization')
@click.argument('name')
def select(name):
    utils.error("Not implemented yet")


@orgs.command(name='current', help='Show currently selected organization')
def select():
    utils.error("Not implemented yet")
