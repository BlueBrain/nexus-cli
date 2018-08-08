import click
from blessings import Terminal
from prettytable import PrettyTable

import config_utils
import nexus_utils
import utils


t = Terminal()


@click.command()
@click.option('--list', '-l', is_flag=True, help='List all nexus organization registered')
@click.option('--organization', '-o', help='The organisation for which to list domains')
@click.option('--public-only', '-p', is_flag=True, default=False, help='List only public datasets (i.e. no authentication)')
def domains(list, organization, public_only):
    """Manage Nexus domains."""
    if list is not None:
        if organization is None:
            utils.error("You must select an organisation using --organization")

        c = config_utils.get_selected_deployment_config()
        if c is None:
            utils.error("You must select a deployment using `deployment --select` prior to running this command.")
        active_deployment_cfg = c[1]

        url = active_deployment_cfg['url'] + "/v0/domains/" + organization
        if public_only:
            print("Limiting results to publicly accessible records")
            authenticate = False
        else:
            authenticate = True
        data = nexus_utils.get_results_by_uri(url, authenticate=authenticate)
        total = data[1]
        results = data[0]

        columns = ["Domain name", "URL"]
        table = PrettyTable(columns)
        table.align[columns[0]] = "l"
        table.align[columns[1]] = "l"
        for item in results:
            domain_url = item['resultId']
            domain_name = domain_url.rsplit("/", 1)[1]
            table.add_row([domain_name, domain_url])
        print(table)
        if len(results) == total:
            print(t.green('Total:' + str(total)))
        else:
            print(t.green('Total: %d of %d' % (str(len(results)), str(total))))

