import click


@click.group()
def cli():
    pass


import profiles
import auth
import orgs
import projects
import resources
