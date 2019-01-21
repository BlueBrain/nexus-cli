import os
import sys
from blessings import Terminal
import json
from pygments import highlight
from pygments.lexers import JsonLdLexer
from pygments.formatters import TerminalFormatter, TerminalTrueColorFormatter
import time
from datetime import datetime
from pathlib import Path

import nexussdk as nxs


t = Terminal()


def error(message):
    print(t.red(message))
    sys.exit(101)


def success(message):
    print(t.green(message))


def print_json(data, colorize=False):
    """
    Print a json payload.
    :param data: the json payload to print
    :param colorize: if true, colorize the output
    """
    json_str = json.dumps(data, indent=2)
    if colorize:
        sys.stdout.write(highlight(json_str, JsonLdLexer(), TerminalFormatter()))
        sys.stdout.flush()
    else:
        print(json_str)


def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset


def print_time(seconds):
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s%dd %dh %dm %ds' % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return '%s%dh %dm %ds' % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return '%s%dm %ds' % (sign_string, minutes, seconds)
    else:
        return '%s%ds' % (sign_string, seconds)


def get_nexus_client():
    key, cfg = get_selected_deployment_config()
    if cfg is None:
        error("You must select a profile.")
    nxs.config.set_environment(cfg["url"])
    nxs.config.set_token(cfg["token"])
    return nxs


def get_selected_deployment_base_url():
    return get_selected_deployment_config()[1]['url'] + "/v0"


def pretty_filesize(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


#######################
# CLI CONFIG

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
        error("Failed to get selected config.")
    token = None
    if 'tokens' in cfg:
        token = cfg['tokens']['access_token']
    return token


def get_selected_deployment_config(config=None):
    """Searches for currently selected nexus profile.
       Returns a tuple containing (name, config) or None if not found.
    """
    if config is None:
        # load from disk if not given
        config = get_cli_config()
    for key in config.keys():
        if 'selected' in config[key] and config[key]['selected'] is True:
            return key, config[key]
    return None, None
