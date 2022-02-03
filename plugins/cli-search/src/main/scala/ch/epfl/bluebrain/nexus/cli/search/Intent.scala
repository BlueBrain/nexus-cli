package ch.epfl.bluebrain.nexus.cli.search

import fs2.io.file.Path

sealed trait Intent extends Product with Serializable

object Intent {
  case class UpdateConfig(path: Path) extends Intent
}
