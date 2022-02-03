package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.{ExitCode, IO}

object RemoveLogin {
  def apply(): IO[ExitCode] =
    Config.remove.as(ExitCode.Success)
}
