import click
import jwt
import webbrowser
from datetime import datetime

from nexuscli.cli import cli
from nexuscli import utils


@cli.group()
def auth():
    """Authentication operations"""


@auth.command('login')
def open_nexus_web():
    base_url = utils.get_selected_deployment_config()[1]['url']
    print("A browser window will now open, please login, copy your token and use the auth --token command "
          "to store it in the CLI")
    input("Press ENTER to continue...")
    webbrowser.open_new(base_url + "/web")


@auth.command('set-token', help='Registers the user token in the current profile')
@click.argument('token')
def set_token(token):
    """Registers the user token in the current profile."""
    config = utils.get_cli_config()

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
    utils.save_cli_config(config)


@auth.command('view-token', help='View token')
def view_token():
    """Show token for current profile."""
    config = utils.get_cli_config()

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
                expires_in = expiry_utc.timestamp() - datetime.now().timestamp()
                when = ""
                if expires_in > 0:
                    when = "in %s" % utils.print_time(expires_in)
                else:
                    when = "%s ago" % utils.print_time(abs(expires_in))
                print("\nExpiry: %s (%s)" % (utils.datetime_from_utc_to_local(expiry_utc), when))

    if _token is None:
        if selected is None:
            utils.error("You haven't selected a profile.")
        else:
            utils.error('No tokens in selected profile: %s' % selected)
