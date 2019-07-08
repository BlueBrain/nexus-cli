import click
from prettytable import PrettyTable

from nexuscli import utils
from nexuscli.cli import cli


@cli.group()
def realms():
    """Realms operations"""


@realms.command(name='create', help='Create a new realm')
@click.argument('label')
@click.option('--name', '-n', help='The name given to the resource')
@click.option('_open_id_config', '--open-id-config-url', '-o', help='The URL to the "well-known" OpenID configuration')
@click.option('--logo', '-l', default=None, help='An optional URL to a logo')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def create(label, name, _open_id_config, logo, _json, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.realms.create(label, name, _open_id_config, logo)
        if _json:
            utils.print_json(response, colorize=pretty)
        utils.success("Realm created.")
    except nxs.HTTPError as e:
        print(e.response.json())
        utils.error(str(e))


@realms.command(name='update', help='Update a realm')
@click.argument('label')
@click.option('--data', '-d', help='Payload to replace it with')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def update(label, data, _json, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.realms.replace_(label, data, data['_rev'])
        if _json:
            utils.print_json(response, colorize=pretty)
        utils.success("Realm updated.")
    except nxs.HTTPError as e:
        print(e.response.json())
        utils.error(str(e))


@realms.command(name='list', help='List all realms')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def _list(_json, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.realms.list()
        if _json:
            utils.print_json(response, colorize=pretty)
        else:
            table = PrettyTable(['Label', 'Name', 'Issuer', 'Revision', 'Deprecated'])
            table.align["Issuer"] = "l"
            table.align["Revision"] = "l"
            table.align["Deprecated"] = "l"
            for r in response["_results"]:
                table.add_row([r["_label"], r["name"], r["_issuer"], r["_rev"], r["_deprecated"]])

            print(table)
    except nxs.HTTPError as e:
        print(e.response.json())
        utils.error(str(e))


@realms.command(name='deprecate', help='Deprecate a realm')
@click.argument('label')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def deprecate(label, _json, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.realms.deprecate(label)
        if _json:
            utils.print_json(response, colorize=pretty)

        utils.success("Realm deprecated.")
    except nxs.HTTPError as e:
        print(e.response.json())
        utils.error(str(e))


@realms.command(name='fetch', help='Fetch a realm')
@click.argument('label')
@click.option('--revision', '-r', default=None, type=int, help='Fetch the realm at a specific revision')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def fetch(label, revision, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.realms.fetch(label, revision)
        utils.print_json(response, colorize=pretty)
    except nxs.HTTPError as e:
        print(e.response.json())
        utils.error(str(e))


@realms.command(name='select', help='Select a realm')
@click.argument('label')
@click.option('_json', '--json', '-j', is_flag=True, default=False, help='Print JSON payload returned by the nexus API')
@click.option('--pretty', is_flag=True, default=False, help='Colorize JSON output')
def select(label, _json, pretty):
    nxs = utils.get_nexus_client()
    try:
        response = nxs.realms.fetch(label)
        if _json:
            utils.print_json(response, colorize=pretty)
        utils.set_default_realm(label, response['_issuer'])
        utils.success("Realm selected.")
    except nxs.HTTPError as e:
        print(e.response.json())
        utils.error(str(e))


@realms.command(name='current', help='Show currently selected realm')
def current():
    realm = utils.get_default_realm()
    if realm is None:
        utils.warn("No realm selected.")
    else:
        print(realm['_label'])
