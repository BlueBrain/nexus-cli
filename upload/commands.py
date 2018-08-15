import click
import requests
import json
import os
from blessings import Terminal
from distutils.version import LooseVersion

import config_utils
import nexus_utils
import utils


t = Terminal()


@click.command()
@click.option('--file', '-f', help='Name of the file to upload.')
@click.option('--organization', '-o', help='The organisation in which to store that file.')
@click.option('--domain', '-d', help='The domain in which to store that file.')
@click.option('--verbose', '-v', is_flag=True, default=False, help='Prints additional information')
def upload(file, organization, domain, verbose):
    """Upload a file in Nexus."""
    if file is None:
        utils.error('ERROR: you must give a filename')

    if not os.path.isfile(file):
        utils.error("ERROR: File doesn't exist:" + os.path.abspath(file))

    base_url = config_utils.get_selected_deployment_config()[1]['url']

    # Check organization and domain exists
    org_url = base_url + "/v0/organizations/" + organization
    org = nexus_utils.get_by_id(org_url, fail_if_not_found=False)
    if org is None:
        utils.error("Could not find organization: " + organization)
    if verbose:
        utils.print_json(org, colorize=True)

    domain_url = base_url + "/v0/domains/" + organization + "/" + domain
    domain_payload = nexus_utils.get_by_id(domain_url, fail_if_not_found=False)
    if domain_payload is None:
        utils.error("Could not find domain '%s' in organization '%s'" % (domain, organization))
    if verbose:
        utils.print_json(domain_payload, colorize=True)

    # Check instance schema is available in that domain
    schemas_url = base_url + "/v0/schemas/" + organization + '/' + domain
    schemas = nexus_utils.get_by_id(schemas_url, fail_if_not_found=False)
    # utils.print_json(schemas, colorize=True)

    # look for instance schema and pick the highest version
    instance_schema_id = None
    instance_schema_version = None
    for schema in schemas['results']:
        schema_id = schema['resultId']
        name_and_version = schema_id.split("/")[-2:]
        name = name_and_version[0]
        version = name_and_version[1]

        if name == 'instance':
            if instance_schema_version is None:
                instance_schema_version = LooseVersion(version[1:])
                instance_schema_id = schema_id
            else:
                tmp = LooseVersion(version[1:])
                if tmp > instance_schema_version:
                    instance_schema_version = tmp
                    instance_schema_id = schema_id

    if instance_schema_version is not None:
        instance_schema_version = "v" + str(instance_schema_version)

    if instance_schema_id is None:
        if verbose:
            print("instance schema NOT found.")
        # import schema
        instance_schema_url = "https://raw.githubusercontent.com/BlueBrain/nexus-kg/v0/modules/kg-schemas/src/main/resources/schemas/nexus/core/instance/v0.1.0.json"
        instance_schema_version = "v0.1.0"
        r = requests.get(instance_schema_url)
        if verbose:
            print("GET %s\nHTTP %d\n%s" % (instance_schema_url, r.status_code, r.content))
        if r.status_code != 200:
            utils.error("Failed to get schema: " + instance_schema_url)
        schema_raw = r.text.replace("{{base}}", nexus_utils.get_selected_deployment_base_url())
        r.close()

        headers = {}
        nexus_utils.add_authorization_to_headers(headers)
        headers['Content-Type'] = 'application/ld+json'
        upload_url = schemas_url + "/instance/" + instance_schema_version
        r = requests.put(upload_url, data=schema_raw, headers=headers)
        print("PUT %s\nHTTP %d\n%s" % (upload_url, r.status_code, r.content))
        if r.status_code == 201:
            print(t.green("Schema 'instance' created"))
        r.close()
        instance_schema_id = upload_url

    else:
        if verbose:
            print("instance schema found: " + instance_schema_id)
            schema_payload = nexus_utils.get_by_id(instance_schema_id)
            utils.print_json(schema_payload, colorize=True)
        # check for deprecation
        if nexus_utils.is_deprecated(instance_schema_id):
            print(t.red(instance_schema_id))
            utils.error("Instance schema is deprecated, you cannot upload a file against it.")

    # make sure schema is published
    nexus_utils.publish_schema(instance_schema_id)

    # create instance
    context = nexus_utils.find_latest_context(organization='nexus', domain='core', context='resource')
    if verbose:
        print("Adding context: " + context)
    instance_payload = {
      "@context": context,
      "@type": [
        "nxv:Instance"
      ],
      "name": file
    }
    if verbose:
        utils.print_json( instance_payload, colorize=True )
    url = base_url + "/v0/data/%s/%s/instance/%s" % (organization, domain, instance_schema_version)
    headers = {'Content-Type': 'application/ld+json'}
    nexus_utils.add_authorization_to_headers(headers)
    r = requests.post(url, data=json.dumps(instance_payload), headers=headers)
    instance_id = None
    if r.status_code == 201:
        response = r.json()
        instance_id = response['@id']
        print(t.green("Instance created: %s" % instance_id))
    else:
        print(t.red("URL: %s\nHTTP %d (%s)\nDetails: %s" % (url, r.status_code, r.reason, r.content)))
        utils.error("Failed to create instance.")

    # attach file to instance
    nexus_utils.upload_file(instance_id, file, verbose=verbose)
    print(t.green("File uploaded"))
    if verbose:
        utils.print_json(nexus_utils.get_by_id(instance_id), colorize=True)