package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import io.circe.Decoder
import io.circe.generic.semiauto._
import org.http4s.Uri
import org.http4s.circe._

import scala.annotation.unused

case class Listing[A](
    `@context`: List[Uri],
    _total: Long,
    _results: List[A]
)

object Listing {

  implicit def listingDecoder[A](implicit @unused A: Decoder[A]): Decoder[Listing[A]] =
    deriveDecoder[Listing[A]]

}
