package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.*
import ch.epfl.bluebrain.nexus.cli.sdk.Label
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api.*
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{Listing, Realm}
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse
import org.http4s.Method.*
import org.http4s.client.Client
import org.http4s.client.dsl.io.*
import org.http4s.headers.{Accept, Authorization}
import org.http4s.{MediaType, Uri}

class Realms(client: Client[IO], endpoint: Uri, auth: Option[Authorization]):

  def get(label: Label): IO[ApiResponse[Option[Realm]]] =
    client.run(GET(endpoint / "realms" / label.value).withAuthOpt(auth)).use { resp =>
      resp.decodeOpt[Realm]
    }

  def list: IO[ApiResponse[Listing[Realm]]] =
    client.run(GET(endpoint / "realms").withAuthOpt(auth)).use { resp =>
      resp.decode[Listing[Realm]]
    }
