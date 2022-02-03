package ch.epfl.bluebrain.nexus.cli.sdk

import cats.implicits._
import com.monovore.decline.Argument
import io.circe.{Decoder, Encoder}
import org.http4s.headers.Authorization
import org.http4s.{AuthScheme, Credentials}

case class BearerToken private (value: String) extends AnyVal {
  def toAuthorization: Authorization = Authorization(Credentials.Token(AuthScheme.Bearer, value))
}

object BearerToken {
  def unsafe(value: String): BearerToken = new BearerToken(value)

  implicit val bearerTokenEncoder: Encoder[BearerToken] = Encoder.encodeString.contramap(_.value)
  implicit val bearerTokenDecoder: Decoder[BearerToken] = Decoder.decodeString.emap(str => Right(unsafe(str)))

  implicit val bearerTokenArgument: Argument[BearerToken] =
    Argument.from("token") { str =>
      Either
        .cond(str.nonEmpty, str.trim, "Token must be a non empty string")
        .toValidatedNel
        .map(value => BearerToken.unsafe(value))
    }
}
