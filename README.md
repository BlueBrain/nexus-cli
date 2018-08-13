# nexus-cli
A command line interface for Nexus

# Setup

As seen in http://click.pocoo.org/6/setuptools/#setuptools-integration
```
   <install conda - https://conda.io/docs/user-guide/install/index.html>

   conda create -y --name nexus-cli python=3.7
   conda activate nexus-cli
   pip install git+https://bitbucket.org/agriness/python-keycloak
   git clone https://github.com/samuel-kerrien/nexus-cli
   cd nexus-cli
   pip install --editable .
```

start using the CLI:
```
    nexus --help
```

# Currently supported features

## deployments
* adding a new deployment (--add <name> --url <URL>)
* removing a locally registered deployment (--remove)
* list locally registered deployment (--list), 
  * show entity count (--count), 
    * show public counts of entities, i.e. no autentication (--public-only) 
  * limit to public entities (--public-only)
* select a locally registered deployment (--select)

## login
* log into the currently selected local deployment of nexus
* show token upon login
* show user's groups from token
* TODO show token status

## tokens
* print information (incl. user and groups) about local tokens (stored post login)
    * ability to decode token (--decode)

## logout
* revoke token from the oauth server and clear token stored locally

## contexts
* List contexts available on the currently selected local deployment of nexus (--list)
    * list contexts URLs without formatting (--no-format)
    * list contexts that are public only, i.e. no-authentication (--public-only)
* search for fragments (--search). Note that this feature isn't following contexts declared in contexts yet, 
  it merely browse the contexts registered in Nexus.

## organisations
* list organizations on the currently selected local deployment of nexus (--list)
    * list organizations that are public only, i.e. no-authentication (--public-only)
* TODO deprecate an organization
* TODO create a new organization
* TODO list ACLs on an organization
* TODO update ACLs ? or should that be a separate command 'acls'

## domains
* list domains of a given organization (--list)
    * list domains that are public only, i.e. no-authentication (--public-only)
* TODO create a new domain in an organisation
* TODO deprecate a domain

## schemas
* list schemas of a given organization/domain (--list)
* TODO create a new schema in an organisation/domain
* TODO deprecate a schema
* TODO list entities for a given schema

# acls
* list all acls by path (--list)
    * filter acls by organizations (--organization) and domains (--domain)
    * filter acls by domains (--domain)
    * ability to limit acl listing to what is public (i.e. no auth, --public-only)
    * show raw ACLs as returned by the Nexus service (--show-raw)

## search (note that the context right now is hard coded)
* search by entity types (--type) and/or by field/value (--field, --value) and list resulting entity IDs
    * override default context (--context)
* search from a provided search query in a file (--query-file)

All the above can use the following options:
    * show the Nexus query generated (--show-query)
    * colorize json-ld output (--pretty)
    * print the resulting entity payloads (--show-entities)
    * limits the count of entities being retrieved (--max-entities)
    * download the metadata and, if any, the data attached to resulting entities (--download)

## get
* retrieve entity payload (i.e. metadata) by its id with auth support (--url)
    * colorize json-ld output (--pretty)
* TODO download attached data if available (--data) 

## upload
* TODO upload a file in a given organization/domain

## download
* TODO given a search query, download all datasets locally along with metadata

## entities
* TODO show entity by ID (latest or specific revision)
* TODO show revisions list of an entity
* TODO update an entity (download metadata, edit metadata, update entity) 

## types
* TODO list entity types supported in the selected nexus instance 
