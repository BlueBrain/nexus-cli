import click
import utils


from cli import cli


@cli.group()
def projects():
    """Projects operations"""


@projects.command(name='create', help='Create a new project')
@click.argument('name')
@click.option('--org', '-o', help='Organization to work on (overrides selection made with --orgs)')
def create(name, org):
    utils.error("Not implemented yet")


@projects.command(name='update', help='Update a project')
@click.argument('id')
@click.option('--org', '-o', help='Organization to work on (overrides selection made with --orgs)')
@click.option('--data', '-d', help='Payload to replace it with')
def update(id, org, data):
    utils.error("Not implemented yet")


@projects.command(name='list', help='List all projects')
@click.option('--org', '-o', help='Organization to work on (overrides selection made with --orgs)')
def _list(org):
    utils.error("Not implemented yet")


@projects.command(name='deprecate', help='Deprecate an project')
@click.argument('name')
@click.option('--org', '-o', help='Organization to work on (overrides selection made with --orgs)')
def deprecate(name, org):
    utils.error("Not implemented yet")


@projects.command(name='select', help='Select an project')
@click.argument('name')
@click.option('--org', '-o', help='Organization to work on (overrides selection made with --orgs)')
def select(name, org):
    utils.error("Not implemented yet")


@projects.command(name='current', help='Show currently selected project')
def current():
    utils.error("Not implemented yet")
