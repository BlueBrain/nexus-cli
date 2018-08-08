import click
import getpass
from keycloak import KeycloakOpenID
from blessings import Terminal
import json
from datetime import datetime
import time
import jwt

import cli
from utils import error, success

t = Terminal()


def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset


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
    c = cli.get_selected_deployment_config(config)
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
        access_token = jwt.decode(token['access_token'], verify=False)
        expiry_utc = datetime.utcfromtimestamp(access_token['exp'])
        print("Token is valid for %s, expiry at %s" % (print_time(token['expires_in']),
                                                       datetime_from_utc_to_local(expiry_utc)))

    active_deployment_cfg['token'] = token
    active_deployment_cfg['userinfo'] = userinfo
    cli.save_cli_config(config)

    if show_token is True:
        if token is None:
            token = active_deployment_cfg['token']
        print(t.yellow("\nAccess-Token:"))
        print(json.dumps(jwt.decode(token['access_token'], verify=False), indent=2))
        print(t.yellow("\nAccess-Token (encoded):"))
        print(token['access_token'])
        print(t.yellow("\nID-Token:"))
        print(json.dumps(jwt.decode(token['id_token'], verify=False), indent=2))
        print(t.yellow("\nRefresh-Token:"))
        print(json.dumps(jwt.decode(token['refresh_token'], verify=False), indent=2))

    if show_groups is True:
        if userinfo is None:
            userinfo = active_deployment_cfg['userinfo']

        groups = userinfo['groups']
        print(t.yellow("\nGroups (" + str(len(groups)) + "):"))
        for g in groups:
            print(g)

