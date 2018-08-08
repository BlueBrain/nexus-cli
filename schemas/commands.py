import click
from blessings import Terminal
from prettytable import PrettyTable

import config_utils
import nexus_utils
import utils


t = Terminal()


@click.command()
@click.option('--list', '-l', is_flag=True, help='List all nexus schemas registered')
@click.option('--organization', '-o', help='The organisation for which to list schemas')
@click.option('--domain', '-d', help='The domain for which to list schemas')
@click.option('--public-only', '-p', is_flag=True, default=False, help='List only public datasets (i.e. no authentication)')
@click.option('--download', '-d', help='List only public datasets (i.e. no authentication)')
def schemas(list, organization, domain, public_only, download):
    """Manage Nexus schemas."""
    if list is not None:
        if organization is None:
            utils.error("You must select an organisation using --organization")
        if domain is None:
            utils.error("You must select an domain using --domain")

        c = config_utils.get_selected_deployment_config()
        if c is None:
            utils.error("You must select a deployment using `deployment --select` prior to running this command.")
        active_deployment_cfg = c[1]

        url = active_deployment_cfg['url'] + "/v0/schemas/" + organization + '/' + domain
        if public_only:
            print("Limiting results to publicly accessible records")
            authenticate = False
        else:
            authenticate = True
        data = nexus_utils.get_results_by_uri(url, authenticate=authenticate)
        total = data[1]
        results = data[0]

        columns = ["Schema name", "Version", "URL"]
        table = PrettyTable(columns)
        table.align[columns[0]] = "l"
        table.align[columns[1]] = "l"
        table.align[columns[2]] = "l"
        for item in results:
            schema_url = item['resultId']
            split = schema_url.rsplit("/", 2)
            schema_name = split[1]
            schema_version = split[2]
            table.add_row([schema_name, schema_version, schema_url])
        print(table)
        if len(results) == total:
            print(t.green('Total:' + str(total)))
        else:
            print(t.green('Total: %d of %d' % (str(len(results)), str(total))))

