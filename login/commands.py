import click
import getpass
from keycloak import KeycloakOpenID

import cli
from utils import error, success


def print_time(seconds):
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s%dd%dh%dm%ds' % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return '%s%dh%dm%ds' % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return '%s%dm%ds' % (sign_string, minutes, seconds)
    else:
        return '%s%ds' % (sign_string, seconds)


@click.command()
@click.option('--nexus_url', '-n', help='URL of the nexus deployment you are trying to log into')
@click.option('--user', '-u', help='username to log you in as')
def login(nexus_url, user):
    """Log the user into a deployment of Nexus."""
    click.echo("login.login")

    config = cli.get_cli_config()
    active_deployment_cfg = None
    for key in config.keys():
        if 'selected' in config[key]:
            active_deployment_cfg = config[key]
    if active_deployment_cfg is None:
        error("You must select a deployment prior to login.")

    if user is None or user == '':
        user = input("Username:")

    auth_server = KeycloakOpenID(server_url="https://bbpteam.epfl.ch/auth/",
                                    realm_name='BBP',
                                    client_id='bbp-nexus-production',
                                    client_secret_key='3feeed86-b6d6-4d87-b825-a792c28780b8')

    password = getpass.getpass('Password:')
    token = auth_server.token(username=user, password=password)
    userinfo = auth_server.userinfo(token['access_token'])

    # store token in user directory (.nexus-cli/)
    if 'expires_in' in token:
        print("Token is valid for %s" % print_time(token['expires_in']))
    active_deployment_cfg['token'] = token
    cli.save_cli_config(config)