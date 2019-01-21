import click
from prettytable import PrettyTable
import jwt
from datetime import datetime

from nexuscli.cli import cli
from nexuscli import utils


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
    # TODO Validate URL
    # data_url = url.rstrip("/") + '/v1'
    # r = requests.get(data_url)
    # if r.status_code != 200:
    #     utils.error("Failed to get entity count from URL: " + data_url +
    #                 '\nRequest status: ' + str(r.status_code))
    config[profile] = {'url': url.rstrip("/")}
    utils.save_cli_config(config)


@profiles.command(name='select', help='Select a profile for subsequent CLI calls')
@click.argument('profile')
def select(profile):
    config = utils.get_cli_config()

    if profile not in config:
        utils.error("Could not find profile '%s' in CLI config" % delete)
    for key in config.keys():
        if 'selected' in config[key] and key != select:
            config[key].pop('selected', None)
            print("deployment '%s' was unselected" % key)
    config[profile]['selected'] = True


@profiles.command(name='delete', help='Delete a profile')
@click.argument('profile')
def delete(profile):
    config = utils.get_cli_config()
    if profile not in config:
        utils.error("Could not find profile '%s' in CLI config" % profile)
    config.pop(profile, None)
    utils.save_cli_config(config)
