import click
import requests
import json
from blessings import Terminal
from prettytable import PrettyTable

import config_utils
import nexus_utils
import utils

t = Terminal()


@click.command()
@click.option('list_', '--list', '-l', is_flag=True, help='List all nexus registered contexts in selected deployment')
@click.option('--organization', '-o', help='The organisation for which to list schemas')
@click.option('--domain', '-d', help='The domain for which to list schemas')
@click.option('--public-only', '-p', is_flag=True, default=False, help='List only public datasets (i.e. no authentication)')
@click.option('--show-raw', '-r', is_flag=True, default=False, help='Show raw data coming from the ACL service')
def acls(list_, organization, domain, public_only, show_raw):
    """Manage Nexus ACLs."""
    c = config_utils.get_selected_deployment_config()
    if c is None:
        utils.error("You must select a deployment using `deployment --select` prior to running this command.")
    cfg_name = c[0]
    config = c[1]

    if list_ is True:
        column_name = 'Context (' + cfg_name + ')'
        table = PrettyTable([column_name])
        table.align[column_name] = "l"

        if public_only:
            print("Limiting results to publicly accessible records")
            authenticate = False
        else:
            authenticate = True

        data_url = config['url'] + '/v0/acls/kg/*/*?self=false&parents=true'
        data = nexus_utils.get_by_id(data_url, authenticate=authenticate)

        if show_raw:
            utils.print_json(data, colorize=True)

        acl = data['acl']
        acl_by_path = {}
        for e in acl:
            path = e['path']
            if path not in acl_by_path:
                acl_by_path[path] = []
            del(e['path'])

            values = list(filter(None, path.split('/')))
            skip = False
            if organization is not None:
                if len(values) < 2:
                    skip = True
                else:
                    if values[1] != organization:
                        skip = True

            if domain is not None:
                if len(values) < 3:
                    skip = True
                else:
                    if values[2] != domain:
                        skip = True

            if not skip:
                acl_by_path[path].append(e)

        for path in acl_by_path.keys():
            entries = acl_by_path[path]
            if len(entries) == 0:
                continue

            print(t.yellow(path))
            columns = ['Type', 'Realm', 'Identity', 'Permissions']
            table = PrettyTable(columns)
            table.align[columns[0]] = "l"
            table.align[columns[1]] = "l"
            table.align[columns[2]] = "l"
            table.align[columns[3]] = "l"

            for e in entries:
                identity = e['identity']
                permissions = e['permissions']
                permissions.sort()

                id_type = identity['@type']
                realm = ''
                if 'realm' in identity:
                    realm = identity['realm']
                id_name = None
                if id_type == 'UserRef':
                    id_name = identity['sub']
                elif id_type == 'GroupRef':
                    id_name = identity['group']
                elif id_type == 'Anonymous':
                    id_name = ''
                elif id_type == 'Authenticated':
                    id_name = ''
                else:
                    print(t.red(("Unsupported Identity Type: " + id_type)))

                perms = "\n".join(permissions)
                table.add_row([id_type, realm, id_name, perms])


            print(table)
            print()