import click
from blessings import Terminal
from datetime import datetime
import jwt

import config_utils
import utils


t = Terminal()


def is_access_token_valid():
    access_token = config_utils.get_access_token()
    decoded = jwt.decode(access_token, verify=False)
    expiry_timestamp = decoded['exp']
    expiry_date = datetime.fromtimestamp(expiry_timestamp)
    _now = datetime.now()
    return expiry_date > _now


def get_token_remaining_time_valid_in_seconds():
    access_token = config_utils.get_access_token()
    decoded = jwt.decode(access_token, verify=False)
    expiry_timestamp = decoded['exp']
    now_ts = int(datetime.now().strftime("%s"))
    return abs(now_ts - expiry_timestamp)


def print_token(token_encoded, decoded=False):
    if decoded:
        t = jwt.decode(token_encoded, verify=False)
        utils.print_json(t, colorize=True)
    else:
        print(token_encoded)



@click.command()
@click.option('--decode', '-d', default=False, is_flag=True, help='print decoded tokens')
def tokens(decode):
    """Information about tokens."""
    deployment_name, config = config_utils.get_selected_deployment_config()
    print("Deployment: %s" % t.yellow(deployment_name))
    if 'token' not in config:
        print(t.red("You must first login to view your token."))
    else:
        exp_info = utils.print_time(get_token_remaining_time_valid_in_seconds())
        if is_access_token_valid():
            print(t.green("Token is valid (expiry in %s)" % exp_info))
        else:
            print(t.red("Token expired %s ago" % exp_info))

        tokens = config['token']
        if 'access_token' in tokens:
            print(t.yellow('\nAccess-Token:'))
            print_token(tokens['access_token'], decoded=decode)

        if 'id_token' in tokens:
            print(t.yellow('\nId-Token:'))
            print_token(tokens['id_token'], decoded=decode)

        if 'refresh_token' in tokens:
            print(t.yellow('\nRefresh-Token:'))
            print_token(tokens['refresh_token'], decoded=decode)

        userinfo = config['userinfo']
        print("\nUser:")
        print("\tId: %s" % userinfo['sub'])
        print("\tFamily name: %s" % userinfo['family_name'])
        print("\tGiven name: %s" % userinfo['given_name'])
        print("\tEmail: %s" % userinfo['email'])
        print("\tPreferred username: %s" % userinfo['preferred_username'])
        groups_ = userinfo['groups']
        print("\tGroups (%d):" % len(groups_))
        for g in groups_:
            print("\t\t"+g)


