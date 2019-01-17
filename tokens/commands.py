import click
from blessings import Terminal
from datetime import datetime
import jwt
import config_utils
import utils


@click.command()
def token():
    """Show token for current profile."""
    config = config_utils.get_cli_config()

    _token = None
    selected = None
    for key in config.keys():
        if 'selected' in config[key] and config[key]['selected'] is True:
            selected = key
            if 'token' in config[key]:
                _token = config[key]['token']
                print(_token)

                decoded = jwt.decode(_token, verify=False)
                print("\nDecoded token:")
                utils.print_json(decoded, colorize=True)
                expiry_utc = datetime.utcfromtimestamp(decoded['exp'])
                print("\nExpiry: %s" % utils.datetime_from_utc_to_local(expiry_utc))

    if _token is None:
        if selected is None:
            utils.error("You haven't selected a profile.")
        else:
            utils.error('No tokens in selected profile: %s' % selected)
