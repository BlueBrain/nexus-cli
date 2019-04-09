import collections

import click
from IPython.utils import path
from prettytable import PrettyTable
import json
import os
import tempfile

from nexuscli.cli import cli
from nexuscli import utils
from nexussdk.utils import http as nexussdk_http


@cli.group()
def resolvers():
    """Resolvers operations"""


@resolvers.command(name='fetch', help='Fetch a resolver')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--revision', '-r', default=None, type=int, help='Fetch the resolver at a specific revision')
@click.option('--tag', '-t', default=None, help='Fetch the resolver at a specific tag')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def fetch(id, _org_label, _prj_label, revision, tag, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.resolvers.fetch(org_label=_org_label, project_label=_prj_label, id=id, rev=revision, tag=tag)
        utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


@resolvers.command(name='create', help='Create a new Resolver')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--id', '-i', help='Id of the Resolver')
@click.option('_projects', '--projects', multiple=True, help='One or many projects to resolve to (format: [org_label/prj_label])')
@click.option('_identities', '--identities', multiple=True, help='One or many identities which can access the resolver (format: [{"@id":"URI", "":"@type":"type", "ream":"Realm"}])')
@click.option('_priority', '--priority', default=None, type=int, help='The resolver priority')
@click.option('_resources_types', '--resources-types', default=None, help='One or many type of resources to resolve. Types valeues should be URIs')
@click.option('_type', '--type', '-t',default="CrossProject", help='One or many resolver types')
@click.option('_payload', '--data', '-d', help='Payload to create a new Resolver')
@click.option('--file', '-f', help='Source file to create new resolver')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def create(_org_label, _prj_label, id, _projects, _identities, _priority, _resources_types, _type, _payload, file,_json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        data = {}
        if _payload is not None and file is not None:
            utils.error("--data and --file are mutually exclusive.")

        if _priority is not None and _identities is not None and _projects is not None:
            response = nxs.resolvers.create(org_label=_org_label, project_label=_prj_label, projects= _projects,identities= _identities, _priority= _priority, _id=id, resources_types = _resources_types)
        else:
            if _payload is not None:
                data = json.loads(_payload)

            if file is not None:
                with open(file) as f:
                    data = json.load(f)
                if len(data) == 0:
                    utils.error("The provided file %s should contain a non empty json payload" % file)

            if not data:
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
            if data:
                if id is not None:
                    utils.error("The resolver id should be provided in the json-ld payload as @id.")
                else:
                    full_url = nexussdk_http._full_url(path=[nxs.resolvers.SEGMENT, _org_label, _prj_label], use_base=False)
                    response = nxs.resolvers.create_(path=full_url, payload=data)
            else:
                utils.error("--data, --file or (--priority, --identities, --projects) are required for creating a resolver.")

        print("Resolver created (id: %s)" % response["@id"])
        if _json:
            utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


@resolvers.command(name='update', help='Update a resolver')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('_projects', '--projects', multiple=True, help='One or many projects to resolve to (format: [org_label/prj_label])')
@click.option('_identities', '--identities', multiple=True, help='One or many identities which can access the resolver (format: [{"@id":"URI", "":"@type":"type", "ream":"Realm"}])')
@click.option('_priority', '--priority', default=None, type=int, help='The resolver priority')
@click.option('_resources_types', '--resources-types', default=None, help='One or many type of resources to resolve. Types valeues should be URIs')
@click.option('_type', '--type', '-t',default="CrossProject", help='One or many resolver types')
@click.option('_payload', '--data', '-d', help='Payload to replace it with')
def update(id, _org_label, _prj_label, _projects, _identities, _priority, _resources_types, _type, _payload):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        data = nxs.resolvers.fetch(org_label=_org_label, project_label=_prj_label, id=id)
        current_revision = data["_rev"]
        data_md5_before = utils.generate_nexus_payload_checksum(data)
        if _priority is not None and _identities is not None and _projects is not None:
            response = nxs.resolvers.update(org_label=_org_label, project_label=_prj_label, projects= _projects,identities= _identities, _priority= _priority, id=id, rev=current_revision,resources_types = _resources_types)
        else:
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
                print("No change in resolver, aborting update.")
            else:
                nxs.resolvers.update_(path=[nxs.resolvers.SEGMENT, _org_label, _prj_label, id], payload= data, rev=current_revision)
                print("Resolver updated.")

    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


@resolvers.command(name='list', help='List all resolvers')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--deprecated', '-d', is_flag=True, default=False, help='Show only deprecated resolvers')
@click.option('_from', '--from', '-f', default=0, help='Offset of the listing')
@click.option('--size', '-s', default=20, help='How many resolvers to list')
@click.option('_type', '--type', '-t', default=None, help='Filter resolvers by type')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def _list(_org_label, _prj_label, deprecated, _from, size, _type, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.resolvers.list(org_label=_org_label, project_label=_prj_label,
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


@resolvers.command(name='deprecate', help='Deprecate a Resolver')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--revision', '-r', default=None, type=int, help='Fetch the resolver at a specific revision')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def deprecate(id, _org_label, _prj_label, revision, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        if revision is not None:
           response = nxs.resolvers.deprecate(org_label=_org_label, project_label=_prj_label, _id=id, rev=revision)
        else:
            response = nxs.resolvers.fetch(org_label=_org_label, project_label=_prj_label, _id=id)

            response = nxs.resolvers._deprecate(resolver_Data=response, rev=response["_rev"])
        if _json:
            utils.print_json(response, colorize=pretty)
        print("Resolver '%s' was deprecated." % id)
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)
