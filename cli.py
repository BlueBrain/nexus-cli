import click
import os
import json
from pathlib import Path
from keycloak import KeycloakOpenID

from login import commands as login
from logout import commands as logout
from upload import commands as upload
from deployment import commands as deployment
from contexts import commands as contexts
from organizations import commands as organizations
from domains import commands as domains
from schemas import commands as schemas


def get_cli_config_dir():
    """Returns absolute path of CLI config directory, creates it if not found."""
    home = str(Path.home())
    cfg_dir = home + '/.nexus-cli'
    if not os.path.exists(cfg_dir):
        print("Creating CLI config directory: " + cfg_dir)
        os.makedirs(cfg_dir)
    cfg_file = cfg_dir + '/config.json'


    return cfg_dir


def get_cli_config():
    """Load CLI config as a dictionary if it exists, if not, return an empty dictionary."""
    cfg_file = get_cli_config_dir() + '/config.json'
    data = {}
    if not os.path.isfile(cfg_file):
        save_cli_config(data)
    else:
        with open(cfg_file, 'r') as fp:
            data = json.load(fp)

    return data


def save_cli_config(dict_cfg):
    """Save the given dictionary in the CLI config directory."""
    cfg_file = get_cli_config_dir() + '/config.json'
    with open(cfg_file, 'w') as fp:
        json.dump(dict_cfg, fp, sort_keys=True, indent=4)

def get_access_token():
    cfg = get_selected_deployment_config()
    token = None
    if 'token' in cfg:
        token = cfg['token']['access_token']
    return token

def get_selected_deployment_config(config=None):
    """Searches for currently selected nexus deployment.
       Returns a tuple containing (name, config) or None if not found.
    """
    if config is None:
        # load from disk if not given
        config = get_cli_config()
    for key in config.keys():
        if 'selected' in config[key] and config[key]['selected'] is True:
            return key, config[key]
    return None

def get_auth_server():
    return KeycloakOpenID(server_url="https://bbpteam.epfl.ch/auth/",
                          realm_name='BBP',
                          client_id='bbp-nexus-production',
                          client_secret_key='3feeed86-b6d6-4d87-b825-a792c28780b8')


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