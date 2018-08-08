import click
from blessings import Terminal

import cli
from utils import error

t = Terminal()


@click.command()
def logout():
    """Logout from currently logged in deployment."""
    # click.echo("logout")
    config = cli.get_cli_config()
    deployment_name, selected_deployment_config = cli.get_selected_deployment_config(config)
    if selected_deployment_config is None:
        error("You haven't selected a nexus deployment.")

    if 'token' not in selected_deployment_config:
        error("You do not appear to have logged into " + deployment_name)

    # invalidate token with auth server
    auth_server = cli.get_auth_server()
    refresh_token = selected_deployment_config['token']['refresh_token']
    auth_server.logout(refresh_token)

    # clear local auth data
    del(selected_deployment_config['token'])
    if 'userinfo' in selected_deployment_config:
        del (selected_deployment_config['userinfo'])
    cli.save_cli_config(config)

    print(t.green("Logout successful"))
