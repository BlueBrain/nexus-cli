package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.{ExitCode, IO}
import ch.epfl.bluebrain.nexus.cli.impl.Config.LoginConfig
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal
import org.http4s.Uri

object ShowLogin:

  def apply(term: Terminal): IO[ExitCode] =
    Config.load.flatMap {
      case Some(LoginConfig(endpoint, realm, token, clientId)) =>
        for
          _ <- term.writeLn(s"Endpoint: $endpoint")
          _ <- term.writeLn(s"Realm: ${realm.value}")
          _ <- term.writeLn(s"Token: ${token.value}")
          _ <- term.writeLn(s"Client Id: $clientId")
        yield ExitCode.Success
      case None => term.write("No login information currently found.").as(ExitCode.Success)
    }
