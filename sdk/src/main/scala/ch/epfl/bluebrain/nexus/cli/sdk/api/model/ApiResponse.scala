package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse.{Successful, Unsuccessful}
import io.circe.Json
import org.http4s._

sealed trait ApiResponse[+A] {
  def status: Status

  def raw: Json

  def headers: Headers

  def map[B](f: A => B): ApiResponse[B] =
    this match {
      case Successful(value, status, raw, headers) => Successful(f(value), status, raw, headers)
      case r: Unsuccessful                         => r
    }

}

object ApiResponse {

  case class Successful[+A](
      value: A,
      status: Status,
      raw: Json,
      headers: Headers
  ) extends ApiResponse[A]

  sealed trait Unsuccessful extends ApiResponse[Nothing]

  object Unsuccessful {

    case class Unauthorized(
        tpe: String,
        reason: String,
        status: Status,
        raw: Json,
        headers: Headers
    ) extends Unsuccessful

    case class Forbidden(
        tpe: String,
        reason: String,
        status: Status,
        raw: Json,
        headers: Headers
    ) extends Unsuccessful

    case class Unknown(
        status: Status,
        raw: Json,
        headers: Headers
    ) extends Unsuccessful

  }
}
