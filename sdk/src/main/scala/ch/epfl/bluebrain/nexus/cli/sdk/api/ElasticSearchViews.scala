package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.Label
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, ResourceMetadata}
import io.circe.Json
import org.http4s.Method.{GET, POST}
import org.http4s.Uri
import org.http4s.circe._
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.Authorization

class ElasticSearchViews(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {

  def metadata(org: Label, proj: Label, id: Uri): IO[Option[ResourceMetadata]] = {
    val uri = endpoint / "views" / org.value / proj.value / id.renderString
    val req = GET(uri, accept).withAuthOpt(auth)
    client.run(req).use { resp =>
      resp.decodeOpt[ResourceMetadata].raiseIfUnsuccessful
    }
  }

  def canBeQueried(org: Label, proj: Label, id: Uri): IO[Boolean] =
    metadata(org, proj, id).map {
      case Some(value) => !value._deprecated
      case None        => false
    }

  def query(org: Label, proj: Label, id: Uri, query: Json): IO[ApiResponse[Json]] = {
    val req = POST(query, endpoint / "views" / org.value / proj.value / id.renderString / "_search", Api.accept)
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decode[Json]
    }
  }
}
