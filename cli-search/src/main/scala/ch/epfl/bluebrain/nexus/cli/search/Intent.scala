package ch.epfl.bluebrain.nexus.cli.search

import fs2.io.file.Path

enum Intent:
  case UpdateConfig(path: Path)
