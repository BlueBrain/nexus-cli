import click
from blessings import Terminal

import json, os
import nexus_utils
import utils


t = Terminal()


@click.command()
@click.option('--organization', '-o', help='The organization to search into.')
@click.option('--domain', help='The domain to search into (you must also give an organization).')
@click.option('entity_type', '--type', '-t', help='The entity type to search for.')
@click.option('--context', '-c', help='Override default context.')
@click.option('--field', '-f', help='The field to filter on.')
@click.option('--value', '-v', help='The field value to filter on.')
@click.option('--query-file', '-q', help='Provide the query from a file.')
@click.option('--show-query', '-s', is_flag=True, help='print the generated search query')
@click.option('--pretty', '-p', is_flag=True, help='colorize output')
@click.option('--show-entities', '-e', is_flag=True, help='Fetch full payload for each entity, otherwise show only ID')
@click.option('--max-entities', '-m', type=int, help='Limits the number of results to show')
@click.option('--download', '-d', is_flag=True, help='Download metadata and data (if available)')
@click.option('--download-directory', '-D', default='.', help='Where to download metadata and attachments (will create if not found)')
@click.option('--verbose', '-v', is_flag=True, help='Prints additional information')
def search(organization, domain, entity_type, context, field, value, query_file, show_query, pretty, show_entities, max_entities, download, download_directory, verbose):
    """Search Nexus."""
    if query_file is not None and (entity_type is not None or field is not None or value is not None):
        utils.error("You must either use --query-file or (--type, --field, --value)")
    elif query_file is None:
        if entity_type is None and (field is None or value is None):
            utils.error("You must give a query parameter, either --type or --field/--value")

    if field is not None and value is None:
        utils.error("if you provide a field, you must give a value")

    if value is not None and field is None:
        utils.error("if you provide a value, you must give a field")

    query = None
    if query_file is not None:
        with open(query_file) as f:
            query = json.load(f)
    else:
        default_context = "https://bbp.epfl.ch/nexus/v0/contexts/neurosciencegraph/core/data/v1.0.3"
        if context is not None:
            c = context
        else:
            c = default_context

        query = {
                  "@context": c,
                  "filter": {
                    "op": "and",
                    "value": []
                  }
                }

        if entity_type is not None:
            query['filter']['value'].append({
                                                "op": "eq",
                                                "path": "rdf:type",
                                                "value": entity_type
                                              })

        if field is not None:
            query['filter']['value'].append({
                "op": "eq",
                "path": field,
                "value": value
            })

    if show_query:
        utils.print_json(query, colorize=pretty)

    # execute query
    results = nexus_utils.search(query, organization, domain, fetch_entities=True, max_results=max_entities, authenticate=True, verbose=verbose)
    for item in results:
        if show_entities:
            utils.print_json(item, colorize=pretty)
        else:
            print(item['@id'])

        if download:
            if download_directory is not None:
                download_directory = os.path.abspath(download_directory)
                if not os.path.exists(download_directory):
                    os.makedirs(download_directory)

            _id = item['@id']
            uuid = _id.split("/")[-1:][0]
            local_dir = download_directory + "/" + uuid
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            with open(local_dir + '/metadata.json', 'w') as outfile:
                json.dump(item, outfile, indent=2)

            # download data if any attachment
            if 'distribution' in item:
                distribution = item['distribution']
                filenames = set()
                for d in distribution:
                    if type(d) is list:
                        print(t.red("WARNING found list in distribution - SKIPPING"))
                        continue
                    filename = d['originalFileName']
                    if filename in filenames:
                        print(t.red("It appears this attachment is duplicated: " + filename + " - SKIPPING"))
                    else:
                        filenames.add(filename)
                        nexus_utils.download_file(d, local_dir, verbose=True)
