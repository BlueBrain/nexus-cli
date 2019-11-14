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
    
    CONP DATS data:     https://github.com/conpdatasets/preventad-open/blob/ff3f54de45c31fc0d3f0e55346e14d7b4c64e631/DATS.json
    
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
    Potential issues in the SDO context:
        - "Treatmet": "sdo:Thing",
        

"""

# global context repo: https://github.com/samuel-kerrien/nexus-dats
GLOBAL_SDO_CONTEXT = "https://raw.githubusercontent.com/samuel-kerrien/nexus-dats/master/dats-context-sdo.json"


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
        print("No @id in this entity")
    else:
        print("Honoring the entity @id: " + _id)

    _org_label = utils.get_organization_label(None)
    _prj_label = utils.get_project_label(None)
    nxs = utils.get_nexus_client()
    try:
        if _id is not None:
            print("Checking if the entity is already in Nexus, searching by @id: " + _id)
            e = fetch_by_id(_id, debug=debug)
            if e is not None:
                if debug:
                    print("An entity with this id (%s) already exists, skipping saving." % _id)
                return _id

        # saving new entity
        response = nxs.resources.create(org_label=_org_label, project_label=_prj_label, schema_id=None,
                                        data=json_payload, resource_id=_id)
        if debug:
            print("Resource created (id: %s)" % response["@id"])
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
        # print("--- triple'")
        # print(str(type(s)) + " > " + str(s))
        # print(str(type(p)) + " > " + str(p))
        # print(str(type(v)) + " > " + str(v))
        if not p in json_dict[s]:
            json_dict[s][p] = {}
        json_dict[s][p].update(v)

    return json_dict


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


@dats.command(name='load', help='Load a DATS file in Nexus')
@click.argument('file')
@click.option('_override', '--override-context', is_flag=True, default=False,
              help='the id of a context stored in Nexus to be use as drop-in replacement for DATS''')
@click.option('--debug', is_flag=True, default=False, help='Print debug statements')
def load(file, _override, debug):
    if debug:
        print("Loading file: " + file)

    with open(file) as json_file:
        json_data = json.load(json_file)
        remove_all_contexts(json_data)
        save_dataset(json_data, debug=debug)


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


def save_dataset(source_dict, debug=False):
    # Build the payload to save in Nexus
    # source_dict['@context']

    add_context_if_missing(source_dict, GLOBAL_SDO_CONTEXT)

    dataset = {
        "@type": source_dict['@type'],
        "@id": source_dict['@id'],
        "@context": GLOBAL_SDO_CONTEXT,
        "title": source_dict["title"]
    }

    if 'creators' in source_dict:
        for c in source_dict['creators']:
            if len(c) == 0:
                if debug:
                    print("Skipping empty creator")
                continue;

            add_context_if_missing(c, GLOBAL_SDO_CONTEXT)

            creator_refs = []
            affiliation_refs = []
            if "affiliations" in c:
                for a in c['affiliations']:
                    add_context_if_missing(a, GLOBAL_SDO_CONTEXT)
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
            add_context_if_missing(d, GLOBAL_SDO_CONTEXT)
            # if 'access' in d:
            #     if '@context' in source_dict['distributions']:
            #         for c in make_list(source_dict['distributions']['@context']):
            #             save_context(c, debug=debug)
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
            sub_dataset_id = save_dataset(d, debug=debug)
            _type = get_expanded_entity_type(d)
            sub_dataset_refs.append({
                "@id": sub_dataset_id,
                "@type": _type
            })
        dataset["hasPart"] = sub_dataset_refs

    # Add optional properties that don't involve entity relations
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="description")

    # Save context of identifier in Nexus prior to saving since this will not be stored in a separate linked entity
    # if 'identifier' in source_dict:
    #     if '@context' in source_dict['identifier']:
    #         for c in make_list(source_dict['identifier']['@context']):
    #             save_context(c, debug=debug)
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="identifier")
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="dates")
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="types")
    add_if_exist(source_dict=source_dict, target_dict=dataset, key="extraProperties")

    return save(dataset, debug=debug)


def add_context_if_missing(json_payload, context):
    if '@context' not in json_payload:
        json_payload['@context'] = context


def add_if_exist(source_dict, target_dict, key):
    if key in source_dict:
        target_dict[key] = source_dict[key]


@dats.command(name='show-schema', help='Show the overall DATS data model')
def show_schema():
    from PIL import Image
    im = Image.open(r"/Users/kerrien/Projects/Nexus/nexus-cli/dats/sdata201759-f1.jpg")
    im.show()


@dats.command(name='visualise', help='render the graph of a given DATS file')
@click.argument('file')
def visualise(file):
    """
        to explore:
            https://www.w3.org/2018/09/rdf-data-viz/
            https://www.oclc.org/developer/news/2016/making-sense-of-linked-data-with-python.en.html
            https://stackoverflow.com/questions/39274216/visualize-an-rdflib-graph-in-python
    """
    print("Loading file: " + file)

    import json
    from rdflib import Graph, plugin
    import rdflib_jsonld
    from rdflib.plugin import register, Serializer
    register('json-ld', Serializer, 'rdflib_jsonld.serializer', 'JsonLDSerializer')

    with open(file) as json_file:
        data = json.load(json_file)

    # context = {
    #     "@context": {
    #         "foaf": "http://xmlns.com/foaf/0.1/",
    #         "vcard": "http://www.w3.org/2006/vcard/ns#country-name",
    #         "job": "http://example.org/job",
    #
    #         "name": {"@id": "foaf:name"},
    #         "country": {"@id": "vcard:country-name"},
    #         "profession": {"@id": "job:occupation"},
    #     }
    # }

    x = [{"name": "bert", "country": "antartica", "profession": "bear"}]
    g = Graph()
    # g.parse(data=json.dumps(x), format='json-ld', context=context)
    result = g.parse(data=json.dumps(x), format='json-ld')

    import rdflib
    from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
    import networkx as nx
    import matplotlib.pyplot as plt

    # url = 'https://www.w3.org/TeamSubmission/turtle/tests/test-30.ttl'
    # g = rdflib.Graph()
    # result = g.parse(url, 'ttl')

    G = rdflib_to_networkx_multidigraph(result)

    # Plot Networkx instance of RDF Graph
    pos = nx.spring_layout(G, scale=2)
    edge_labels = nx.get_edge_attributes(G, 'r')
    nx.draw_networkx_edge_labels(G, pos, labels=edge_labels)
    nx.draw(G, with_labels=True)

    g.close()