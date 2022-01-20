package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import io.circe.Json
import org.http4s.*

enum ApiResponse[+A]:

  def status: Status

  def raw: Json

  def headers: Headers

  case Successful[+A](
      value: A,
      status: Status,
      raw: Json,
      headers: Headers
  ) extends ApiResponse[A]

  case Unauthorized(
      tpe: String,
      reason: String,
      status: Status,
      raw: Json,
      headers: Headers
  ) extends ApiResponse[Nothing]

  case Forbidden(
      tpe: String,
      reason: String,
      status: Status,
      raw: Json,
      headers: Headers
  ) extends ApiResponse[Nothing]

  case Unsuccessful(
      status: Status,
      raw: Json,
      headers: Headers
  ) extends ApiResponse[Nothing]

  def map[B](f: A => B): ApiResponse[B] =
    this match
      case Successful(value, status, raw, headers) => Successful(f(value), status, raw, headers)
      case r: Unauthorized                         => r
      case r: Forbidden                            => r
      case r: Unsuccessful                         => r
