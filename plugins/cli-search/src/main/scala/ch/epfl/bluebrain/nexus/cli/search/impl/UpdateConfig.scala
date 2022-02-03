package ch.epfl.bluebrain.nexus.cli.search.impl

import cats.effect.{ExitCode, IO}
import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api.RichIOAPIResponseA
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.Project
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, PathUtils, Terminal}
import fs2.io.file.Path
import io.circe.Json
import org.http4s.Uri
import org.http4s.implicits._

object UpdateConfig {

  val searchViewId: Uri = uri"https://bluebrain.github.io/nexus/vocabulary/searchView"

  def apply(compositeViewPath: Path, term: Terminal, api: Api): IO[ExitCode] =
    for {
      view     <- PathUtils.loadPathAsJson(compositeViewPath)
      projects <- api.projects
                    .list(None, Some(1000), Some(false))
                    .raiseIfUnsuccessful
                    .map(_._results.sortBy(p => s"${p._organizationLabel.value}/${p._label.value}"))
      _        <- term.writeLn(s"Found ${projects.size} to update.")
      _        <- projects.traverse(p => updateView(p, view, term, api))
    } yield ExitCode.Success

  private def updateView(p: Project, view: Json, term: Terminal, api: Api): IO[Unit] =
    for {
      _ <- term.write(s"Updating ${p._organizationLabel.value}/${p._label.value} .")
      _ <- updateHandled(p, view, term, api)
    } yield ()

  private def updateHandled(p: Project, view: Json, term: Terminal, api: Api): IO[Unit] =
    api.compositeViews
      .updateIfSourceIsDifferent(p._organizationLabel, p._label, searchViewId, view)
      .redeemWith(
        {
          case th @ Err.UnsuccessfulResponseErr(resp) =>
            val bodyAsText = resp.raw.spaces2
            if (
              bodyAsText.contains("Substream Source(EntitySource) cannot be materialized more than once") || bodyAsText
                .contains("An unexpected error occurred. Please try again later or contact the administrator")
            )
              term.write("e") >> updateHandled(p, view, term, api)
            else term.writeLn(" Failed, skipping.") >> th.println(term)
          case th                                     => IO.raiseError(th)
        },
        _ => term.writeLn(" Ok")
      )

}
