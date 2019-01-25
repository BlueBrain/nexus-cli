from typing import List, Dict

import click
from prettytable import PrettyTable

from nexuscli.cli import cli
from nexuscli import utils


_ANONYMOUS_ = {
            "@id": "http://dev.nexus.ocp.bbp.epfl.ch/v1/anonymous",
            "@type": "Anonymous"
          }

_PROJECTS_READ_ = "projects/read"


@cli.group()
def acls():
    """ACLs operations"""


@acls.command(name='list', help='List ACLs for the given <org>/<project>/<subpath>')
@click.option('_org_label', '--org', '-o', default=None,
              help='Organization to work on, use ''*'' for Any, otherwise overrides selection made via orgs command.')
@click.option('_prj_label', '--project', '-p', default=None,
              help='Project to work on, use ''*'' for Any, overrides selection made via projects command')
@click.option('--subpath', default=None, help='subpath inside an org/project')
@click.option('_ancestor', '--include-ancestor', is_flag=True, default=False, help='Include ancestor paths')
@click.option('_self', '--exclude-self', is_flag=True, default=True, help='Exclude self')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', '-p', is_flag=True, default=False, help='Colorize JSON output')
@click.option('--verbose', '-v', is_flag=True, default=False, help='Show debug info')
def _list(_org_label, _prj_label, subpath, _ancestor, _self, _json, pretty, verbose):
    if _org_label != '*':
        _org_label = utils.get_organization_label(_org_label)
    if _prj_label != '*':
        _prj_label = utils.get_project_label(_prj_label)

    nxs = utils.get_nexus_client()
    try:
        path = _org_label + '/' + _prj_label
        if subpath is not None:
            path += '/' + subpath
        if verbose:
            print("subpath: %s" % path)
            print("self: %s" % _self)
            print("ancestors: %s" % _ancestor)
        response = nxs.acls.list(subpath=path, ancestors=_ancestor, self=_self)
        if _json:
            utils.print_json(response, colorize=pretty)
        else:
            columns = ['Path', 'Identity', 'Permissions']
            table = PrettyTable(columns)
            for c in columns:
                table.align[c] = "l"
            for _acl in response["_results"]:
                for entry in _acl["acl"]:
                    i = entry["identity"]
                    _type = i["@type"]
                    printed_identity = _type
                    if _type == "User":
                        printed_identity = "%s: %s (realm: %s)" % (_type, i["subject"], i["realm"])
                    elif _type == "Group":
                        printed_identity = "%s: %s (realm: %s)" % (_type, i["group"], i["realm"])
                    elif _type == "Authenticated":
                        printed_identity = "%s (realm: %s)" % (_type, i["realm"])

                    _permissions = "\n".join(entry["permissions"])
                    table.add_row([_acl["_path"], printed_identity, _permissions])
            print(table)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@acls.command(name='show-permissions', help='Show permissions supported')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', '-p', is_flag=True, default=False, help='Colorize JSON output')
def show_permissions(_json, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.permissions.fetch()
        if _json:
            utils.print_json(response, colorize=pretty)
        else:
            columns = ['Permissions']
            table = PrettyTable(columns)
            for c in columns:
                table.align[c] = "l"
            for p in response["permissions"]:
                table.add_row([p])
            print(table)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@acls.command(name='make-public', help='Make current project public')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
def make_public(_org_label, _prj_label):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        path = _org_label + '/' + _prj_label
        response = nxs.acls.fetch(subpath=path)
        utils.print_json(response, colorize=True)

        # count = len(response["_results"])
        # if count > 1:
        #     utils.error("More than one ACL matching: %d" % count)
        # elif count == 0:
        #     utils.warn("No ACL matching")

        # current_rev = response["_results"][0]['_rev']
        _identities = [_ANONYMOUS_]
        _permissions = [_PROJECTS_READ_]
        payload = _payload(_permissions, _identities, "Append")
        utils.print_json(payload, colorize=True)
        nxs.acls.append(subpath=path, identities=_identities, permissions=_permissions, rev=1)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


def _payload(permissions: List[List[str]], identities: List[Dict], operation: str = None) -> Dict:
    """Create an ACLs payload. ``permissions`` and ``identities`` have the same order.

    :param permissions: List of list of permissions.
    :param identities: List of identities to which the permissions apply.
    :param operation: (optional) Corresponding operation: 'Append' or 'Subtract'.
    :return: Payload of the ACLs.
    """
    payload = {
        "acl": [
            {
                "permissions": x,
                "identity": y,
            } for x, y in zip(permissions, identities)
        ]
    }
    if operation is not None:
        payload["@type"] = operation
    return payload