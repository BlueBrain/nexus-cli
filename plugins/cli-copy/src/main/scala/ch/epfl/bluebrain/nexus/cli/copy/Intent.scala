package ch.epfl.bluebrain.nexus.cli.copy

import cats.data.NonEmptyList
import ch.epfl.bluebrain.nexus.cli.copy.impl.CopyRef
import fs2.io.file.Path

sealed trait Intent extends Product with Serializable

object Intent {

  case class Copy(
      source: CopyRef,
      target: CopyRef,
      offset: Option[String],
      concurrency: Int,
      preload: Option[NonEmptyList[Path]]
  ) extends Intent

}
