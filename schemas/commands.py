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
@click.option('--add', '-a', help='Name of the nexus schemas to be locally added')
@click.option('--deprecate', '-r', help='Name of the nexus schemas to be locally deprecated')
@click.option('--list', '-l', is_flag=True, help='List all nexus schemas registered')
def schemas(add, deprecate, list):
    """Manage Nexus schemas."""
    error("schemas command not implemented yet.")

