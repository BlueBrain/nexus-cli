package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.Err
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse
import io.circe.*
import io.circe.parser.*
import org.http4s.headers.{Accept, Authorization}
import org.http4s.{MediaType, Request, Response, Status}

object Api:

  val accept: Accept        = Accept(MediaType.application.json)
  val `application/ld+json` = new MediaType("application", "ld+json", compressible = true, binary = false)

  extension (r: Request[IO])
    def withAuthOpt(value: Option[Authorization]): Request[IO] =
      value match
        case Some(auth) => r.withHeaders(r.headers.put(auth))
        case None       => r

  extension (r: Response[IO])
    def decode[A](using Decoder[A]): IO[ApiResponse[A]] =
      checkCt >>
        bodyAsJson
          .map { raw =>
            r.status match
              case status if status.isSuccess =>
                raw.as[A] match
                  case Right(value) => ApiResponse.Successful(value, status, raw, r.headers)
                  case Left(err)    => ApiResponse.Unsuccessful(status, raw, r.headers)
              case Status.Unauthorized        =>
                raw.as[ErrorResponse] match
                  case Left(err)    => ApiResponse.Unsuccessful(r.status, raw, r.headers)
                  case Right(value) => ApiResponse.Unauthorized(value.`@type`, value.reason, r.status, raw, r.headers)
              case Status.Forbidden           =>
                raw.as[ErrorResponse] match
                  case Left(err)    => ApiResponse.Unsuccessful(r.status, raw, r.headers)
                  case Right(value) => ApiResponse.Forbidden(value.`@type`, value.reason, r.status, raw, r.headers)
              case status                     => ApiResponse.Unsuccessful(status, raw, r.headers)
          }

    def decodeOpt[A](using Decoder[A]): IO[ApiResponse[Option[A]]] =
      checkCt >>
        bodyAsJson
          .map { raw =>
            r.status match
              case status if status.isSuccess =>
                raw.as[A] match
                  case Right(value) => ApiResponse.Successful(Option(value), status, raw, r.headers)
                  case Left(err)    => ApiResponse.Unsuccessful(status, raw, r.headers)
              case Status.NotFound            => ApiResponse.Successful(None, r.status, raw, r.headers)
              case Status.Unauthorized        =>
                raw.as[ErrorResponse] match
                  case Left(err)    => ApiResponse.Unsuccessful(r.status, raw, r.headers)
                  case Right(value) => ApiResponse.Unauthorized(value.`@type`, value.reason, r.status, raw, r.headers)
              case Status.Forbidden           =>
                raw.as[ErrorResponse] match
                  case Left(err)    => ApiResponse.Unsuccessful(r.status, raw, r.headers)
                  case Right(value) => ApiResponse.Forbidden(value.`@type`, value.reason, r.status, raw, r.headers)
              case status                     => ApiResponse.Unsuccessful(status, raw, r.headers)
          }

    private def checkCt: IO[Unit] =
      IO.raiseUnless(
        r.contentType
          .map(ct =>
            ct.mediaType.satisfies(MediaType.application.json) || ct.mediaType.satisfies(`application/ld+json`)
          )
          .getOrElse(false)
      )(
        Err.UnsupportedContentType(r.contentType)
      )

    private def bodyAsText: IO[String] =
      r.bodyText.compile.fold("")(_ + _)

    private def bodyAsJson: IO[Json] =
      bodyAsText.flatMap { str =>
        parse(str) match
          case Left(value)  => IO.raiseError(Err.ParseErr(value.message))
          case Right(value) => IO.pure(value)
      }

  private case class ErrorResponse(`@type`: String, reason: String) derives Decoder
