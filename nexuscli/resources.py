import json
import os
import tempfile

import click
from prettytable import PrettyTable

from nexuscli import utils
from nexuscli.cli import cli


@cli.group()
def resources():
    """Resources operations"""


@resources.command(name='create', help='Create a new resource')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--id', '-i', help='Id of the resource')
@click.option('--file', '-f', help='Source file to create new resource')
@click.option('_type', '--type', '-t', default=None, help='Type of resource to load')
@click.option('_payload', '--data', '-d', help='source payload to create new resource')
@click.option('--format', default="json", help='Source file extension [json,csv]')
@click.option('--idcolumn', default=None, help='The column name containing csv row identifier')
@click.option('--idnamespace', default=None, help='The namespace of the csv entity identifiers: e.g https:doi.org/')
@click.option('--mergewith', '-m', default=None, multiple=True, help='CSV source file to merge with. Multiple files can be provided')
@click.option('--aggreg-column', '-a', default=None, multiple=True, help='The columns to aggregate per entity. Multiple columns can be provided')
@click.option('--mergeon', default=None, help='CSV column name to merge on')
@click.option('--max-connections', '-c', default=50, help='Maximum number of concurrent connections when loading CSV data')
@click.option('--schema', '-s', default='_', help='Schema to validate this resource against')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def create(_org_label, _prj_label, id, file, _type, _payload, format, idcolumn, idnamespace, mergewith, aggreg_column, mergeon, max_connections, schema, _json, pretty):

    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    data_model = dict()
    data_model["_org_label"] = _org_label
    data_model["_prj_label"] = _prj_label
    data_model["schema"] = schema

    nxs = utils.get_nexus_client()
    try:
        data = {}
        if _payload is not None and file is not None:
            utils.error("--data and --file are mutually exclusive.")
        if _payload is not None:
            data = json.loads(_payload)

        if file is not None and format == "json":
            if format == "json":
                with open(file) as f:
                    data = json.load(f)
                if len(data) == 0:
                    utils.error("You must give a non empty payload")
        if data:

            if _type:
                types = [] if "@type" not in data else data["@type"]
                if type(types) is not list:
                    types = [types]
                types.append(_type)

                data["@type"] = types
            
            if isinstance(data,list):
                utils.create_in_nexus(data_model,data,max_connections)
            else:
                response = nxs.resources.create(org_label=_org_label, project_label=_prj_label, data=data,
                                            schema_id=schema, resource_id=id)
                print("Resource created (id: %s)" % response["@id"])
            if _json:
                utils.print_json(response, colorize=pretty)


        if file is not None and format == "csv":
           utils.load_csv(_org_label, _prj_label, schema, file_path=file, merge_with=mergewith, merge_on=mergeon, _type=_type, id_colum=idcolumn, id_namespace=idnamespace, aggreg_column=aggreg_column,max_connections=max_connections)
           print("Finished loading.")

    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))




@resources.command(name='fetch', help='Fetch a resource')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--schema', '-s', default='_', help='Schema of the resource')
@click.option('--revision', '-r', default=None, type=int, help='Fetch the resource at a specific revision')
@click.option('--tag', '-t', default=None, help='Fetch the resource at a specific tag')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def fetch(id, _org_label, _prj_label, schema, revision, tag, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.resources.fetch(org_label=_org_label, project_label=_prj_label, schema_id=schema,
                                       resource_id=id, rev=revision, tag=tag)
        utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@resources.command(name='update', help='Update a resource')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('_payload', '--data', '-d', help='Payload to replace it with')
def update(id, _org_label, _prj_label, _payload):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        data = nxs.resources.fetch(org_label=_org_label, project_label=_prj_label, schema_id='_', resource_id=id)
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
            nxs.resources.update(resource=data, rev=current_revision)
            print("Resource updated.")
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))



@resources.command(name='list', help='List all resources')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--deprecated', '-d', is_flag=True, default=False, help='Show only deprecated resources')
@click.option('_from', '--from', '-f', default=0, help='Offset of the listing')
@click.option('--size', '-s', default=20, help='How many resource to list')
@click.option('_type', '--type', '-t', default=None, help='Filter by type')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def _list(_org_label, _prj_label, deprecated, _from, size, _type, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.resources.list(org_label=_org_label, project_label=_prj_label,
                                      pagination_from=_from, pagination_size=size, type=_type,
                                      deprecated=deprecated)
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
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@resources.command(name='deprecate', help='Deprecate a resource')
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
        response = nxs.resources.fetch(org_label=_org_label, project_label=_prj_label, schema_id='_', resource_id=id)
        if _json:
            utils.print_json(response, colorize=pretty)
        response = nxs.resources.deprecate(resource=response, rev=response["_rev"])
        if _json:
            utils.print_json(response, colorize=pretty)
        print("Resource '%s' was deprecated." % (id))
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))
