package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, ProjectRef}
import io.circe.Json
import org.http4s.Method.{POST, PUT}
import org.http4s.circe._
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.Authorization
import org.http4s.{Status, Uri}

class Resources(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {

  def ensureExists(project: ProjectRef, json: Json): IO[Unit] = {
    val req = POST(json, endpoint / "resources" / project.org.value / project.project.value, accept, contentTypeJsonLd)
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decode[Json].flatMap {
        case _: ApiResponse.Successful[_]                                       => IO.unit
        case r: ApiResponse.Unsuccessful.Unknown if r.status == Status.Conflict => IO.unit
        case other                                                              => IO.pure(other).raiseIfUnsuccessful.void
      }
    }
  }

  def createOrUpdate(project: ProjectRef, resourceId: Uri, json: Json, rev: Option[Long]): IO[ApiResponse[Unit]] = {
    val uri =
      endpoint / "resources" / project.org.value / project.project.value / "_" / resourceId.renderString +?? ("rev" -> rev)
    val req = PUT(json, uri, accept, contentTypeJsonLd)
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decode[Json].map(_.map(_ => ()))
    }
  }

}
