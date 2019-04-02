import click
from prettytable import PrettyTable
import os, tempfile
import json

from nexuscli import utils
from nexuscli.cli import cli


@cli.group()
def projects():
    """Projects operations"""


@projects.command(name='create', help='Create a new project')
@click.argument('label')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('--description', '-d', default=None, help='The description of this project')
@click.option('--base', '-b', default=None, help='The base of this project')
@click.option('--vocab', '-v', default=None, help='The vocab of this project')
@click.option('_api_mapping', '--api-mapping', '-am', multiple=True, help='API Mapping, can be used multiple times (format: <prefix>=<namespace>)')
@click.option('_resolver_payload', '--resolver-payload', help='Payload of a resolver to initialize the project with')
@click.option('_resolver_id', '--resolver-id', help='Identifier of the resolver to initialize the project with')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', '-p', is_flag=True, default=False, help='Colorize JSON output')
def create(label, _org_label, description, base, vocab, _api_mapping, _resolver_payload, _resolver_id, _resolve_to_project, priority, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    try:
        mappings = None

        if _api_mapping is not None:
            mappings = []
            for am in _api_mapping:
                if "=" not in am:
                    utils.error("Invalid API Mapping, it should be in the format <prefix>=<URL>: %s" % am)
                key, value = am.split("=", 1)
                entry = {
                    "prefix": key,
                    "namespace": value
                }
                mappings.append(entry)

        nxs = utils.get_nexus_client()
        response = nxs.projects.create(org_label=_org_label, project_label=label, description=description,
                                       api_mappings=mappings, vocab=vocab, base=base)
        print("Project created (id: %s)" % response["@id"])

        if _resolver_payload is not None:
            print("Initializing a resolver within the project (id: %s)" % response["@id"])
            resolver_data = {}
            resolver_data = json.loads(_resolver_payload)
            resolver_response = nxs.resolvers.create(org_label=_org_label, project_label=label, resolver_data=resolver_data, resolver_id=_resolver_id)
            print("Resolver created (id: %s)" % resolver_response["@id"])
        if _json:
            utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))

@projects.command(name='fetch', help='Fetch a project')
@click.argument('label')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('--revision', '-r', default=None, type=int, help='Fetch the project at a specific revision')
@click.option('--pretty', '-p', is_flag=True, default=False, help='Colorize JSON output')
def fetch(label, _org_label, revision, pretty):
    _org_label = utils.get_organization_label(_org_label)
    try:
        nxs = utils.get_nexus_client()
        response = nxs.projects.fetch(org_label=_org_label, project_label=label, rev=revision)
        if revision is not None and response["_rev"] != revision:
            utils.error("Revision '%s' does not exist" % revision)
        utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@projects.command(name='update', help='Update a project')
@click.argument('label')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_payload', '--data', '-d', help='Payload to replace it with')
def update(label, _org_label, _payload):
    _org_label = utils.get_organization_label(_org_label)
    try:
        nxs = utils.get_nexus_client()
        data = nxs.projects.fetch(org_label=_org_label, project_label=label)
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
            print("No change in project, aborting update.")
        else:
            nxs.projects.update(project=data, rev=current_revision)
            print("Project updated.")
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@projects.command(name='list', help='List all projects')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_from', '--from', '-f', default=0, help='Offset of the listing')
@click.option('--size', '-s', default=20, help='How many resource to list')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', '-p', is_flag=True, default=False, help='Colorize JSON output')
def _list(_org_label, _from, size, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    try:
        nxs = utils.get_nexus_client()
        response = nxs.projects.list(org_label=_org_label, pagination_from=_from, pagination_size=size)
        if _json:
            utils.print_json(response, colorize=pretty)
        else:
            table = PrettyTable(['Label', 'Description', 'Id', 'Deprecated'])
            table.align["Label"] = "l"
            table.align["Description"] = "l"
            table.align["Id"] = "l"
            table.align["Deprecated"] = "l"
            for r in response["_results"]:
                if "description" in r:
                    table.add_row([r["_label"], r["description"], r["@id"], r["_deprecated"]])
                else:
                    table.add_row([r["_label"], "", r["@id"], r["_deprecated"]])
            print(table)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@projects.command(name='deprecate', help='Deprecate an project')
@click.argument('label')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', '-p', is_flag=True, default=False, help='Colorize JSON output')
def deprecate(label, _org_label, _json, pretty):
    _org_label = utils.get_organization_label(_org_label)
    try:
        nxs = utils.get_nexus_client()
        response = nxs.projects.fetch(org_label=_org_label, project_label=label)
        if _json:
            utils.print_json(response, colorize=pretty)
        response = nxs.projects.deprecate(project=response, rev=response["_rev"])
        if _json:
            utils.print_json(response, colorize=pretty)
        print("Project '%s' under organization '%s' was deprecated." % (label, _org_label))
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@projects.command(name='select', help='Select an project')
@click.argument('label')
@click.option('_org_label', '--org', '-o', help='Organization to work on (overrides selection made via orgs command)')
def select(label, _org_label):
    _org_label = utils.get_organization_label(_org_label)
    try:
        nxs = utils.get_nexus_client()
        nxs.projects.fetch(org_label=_org_label, project_label=label)
    except nxs.HTTPError as e:
        if e.response.status_code == 404:
            utils.error("Could not find project with label '%s' under organization '%s'." % (label, _org_label))
        else:
            # unexpected error
            utils.print_json(e.response.json(), colorize=True)
            utils.error(str(e))

    utils.set_default_project(label)
    print("Project selected.")


@projects.command(name='current', help='Show currently selected project')
def current():
    config = utils.get_cli_config()
    profile, selected_config = utils.get_selected_deployment_config(config)
    if selected_config is None:
        utils.error("You must first select a profile using the 'profiles' command")

    default_project = utils.get_default_project()
    if default_project is not None:
        print(default_project)
    else:
        utils.error("No default project selected in profile '%s'" % profile)
