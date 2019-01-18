import click
import utils

from cli import cli


@cli.group()
def resources():
    """Resources operations"""


@resources.command(name='create', help='Create a new resource')
@click.argument('name')
@click.option('--org', '-o', help='Organization to work on (overrides selection made with --orgs)')
@click.option('--project', '-p', help='Project to work on (overrides selection made with --projects)')
@click.option('--id', '-f', help='Id of the resource')
@click.option('--file', '-f', help='source file to create new resource')
@click.option('--data', '-d', help='source payload to create new resource')
def create(name, org, project, id, file, data):
    utils.error("Not implemented yet")


@resources.command(name='update', help='Update a resource')
@click.argument('id')
@click.option('--org', '-o', help='Organization to work on (overrides selection made with --orgs)')
@click.option('--project', '-p', help='Project to work on (overrides selection made with --projects)')
@click.option('--data', '-d', help='Payload to replace it with')
def update(id, org, project, data):
    utils.error("Not implemented yet")


@resources.command(name='list', help='List all resources')
@click.option('--org', '-o', help='Organization to work on (overrides selection made with --orgs)')
@click.option('--project', '-p', help='Project to work on (overrides selection made with --projects)')
def _list(org, project):
    utils.error("Not implemented yet")


@resources.command(name='deprecate', help='Deprecate an resource')
@click.argument('id')
@click.option('--org', '-o', help='Organization to work on (overrides selection made with --orgs)')
@click.option('--project', '-p', help='Project to work on (overrides selection made with --projects)')
def deprecate(id, org, project):
    utils.error("Not implemented yet")


@resources.command(name='fetch', help='Get payload of a resource by id')
@click.argument('id')
@click.option('--org', '-o', help='Organization to work on (overrides selection made with --orgs)')
@click.option('--project', '-p', help='Project to work on (overrides selection made with --projects)')
def fetch(id, org, project):
    utils.error("Not implemented yet")
