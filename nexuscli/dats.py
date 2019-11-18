import json
from collections import OrderedDict

import click
from nexuscli import utils
from nexuscli.cli import cli


"""
    DATS paper:         https://www.nature.com/articles/sdata201759/
    DATS tools:         https://github.com/datatagsuite
                        https://github.com/datatagsuite/dats-tools
    Example datasets:   https://github.com/datatagsuite/examples
    PyLD:               https://pypi.org/project/PyLD/
    rdflib json-ld:     https://github.com/RDFLib/rdflib-jsonld
    Compat rdflib/pyld: https://github.com/zimeon/iiif-ld-demo/tree/master/jsonld-in-python
    rdflib graph to json: https://gist.github.com/edsu/76729/1e1113908c7f13ed1ad03b353de2d1af42a9bfa2
    json-ld:            https://github.com/json-ld/json-ld.org/
    json-ld framing:    https://json-ld.org/spec/latest/json-ld-framing/
    RDF viz:            https://www.w3.org/2018/09/rdf-data-viz/
    JSON Schema:        https://json-schema.org/implementations.html (validators)
    
    Framing             https://json-ld.org/spec/latest/json-ld-framing/#framing
    Framing example:    https://codemeta.github.io/codemetar/articles/JSON-LD-framing.html
                        https://www.carlboettiger.info/2017/05/17/json-ld-framing-strategy/
    
    CONP DATS data:      https://github.com/conpdatasets/
                         https://github.com/conpdatasets/preventad-open/blob/ff3f54de45c31fc0d3f0e55346e14d7b4c64e631/DATS.json
    
    Contexts:
        https://datatagsuite.github.io/context/
        https://github.com/datatagsuite/context/tree/master/sdo
        https://datatagsuite.github.io/context/sdo/dataset_sdo_context.jsonld
        
    Data examples: https://github.com/datatagsuite/examples/blob/master/BDbag-AGR-example.json
    Notebook: https://hub.gke.mybinder.org/user/datatagsuite-dats-tools-bxg5y72t/notebooks/notebooks/dats_agr.ipynb    
"""

# Opened github issues:
#   Context with a bugfix, see https://github.com/datatagsuite/examples/issues/1
#   SDO context issue: https://github.com/datatagsuite/examples/issues/2
#   Typo in Access context: https://github.com/datatagsuite/examples/issues/3

"""
    Potential issues in the DATS SDO context:
        - "Treatmet": "sdo:Thing",
"""


# Public URL for an SDO merged context
# Public github repository: https://github.com/samuel-kerrien/nexus-dats
GLOBAL_SDO_CONTEXT = "https://raw.githubusercontent.com/samuel-kerrien/nexus-dats/master/dats-context-sdo.json"


# TODO Make Access (under distributions) it's own entity
# TODO Add support for Dataset -> DataRepository
# TODO Add support for DatasetDistribution -> DataRepository
# TODO Add support for DatasetDistribution -> DataStandard
# TODO Add support for Dataset -> License
# TODO Add support for Dataset -> Publication
# TODO Add support for Dataset -> DataType
# TODO Add support for Dataset -> Dimension
# TODO Add support for Dimension -> DataType
# TODO Add support for Dataset -> Material
# TODO Add support for Material -> Material
# TODO Add support for Publication -> Grant
# TODO Add support for Grant -> (Organization, Person)


@cli.group()
def dats():
    """DAta Tag Suite (DATS) format related operations"""


def get_entity_by_type_and_property(_type, _property, _value, debug=False):
    _org_label = utils.get_organization_label(None)
    _prj_label = utils.get_project_label(None)
    nxs = utils.get_nexus_client()
    q = """
    PREFIX sdo:<https://schema.org/> 
    SELECT ?s 
    WHERE { 
        ?s a <%s> .
        ?s <%s> ?name .
        FILTER (str(?name) = "%s") . 
    }
    """ % (_type, _property, _value)
    if debug:
        print(q)
    view_id = "nxv:defaultSparqlIndex"
    try:
        response = nxs.views.query_sparql(org_label=_org_label, project_label=_prj_label, query=q, view_id=view_id)
        if len(response["results"]["bindings"]) == 0:
            if debug:
                print("no results")
            return None
        for b in response["results"]["bindings"]:
            return b["s"]["value"]
    except nxs.HTTPError as e:
        print("Failed to load entity by property(%s, '%s') and type (%s)" % (_property, _value, _type))
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


