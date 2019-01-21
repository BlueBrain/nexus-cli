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
* Adding a new profile (create <name> <URL>)
* Deleting a locally registered profile (delete <name>)
* List locally registered profiles (list), 
* Select a locally registered profile (select <name>)

## auth
* Log into the currently selected deployment of Blue Brain Nexus
* Show token upon login with expiry status

## token (stored in ${HOME}/.nexus-cli/config.json)
* Print encoded token
* Print decoded token and expiry information
