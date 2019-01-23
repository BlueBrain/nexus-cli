import click
import jwt
import webbrowser
from datetime import datetime

import nexuscli.config
from nexuscli.cli import cli
from nexuscli import utils
from nexuscli.config import _TOKEN_KEY_, _URL_KEY_


@cli.group()
def auth():
    """Authentication operations"""


@auth.command('login')
def open_nexus_web():
    # TODO investigate more user friendly ways to login
    # TODO e.g. https://github.com/burnash/gspread/wiki/How-to-get-OAuth-access-token-in-console%3F
    base_url = utils.get_selected_deployment_config()[1][_URL_KEY_]
    print("A browser window will now open, please login, copy your token and use the auth set-token command "
          "to store it in the CLI")
    input("Press ENTER to continue...")
    webbrowser.open_new(base_url.strip("/v1") + "/web")


@auth.command('set-token', help='Registers the user token in the current profile')
@click.argument('token')
def set_token(token):
    """Registers the user token in the current profile."""
    config = utils.get_cli_config()

    selected_profile = None
    for key in config.keys():
        if nexuscli.config._SELECTED_KEY_ in config[key] and config[key][nexuscli.config._SELECTED_KEY_] is True:
            selected_profile = key
            break
    if selected_profile is None:
        utils.error("No profile selected, please use the profiles select to do that.")

    try:
        jwt.decode(token, verify=False)
    except jwt.exceptions.DecodeError:
        utils.error("Provided tokens could not be decoded. Please provide a valid tokens.")

    config[selected_profile][_TOKEN_KEY_] = token
    utils.save_cli_config(config)


@auth.command('view-token', help='View token')
def view_token():
    """Show token for current profile."""
    config = utils.get_cli_config()

    _token = None
    selected = None
    for key in config.keys():
        if nexuscli.config._SELECTED_KEY_ in config[key] and config[key][nexuscli.config._SELECTED_KEY_] is True:
            selected = key
            if _TOKEN_KEY_ in config[key]:
                _token = config[key][_TOKEN_KEY_]
                print(_token)

                decoded = jwt.decode(_token, verify=False)
                print("\nDecoded token:")
                utils.print_json(decoded, colorize=True)
                expiry_utc = datetime.utcfromtimestamp(decoded['exp'])
                expires_in = expiry_utc.timestamp() - datetime.now().timestamp()
                if expires_in > 0:
                    when = "in %s" % utils.print_time(expires_in)
                    message_color = 'green'
                else:
                    when = "%s ago" % utils.print_time(abs(expires_in))
                    message_color = 'red'
                msg = "\nExpiry: %s (%s)" % (utils.datetime_from_utc_to_local(expiry_utc), when)
                click.echo(click.style(msg, fg=message_color))

    if _token is None:
        if selected is None:
            utils.error("You haven't selected a profile.")
        else:
            utils.error('No tokens in selected profile: %s' % selected)
