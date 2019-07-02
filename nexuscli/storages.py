import click
from prettytable import PrettyTable
import json
import os
import tempfile

from nexuscli.cli import cli
from nexuscli import utils
from nexussdk.utils import http as nexussdk_http
from urllib.parse import quote_plus as encode_url


@cli.group()
def storages():
    """Storages operations"""


@storages.command(name='fetch', help='Fetch a storage')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p',
              help='Project to work on (overrides selection made via projects command)')
@click.option('--revision', '-r', default=None, type=int, help='Fetch the storage at a specific revision')
@click.option('--tag', '-t', default=None, help='Fetch the storage at a specific tag')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def fetch(id, _org_label, _prj_label, revision, tag, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.storages.fetch(org_label=_org_label, project_label=_prj_label, storage_id=id, rev=revision, tag=tag)
        utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


@storages.command(name='list', help='List all storages')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p',
              help='Project to work on (overrides selection made via projects command)')
@click.option('--deprecated', '-d', is_flag=True, default=False, help='Show only deprecated storages')
@click.option('_from', '--from', '-f', default=0, help='Offset of the listing')
@click.option('--size', '-s', default=20, help='How many storages to list')
@click.option('_type', '--type', '-t', default=None, help='Filter storages by type')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def _list(_org_label, _prj_label, deprecated, _from, size, _type, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.storages.list(org_label=_org_label, project_label=_prj_label,
                                     pagination_from=_from, pagination_size=size,
                                     deprecated=deprecated, type=_type)
        if _json:
            utils.print_json(response, colorize=pretty)
        else:
            table = PrettyTable(['Id', 'Type', 'Revision', 'Deprecated'])
            table.align["Id"] = "l"
            table.align["Type"] = "l"
            table.align["Revision"] = "l"
            table.align["Deprecated"] = "l"
            for r in response["_results"]:
                types = utils.format_json_field(r, "@type")
                table.add_row([r["@id"], types, r["_rev"], r["_deprecated"]])
            print(table)
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


@storages.command(name='create', help='Create a new storage')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p',
              help='Project to work on (overrides selection made via projects command)')
@click.option('--id', '-i', help='Id of the storage')
@click.option('_payload', '--data', '-d', help='Payload to create a new storage')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def create(_org_label, _prj_label, id, _payload, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        data = {}
        if _payload is not None:
            data = json.loads(_payload)
        response = nxs.storages.create_(org_label=_org_label, project_label=_prj_label, payload=data, storage_id=id)
        print("Storage created (id: %s)" % response["@id"])
        if _json:
            utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


@storages.command(name='update', help='Update a storage')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p',
              help='Project to work on (overrides selection made via projects command)')
@click.option('_payload', '--data', '-d', help='Payload to replace it with')
def update(id, _org_label, _prj_label, _payload):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        storage = nxs.storages.fetch(org_label=_org_label, project_label=_prj_label, storage_id=id)
        storage_md5_before = utils.generate_nexus_payload_checksum(storage, debug=True)
        current_revision = storage["_rev"]

        if _payload is not None:
            storage = json.loads(_payload)
        else:
            # If no payload given, load up the entry in a text file and open default editor
            new_file, filename = tempfile.mkstemp()
            print("Opening an editor: %s" % filename)
            f = open(filename, "w")
            f.write(json.dumps(storage, indent=2))
            f.close()
            click.edit(filename=filename)
            f = open(filename, "r")
            storage = json.loads(f.read())
            f.close()
            os.remove(filename)

        storage_md5_after = utils.generate_nexus_payload_checksum(storage, debug=True)
        if storage_md5_before == storage_md5_after:
            print("No change in storage, aborting update.")
        else:
            nxs.storages.update_(_org_label, _prj_label, payload=storage, storage_id=id, rev=current_revision)
            print("Storage updated.")
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


@storages.command(name='deprecate', help='Deprecate a storage')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p',
              help='Project to work on (overrides selection made via projects command)')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def deprecate(id, _org_label, _prj_label, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.storages.fetch(org_label=_org_label, project_label=_prj_label, storage_id=id)
        if _json:
            utils.print_json(response, colorize=pretty)
        response = nxs.storages.deprecate(_org_label, _prj_label, id, rev=response["_rev"])
        if _json:
            utils.print_json(response, colorize=pretty)
        print("Storage '%s' was deprecated." % id)
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)
