import getpass
from datetime import datetime

import click
import jwt
import nexussdk as nxs
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from prettytable import PrettyTable

import nexuscli.config
from nexuscli import utils
from nexuscli.cli import cli
from nexuscli.config import TOKEN_KEY, URL_KEY


@cli.group()
def auth():
    """Authentication operations"""


@auth.command('login', help='Login interactively against a specific realm, with username, password and client ID.')
@click.option('--realm-label', '-r', default=None, help='The realm label')
def interactive_login(realm_label):
    """Logs in interactively."""
    env, config = utils.get_selected_deployment_config()
    if config is not None and URL_KEY in config:
        nxs.config.set_environment(config[URL_KEY])
    else:
        utils.error("You must first select a profile using the 'profiles' command")

    issuer = ''
    if realm_label:
        try:
            response = nxs.realms.fetch(realm_label)
            issuer = response['_issuer']
        except nxs.HTTPError as e:
            print(e.response.json())
            utils.error(str(e))
    else:
        realm = utils.get_default_realm()
        if realm is None:
            realm = _select_realm()
            issuer = realm['_issuer']
            label = realm['_label']
            print("Saving realm '%s' in your profile" % realm['_label'])
            utils.set_default_realm(label, issuer)
        else:
            print("Using default realm '%s' set in your profile. Use --realm to override." % realm['_label'])

    default_client_id = utils.get_default_client_id()
    client_id = input("Please enter the client ID [%s]: " % default_client_id)
    if not client_id:
        client_id = default_client_id
    utils.set_default_client_id(client_id)

    detected_user = getpass.getuser()
    username = input("Username [%s]: " % detected_user)
    if not username:
        username = detected_user
    password = getpass.getpass()
    try:
        url, name = issuer.split("realms/")
        keycloak_openid = KeycloakOpenID(server_url=url, client_id=client_id, realm_name=name, verify=True)
        response = keycloak_openid.token(username, password)
        token = response['access_token']
        _set_token(token)
        utils.success("Authentication successful. Use 'view-token' to show your credentials.")
    except KeycloakError as e:
        utils.error("Authentication failed: %s" % e)


def _select_realm():
    try:
        print("Listing available realms...")
        response = nxs.realms.list()
        table = PrettyTable(['Realm', 'Label', 'Name', 'Issuer'])
        table.align["Issuer"] = "l"
        for i, r in enumerate(response["_results"], start=1):
            table.add_row([i, r["_label"], r["name"], r["_issuer"]])

        print(table)
        number = int(input("Please select realm number: "))
        realm = response["_results"][number - 1]
        return realm
    except nxs.HTTPError as e:
        print(e.response.json())
        utils.error(str(e))
    except IndexError:
        utils.error("Invalid input.")
    except ValueError:
        utils.error("Invalid input.")


@auth.command('set-token', help='Registers the user token in the current profile')
@click.argument('token')
def set_token(token):
    """Registers the user token in the current profile."""
    _set_token(token)


def _set_token(token):
    config = utils.get_cli_config()

    selected_profile = None
    for key in config.keys():
        if nexuscli.config.SELECTED_KEY in config[key] and config[key][nexuscli.config.SELECTED_KEY] is True:
            selected_profile = key
            break
    if selected_profile is None:
        utils.error("No profile selected, please use the profiles select to do that.")

    try:
        jwt.decode(token, verify=False)
    except jwt.exceptions.DecodeError:
        utils.error("Provided tokens could not be decoded. Please provide a valid tokens.")

    config[selected_profile][TOKEN_KEY] = token
    utils.save_cli_config(config)


@auth.command('view-token', help='View token')
def view_token():
    """Show token for current profile."""
    config = utils.get_cli_config()

    _token = None
    selected = None
    for key in config.keys():
        if nexuscli.config.SELECTED_KEY in config[key] and config[key][nexuscli.config.SELECTED_KEY] is True:
            selected = key
            if TOKEN_KEY in config[key]:
                _token = config[key][TOKEN_KEY]
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
