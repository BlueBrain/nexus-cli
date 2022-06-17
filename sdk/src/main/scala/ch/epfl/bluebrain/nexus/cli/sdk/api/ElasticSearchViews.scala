package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.Label
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import io.circe.Json
import org.http4s.Method.PUT
import org.http4s.Uri
import org.http4s.circe._
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.Authorization

class ElasticSearchViews(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {
  def query(org: Label, proj: Label, id: Uri, query: Json): IO[Json] = {
    val req = PUT(query, endpoint / "views" / org.value / proj.value / id.renderString, Api.accept)
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decode[Json].raiseIfUnsuccessful
    }
  }
}
