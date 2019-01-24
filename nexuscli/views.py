import collections

import click
from prettytable import PrettyTable
import json
import os
import tempfile

from nexuscli.cli import cli
from nexuscli import utils


@cli.group()
def views():
    """Views operations"""


@views.command(name='create', help='Create a new ElasticView')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--id', '-i', help='Id of the ElasticView')
@click.option('_payload', '--data', '-d', help='Payload to create a new ElasticView')
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
        response = nxs.views.create_es(org_label=_org_label, project_label=_prj_label, view_data=data, id=id)
        print("View created (id: %s)" % response["@id"])
        if _json:
            utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@views.command(name='fetch', help='Fetch a view')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--revision', '-r', default=None, type=int, help='Fetch the view at a specific revision')
@click.option('--tag', '-t', default=None, help='Fetch the view at a specific tag')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def fetch(id, _org_label, _prj_label, revision, tag, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        print(id)
        response = nxs.views.fetch(org_label=_org_label, project_label=_prj_label, view_id=id, rev=revision, tag=tag)
        utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@views.command(name='update', help='Update an ElasticView')
@click.argument('id')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('_payload', '--data', '-d', help='Payload to replace it with')
def update(id, _org_label, _prj_label, _payload):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        view = nxs.views.fetch(org_label=_org_label, project_label=_prj_label, view_id=id)
        view_md5_before = utils.generate_nexus_payload_checksum(view)
        current_revision = view["_rev"]

        if _payload is not None:
            view = json.loads(_payload)
        else:
            # If no payload given, load up the entry in a text file and open default editor
            new_file, filename = tempfile.mkstemp()
            print("Opening an editor: %s" % filename)
            f = open(filename, "w")
            f.write(json.dumps(view, indent=2))
            f.close()
            click.edit(filename=filename)
            f = open(filename, "r")
            view = json.loads(f.read())
            f.close()
            os.remove(filename)

        view_md5_after = utils.generate_nexus_payload_checksum(view)
        if view_md5_before == view_md5_after:
            print("No change in view, aborting update.")
        else:
            nxs.views.update_es(esview=view, rev=current_revision)
            print("View updated.")
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@views.command(name='list', help='List all views')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--deprecated', '-d', is_flag=True, default=False, help='Show only deprecated views')
@click.option('_from', '--from', '-f', default=0, help='Offset of the listing')
@click.option('--size', '-s', default=20, help='How many views to list')
@click.option('--view_type', '-t', default=None, help='Filter views by type')
@click.option('--search', default=None, help='Full text search on the views')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def _list(_org_label, _prj_label, deprecated, _from, size, view_type,search, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.views.list(org_label=_org_label, project_label=_prj_label,
                                  pagination_from=_from, pagination_size=size,
                                  deprecated = deprecated, view_type=view_type, full_text_search_query=search)
        if _json:
            utils.print_json(response, colorize=pretty)
        else:
            table = PrettyTable(['Id', 'Type', 'Revision', 'Deprecated'])
            table.align["Id"] = "l"
            table.align["Type"] = "l"
            table.align["Revision"] = "l"
            table.align["Deprecated"] = "l"
            for r in response["_results"]:
                types = ""
                if "@type" in r:
                    if type(r["@type"]) is str:
                        types = r["@type"]
                    elif isinstance(r["@type"], collections.Sequence):
                        for t in r["@type"]:
                            types += t + "\n"
                    else:
                        utils.warn("Unsupported type: " + type(r["@type"]))
                        types = r["@type"]
                else:
                    types = '-'

                table.add_row([r["@id"], types, r["_rev"], r["_deprecated"]])
            print(table)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@views.command(name='deprecate', help='Deprecate an ElasticView')
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
        response = nxs.views.fetch(org_label=_org_label, project_label=_prj_label, view_id=id)
        if _json:
            utils.print_json(response, colorize=pretty)
        response = nxs.views.deprecate_es(esview=response, rev=response["_rev"])
        if _json:
            utils.print_json(response, colorize=pretty)
        print("View '%s' was deprecated." % (id))
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@views.command(name='esquery', help='Query an ElasticView')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--id', '-i', default="documents", help='Id of the view')
@click.option('_payload', '--data', '-d',required=True, help='Query payload')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def esquery(_org_label, _prj_label, id, _payload, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.views.query_es(org_label=_org_label, project_label=_prj_label, query=_payload, id=id)
        if _json:
            utils.print_json(response, colorize=pretty)
        else:
            table = PrettyTable(['Id', 'Type', 'Revision', 'Deprecated'])
            table.align["Id"] = "l"
            table.align["Type"] = "l"
            table.align["Revision"] = "l"
            table.align["Deprecated"] = "l"
            for r in response["hits"]["hits"]:
                types = ""
                if "_source" in r and "@type" in r["_source"]:
                    if type(r["_source"]["@type"]) is str:
                        types = r["_source"]["@type"]
                    elif isinstance(r["_source"]["@type"], collections.Sequence):
                        for t in r["_source"]["@type"]:
                            types += t + "\n"
                    else:
                        utils.warn("Unsupported type: " + type(r["_source"]["@type"]))
                        types = r["_source"]["@type"]
                else:
                    types = '-'

                table.add_row([r["_source"]["@id"], types, r["_source"]["_rev"], r["_source"]["_deprecated"]])
            print(table)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@views.command(name='sparqlquery', help='Query a SparqlView')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('_payload', '--data', '-d',required=True, help='Query payload')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def sparqlquery(_org_label, _prj_label, _payload, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.views.query_sparql(org_label=_org_label, project_label=_prj_label, query=_payload)
        utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))