def fetch_by_id(_id, debug=False):
    _org_label = utils.get_organization_label(None)
    _prj_label = utils.get_project_label(None)
    nxs = utils.get_nexus_client()
    try:
        return nxs.resources.fetch(org_label=_org_label, project_label=_prj_label, resource_id=_id)
    except nxs.HTTPError as e:
        # Not found ?
        if e.response.status_code == 404:
            return None
        # Then it's an error
        print("Failed to fetch resource by @id: " + _id)
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


def make_list(payload):
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        return [payload]
    elif isinstance(payload, list):
        return payload
    else:
        utils.error("Unknown type: " + str(type(payload)))


# TODO cache contexts to avoid looking them up multiple times from Nexus
context_saved_in_nexus = {}


def save_context(context_payload, debug=False):
    """
    if context is a string, save context into Nexus using that URL.
    :param context_payload: the context payload (could be a str, dict)
    :param debug: if True, print additional info
    :return:
    """
    if isinstance(context_payload, str):
        context_url = context_payload
        if debug:
            print("context: " + context_url)

        if context_url in context_saved_in_nexus:
            # already looked up before
            if debug:
                print('context already found in Nexus (cached): ' + context_url)
        else:
            # first lookup
            fetched = fetch_by_id(context_url, debug=debug)
            if fetched is None:
                # save it
                import requests
                r = requests.get(context_url)
                context_data = r.json()
                try:
                    _org_label = utils.get_organization_label(None)
                    _prj_label = utils.get_project_label(None)
                    nxs = utils.get_nexus_client()
                    r = nxs.resources.create(org_label=_org_label, project_label=_prj_label, schema_id=None,
                                             data=context_data, resource_id=context_url)
                    # cache outcome
                    context_saved_in_nexus[context_url] = fetched
                    if debug:
                        print("Resource (context) created (id: %s)" % r["@id"])
                except nxs.HTTPError as e:
                    utils.print_json(e.response.json(), colorize=True)
                    utils.error(str(e))
            else:
                # found it
                if debug:
                    print('context found in Nexus: ' + context_url)

                # cache outcome
                context_saved_in_nexus[context_url] = fetched


def save(json_payload, debug=False):
    if debug:
        print("SAVING")
        utils.print_json(json_payload, colorize=True)
        print('---')

    if '@context' in json_payload:
        # check that the context is already in Nexus
        for c in make_list(json_payload['@context']):
            save_context(c, debug=debug)

    _id = None
    if '@id' in json_payload:
        _id = json_payload['@id']
    if _id is None:
        if debug:
            print("No @id in this entity")
    else:
        if debug:
            print("Honoring the entity @id: " + _id)

    _org_label = utils.get_organization_label(None)
    _prj_label = utils.get_project_label(None)
    nxs = utils.get_nexus_client()
    try:
        if _id is not None:
            if debug:
                print("Checking if the entity is already in Nexus, searching by @id: " + _id)
            e = fetch_by_id(_id, debug=debug)
            if e is not None:
                if debug:
                    print("An entity with this id (%s) already exists, skipping saving." % _id)
                return _id

        # saving new entity
        response = nxs.resources.create(org_label=_org_label, project_label=_prj_label, schema_id=None,
                                        data=json_payload, resource_id=_id)
        _type = json_payload['@type']
        print("Resource of type '%s' created (id: %s)" % (_type, response["@id"]))
        if debug:
            utils.print_json(response, colorize=True)
        return response["@id"]
    except nxs.HTTPError as e:
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


