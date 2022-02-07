package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.Label
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.Org
import io.circe.Json
import org.http4s.Method.{GET, PUT}
import org.http4s.Uri
import org.http4s.circe._
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.Authorization

class Orgs(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {

  def get(label: Label): IO[Option[Org]] =
    client.run(GET(endpoint / "orgs" / label.value).withAuthOpt(auth)).use { resp =>
      resp.decodeOpt[Org].raiseIfUnsuccessful
    }

  def save(label: Label, description: Option[String] = None, rev: Option[Long] = None): IO[Unit] = {
    val body = description match {
      case Some(value) => Json.obj("description" -> Json.fromString(value))
      case None        => Json.obj()
    }
    val req  = PUT(body, endpoint / "orgs" / label.value +?? ("rev" -> rev), Api.accept, contentTypeJsonLd)
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decodeOpt[Json].raiseIfUnsuccessful.void
    }
  }

  def ensureExists(label: Label, description: Option[String] = None): IO[Unit] =
    get(label).flatMap {
      case Some(_) => IO.unit
      case None    => save(label, description)
    }

}
