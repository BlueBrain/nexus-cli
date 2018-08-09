# nexus-cli
A command line interface for Nexus

# Setup

As seen in http://click.pocoo.org/6/setuptools/#setuptools-integration
```
   <install python3>
   <install virtualenv>
   <install pip3>

   virtualenv -p python3 venv
   . venv/bin/activate
   pip3 install --editable .
```

start using the CLI:
```
    nexus-cli --help
```

# Currently supported features

## deployments
 * adding a new deployment (--add)
* removing a locally registered deployment (--remove)
* list locally registered deployment (--list), show entity count (--count), limit to public entities (--public-only)
* select a locally registered deployment (--select)

## login
* log into the currently selected local deployment of nexus
* show token upon login
* show user's groups from token
* TODO show token status

## logout
 * revoke token from the oauth server and clear token stored locally

## contexts
* List contexts available on the currently selected local deployment of nexus
* search for fragments

## organisations
* list organizations on the currently selected local deployment of nexus
* TODO deprecate an organization
* TODO create a new organization
* TODO list ACLs on an organization
* TODO update ACLs ? or should that be a separate command 'acls'

## domains
* list domains of a given organization (--list)
* TODO create a new domain in an organisation (--new)
* TODO deprecate a domain

## schemas
* list schemas of a given organization/domain (--list)
* TODO create a new schema in an organisation/domain (--new)
* TODO deprecate a schema
* TODO list entities for a given schema

## types
* TODO list entity types supported in the selected nexus instance 

## search
* WIP search by entity types

## get
* retrieve entity payload by its id with auth support

## upload
* TODO upload a file in a given organization/domain

## download
* TODO given a search query, download all datasets locally along with metadata

## entities
* TODO show entity by ID (latest or specific revision)
* TODO show revisions list of an entity
* TODO update an entity (download metadata, edit metadata, update entity) 

