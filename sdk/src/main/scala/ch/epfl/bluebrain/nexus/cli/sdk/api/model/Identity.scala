package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import ch.epfl.bluebrain.nexus.cli.sdk.Label
import io.circe.generic.semiauto._
import io.circe.{Decoder, DecodingFailure}

sealed trait Identity extends Product with Serializable

object Identity {
  case object Anonymous                          extends Identity
  case class Authenticated(realm: Label)         extends Identity
  case class User(realm: Label, subject: String) extends Identity
  case class Group(realm: Label, group: String)  extends Identity

  implicit val identityDecoder: Decoder[Identity] =
    Decoder.instance { cursor =>
      cursor.get[String]("@type") match {
        case Right("Anonymous")     => Right(Anonymous)
        case Right("Authenticated") => deriveDecoder[Authenticated].tryDecode(cursor)
        case Right("User")          => deriveDecoder[User].tryDecode(cursor)
        case Right("Group")         => deriveDecoder[Group].tryDecode(cursor)
        case Right(unknown)         => Left(DecodingFailure(s"Unknown Identity type '$unknown'", cursor.history))
        case Left(err)              => Left(err)
      }
    }
}
