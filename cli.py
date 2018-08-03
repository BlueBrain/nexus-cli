import click
import os
import json
from pathlib import Path
from login import commands as login
from upload import commands as upload
from deployment import commands as deployment


def get_cli_config_dir():
    """Returns absolute path of CLI config directory, creates it if not found."""
    home = str(Path.home())
    cfg_dir = home + '/.nexus-cli'
    if not os.path.exists(cfg_dir):
        print("Creating CLI config directory: " + cfg_dir)
        os.makedirs(cfg_dir)
    cfg_file = cfg_dir + '/config.json'


    return cfg_dir


def get_cli_config():
    """Load CLI config as a dictionary if it exists, if not, return an empty dictionary."""
    cfg_file = get_cli_config_dir() + '/config.json'
    data = {}
    if not os.path.isfile(cfg_file):
        save_cli_config(data)
    else:
        with open(cfg_file, 'r') as fp:
            data = json.load(fp)

    return data


def save_cli_config(dict_cfg):
    """Save the given dictionary in the CLI config directory."""
    cfg_file = get_cli_config_dir() + '/config.json'
    with open(cfg_file, 'w') as fp:
        json.dump(dict_cfg, fp, sort_keys=True, indent=4)


@click.group()
def entry_point():
    """CLI entry point to all commands."""
    pass


entry_point.add_command(deployment.deployment)
entry_point.add_command(login.login)
entry_point.add_command(upload.upload)

if __name__ == "__main__":
    entry_point()