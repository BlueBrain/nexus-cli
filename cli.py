import click

from login import commands as login
from logout import commands as logout
from upload import commands as upload
from deployment import commands as deployment
from contexts import commands as contexts
from organizations import commands as organizations
from domains import commands as domains
from schemas import commands as schemas


@click.group()
def entry_point():
    """Nexus CLI"""
    pass


entry_point.add_command(deployment.deployment)
entry_point.add_command(login.login)
entry_point.add_command(logout.logout)
entry_point.add_command(upload.upload)
entry_point.add_command(contexts.contexts)
entry_point.add_command(organizations.organizations)
entry_point.add_command(domains.domains)
entry_point.add_command(schemas.schemas)


if __name__ == "__main__":
    entry_point()