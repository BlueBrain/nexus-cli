import click
from prettytable import PrettyTable
import jwt
from datetime import datetime

from nexuscli.cli import cli
from nexuscli import utils
from nexuscli.config import _SELECTED_KEY_, _URL_KEY_


@cli.group()
def profiles():
    """Profiles management operations"""


@profiles.command(name='list', help='List all profiles')
def list_profiles():
    config = utils.get_cli_config()
    table = PrettyTable(['Profile', 'Selected', 'URL', 'Token'])
    table.align["Profile"] = "l"
    table.align["URL"] = "l"
    for key in config.keys():
        selected = ""
        if 'selected' in config[key] and config[key]['selected'] is True:
            selected = "Yes"
        token = 'None'
        if 'token' in config[key]:
            decoded = jwt.decode(config[key]['token'], verify=False)
            expiry_utc = datetime.utcfromtimestamp(decoded['exp'])
            token = "Expiry: %s" % utils.datetime_from_utc_to_local(expiry_utc)
        table.add_row([key, selected, config[key]['url'], token])
    print(table)


@profiles.command(name='create', help='Create a new profile')
@click.argument('profile')
@click.argument('url')
def create(profile, url):
    config = utils.get_cli_config()
    if profile in config and 'url' in config[profile]:
        utils.error("This deployment already exist (%s) with url: %s" % (create, config[create]))
    url = validate_nexus_url(url)
    config[profile] = {_URL_KEY_: url}
    if len(config) == 1:
        config[profile][_SELECTED_KEY_] = True
    utils.save_cli_config(config)
    print("Profile created.")


def validate_nexus_url(url):
    try:
        import nexussdk as nxs
        url = url.rstrip("/")
        nxs.config.set_environment(url)
        nxs.identities.fetch()
    except nxs.HTTPError as e:
        utils.error("Provided URL isn't valid or the service isn't responding: %s" % url)
    return url


@profiles.command(name='select', help='Select a profile for subsequent CLI calls')
@click.argument('profile')
def select(profile):
    config = utils.get_cli_config()
    if profile not in config:
        utils.error("Could not find profile '%s' in CLI config" % delete)
    for key in config.keys():
        if _SELECTED_KEY_ in config[key] and key != select:
            config[key].pop(_SELECTED_KEY_, None)
    config[profile][_SELECTED_KEY_] = True
    utils.save_cli_config(config)
    print("Selected profile: %s" % profile)


@profiles.command(name='current', help='Show current selected profile')
def current():
    config = utils.get_cli_config()
    found = False
    for key in config.keys():
        if _SELECTED_KEY_ in config[key] and key != select:
            print(key)
            found = True
    if not found:
        print("No profile selected.")


@profiles.command(name='delete', help='Delete a profile')
@click.argument('profile')
def delete(profile):
    config = utils.get_cli_config()
    if profile not in config:
        utils.error("Could not find profile '%s' in CLI config" % profile)
    config.pop(profile, None)
    utils.save_cli_config(config)
    print("Profile deleted.")
