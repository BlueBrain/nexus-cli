import click
from prettytable import PrettyTable
import os, tempfile
import json

from nexuscli import utils
from nexuscli.cli import cli


@cli.group()
def orgs():
    """Organizations operations"""


@orgs.command(name='fetch', help='Fetch an organization')
@click.argument('label')
@click.option('--revision', '-r', default=None, type=int, help='Fetch the organization at a specific revision')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def fetch(label, revision, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.organizations.fetch(org_label=label, rev=revision)
        if revision is not None and response["_rev"] != revision:
            utils.error("Revision '%s' does not exist" % revision)
        utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@orgs.command(name='create', help='Create a new organization')
@click.argument('label')
@click.option('--description', '-d', help='Description of the organization')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def create(label, description, _json, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.organizations.create(org_label=label, description=description)
        print("Organization created (id: %s)" % response["@id"])
        if _json:
            utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@orgs.command(name='update', help='Update an organization')
@click.argument('label')
@click.option('_payload', '--data', help='The new payload for that organization')
@click.option('--name', '-n', type=str, help='new name for this organization')
@click.option('--description', '-d', type=str, help='New description for this organization')
def update(label, _payload, name, description):
    nxs = utils.get_nexus_client()
    try:
        data = nxs.organizations.fetch(org_label=label)
        current_revision = data["_rev"]
        data_md5_before = utils.generate_nexus_payload_checksum(data)

        if _payload is None and (name is not None or description is not None):
            if name is not None:
                data["name"] = name
            if description is not None:
                data["description"] = description
        elif _payload is not None:
            data = json.loads(_payload)
        else:
            # If nothing given, load up the entry in a text file and open default editor
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
            print("No change in organization, aborting update.")
        else:
            nxs.organizations.update(org=data, rev=current_revision)
            print("Organization updated.")
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@orgs.command(name='list', help='List all organizations')
@click.option('_from', '--from', '-f', default=0, help='Offset of the listing')
@click.option('--size', '-s', default=20, help='How many resource to list')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def _list(_from, size, _json, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.organizations.list(pagination_from=_from, pagination_size=size)
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


@orgs.command(name='deprecate', help='Deprecate an organization')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
@click.argument('label')
def deprecate(label, _json, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.organizations.fetch(label)
        if _json:
            utils.print_json(response, colorize=pretty)
        response = nxs.organizations.deprecate(org_label=label, rev=response["_rev"])
        if _json:
            utils.print_json(response, colorize=pretty)
        print("Organization '%s' was deprecated." % label)
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@orgs.command(name='select', help='Select an organization')
@click.argument('label')
def select(label):
    nxs = utils.get_nexus_client()
    try:
        nxs.organizations.fetch(org_label=label)
    except nxs.HTTPError as e:
        if e.response.status_code == 404:
            utils.error("Could not find organization with label '%s'." % label)
        else:
            # unexpected error
            utils.print_json(e.response.json(), colorize=True)
            utils.error(str(e))

    utils.set_default_organization(label)
    print("organization selected.")


@orgs.command(name='current', help='Show the currently selected organization')
def current():
    config = utils.get_cli_config()
    profile, selected_config = utils.get_selected_deployment_config(config)
    if selected_config is None:
        utils.error("You must first select a profile using the 'profiles' command")

    default_org = utils.get_default_organization()
    if default_org is not None:
        print(default_org)
    else:
        utils.error("No default organization selected in profile '%s'" % profile)
