package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect._
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import ch.epfl.bluebrain.nexus.cli.sdk.api.Identities._
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, Identity}
import io.circe.Decoder
import io.circe.generic.semiauto._
import org.http4s.Method._
import org.http4s.Uri
import org.http4s.circe._
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.Authorization

class Identities(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {

  def list: IO[ApiResponse[List[Identity]]] =
    client.run(GET(endpoint / "identities").withAuthOpt(auth)).use { resp =>
      resp.decode[IdentityListingResponse].map(_.map(_.identities))
    }
}

object Identities {

  private[api] case class IdentityListingResponse(
      `@context`: List[Uri],
      identities: List[Identity]
  )
  object IdentityListingResponse {
    implicit val identityListingResponseDecoder: Decoder[IdentityListingResponse] =
      deriveDecoder[IdentityListingResponse]
  }
}
