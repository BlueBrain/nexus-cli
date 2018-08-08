import click
from blessings import Terminal

import nexus_utils
import utils


t = Terminal()


@click.command()
@click.option('--url', '-u', help='The URL (ID) of the entity to retrieve')
@click.option('--pretty', '-p', is_flag=True, help='Colorize output')
def get(url, pretty):
    """retrieve an entity by its ID."""
    if url is None:
        utils.error("You must give the URL (ID) of the entity to retrieve")

    json = nexus_utils.get_by_id(url)
    utils.print_json(json, colorize=pretty)

