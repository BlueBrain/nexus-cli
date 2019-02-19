from nexuscli import helpers

from nexuscli import utils

from urllib.parse import quote
import requests

from rdflib_jsonld.util import  urljoin
from rdflib_jsonld import errors
from rdflib_jsonld.keys import (BASE, CONTAINER, CONTEXT, GRAPH, ID, INDEX, LANG, LIST,
                                REV, SET, TYPE, VALUE, VOCAB)
import json
from nexuscli.helpers import filehelper

import nexussdk as nxs

DEPRECATED = "owl:deprecated"
UPDATE_IF_EXISTS = "UPDATE_IF_EXISTS"
UPDATE_IF_DIFFERENT = "UPDATE_IF_DIFFERENT"

def __fill_placeholders(template, placeholder, base):
    if placeholder and base:
        template = template.replace(placeholder, base)
        # in our structure, the port is already included within the host string -
        # to make sure we don't have any broken namespaces, we have to remove it from the template
    return template


def _remove_version(self, source_uri):
    odsv = str(source_uri).split("/schemas/")[1]
    nx_resources = odsv.split("/")
    if len(nx_resources) == 4:
        org = nx_resources[0]
        dom = nx_resources[1]
        schema_name = nx_resources[2]
        version = nx_resources[3]
        source_uri = source_uri.replace("/" + str(version), '')

    return source_uri





def _prep_schemas_sources(inputs, sources, schemas_lookup_base,_schemas_ns,referenced_contexts=None, in_source_url=None):
    referenced_contexts = referenced_contexts or set()

    for source in inputs:
        if isinstance(source, str):

            source_uri = source

            k,v= next((k,v) for k,v in schemas_lookup_base.items() if str(source).startswith(k) )
            source = __fill_placeholders(source, k,v)

            source_file_path = source + "/schema.json"
            if filehelper.is_file(source_file_path) == False:
                source_parts = source_uri.split("/")

                results = filehelper.find_all(source_parts[-1], v)


                source =__fill_placeholders(source_uri, placeholder=_schemas_ns ,base=results[0].rstrip('\/'))

                source_file_path = source + "/schema.json"
            # source = self._remove_version(source)

            source = source_file_path if filehelper.is_file(source_file_path) else source


            source_url = urljoin(v, source)

            if source_url not in referenced_contexts:
                referenced_contexts.add(source_url)
                try:
                    source = _get_resource_by_adress(source_url)

                except ResourceNotFoundException as rnfe:
                    message = """Failed to build the transitive import closure of the schema %s.""" % (source_url)
                    raise OWLImportException(message) from rnfe
                if '@type' in source:
                    source["@id"] = source_uri
                if 'imports' in source:
                    _prep_schemas_sources(source['imports'], sources, schemas_lookup_base,_schemas_ns,referenced_contexts, source_url)

        else:
            source_url = in_source_url
        if isinstance(source, list):
            _prep_schemas_sources(source, sources, schemas_lookup_base,_schemas_ns,referenced_contexts, source_url)
        else:
            sources.append((source_url, source))


def _get_resource_by_adress(source_url):
    if filehelper.is_file(source_url):
        source = filehelper.open_as_json(source_url)

    else:
        # The resource is taken from Nexus
        nxs = utils.get_nexus_client()
        _org_label = utils.get_organization_label()
        _prj_label = utils.get_project_label()
        source = nxs.schemas.fetch(org_label=_org_label, project_label=_prj_label, schema_id=source_url)

    if source is None:
        message = """Failed to find the resource %s.""" % source_url
        raise ResourceNotFoundException(message)
    return source


def get_schema_transitive_import_closure(schema_json,schemas_lookup_base,_schemas_ns):
    imported_schemas = schema_json["imports"]
    sources = []
    imported_schemas = imported_schemas if isinstance(imported_schemas, list) else [imported_schemas]

    _prep_schemas_sources(imported_schemas, sources,schemas_lookup_base,_schemas_ns)
    return sources

