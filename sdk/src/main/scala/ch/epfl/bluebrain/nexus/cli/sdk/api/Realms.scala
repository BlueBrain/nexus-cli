package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect._
import ch.epfl.bluebrain.nexus.cli.sdk.Label
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, Listing, Realm}
import org.http4s.Method._
import org.http4s.Uri
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.Authorization

class Realms(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {

  def get(label: Label): IO[ApiResponse[Option[Realm]]] =
    client.run(GET(endpoint / "realms" / label.value).withAuthOpt(auth)).use { resp =>
      resp.decodeOpt[Realm]
    }

  def list: IO[ApiResponse[Listing[Realm]]] =
    client.run(GET(endpoint / "realms").withAuthOpt(auth)).use { resp =>
      resp.decode[Listing[Realm]]
    }
}
