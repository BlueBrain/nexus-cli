from blessings import Terminal
import json
from pygments import highlight
from pygments.lexers import JsonLdLexer
from pygments.formatters import TerminalFormatter
import time
from datetime import datetime
from pathlib import Path
import hashlib
import os
import sys
from collections import OrderedDict

import nexussdk as nxs

from nexuscli.config import _DEFAULT_ORGANISATION_KEY_, _DEFAULT_PROJECT_KEY_, _URL_KEY_, _TOKEN_KEY_, _SELECTED_KEY_


def error(message: str):
    t = Terminal()
    print(t.red(message))
    sys.exit(101)


def warn(message: str):
    t = Terminal()
    print(t.yellow(message))


def success(message: str):
    t = Terminal()
    print(t.green(message))


def print_json(data: dict, colorize: bool=False):
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


def datetime_from_utc_to_local(utc_datetime: int):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset


def print_time(seconds: int):
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
    nxs.config.set_environment(cfg[_URL_KEY_])
    if _TOKEN_KEY_ in cfg:
        nxs.config.set_token(cfg[_TOKEN_KEY_])
    else:
        warn("WARNING - you haven not set a token in your profile, use the 'auth set-token' command to do it.")
    return nxs


def pretty_filesize(num: int , suffix: str='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def remove_nexus_metadata(d: dict):
    """ Returns a copy of the provided dictionary without nexus metadata (i.e. root keys starting with '_'). """
    x = dict()
    for k in d.keys():
        if not k.startswith('_'):
            x[k] = d[k]
    return x


def generate_nexus_payload_checksum(payload: dict):
    """ Given a nexus payload, remove nexus metadata, order the keys and generate a MD5. """
    filtered = remove_nexus_metadata(payload)
    data_ordered = OrderedDict(sorted(filtered.items()))
    return hashlib.md5(json.dumps(data_ordered, indent=2).encode('utf-8')).hexdigest()


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


def save_cli_config(dict_cfg: dict):
    """Save the given dictionary in the CLI config directory."""
    cfg_file = get_cli_config_file()
    with open(cfg_file, 'w') as fp:
        json.dump(dict_cfg, fp, sort_keys=True, indent=4)


def get_selected_deployment_config(config: dict=None):
    """Searches for currently selected nexus profile.
       Returns a tuple containing (name, config) or None if not found.
    """
    if config is None:
        # load from disk if not given
        config = get_cli_config()
    for key in config.keys():
        if _SELECTED_KEY_ in config[key] and config[key][_SELECTED_KEY_] is True:
            return key, config[key]
    return None, None


def get_default_organization():
    config = get_cli_config()
    profile, selected_config = get_selected_deployment_config(config)
    if selected_config is None:
        error("You must first select a profile using the 'profiles' command")
    if _DEFAULT_ORGANISATION_KEY_ in selected_config:
        return selected_config[_DEFAULT_ORGANISATION_KEY_]
    else:
        return None


def set_default_organization(org_label: str):
    config = get_cli_config()
    profile, selected_config = get_selected_deployment_config(config)
    if selected_config is None:
        error("You must first select a profile using the 'profiles' command")
    config[profile][_DEFAULT_ORGANISATION_KEY_] = org_label
    save_cli_config(config)


def get_organization_label(given_org_label: str):
    if given_org_label is None:
        given_org_label = get_default_organization()
        if given_org_label is None:
            error("No organization specified, either set default using the 'orgs' command or pass it as a "
                  "parameter using --org")
    return given_org_label


def get_default_project():
    config = get_cli_config()
    profile, selected_config = get_selected_deployment_config(config)
    if selected_config is None:
        error("You must first select a profile using the 'profiles' command")
    if _DEFAULT_PROJECT_KEY_ in selected_config:
        return selected_config[_DEFAULT_PROJECT_KEY_]
    else:
        return None


def set_default_project(project_label: str):
    config = get_cli_config()
    profile, selected_config = get_selected_deployment_config(config)
    if selected_config is None:
        error("You must first select a profile using the 'profiles' command")
    config[profile][_DEFAULT_PROJECT_KEY_] = project_label
    save_cli_config(config)


def get_project_label(given_project_label: str):
    if given_project_label is None:
        given_project_label = get_default_project()
        if given_project_label is None:
            error("No project specified, either set default using the 'projects' command or pass it as a "
                  "parameter using --project")
    return given_project_label
