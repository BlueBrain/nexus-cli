# nexus-cli
A command line interface for Nexus

# Setup

As seen in http://click.pocoo.org/6/setuptools/#setuptools-integration
```
   <install conda - https://conda.io/docs/user-guide/install/index.html>

   conda create -y --name nexus-cli python=3.5
   conda activate nexus-cli
   git clone https://github.com/BlueBrain/nexus-cli
   cd nexus-cli
   git checkout nexus_v1
   pip install --editable .
```

start using the CLI:
```
    nexus --help
```

# Currently supported features

## profiles
* adding a new profile (--create <name> --url <URL>)
* Deleting a locally registered deployment (--delete <name>)
* list locally registered deployment (--list), 
* select a locally registered deployment (--select <name>)

## login
* log into the currently selected local deployment of nexus
* show token upon login with expiry status

## token (stored in ${HOME}/.nexus-cli/config.json)
* print encoded token
* print decoded token and expiry information
