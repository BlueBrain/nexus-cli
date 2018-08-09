import click

from login import commands as login
from logout import commands as logout
from upload import commands as upload
from deployments import commands as deployments
from contexts import commands as contexts
from organizations import commands as organizations
from domains import commands as domains
from schemas import commands as schemas
from search import commands as search
from get import commands as get


@click.group()
def entry_point():
    """Nexus CLI"""
    pass


entry_point.add_command(deployments.deployments)
entry_point.add_command(login.login)
entry_point.add_command(logout.logout)
entry_point.add_command(upload.upload)
entry_point.add_command(contexts.contexts)
entry_point.add_command(organizations.organizations)
entry_point.add_command(domains.domains)
entry_point.add_command(schemas.schemas)
entry_point.add_command(schemas.schemas)
entry_point.add_command(search.search)
entry_point.add_command(get.get)


if __name__ == "__main__":
    entry_point()