def jsonld_expand(jsonld_payload):
    from pyld import jsonld
    return jsonld.expand(jsonld_payload)


def get_expanded_entity_type(jsonld_payload):
    expanded = jsonld_expand(jsonld_payload)
    if '@type' in expanded[0]:
        return expanded[0]['@type'][0]
    else:
        pass
        utils.print_json(jsonld_payload, colorize=True)
        print("EXPANDED TO")
        utils.print_json(expanded, colorize=True)


def jsonld_compact(jsonld_payload):
    from pyld import jsonld
    context = None
    if "@context" in jsonld_payload:
        if isinstance(jsonld_payload['@context'], dict):
            context = jsonld_payload['@context']
        elif isinstance(jsonld_payload['@context'], str):
            url = jsonld_payload['@context']
            import requests
            context = requests.get(url).json()
        else:
            utils.error("Unknown context type: " + type(jsonld_payload['@context']))
    else:
        utils.print_json(jsonld_payload, colorize=True)
        utils.error("Cannot compact JSON-LD without a context")

    return jsonld.compact(input_=jsonld_payload, ctx=context)


def load_dict_into_graph(json_dict):
    import json
    from rdflib import Graph, plugin
    import rdflib_jsonld
    from rdflib.plugin import register, Serializer
    register('json-ld', Serializer, 'rdflib_jsonld.serializer', 'JsonLDSerializer')
    g = Graph()
    return g.parse(data=json.dumps(json_dict), format='json-ld')


def json_for_graph(g):
    """
    Pass in a rdflib.Graph and get back a chunk of JSON using
    the Talis JSON serialization for RDF:
    http://n2.talis.com/wiki/RDF_JSON_Specification
    """
    import json
    import rdflib
    json_dict = {}

    # go through all the triples in the graph
    for s, p, o in g:

        # initialize property dictionary if we've got a new subject
        if not s in json_dict:
            json_dict[s] = {}

        # initialize object list if we've got a new subject-property combo
        if not p not in json_dict[s]:
            json_dict[s][p] = []

        # determine the value dictionary for the object
        v = {'value': str(o)}
        if isinstance(o, rdflib.URIRef):
            v['type'] = 'uri'
        elif isinstance(o, rdflib.BNode):
            v['type'] = 'bnode'
        elif isinstance(o, rdflib.Literal):
            v['type'] = 'literal'
            if o.language:
                v['lang'] = o.language
            if o.datatype:
                v['datatype'] = str(o.datatype)

        # add the triple
        if not p in json_dict[s]:
            json_dict[s][p] = {}
        json_dict[s][p].update(v)

    return json_dict


def add_context_if_missing(json_payload, context):
    if '@context' not in json_payload:
        json_payload['@context'] = context


def add_if_exist(source_dict, target_dict, key):
    if key in source_dict:
        target_dict[key] = source_dict[key]


def remove_all_contexts(json_data):
    for key in list(json_data.keys()):
        if isinstance(json_data[key], dict):
            remove_all_contexts(json_data[key])
        elif isinstance(json_data[key], list):
            for x in json_data[key]:
                if isinstance(x, dict):
                    remove_all_contexts(x)
        else:
            if key == "@context":
                del json_data["@context"]


