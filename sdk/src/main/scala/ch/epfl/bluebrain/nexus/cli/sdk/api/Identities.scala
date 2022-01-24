package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.*
import ch.epfl.bluebrain.nexus.cli.sdk.Label
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api.*
import ch.epfl.bluebrain.nexus.cli.sdk.api.Identities.*
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, Identity, Listing, Realm}
import io.circe.Decoder
import org.http4s.Method.*
import org.http4s.circe.*
import org.http4s.client.Client
import org.http4s.client.dsl.io.*
import org.http4s.headers.{Accept, Authorization}
import org.http4s.{MediaType, Uri}

class Identities(client: Client[IO], endpoint: Uri, auth: Option[Authorization]):

  def list: IO[ApiResponse[List[Identity]]] =
    client.run(GET(endpoint / "identities").withAuthOpt(auth)).use { resp =>
      resp.decode[IdentityListingResponse].map(_.map(_.identities))
    }

object Identities:

  private case class IdentityListingResponse(
      `@context`: List[Uri],
      identities: List[Identity]
  ) derives Decoder
