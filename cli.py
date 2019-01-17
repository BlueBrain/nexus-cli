import click

from profiles import commands as profiles
from login import commands as login
from tokens import commands as token


@click.group()
def entry_point():
    """Nexus CLI"""
    pass


entry_point.add_command(profiles.profiles)
entry_point.add_command(login.login)
entry_point.add_command(token.token)


if __name__ == "__main__":
    entry_point()
