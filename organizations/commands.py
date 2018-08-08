import click
import re
import requests
import json
from blessings import Terminal
from prettytable import PrettyTable

import cli
from utils import error

t = Terminal()


@click.command()
@click.option('--add', '-a', help='Name of the nexus organization to be locally added')
@click.option('--deprecate', '-r', help='Name of the nexus organization to be locally deprecated')
@click.option('--list', '-l', is_flag=True, help='List all nexus organization registered')
def organizations(add, deprecate, list):
    """Manage Nexus organizations."""
    error("organization command not implemented yet.")

