import click

from nexuscli import utils
from nexuscli.nexus_utils import get_nexus_client

from nexuscli.cli import cli


@cli.group()
def realms():
    """Realms operations"""


@realms.command(name='create', help='Create a new realm')
@click.argument('name')
def create(name):
    utils.error("Not implemented yet")


@realms.command(name='update', help='Update an realm')
@click.argument('id')
@click.option('--data', '-d', help='Payload to replace it with')
def update(id, data):
    utils.error("Not implemented yet")


@realms.command(name='list', help='List all realms')
def _list():
    nxs = get_nexus_client()
    try:
        response = nxs.realms.list()
        for r in response["results"]:
            print(r["name"], r["deprecated"])
    except nxs.HTTPError as e:
        print(e.response.json())
        utils.error(str(e))


@realms.command(name='deprecate', help='Deprecate an realm')
@click.argument('name')
def deprecate(name):
    utils.error("Not implemented yet")


@realms.command(name='select', help='Select an realm')
@click.argument('name')
def select(name):
    utils.error("Not implemented yet")


@realms.command(name='current', help='Show currently selected realm')
def select():
    utils.error("Not implemented yet")
