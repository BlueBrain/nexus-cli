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
    pip install git+https://github.com/BlueBrain/nexus-cli@nexus_v1
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
* update: update an resource
* deprecate: deprecate a resource
