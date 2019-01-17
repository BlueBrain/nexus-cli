# nexus-cli
A command line interface for Nexus

# Setup

As seen in http://click.pocoo.org/6/setuptools/#setuptools-integration
```
   <install conda - https://conda.io/docs/user-guide/install/index.html>

   conda create -y --name nexus-cli python=3.7
   conda activate nexus-cli-v1
   git clone https://github.com/samuel-kerrien/nexus-cli
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
* adding a new profile (--add <name> --url <URL>)
* removing a locally registered deployment (--remove <name>)
* list locally registered deployment (no param), 
* select a locally registered deployment (--select <name>)

## login
* log into the currently selected local deployment of nexus
* show token upon login
* show user's groups from token
* TODO show token status

## token
* print information about local tokens (stored post login)
