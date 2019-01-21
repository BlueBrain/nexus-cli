import os
import json
from pathlib import Path

import utils


def get_cli_config_dir():
    """Returns absolute path of CLI config directory, creates it if not found."""
    home = str(Path.home())
    cfg_dir = home + '/.nexus-cli'
    if not os.path.exists(cfg_dir):
        print("Creating CLI config directory: " + cfg_dir)
        os.makedirs(cfg_dir)
    return cfg_dir


def get_cli_config_file():
    """Returns the path of the CLI config file."""
    return get_cli_config_dir() + '/config.json'


def get_cli_config():
    """Load CLI config as a dictionary if it exists, if not, return an empty dictionary."""
    cfg_file = get_cli_config_file()
    data = {}
    if not os.path.isfile(cfg_file):
        save_cli_config(data)
    else:
        with open(cfg_file, 'r') as fp:
            data = json.load(fp)
    return data


def save_cli_config(dict_cfg):
    """Save the given dictionary in the CLI config directory."""
    cfg_file = get_cli_config_file()
    with open(cfg_file, 'w') as fp:
        json.dump(dict_cfg, fp, sort_keys=True, indent=4)


def get_access_token():
    name, cfg = get_selected_deployment_config()
    if cfg is None:
        utils.error("Failed to get selected config.")
    token = None
    if 'tokens' in cfg:
        token = cfg['tokens']['access_token']
    return token


def get_selected_deployment_config(config=None):
    """Searches for currently selected nexus deployment.
       Returns a tuple containing (name, config) or None if not found.
    """
    if config is None:
        # load from disk if not given
        config = get_cli_config()
    for key in config.keys():
        if 'selected' in config[key] and config[key]['selected'] is True:
            return key, config[key]
    return None, None
