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


@views.command(name='create', help='Create a new view')
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
        response = nxs.views.create_(org_label=_org_label, project_label=_prj_label, payload=data, view_id=id)
        print("View created (id: %s)" % response["@id"])
        if _json:
            utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


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
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


@views.command(name='update', help='Update a view')
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
        view_md5_before = utils.generate_nexus_payload_checksum(view, debug=True)
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

        view_md5_after = utils.generate_nexus_payload_checksum(view, debug=True)
        if view_md5_before == view_md5_after:
            print("No change in view, aborting update.")
        else:
            nxs.views.update_es(esview=view, rev=current_revision)
            print("View updated.")
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


@views.command(name='list', help='List all views')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--deprecated', '-d', is_flag=True, default=False, help='Show only deprecated views')
@click.option('_from', '--from', '-f', default=0, help='Offset of the listing')
@click.option('--size', '-s', default=20, help='How many views to list')
@click.option('_type', '--type', '-t', default=None, help='Filter views by type')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def _list(_org_label, _prj_label, deprecated, _from, size, _type, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        response = nxs.views.list(org_label=_org_label, project_label=_prj_label,
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


@views.command(name='deprecate', help='Deprecate a view')
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
        print("View '%s' was deprecated." % id)
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


def get_query_from_payload_xor_data_otherwise_editor(_payload, file, default_query, file_prefix):
    """ If a payload or a file is provided, use it. Otherwise, propose the user an editor with a default query.
        :param _payload: the query as a dict or str
        :param file: the filename from which to load the query
        :param default_query: the query to load in the editor
        :param file_prefix: the prefix of the editor file to save in the current dir
        :return: the query as text.
    """

    if _payload is not None and file is not None:
        utils.error("--data and --file are mutually exclusive.")

    if _payload is not None:
        if isinstance(_payload, dict):
            data = json.dumps(_payload, indent=2)
        else:
            data = _payload
    elif file is not None:
        f = open(file, "r")
        data = f.read()
        f.close()
    else:
        new_file, filename = tempfile.mkstemp(dir=".", prefix=file_prefix+"-")
        print("Opening an editor: %s" % filename)
        f = open(filename, "w")
        q = default_query
        if isinstance(default_query, dict):
            q = json.dumps(default_query, indent=2)
        f.write(q)
        f.close()
        click.edit(filename=filename)
        f = open(filename, "r")
        data = f.read()
        f.close()
    return data


@views.command(name='query-es', help='Query an ElasticView')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('--id', '-i', default="documents", help='Id of the ElasticView')
@click.option('_payload', '--data', '-d', help='Query payload')
@click.option('--file', '-f', help='Query from file')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def query_es(_org_label, _prj_label, id, _payload, file, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        default_query = {
            "query": {
                "query_string": {
                    "query": "*"
                }
            }
        }
        data = get_query_from_payload_xor_data_otherwise_editor(_payload, file, default_query, file_prefix="query-es")
        response = nxs.views.query_es(org_label=_org_label, project_label=_prj_label, view_id=id, query=data)
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
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)


@views.command(name='query-sparql', help='Query a SparqlView')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_prj_label', '--project', '-p', help='Project to work on (overrides selection made via projects command)')
@click.option('_payload', '--data', '-d', help='Query payload')
@click.option('--file', '-f', help='Query from file')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def query_sparql(_org_label, _prj_label, _payload, file, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    _prj_label = utils.get_project_label(_prj_label)
    nxs = utils.get_nexus_client()
    try:
        default_query = "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
        data = get_query_from_payload_xor_data_otherwise_editor(_payload, file, default_query, file_prefix="query-sparql")
        response = nxs.views.query_sparql(org_label=_org_label, project_label=_prj_label, query=data)
        if _json:
            utils.print_json(response, colorize=pretty)
        else:
            vars = response["head"]["vars"]
            table = PrettyTable(vars)
            for v in vars:
                table.align[v] = "l"
            for b in response["results"]["bindings"]:
                cells = []
                for v in vars:
                    cells.append(b[v]["value"])
                table.add_row(cells)
            print(table)
    except nxs.HTTPError as e:
        utils.error(str(e))
        utils.print_json(e.response.json(), colorize=True)
