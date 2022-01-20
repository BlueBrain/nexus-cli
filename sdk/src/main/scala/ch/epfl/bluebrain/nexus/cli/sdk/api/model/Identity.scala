package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import ch.epfl.bluebrain.nexus.cli.sdk.Label
import io.circe.Codec
import io.circe.Decoder
import io.circe.Derivation.*
import io.circe.DecodingFailure

enum Identity:
  case Anonymous
  case Authenticated(realm: Label)
  case User(realm: Label, subject: String)
  case Group(realm: Label, group: String)

object Identity:

  given Decoder[Identity] =
    Decoder.instance { cursor =>
      cursor.get[String]("@type") match {
        case Right("Anonymous")     => Right(Anonymous)
        case Right("Authenticated") => summonDecoder[Authenticated].tryDecode(cursor)
        case Right("User")          => summonDecoder[User].tryDecode(cursor)
        case Right("Group")         => summonDecoder[Group].tryDecode(cursor)
        case Right(unknown)         => Left(DecodingFailure(s"Unknown Identity type '$unknown'", cursor.history))
        case Left(err)              => Left(err)
      }
    }