def _import_schema(url, schema, _org_label, _prj_label,_strategy ):
    nxs = utils.get_nexus_client()
    if "@id" in schema:
        schema_uri = schema["@id"]
        try:
            schema_in_nexus = nxs.schemas.fetch(org_label=_org_label, project_label=_prj_label, schema_id=schema_uri)
            schema_in_nexus = json.loads(json.dumps(schema_in_nexus))
            current_revision = 0
            if "_rev" in schema_in_nexus:
                current_revision = schema_in_nexus["_rev"]
            # The schema exists

            if "_self" in schema_in_nexus:
                schema["_self"] =schema_in_nexus["_self"]
            else:
                raise SchemaBadFrameException("The schema {} as retrieved from Nexus is not correctly shapes: missing the _self key".format(schema_uri))
            if _strategy == UPDATE_IF_DIFFERENT:
                schema_md5_before = utils.generate_nexus_payload_checksum(schema_in_nexus)
                schema_md5_after = utils.generate_nexus_payload_checksum(schema)

                if schema_md5_before != schema_md5_after:
                    nxs.schemas.update(schema=schema, rev=current_revision)
            if _strategy == UPDATE_IF_EXISTS:
                nxs.schemas.update(schema=schema, rev=current_revision)
        except nxs.HTTPError as e:

            if e.response.status_code == 404: # the schema does not exist
                return nxs.schemas.create(org_label=_org_label, project_label=_prj_label, schema_obj=schema,
                                          schema_id=None)



def import_schemas( path, org, domain, schemas_lookup_base, _schemas_ns, _strategy=UPDATE_IF_DIFFERENT):
        _already_imported_schemas=[]

        schema_file_uris=filehelper.get_files_by_extensions(path, ".json")
        print("""Importing %s schemas from %s""" % (len(schema_file_uris), path))
        imported = []
        not_imported = []
        for schema_file_uri in schema_file_uris:

            if schema_file_uri not in _already_imported_schemas:
                try:
                    json_data = helpers.filehelper.open_as_json(schema_file_uri)
                    if DEPRECATED not in json_data:
                        if 'imports' in json_data:
                            imports_closure= get_schema_transitive_import_closure(json_data,schemas_lookup_base,_schemas_ns)

                            for source_url, source in imports_closure:
                                if source_url and source_url not in _already_imported_schemas:
                                    schema_json = helpers.filehelper.open_as_json(source_url)

                                    if DEPRECATED in schema_json: #and source_url != resources_lookup_base+"/schemas/neurosciencegraph/commons/entity/v0.1.0.json":
                                        message = """Unable to import the schema: it imported a deprecated schema %s""" % (schema_file_uri,source_url)
                                        raise DeprecatedSchemaImportException(message)

                                    _import_schema(source_url,schema_json,org,domain,_strategy)
                                    _already_imported_schemas.append(source_url)
                                    imported.append(source_url)
                        _import_schema(schema_file_uri,json_data,org,domain,_strategy)
                        _already_imported_schemas.append(schema_file_uri)
                        imported.append(schema_file_uri)
                except FileNotFoundError as e:
                    message = """Unable to import the schema %s: %s""" % (schema_file_uri,str(e))
                    not_imported.append((schema_file_uri,FileNotFoundError.__name__,message))
                except errors.JSONLDException as jlde:
                    message = """Unable to import the schema %s: %s""" % (schema_file_uri,str(jlde))
                    not_imported.append((schema_file_uri, errors.JSONLDException.__name__, message))
                except OWLImportException as oie:
                    message = """Failed to build the transitive import closure of the schema %s: %s""" % (schema_file_uri,str(oie))
                    not_imported.append((schema_file_uri, OWLImportException.__name__, message))
                except ValueError as ve:
                    message = """Unable to import the schema %s: %s""" % (schema_file_uri,str(ve))
                    not_imported.append((schema_file_uri, ValueError.__name__, message))
                except ContextImportException as cie:
                    message = """Failed to build the transitive contexts closure of the schema %s.""" % (schema_file_uri)
                    not_imported.append((schema_file_uri, ContextImportException.__name__, message))
                except SchemaBadFrameException as sbfe:
                    message = """Failed to import the schema %s: %s.""" % (schema_file_uri,str(sbfe))
                    not_imported.append((schema_file_uri, ContextImportException.__name__, message))
                except DeprecatedSchemaImportException as dse:
                    message = """Failed to import the schema %s: %s""" % (schema_file_uri, str(dse))
                    not_imported.append((schema_file_uri, DeprecatedSchemaImportException.__name__, message))
                except nxs.HTTPError as e:
                    message = """Failed to import the schema %s: %s""" % (schema_file_uri, str(e))
                    not_imported.append((schema_file_uri, nxs.HTTPError.__name__, message))

        return (imported, not_imported)


class SchemaImportException(Exception):
    pass

class SchemaBadFrameException(Exception):
    pass

class OWLImportException(ValueError):
    pass

class ResourceNotFoundException(ValueError):
    pass

class ContextImportException(errors.JSONLDException):
    pass

class DeprecatedSchemaImportException(ValueError):
    pass