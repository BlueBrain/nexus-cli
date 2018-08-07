import click
import getpass
from keycloak import KeycloakOpenID
from blessings import Terminal

import cli
from utils import error, success

t = Terminal()


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
@click.option('--user', '-u', help='username to log you in as')
@click.option('--show-token', '-t', is_flag=True, help='Show token acquired upon successful login')
@click.option('--show-groups', '-g', is_flag=True, help='Show groups the user belongs to upon successful login')
def login(user, show_token, show_groups):
    """Log the user into a deployment of Nexus."""
    config = cli.get_cli_config()
    c = cli.get_selected_deployment_config()
    if c is None:
        error("You must select a deployment using `deployment --select` prior to running this command.")
    active_deployment_cfg = c[1]

    if user is None or user == '':
        user = input("Username:")

    auth_server = KeycloakOpenID(server_url="https://bbpteam.epfl.ch/auth/",
                                 realm_name='BBP',
                                 client_id='bbp-nexus-production',
                                 client_secret_key='3feeed86-b6d6-4d87-b825-a792c28780b8')

    password = getpass.getpass('Password:')
    try:
        token = auth_server.token(username=user, password=password)
    except Exception as e:
        error("Login failed: {0}".format(e))

    userinfo = auth_server.userinfo(token['access_token'])

    print(t.green("Login successful"))
    if 'expires_in' in token:
        print("Token is valid for %s" % print_time(token['expires_in']))
    active_deployment_cfg['token'] = token
    cli.save_cli_config(config)

    if show_token is True:
        if token is None:
            token = active_deployment_cfg['token']
        print("\nAccess-Token:")
        print(token['access_token'])

    if show_groups is True:
        if userinfo is not None:
            groups = userinfo['groups']
            print("\nGroups (" + str(len(groups)) + "):")
            for g in groups:
                print(g)

