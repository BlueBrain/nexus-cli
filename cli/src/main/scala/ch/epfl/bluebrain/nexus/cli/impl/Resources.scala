package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.{ExitCode, IO}
import ch.epfl.bluebrain.nexus.cli.Intent
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api.RichIOAPIResponseA

object Resources {

  def apply(intent: Intent.ListResources, api: Api, term: Terminal): IO[ExitCode] = {
    val stream =
      if (intent.includeAll) api.resources.listAll(intent.project)
      else api.resources.list(intent.project)
    stream
      .evalMap { meta => term.writeLn(meta.`@id`.renderString) }
      .compile
      .drain
      .as(ExitCode.Success)
  }

  def apply(intent: Intent.GetResourceSource, api: Api, term: Terminal): IO[ExitCode] =
    for {
      source <- api.resources.getSource(intent.project, intent.id).raiseIfUnsuccessful
      json   <- term.renderJson(source)
      _      <- term.writeLn(json)
    } yield ExitCode.Success

  def apply(intent: Intent.UpdateResource, api: Api): IO[ExitCode] =
    api.resources.update(intent.project, intent.id, intent.source).raiseIfUnsuccessful.as(ExitCode.Success)

}
