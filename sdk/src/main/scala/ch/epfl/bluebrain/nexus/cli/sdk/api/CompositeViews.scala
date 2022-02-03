package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.Label
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import io.circe.Json
import org.http4s.Method.{GET, PUT}
import org.http4s.Uri
import org.http4s.circe._
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.Authorization

class CompositeViews(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {

  def sourceOf(org: Label, proj: Label, id: Uri): IO[Option[Json]] = {
    val req = GET(endpoint / "views" / org.value / proj.value / id.renderString / "source")
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decodeOpt[Json].raiseIfUnsuccessful
    }
  }

  def revisionOf(org: Label, proj: Label, id: Uri): IO[Option[Long]] = {
    val req = GET(endpoint / "views" / org.value / proj.value / id.renderString)
    client
      .run(req.withAuthOpt(auth))
      .use { resp =>
        resp.decodeOpt[Json].raiseIfUnsuccessful
      }
      .map {
        case Some(json) =>
          val typesAndRev = for {
            types <- json.hcursor.get[List[String]]("@type")
            rev   <- json.hcursor.get[Long]("_rev")
          } yield (types, rev)
          typesAndRev match {
            case Right((types, rev)) if types.contains("CompositeView") => Some(rev)
            case _                                                      => None
          }
        case None       => None
      }
  }

  def updateIfSourceIsDifferent(org: Label, proj: Label, id: Uri, view: Json): IO[Unit] =
    revisionOf(org, proj, id).flatMap { revOpt =>
      sourceOf(org, proj, id).flatMap {
        case Some(source) if source == view => IO.unit
        case _                              => createOrUpdate(org, proj, id, view, revOpt)
      }
    }

  def createOrUpdate(org: Label, proj: Label, id: Uri, view: Json, rev: Option[Long]): IO[Unit] = {
    val req = PUT(view, endpoint / "views" / org.value / proj.value / id.renderString +?? ("rev", rev), Api.accept)
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decodeOpt[Json].raiseIfUnsuccessful.void
    }
  }
}
