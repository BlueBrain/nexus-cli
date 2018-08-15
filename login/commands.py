import click
import getpass
from blessings import Terminal
from datetime import datetime
import requests

import jwt

import config_utils
import utils


t = Terminal()


@click.command()
@click.option('--user', '-u', help='username to log you in as')
def login(user):
    """Log the user into a deployment of Nexus."""
    config = config_utils.get_cli_config()
    c = config_utils.get_selected_deployment_config(config)
    if c is None:
        utils.error("You must select a deployment using `deployment --select` prior to running this command.")
    active_deployment_cfg = c[1]

    if user is None or user == '':
        user = input("Username:")

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = "https://bbpteam.epfl.ch/auth/realms/BBP/protocol/openid-connect/token"
    password = getpass.getpass('Password:')
    payload = "grant_type=password&username=%s&password=%s&client_id=bbp-nexus-public&scope=nexus" % (user, password)
    r = requests.post(url, data=payload, headers=headers)
    token = r.json()
    access_token = token['access_token']
    print(t.green("Login successful"))

    url = "https://bbpteam.epfl.ch/auth/realms/BBP/protocol/openid-connect/userinfo"
    headers = {"Authorization": "Bearer " + access_token}
    r = requests.get(url, headers=headers)
    userinfo = r.json()

    if 'expires_in' in token:
        access_token = jwt.decode(token['access_token'], verify=False)
        expiry_utc = datetime.utcfromtimestamp(access_token['exp'])
        print("Token is valid for %s, expiry at %s" % (utils.print_time(token['expires_in']),
                                                       utils.datetime_from_utc_to_local(expiry_utc)))

    active_deployment_cfg['token'] = token
    active_deployment_cfg['userinfo'] = userinfo
    config_utils.save_cli_config(config)
