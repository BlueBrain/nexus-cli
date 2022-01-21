package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.{ExitCode, IO}
import ch.epfl.bluebrain.nexus.cli.impl.Config.LoginConfig
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal
import org.http4s.Uri

object RemoveLogin:

  def apply(): IO[ExitCode] =
    Config.remove.as(ExitCode.Success)