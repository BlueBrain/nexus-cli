import click
from blessings import Terminal
import requests
import jwt
import config_utils
import utils


@click.command()
@click.option('--profile', '-p', help='Named profile of this configuration')
@click.option('--tokens', '-t', help='Authentication tokens')
@click.option('--verbose', '-v', is_flag=True, default=False, help='enable verbose display')
def login(profile, token, verbose):
    """Log the user into a deployment of Nexus."""
    config = config_utils.get_cli_config()
    if profile not in config:
        utils.error("Profile '%s' does not exist." % profile)

    try:
        decoded = jwt.decode(token, verify=False)
        if verbose:
            print("Decoded tokens:")
            utils.print_json(decoded, colorize=True)
    except jwt.exceptions.DecodeError:
        utils.error("Provided tokens could not be decoded. Please provide a valid tokens.")

    config[profile]['tokens'] = token
    config_utils.save_cli_config(config)