def save_dataset(source_dict, _context, debug=False):
    # Build the payload to save in Nexus
    add_context_if_missing(source_dict, GLOBAL_SDO_CONTEXT)
    dataset = {
        "@type": source_dict['@type'],
        "@context": _context,
        "title": source_dict["title"]
    }

    # Look up payload for a valid @id
    if '@id' in source_dict:
        dataset['@id'] = source_dict['@id']
    else:
        if 'identifier' in source_dict and 'identifier' in source_dict['identifier']:
            i = source_dict['identifier']['identifier']
            if utils.is_valid_IRI(i):
                if debug:
                    print("Using 'identifier' as @id: %s" % i)
                dataset['@id'] = i

        if '@id' not in dataset and 'alternateIdentifiers' in source_dict:
            for ai in source_dict['alternateIdentifiers']:
                if utils.is_valid_IRI(ai["identifier"]):
                    if debug:
                        print("Using 'alternateIdentifiers' as @id: %s" % ai["identifier"])
                    dataset['@id'] = ai["identifier"]
                    break

    if 'creators' in source_dict:
        for c in source_dict['creators']:
            if len(c) == 0:
                if debug:
                    print("Skipping empty creator")
                continue;

            add_context_if_missing(c, _context)

            creator_refs = []
            affiliation_refs = []
            if "affiliations" in c:
                for a in c['affiliations']:
                    add_context_if_missing(a, _context)
                    _type = get_expanded_entity_type(a)
                    e = get_entity_by_type_and_property(_type, 'https://schema.org/name', a['name'], debug=debug)
                    if e is not None:
                        # found it in Nexus, reuse it
                        affiliation_refs.append({
                            "@id": e,
                            "@type": _type
                        })
                    else:
                        # doesn't exist, save it and reuse id
                        e = save(a, debug=debug)
                        affiliation_refs.append({
                            "@id": e,
                            "@type": a['@type']
                        })

            # replace original creator payload with affiliations in Nexus
            c['affiliations'] = affiliation_refs

            if '@id' not in c:
                creator_id = save(c, debug=debug)
            else:
                if fetch_by_id(c['@id'], debug=debug) is None:
                    creator_id = save(c, debug=debug)
                else:
                    creator_id = c['@id']

            _type = get_expanded_entity_type(c)
            creator_refs.append({
                "@id": creator_id,
                "@type": _type
            })

            dataset["creators"] = creator_refs

    if "distributions" in source_dict:
        distribution_refs = []
        for d in source_dict['distributions']:
            add_context_if_missing(d, _context)
            distribution_id = save(d, debug=debug)
            _type = get_expanded_entity_type(d)
            distribution_refs.append({
                "@id": distribution_id,
                "@type": _type
            })
        dataset['distributions'] = distribution_refs

    if "hasPart" in source_dict:
        sub_dataset_refs = []
        for d in source_dict['hasPart']:
            sub_dataset_id = save_dataset(d, _context, debug=debug)
            _type = get_expanded_entity_type(d)
            sub_dataset_refs.append({
                "@id": sub_dataset_id,
                "@type": _type
            })
        dataset["hasPart"] = sub_dataset_refs

    # Add optional properties that don't involve entity relations
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="description")
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="identifier")
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="alternateIdentifiers")
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="dates")
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="types")
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="extraProperties")

    return save(dataset, debug=debug)


def process_register_context(file, context_id, debug):
    with open(file) as json_file:
        context_data = json.load(json_file)

    _org_label = utils.get_organization_label(None)
    _prj_label = utils.get_project_label(None)
    nxs = utils.get_nexus_client()
    try:
        if context_id is not None:
            if debug:
                print("Checking if the context is already in Nexus, searching by @id: " + context_id)
            e = fetch_by_id(context_id, debug=debug)
            if e is not None:
                if debug:
                    print("An entity with this id (%s) already exists, updating...")
                context_data['@id'] = context_id
                context_data['_self'] = e["_self"]
                response = nxs.resources.update(resource=context_data, rev=e["_rev"])
                if debug:
                    print("Context updated (id: %s)" % response["@id"])
            else:
                # saving new context
                response = nxs.resources.create(org_label=_org_label, project_label=_prj_label, schema_id=None,
                                                data=context_data, resource_id=context_id)
                if debug:
                    print("Context created (id: %s)" % response["@id"])
                    utils.print_json(response, colorize=True)
                return response["@id"]
    except nxs.HTTPError as e:
        print("Failed to load context into Nexus.")
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


def get_code_root_directory():
    import os
    return os.path.dirname(os.path.realpath(__file__)) + "/.."


