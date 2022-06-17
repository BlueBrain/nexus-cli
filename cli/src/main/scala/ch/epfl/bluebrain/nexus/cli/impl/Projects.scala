package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.{ExitCode, IO}
import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.Intent
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api

object Projects {

  def apply(intent: Intent.ListProjects, api: Api, term: Terminal): IO[ExitCode] =
    for {
      projects <- api.projects.list(intent.org, intent.from, intent.size, intent.deprecated)
      _        <- projects._results.traverse(p => term.writeLn(s"${p._organizationLabel.value}/${p._label.value}"))
    } yield ExitCode.Success

}
