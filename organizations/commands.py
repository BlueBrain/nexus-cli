import click
from blessings import Terminal
from prettytable import PrettyTable

import config_utils
import nexus_utils
import utils


t = Terminal()


@click.command()
@click.option('--add', '-a', help='Name of the nexus organization to be locally added')
@click.option('--deprecate', '-r', help='Name of the nexus organization to be locally deprecated')
@click.option('do_list', '--list', '-l', is_flag=True, help='List all nexus organization registered')
@click.option('--public-only', '-p', is_flag=True, default=False, help='List only public datasets (i.e. no authentication)')
@click.option('--no-format', '-n', is_flag=True, default=False, help='Present output without table formatting')
def organizations(add, deprecate, do_list, public_only, no_format):
    """Manage Nexus organizations."""
    if do_list is not None:
        c, active_deployment_cfg = config_utils.get_selected_deployment_config()
        if c is None:
            utils.error("You must select a deployment using `deployment --select` prior to running this command.")

        url = active_deployment_cfg['url'] + "/v0/organizations"
        if public_only:
            print("Limiting results to publicly accessible records")
            authenticate = False
        else:
            authenticate = True
        data = nexus_utils.get_results_by_uri(url, authenticate=authenticate)
        total = data[1]
        results = data[0]

        if no_format:
            for item in results:
                org_url = item['resultId']
                org_name = org_url.rsplit("/", 1)[1]
                print("%s,%s"% (org_name, org_url))
        else:
            columns = ["Organization name", "URL"]
            table = PrettyTable(columns)
            table.align[columns[0]] = "l"
            table.align[columns[1]] = "l"
            for item in results:
                org_url = item['resultId']
                org_name = org_url.rsplit("/", 1)[1]
                table.add_row([org_name, org_url])
            print(table)
            if len(results) == total:
                print(t.green('Total:' + str(total)))
            else:
                print(t.green('Total: %d of %d' % (str(len(results)), str(total))))

    if add is not None:
        utils.error("--add not implemented yet")

    if deprecate is not None:
        utils.error("--deprecate not implemented yet")

