import click
import os
import requests
import json
from blessings import Terminal
from http.client import responses

import config_utils
import nexus_utils
import utils


t = Terminal()


@click.command()
@click.option('--entity-type', '-t', help='The entity type to search for.')
@click.option('--field', '-f', help='The field to filter on.')
@click.option('--value', '-v', help='The field value to filter on.')
@click.option('--show-query', '-s', is_flag=True, help='print the generated search query')
@click.option('--pretty', '-p', is_flag=True, help='colorize output')
def search(entity_type, field, value, show_query, pretty):
    """Search Nexus."""

    query = {
              "@context": "https://bbp.epfl.ch/nexus/v0/contexts/neurosciencegraph/core/data/v1.0.3",
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

    if field is not None and value is None:
        utils.error("if you provide a field, you must give a value")

    if value is not None and field is None:
        utils.error("if you provide a value, you must give a field")

    if field is not None:
        query['filter']['value'].append({
            "op": "eq",
            "path": field,
            "value": value
        })

    if show_query:
        utils.print_json(query, colorize=pretty)

    # execute query

    search_url = config_utils.get_selected_deployment_config()[1]['url'] + "/v0/queries"
    headers = {"Content-Type": "application/json"}
    access_token = config_utils.get_access_token()
    if access_token is not None:
        headers["Authorization"] = "Bearer " + access_token

    r = requests.post(search_url, data=query, headers=headers)
    if r.status_code != 200:
        utils.error("Failed to search from URL: " + search_url +
                    '\nRequest status: ' + str(r.status_code) + ' (' + responses[r.status_code] + ')')

    # TODO print results


