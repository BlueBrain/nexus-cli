# nexus-cli
A command line interface for Nexus

# Setup

As seen in http://click.pocoo.org/7/setuptools/#setuptools-integration
```
   <install conda - https://conda.io/docs/user-guide/install/index.html>

   conda create -n nexus-cli python=3.5
   conda activate nexus-cli
   git clone https://github.com/BlueBrain/nexus-cli
   cd nexus-cli
   git checkout nexus_v1
   pip install --editable .
```

or with straight from github:
```
    conda create -n nexus-cli python=3.5
    conda activate nexus-cli
    pip install git+https://github.com/BlueBrain/nexus-cli
```

Start using the CLI:
```
    nexus --help
```

# Currently supported features

## profiles
* create: adding a new profile (create <name> <URL>)
* delete: deleting a locally registered profile (delete <name>)
* list: list locally registered profiles (list), 
* select: select a locally registered profile (select <name>)
* current: show currently selected profile

## auth
* login: opens Nexus Web in your browser so that the user can login and get his/her token
* set-token: saves a token in the currently selected profile
* view-token: prints token from the currently selected profile (encoded, decoded, expiry time)

## orgs
* list: list all organizations
* create: create a new organization
* fetch: shows the json payload of an organization
* update: update an organization (name and description only!)
* deprecate: deprecate an organization
* select: select the organization to use in subsequent calls of the CLI (local to the currently selected profile)
* current: shows the currently selected organization

## projects (local to a specific organization)
* list: list all projects
* create: create a new project
* fetch: shows the json payload of an project
* update: update an project (name and description only!)
* deprecate: deprecate an project
* select: select the project to use in subsequent calls of the CLI (local to the currently selected profile)
* current: shows the currently selected project

## resources (local to a specific organization and project)
* list: list all resources
* create: create a new resource
* fetch: shows the json payload of a resource
* update: update a resource
* deprecate: deprecate a resource

## schemas (local to a specific organization and project)
* list: list all schemas
* create: create a new schema
* fetch: shows the json payload of a schema
* update: update a schema
* deprecate: deprecate a schema

## views (local to a specific organization and project)
* list: list all views
* create: create a new ElasticSearchView
* fetch: shows the json payload of a view
* update: update a view configuration
* deprecate: deprecate a view
* query-es: run a query against a specific ElasticSearch view
* query-sparql: run a query against the default SPARQL view

## acls
* list: list acls
* show-identities: show identities that can be added in ACLs
* show-permissions: show permissions that can be added in ACLs
* make-public: make a project public to the world