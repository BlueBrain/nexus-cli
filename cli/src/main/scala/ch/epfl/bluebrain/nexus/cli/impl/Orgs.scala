package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.{ExitCode, IO}
import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.Intent
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api

object Orgs {

  def apply(intent: Intent.ListOrgs, api: Api, term: Terminal): IO[ExitCode] =
    for {
      orgs <- api.orgs.list(intent.from, intent.size, intent.deprecated)
      _    <- orgs._results.traverse(o => term.writeLn(o._label.value))
    } yield ExitCode.Success

}
