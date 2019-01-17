import click

from profiles import commands as profiles
from login import commands as login
from tokens import commands as token
from organizations import commands as organizations
from projects import commands as projects
from resources import commands as resources


@click.group()
def entry_point():
    """Nexus CLI"""
    pass


entry_point.add_command(profiles.profiles)
entry_point.add_command(login.login)
entry_point.add_command(token.token)
entry_point.add_command(organizations.organizations)
entry_point.add_command(projects.projects)
entry_point.add_command(resources.resources)


if __name__ == "__main__":
    entry_point()
