import collections

import click
from prettytable import PrettyTable
import json
import os
import tempfile

from nexuscli.cli import cli
from nexuscli import utils


@cli.group()
def schemas():
    """Schemas operations"""


@schemas.command(name='create', help='Create a new schemas')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--id', '-i', help='Id of the resource')
@click.option('_payload', '--data', '-d', help='source payload to create new resource')
@click.option('--file', '-f', help='source payload to create new resource')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def create(_org_label, _prj_label, id, _payload, file, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        data = {}
        if _payload is not None and file is not None:
            utils.error("--data and --file are mutually exclusive.")
        if _payload is not None:
            data = json.loads(_payload)
        if file is not None:
            with open(file) as f:
                data = json.load(f)
        response = nxs.schemas.create(org_label=_org_label, project_label=_prj_label, schema_obj=data, schema_id=id)
        print("Schema created (id: %s)" % response["@id"])
        if _json:
            utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@schemas.command(name='fetch', help='Fetch a schemas')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--revision', '-r', default=None, type=int, help='Fetch the resource at a specific revision')
@click.option('--tag', '-t', default=None, help='Fetch the resource at a specific tag')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def fetch(id, _org_label, _prj_label, revision, tag, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.schemas.fetch(org_label=_org_label, project_label=_prj_label, schema_id=id,
                                     rev=revision, tag=tag)
        utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@schemas.command(name='update', help='Update a schemas')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('_payload', '--data', '-d', help='Payload to replace it with')
def update(id, _org_label, _prj_label, _payload):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        data = nxs.schemas.fetch(org_label=_org_label, project_label=_prj_label, schema_id=id)
        data_md5_before = utils.generate_nexus_payload_checksum(data)
        current_revision = data["_rev"]

        if _payload is not None:
            data = json.loads(_payload)
        else:
            # If no payload given, load up the entry in a text file and open default editor
            new_file, filename = tempfile.mkstemp()
            print("Opening an editor: %s" % filename)
            f = open(filename, "w")
            f.write(json.dumps(data, indent=2))
            f.close()
            click.edit(filename=filename)
            f = open(filename, "r")
            data = json.loads(f.read())
            f.close()
            os.remove(filename)

        data_md5_after = utils.generate_nexus_payload_checksum(data)
        if data_md5_before == data_md5_after:
            print("No change in resource, aborting update.")
        else:
            nxs.schemas.update(schema=data, previous_rev=current_revision)
            print("Schema updated.")
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@schemas.command(name='list', help='List all schemas')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--deprecated', '-d', is_flag=True, default=False, help='Show only deprecated resources')
@click.option('_from', '--from', '-f', default=0, help='Offset of the listing')
@click.option('--size', '-s', default=20, help='How many resource to list')
@click.option('--search', default=None, help='Full text search on the resources')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def _list(_org_label, _prj_label, deprecated, _from, size, search, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.schemas.list(org_label=_org_label, project_label=_prj_label,
                                    pagination_from=_from, pagination_size=size,
                                    deprecated=deprecated, full_text_search_query=search)
        if _json:
            utils.print_json(response, colorize=pretty)
        else:
            columns = ['Id', 'Types', 'Label', 'Imports', 'NodeShapes', 'PropertyShapes', 'Revision', 'Deprecated']
            table = PrettyTable(columns)
            for c in columns:
                table.align[c] = "l"

            for r in response["_results"]:
                types = utils.format_json_field(r, "@type")

                # Get extra info from the schema itself
                schema = nxs.schemas.fetch(org_label=_org_label, project_label=_prj_label, schema_id=r["@id"])
                imports = utils.format_json_field(schema, "imports")
                node_shapes = get_shapes_id_by_node_kind(schema, ["sh:NodeShape", "NodeShape"])
                property_shapes = get_shapes_id_by_node_kind(schema, ["sh:PropertyShapes", "PropertyShapes"])
                dummy_payload = {
                    "nodes": node_shapes,
                    "properties": property_shapes
                }
                nodes = utils.format_json_field(dummy_payload, "nodes")
                properties = utils.format_json_field(dummy_payload, "properties")
                label = ""
                if "label" in schema:
                    label = schema["label"]

                table.add_row([r["@id"], types, label, imports, nodes, properties, r["_rev"], r["_deprecated"]])
            print(table)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


def get_shapes_id_by_node_kind(payload: dict, node_kinds):
    shape_ids = []
    if "shapes" in payload:
        for shape in payload["shapes"]:
            for kind in node_kinds:
                if type(shape["@type"]) is list and kind in shape["@type"]:
                    # array
                    shape_ids.append(shape["@id"])
                elif kind == shape["@type"]:
                    # literal
                    shape_ids.append(shape["@id"])
    return shape_ids


@schemas.command(name='deprecate', help='Deprecate an schemas')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def deprecate(id, _org_label, _prj_label, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.schemas.fetch(org_label=_org_label, project_label=_prj_label, schema_id=id)
        if _json:
            utils.print_json(response, colorize=pretty)
        response = nxs.schemas.deprecate(schema=response, rev=response["_rev"])
        if _json:
            utils.print_json(response, colorize=pretty)
        print("Schema '%s' was deprecated." % (id))
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))
