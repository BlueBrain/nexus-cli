from typing import List, Dict

import click
from prettytable import PrettyTable

from nexuscli.cli import cli
from nexuscli import utils


_ANONYMOUS_ = {
            "@id": "http://dev.nexus.ocp.bbp.epfl.ch/v1/anonymous",
            "@type": "Anonymous"
          }

_AUTHENTICATED_ = {
            "@id": "http://dev.nexus.ocp.bbp.epfl.ch/v1/authenticated",
            "@type": "Authenticated"
          }

_PROJECTS_READ_ = "projects/read"
_RESOURCES_READ_ = "resources/read"
_VIEWS_QUERY_ = "views/query"


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
@click.option('_self', '--non-self', is_flag=True, default=True, help='Show also non self ACLs')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', '-p', is_flag=True, default=False, help='Colorize JSON output')
@click.option('--verbose', '-v', is_flag=True, default=False, help='Show debug info')
def _list(_org_label, _prj_label, subpath, _ancestor, _non_self, _json, pretty, verbose):
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
            print("non-self: %s" % _non_self)
            print("ancestors: %s" % _ancestor)
        response = nxs.acls.list(subpath=path, ancestors=_ancestor, self=_non_self)
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
            table = PrettyTable(['Permissions'])
            table.align['Permissions'] = "l"
            for p in response["permissions"]:
                table.add_row([p])
            print(table)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@acls.command(name='show-identities', help='Show identities supported')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', '-p', is_flag=True, default=False, help='Colorize JSON output')
def show_identities(_json, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.identities.fetch()
        if _json:
            utils.print_json(response, colorize=pretty)
        else:
            columns = ["Id", "Type", "Realm", "User", "Group"]
            table = PrettyTable(columns)
            for c in columns:
                table.align[c] = "l"
            for i in response["identities"]:
                realm = ""
                if "realm" in i:
                    realm = i["realm"]

                user = ""
                if "subject" in i:
                    user = i["subject"]

                group = ""
                if "group" in i:
                    realm = i["group"]

                table.add_row([i["@id"], i["@type"], realm, user, group])
            print(table)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@acls.command(name='make-public', help='Make current project public (i.e. Add permission ''projects/read'' to ''Anonymous'')')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('_replace', '--replace-existing', is_flag=True, default=False,
              help='If set, remove existing ACLs on this project and ')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', '-p', is_flag=True, default=False, help='Colorize JSON output')
def make_public(_org_label, _prj_label, _replace, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        path = _org_label + '/' + _prj_label

        utils.warn("You are about to make the data in your project public to the world.")
        input("Press <ENTER> to continue, CTRL+C to cancel...")

        response = nxs.acls.fetch(subpath=path)
        count = len(response["_results"])
        if count > 1:
            utils.error("More than one ACL matching: %d" % count)
        elif count == 0:
            utils.warn("No ACL found specifically for this organization '%s' and project '%s'." % (_org_label, _prj_label))
            current_rev = 0
        else:
            current_rev = response["_results"][0]['_rev']

        _identities = [_ANONYMOUS_]
        _permissions = [_PROJECTS_READ_, _RESOURCES_READ_, _VIEWS_QUERY_]
        if _replace:
            print("Replacing existing ACLs on project '%s' in organization '%s'" % (_prj_label, _org_label))
            response = nxs.acls.replace(subpath=path, identities=_identities, permissions=[_permissions],
                                        rev=current_rev)
        else:
            print("Adding to existing ACLs on project '%s' in organization '%s'" % (_prj_label, _org_label))
            response = nxs.acls.append(subpath=path, identities=_identities, permissions=[_permissions],
                                       rev=current_rev)
        if _json:
            utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


def count_not_None(_list):
    count = 0
    for item in _list:
        if type(item) is bool and item is True:
            count += 1
        elif type(item) is str and len(item) > 0:
            count += 1
    return count


# Identities definition: https://bluebrain.github.io/nexus/docs/api/iam/iam-identities.html
def build_identity(_anonymous, _authenticated, _user, _group, _realm):
    identities = []
    if _anonymous is True:
        identities.append(_ANONYMOUS_)
    elif _authenticated is True:
        identities.append(_AUTHENTICATED_)
    elif _user is not None:
        identities.append({
              "@type": "User",
              "realm": _realm,
              "subject": _user
        })
    elif _group is not None:
        identities.append({
            "@type": "Group",
            "group": _group,
            "realm": _realm
        })
    return identities


def build_permissions_param(_permissions):
    param = []
    for p in _permissions:
        param.append(p)
    return [param]


@acls.command(name='append', help='Add permissions')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('_anonymous', '--anonymous', is_flag=True, default=False, help='Grant permissions to Anonymous')
@click.option('_authenticated', '--authenticated', is_flag=True, default=False, help='Grant permissions to Authenticated')
@click.option('_group', '--group', help='Grant permissions to a specific User')
@click.option('_user', '--user', help='Grant permissions to a specific User')
@click.option('_realm', '--realm', help='Specify the Realm for Authenticated user, specific User or Group')
@click.option('_permissions', '--permission', multiple=True, help='The permission to grant')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', '-p', is_flag=True, default=False, help='Colorize JSON output')
@click.option('--verbose', '-v', is_flag=True, default=False, help='Print verbose information')
def append_permissions(_org_label, _prj_label, _anonymous, _authenticated, _group, _user, _realm, _permissions,
                       _json, pretty, verbose):

    count = count_not_None([_anonymous, _authenticated, _group, _user])
    if count == 0:
        utils.error("You must choose to whom you will grant permissions using one of: --anonymous, --authenticated, "
                    "--group, --user.")
    elif count > 1:
        utils.error("The following options are mutually exclusive: --anonymous, --authenticated, --group, --user.")

    if count_not_None([_authenticated, _user, _group]) > 0 and _realm is None:
        utils.error("You must set a Realm if you want to grant permissions to --authenticated, --user or --group.")

    if len(_permissions) == 0:
        utils.error("You must define the permissions to grant.")

    for p in _permissions:
        print(p)

    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        path = _org_label + '/' + _prj_label

        response = nxs.acls.fetch(subpath=path)
        count = len(response["_results"])
        if count > 1:
            utils.error("More than one ACL matching: %d" % count)
        elif count == 0:
            utils.warn("No ACL found specifically for this organization '%s' and project '%s'." % (_org_label, _prj_label))
            current_rev = 0
        else:
            current_rev = response["_results"][0]['_rev']

        _identities = build_identity(_anonymous, _authenticated, _user, _group, _realm)
        _permissions_param = build_permissions_param(_permissions)

        print("Adding to existing ACLs on project '%s' in organization '%s'" % (_prj_label, _org_label))
        if verbose:
            utils.print_json(path)
            utils.print_json(_identities)
            utils.print_json(_permissions)
            utils.print_json(current_rev)
        response = nxs.acls.append(subpath=path, identities=_identities, permissions=_permissions_param, rev=current_rev)

        if _json:
            utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))
