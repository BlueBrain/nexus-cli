# nexus-cli
A command line interface for Nexus

## Development

Native image compilation may produce artefacts that fail at runtime because of the use of reflection. In order to find
the correct reflection configuration, run the tool with native image agent:
```
$JAVA_HOME/bin/java -agentlib:native-image-agent=config-output-dir=/path/to/config-dir/ -cp ...\
  ch.epfl.bluebrain.nexus.cli.Main list-plugins
```

[This](https://github.com/lampepfl/dotty/issues/13985) issue tracks the progress of the use of reflection in scala 3.

## Funding & Acknowledgment

The development of this software was supported by funding to the Blue Brain Project, a research center of the École polytechnique fédérale de
Lausanne (EPFL), from the Swiss government's ETH Board of the Swiss Federal Institutes of Technology.

Copyright © 2015-2022 Blue Brain Project/EPFL