@dats.command(name='build-merged-context', help='Merge all DATS contexts into a single file')
@click.option('--debug', is_flag=True, default=False, help='Print debug statements')
def build_merged_context(debug):
    print("1 - SDO")
    print("2 - OBO")
    print("3 - DCAT")
    choice = -1
    while choice not in (1, 2, 3):
        choice = int(input("Please select your context: "))

    choices = ['sdo', 'obo', 'dcat']

    context_paths = [
        "/context/sdo",
        "/context/obo",
        "/context/dcat"
    ]

    import git, tempfile
    temp_dir = tempfile.mkdtemp(prefix='tmp')
    if debug:
        print(temp_dir)
    git.Git(temp_dir).clone("https://github.com/datatagsuite/context")
    context_dir = temp_dir + context_paths[choice-1]

    # merge file with an extension '.jsonld'
    import glob
    merged_context = {}
    errors = 0
    for f in glob.glob(context_dir + "/*.jsonld"):
        if debug:
            print("\n--- " + f)
        with open(f) as json_file:
            c = json.load(json_file)
            if debug:
                utils.print_json(c, colorize=True)
            if len(c) == 1:
                if '@context' in c:
                    c = c['@context']
            else:
                # buggy context?
                print("[ERROR] Unexpected count of keys, expected 1: " + str(len(c)))
                print(f)
                errors += 1
                continue  # skip this file, don't merge it

            merged_context.update(c)

    final_merged_context = {
        '@context': OrderedDict(sorted(merged_context.items(), key=lambda i: i[0].lower()))
    }

    if debug:
        print("\n--- Merged context:")
        utils.print_json(final_merged_context, colorize=True)

    if errors > 0:
        print("------ %s errors" % errors)

    filename = 'dats-context-' + choices[choice-1] + '.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(final_merged_context, f, indent=2)
    print("Merged context saved: " + filename)

    # cleanup
    import shutil
    shutil.rmtree(temp_dir)


@dats.command(name='register-context', help='Load a given context into Nexus')
@click.argument('file')
@click.argument('context_id')
@click.option('--debug', is_flag=True, default=False, help='Print debug statements')
def register_context(file, context_id, debug):
    process_register_context(file=file, context_id=context_id, debug=debug)


@dats.command(name='load', help='Load given DATS file in Nexus')
@click.argument('file')
@click.option('_override_context', '--override-context', default=GLOBAL_SDO_CONTEXT,
              help='The id of a context stored in Nexus to be use as drop-in replacement for DATS''')
@click.option('--debug', is_flag=True, default=False, help='Print debug statements')
def load(file, _override_context, debug):
    if debug:
        print("Loading file: " + file)

    # Check if DATS-SDO context already exists in Nexus, if not, register it
    context_file_path = get_code_root_directory() + "/dats/dats-context-sdo.json"
    process_register_context(file=context_file_path, context_id=GLOBAL_SDO_CONTEXT, debug=False)

    with open(file) as json_file:
        json_data = json.load(json_file)
        remove_all_contexts(json_data)
        save_dataset(json_data, _override_context, debug=debug)


@dats.command(name='search', help='Search for DATS datasets in Nexus (using ElasticSearchView)')
@click.argument('query')
@click.option('_from', '--from', default=0, help='index of the first entity to return (default:0, ie. the first one)')
@click.option('_page_size', '--page-size', default=100, help='Page size (default:100)')
@click.option('--field', help='Field targeted by the search (default: _all_fields)')
@click.option('--exact', is_flag=True, default=False,
              help='If set, will only match exact text. If not, use fuzzy search.')
