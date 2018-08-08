import click
import os
from blessings import Terminal

import config_utils
import nexus_utils
import utils


t = Terminal()


@click.command()
@click.option('--file',   help='name of the file to updload.')
@click.option('--org',    help='The organisation in which to store that file.')
@click.option('--domain', help='The domain in which to store that file.')
@click.option('--type',   default='nxv:Entity', help='The type of the entity to be uploaded.')
def upload(file, org, domain, type):
    """Upload a file in Nexus."""
    utils.error("upload not implemented yet")

    """Upload a given file into Nexus"""
    if file is None:
        utils.error('ERROR: you must give a filename')

    print(os.path.abspath(file))
    if not os.path.isfile(file):
        utils.error('ERROR: File doesn''t exist:' + file)
    else:
        utils.success('File found.')

        # TODO perform upload into Nexus