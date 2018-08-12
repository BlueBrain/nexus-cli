import click
import requests
import json
from blessings import Terminal
from http.client import responses

import config_utils
import nexus_utils
import utils


t = Terminal()


@click.command()
@click.option('entity_type', '--type', '-t', help='The entity type to search for.')
@click.option('--context', '-c', help='Override default context.')
@click.option('--field', '-f', help='The field to filter on.')
@click.option('--value', '-v', help='The field value to filter on.')
@click.option('--show-query', '-s', is_flag=True, help='print the generated search query')
@click.option('--pretty', '-p', is_flag=True, help='colorize output')
@click.option('--show-entities', '-e', is_flag=True, help='Fetch full payload for each entity, otherwise show only ID')
@click.option('--max-entities', '-m', type=int, help='Limits the number of results to show')
@click.option('--verbose', '-v', is_flag=True, help='Prints additional information')
def search(entity_type, context, field, value, show_query, pretty, show_entities, max_entities, verbose):
    """Search Nexus."""
    if entity_type is None and (field is None or value is None):
        utils.error("You must give a query parameter, either --type or --field/--value")

    if field is not None and value is None:
        utils.error("if you provide a field, you must give a value")

    if value is not None and field is None:
        utils.error("if you provide a value, you must give a field")

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
    results = nexus_utils.search(query, fetch_entities=show_entities, max_results=max_entities, authenticate=True, verbose=verbose)
    for item in results:
        if type(item) is dict:
            utils.print_json(item, colorize=pretty)
        else:
            print(item)
