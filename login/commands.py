import click
from blessings import Terminal
import requests
import jwt
import config_utils
import utils


@click.command()
@click.option('--token', '-t', help='Authentication token')
def login(token):
    """Log the user into a deployment of Nexus."""
    config = config_utils.get_cli_config()

    selected_profile = None
    for key in config.keys():
        if 'selected' in config[key] and config[key]['selected'] is True:
            selected_profile = key
            break
    if selected_profile is None:
        utils.error("No profile selected, please use the profiles --select to do that.")

    try:
        jwt.decode(token, verify=False)
    except jwt.exceptions.DecodeError:
        utils.error("Provided tokens could not be decoded. Please provide a valid tokens.")

    config[selected_profile]['token'] = token
    config_utils.save_cli_config(config)
