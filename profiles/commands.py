import click
from prettytable import PrettyTable
import jwt
from datetime import datetime
import config_utils
import utils


@click.command()
@click.option('--add', '-a', help='Add a new profile')
@click.option('--url', '-u', help='URL of the Nexus deployment')
@click.option('--select', '-s', help='Select a profile for subsequent CLI calls')
@click.option('--remove', '-r', help='Remove a profile')
def profiles(add, url, select, remove):
    """Management of profiles."""
    config = config_utils.get_cli_config()

    if add is None and remove is None and select is None:
        # list all profiles
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

    if add is not None:
        if remove is not None or select is not None:
            utils.error("Only one sub-command can be run: add, remove, select")
        if url is None:
            utils.error("You must have a URL (--url) in order to add a profile")
        if add in config and 'url' in config[add]:
            utils.error("This deployment already exist (%s) with url: %s" % (add, config[add]))
        # TODO Validate URL
        # data_url = url.rstrip("/") + '/v1'
        # r = requests.get(data_url)
        # if r.status_code != 200:
        #     utils.error("Failed to get entity count from URL: " + data_url +
        #                 '\nRequest status: ' + str(r.status_code))
        config[add] = {'url': url.rstrip("/")}

    if remove is not None:
        if add is not None or select is not None:
            utils.error("Only one sub-command can be run: add, remove, select")
        if remove not in config:
            utils.error("Could not find profile '%s' in CLI config" % remove)
        config.pop(remove, None)
        config_utils.save_cli_config(config)

    if select is not None:
        if add is not None or remove is not None:
            utils.error("Only one sub-command can be run: add, remove, select")
        if select not in config:
            utils.error("Could not find profile '%s' in CLI config" % remove)
        for key in config.keys():
            if 'selected' in config[key] and key != select:
                config[key].pop('selected', None)
                print("deployment '%s' was unselected" % key)
        config[select]['selected'] = True

    config_utils.save_cli_config(config)
