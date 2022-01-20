package ch.epfl.bluebrain.nexus.cli.sdk

import io.circe.{Decoder, Encoder}
import org.http4s.headers.Authorization
import org.http4s.{AuthScheme, Credentials}

opaque type BearerToken = String

object BearerToken:
  extension (token: BearerToken)
    def value: String                  = token
    def toAuthorization: Authorization = Authorization(Credentials.Token(AuthScheme.Bearer, value))

  def unsafe(value: String): BearerToken = value

  given Encoder[BearerToken] = Encoder.encodeString.contramap(_.value)
  given Decoder[BearerToken] = Decoder.decodeString.emap(str => Right(unsafe(str)))
