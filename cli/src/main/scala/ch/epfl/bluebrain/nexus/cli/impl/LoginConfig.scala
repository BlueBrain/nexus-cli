package ch.epfl.bluebrain.nexus.cli.impl

import cats.implicits.toFunctorOps
import ch.epfl.bluebrain.nexus.cli.impl.LoginConfig.{AnonymousLoginConfig, UserLoginConfig}
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, Label}
import io.circe.generic.semiauto._
import io.circe.{Decoder, Encoder}
import org.http4s.Uri
import org.http4s.circe._

import scala.annotation.unused

sealed trait LoginConfig extends Product with Serializable {
  def endpoint: Uri

  def asAnonymousLogin: Option[AnonymousLoginConfig] =
    this match {
      case v: AnonymousLoginConfig => Some(v)
      case _: UserLoginConfig      => None
    }

  def asUserLogin: Option[UserLoginConfig] =
    this match {
      case _: AnonymousLoginConfig => None
      case v: UserLoginConfig      => Some(v)
    }

}

object LoginConfig {

  case class AnonymousLoginConfig(endpoint: Uri)                                                extends LoginConfig
  case class UserLoginConfig(endpoint: Uri, realm: Label, token: BearerToken, clientId: String) extends LoginConfig

  implicit val loginConfigEncoder: Encoder[LoginConfig] = {
    val anon = deriveEncoder[AnonymousLoginConfig]
    val user = deriveEncoder[UserLoginConfig]
    Encoder.encodeJsonObject.contramap {
      case v: AnonymousLoginConfig => anon.encodeObject(v)
      case v: UserLoginConfig      => user.encodeObject(v)
    }
  }

  implicit val loginConfigDecoder: Decoder[LoginConfig] = {
    @unused val anon = deriveDecoder[AnonymousLoginConfig].widen[LoginConfig]
    val user         = deriveDecoder[UserLoginConfig]
    user.or(anon)
  }
}