@click.option('--fuzziness', default=2, help='Level of fuzziness in string matching (default: 0, i.e. none).')
@click.option('--debug', is_flag=True, default=False, help='Print debug statements')
def search(query, _from, _page_size, field, exact, fuzziness, debug):
    default_field = '_all_fields'
    if exact and fuzziness>0:
        utils.error("You cannot request an exact query with fuzziness greater than zero (%s)" % fuzziness)

    _org_label = utils.get_organization_label(None)
    _prj_label = utils.get_project_label(None)
    nxs = utils.get_nexus_client()

    # create ElasticSearchView for datasets if missing
    (_, config) = utils.get_selected_deployment_config()
    nexus_base_url = config['url']
    view_id = "%s/resources/%s/%s/_/DatsDatasetsElasticSearchView" % (nexus_base_url, _org_label, _prj_label)
    _view = fetch_by_id(view_id)
    if _view is None:
        print("Creating ElasticSearch View for DATS Datasets...")
        # load definition
        view_definition_file = get_code_root_directory() + "/dats/dataset-es-view.json"
        with open(view_definition_file) as json_file:
            view_definition = json.load(json_file)
            # create view in Nexus
            try:
                nxs.views.create_(org_label=_org_label, project_label=_prj_label, payload=view_definition, view_id=view_id)
                if debug:
                    print("View created")
            except nxs.HTTPError as e:
                print("Failed to create ElasticSearchView for Dataset.")
                utils.print_json(e.response.json(), colorize=True)
                utils.error(str(e))
    else:
        if debug:
            print("View already exist: " + view_id)

    # Before querying, verify that the view is fully indexed, if not, wait...
    wait_for_view_indexing_to_complete(view_id=view_id, debug=debug)

    try:
        _field = default_field
        if field is not None:
            _field = field
        es_query = {
            "from": _from,
            "size": _page_size,
            "query": {
                "match": {
                    _field: {
                        "query": query
                    }
                }
            }
        }

        if not exact and fuzziness is not None:
            es_query['query']['match'][_field]['fuzziness'] = int(fuzziness)

        if debug:
            print("\nElasticSearch Query:")
            utils.print_json(es_query, colorize=True)

        response = nxs.views.query_es(org_label=_org_label, project_label=_prj_label, view_id=view_id, query=es_query)
        from prettytable import PrettyTable
        import collections
        table = PrettyTable(['Id', 'Title', 'Description'])
        table.align["Id"] = "l"
        table.align["Title"] = "l"
        table.align["Description"] = "l"
        for r in response["hits"]["hits"]:
            _description = ""
            if "description" in r["_source"]:
                _description = r["_source"]["description"]
            table.add_row([r["_source"]["@id"], r["_source"]["title"], _description])
        doc_count = response['hits']['total']['value']
        print("Total results: %s (took: %sms)" % (doc_count, response['took']))
        if doc_count > _page_size:
            utils.warn("WARNING - There is more data to be shows, increase the page size using: --page-size")
        print(table)

        if debug:
            print("Raw ElasticSearch response:")
            utils.print_json(response, colorize=True)
    except nxs.HTTPError as e:
        print("Failed to execute ElasticSearch query: '%s'" % query)
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


def wait_for_view_indexing_to_complete(view_id, debug):
    _org_label = utils.get_organization_label(None)
    _prj_label = utils.get_project_label(None)
    nxs = utils.get_nexus_client()
    completed = False
    try:
        while not completed:
            response = nxs.views.stats(org_label=_org_label, project_label=_prj_label, view_id=view_id)
            if debug:
                utils.print_json(response, colorize=True)
            remaining = int(response["remainingEvents"])
            if remaining == 0:
                completed = True
                if debug:
                    print("Indexing complete")
            else:
                if debug:
                    print("Waiting for indexing to complete (%s left)..." % remaining)
                import time
                time.sleep(2)  # sleep 2 seconds

    except nxs.HTTPError as e:
        print("Failed to wait for view to complete indexing: '%s'" % view_id)
        utils.print_json(e.response.json(), colorize=True)
        utils.error(str(e))


@dats.command(name='show-schema', help='Render picture of the overall DATS data model')
def show_schema():
    path = get_code_root_directory() + "/dats/sdata201759-f1.jpg"
    from PIL import Image
    im = Image.open(path)
    im.show()
