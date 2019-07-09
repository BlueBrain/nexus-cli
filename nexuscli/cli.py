import click
import atexit
from colorama import init, deinit

init(autoreset=True)
atexit.register(deinit)

@click.group()
@click.version_option()
def cli():
    pass


from nexuscli import profiles, auth, orgs, projects, resources, views, schemas, acls, helpers, realms, resolvers, storages

