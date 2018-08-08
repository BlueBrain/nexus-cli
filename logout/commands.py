import click
from blessings import Terminal

import config_utils
import auth_utils
import utils


t = Terminal()


@click.command()
def logout():
    """Logout from currently logged in deployment."""
    # click.echo("logout")
    config = config_utils.get_cli_config()
    deployment_name, selected_deployment_config = config_utils.get_selected_deployment_config(config)
    if selected_deployment_config is None:
        utils.error("You haven't selected a nexus deployment.")

    if 'token' not in selected_deployment_config:
        utils.error("You do not appear to have logged into " + deployment_name)

    # invalidate token with auth server
    auth_server = auth_utils.get_auth_server()
    refresh_token = selected_deployment_config['token']['refresh_token']
    auth_server.logout(refresh_token)

    # clear local auth data
    del(selected_deployment_config['token'])
    if 'userinfo' in selected_deployment_config:
        del (selected_deployment_config['userinfo'])
    config_utils.save_cli_config(config)

    print(t.green("Logout successful"))
