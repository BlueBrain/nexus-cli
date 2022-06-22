package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.{IO, Resource}
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse.Successful
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse.Unsuccessful._
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, Err, Terminal}
import fs2.Stream
import io.circe._
import io.circe.parser._
import org.http4s._
import org.http4s.client.Client
import org.http4s.headers.{`Content-Type`, Accept, Authorization}

import scala.concurrent.duration.FiniteDuration

class Api(val client: Client[IO], val endpoint: Uri, val auth: Option[Authorization]) {
  val realms: Realms                         = new Realms(client, endpoint, auth)
  val identities: Identities                 = new Identities(client, endpoint, auth)
  val orgs: Orgs                             = new Orgs(client, endpoint, auth)
  val projects: Projects                     = new Projects(client, endpoint, auth)
  val compositeViews: CompositeViews         = new CompositeViews(client, endpoint, auth)
  val elasticSearchViews: ElasticSearchViews = new ElasticSearchViews(client, endpoint, auth)
  val resources: Resources                   = new Resources(client, endpoint, auth)
  val files: Files                           = new Files(client, endpoint, auth)
}

object Api {

  def apply(client: Client[IO], endpoint: Uri): Api =
    new Api(client, endpoint, None)

  def apply(client: Client[IO], endpoint: Uri, token: BearerToken): Api =
    new Api(client, endpoint, Some(token.toAuthorization))

  def apply(client: Client[IO], endpoint: Uri, token: Option[BearerToken]): Api =
    new Api(client, endpoint, token.map(_.toAuthorization))

  val accept: Accept                    = Accept(MediaType.application.json)
  val acceptAll: Accept                 = Accept(MediaRange.`*/*`)
  val `application/ld+json`: MediaType  = new MediaType("application", "ld+json", compressible = true, binary = false)
  val contentTypeJsonLd: `Content-Type` = `Content-Type`(`application/ld+json`)

  implicit class RichRequestIO(val r: Request[IO]) extends AnyVal {
    def withAuthOpt(value: Option[Authorization]): Request[IO] =
      value match {
        case Some(auth) => r.withHeaders(r.headers.put(auth))
        case None       => r
      }
  }

  implicit class RichResponseIO(val r: Response[IO]) extends AnyVal {
    def decode[A: Decoder]: IO[ApiResponse[A]] =
      checkCt >>
        bodyAsJson(r)
          .map { raw =>
            r.status match {
              case status if status.isSuccess =>
                raw.as[A] match {
                  case Right(value) => Successful(value, status, raw, r.headers)
                  case Left(_)      => Unknown(status, raw, r.headers)
                }
              case Status.Unauthorized        =>
                raw.as[ErrorResponse] match {
                  case Left(_)      => Unknown(r.status, raw, r.headers)
                  case Right(value) => Unauthorized(value.`@type`, value.reason, r.status, raw, r.headers)
                }
              case Status.Forbidden           =>
                raw.as[ErrorResponse] match {
                  case Left(_)      => Unknown(r.status, raw, r.headers)
                  case Right(value) => Forbidden(value.`@type`, value.reason, r.status, raw, r.headers)
                }
              case status                     => Unknown(status, raw, r.headers)
            }
          }

    def decodeOpt[A: Decoder]: IO[ApiResponse[Option[A]]] =
      checkCt >>
        bodyAsJson(r)
          .map { raw =>
            r.status match {
              case status if status.isSuccess =>
                raw.as[A] match {
                  case Right(value) => Successful(Option(value), status, raw, r.headers)
                  case Left(_)      => Unknown(status, raw, r.headers)
                }
              case Status.NotFound            => Successful(None, r.status, raw, r.headers)
              case Status.Unauthorized        =>
                raw.as[ErrorResponse] match {
                  case Left(_)      => Unknown(r.status, raw, r.headers)
                  case Right(value) => Unauthorized(value.`@type`, value.reason, r.status, raw, r.headers)
                }
              case Status.Forbidden           =>
                raw.as[ErrorResponse] match {
                  case Left(_)      => Unknown(r.status, raw, r.headers)
                  case Right(value) => Forbidden(value.`@type`, value.reason, r.status, raw, r.headers)
                }
              case status                     => Unknown(status, raw, r.headers)
            }
          }

    def discard: IO[ApiResponse[Unit]] =
      r.status match {
        case status if status.isSuccess => IO.pure(Successful((), status, Json.obj(), r.headers))
        case status                     =>
          checkCt >>
            bodyAsJson(r).map { raw =>
              status match {
                case Status.Unauthorized =>
                  raw.as[ErrorResponse] match {
                    case Left(_)      => Unknown(r.status, raw, r.headers)
                    case Right(value) => Unauthorized(value.`@type`, value.reason, r.status, raw, r.headers)
                  }
                case Status.Forbidden    =>
                  raw.as[ErrorResponse] match {
                    case Left(_)      => Unknown(r.status, raw, r.headers)
                    case Right(value) => Forbidden(value.`@type`, value.reason, r.status, raw, r.headers)
                  }
                case _                   => Unknown(status, raw, r.headers)
              }
            }
      }

    private def checkCt: IO[Unit] =
      IO.raiseUnless(
        r.contentType.exists(ct =>
          ct.mediaType.satisfies(MediaType.application.json) || ct.mediaType.satisfies(`application/ld+json`)
        )
      )(Err.UnsupportedContentTypeErr(r.contentType))

  }

  private def bodyAsText(r: Response[IO]): IO[String] =
    r.bodyText.compile.fold("")(_ + _)

  private def bodyAsJson(r: Response[IO]): IO[Json] =
    bodyAsText(r).flatMap { str =>
      parse(str) match {
        case Left(value)  => IO.raiseError(Err.ParseErr(value.message))
        case Right(value) => IO.pure(value)
      }
    }

  implicit class RichResourceApiResponse(val res: Resource[IO, Response[IO]]) extends AnyVal {
    def decodeAsStream: Resource[IO, ApiResponse[(Stream[IO, Byte], Option[Long])]] =
      res.flatMap { r =>
        r.status match {
          case status if status.isSuccess =>
            Resource.pure(Successful((r.body, r.contentLength), status, Json.obj(), r.headers))
          case Status.Unauthorized        =>
            Resource.eval(bodyAsJson(r)).map { raw =>
              raw.as[ErrorResponse] match {
                case Left(_)      => Unknown(r.status, raw, r.headers)
                case Right(value) => Unauthorized(value.`@type`, value.reason, r.status, raw, r.headers)
              }
            }
          case Status.Forbidden           =>
            Resource.eval(bodyAsJson(r)).map { raw =>
              raw.as[ErrorResponse] match {
                case Left(_)      => Unknown(r.status, raw, r.headers)
                case Right(value) => Forbidden(value.`@type`, value.reason, r.status, raw, r.headers)
              }
            }
          case status                     =>
            Resource.eval(bodyAsJson(r)).map { raw =>
              Unknown(status, raw, r.headers)
            }

        }
      }
  }

  implicit class RichIOAPIResponseA[A](val r: IO[ApiResponse[A]]) extends AnyVal {
    def raiseIfUnsuccessful: IO[A]                                                            =
      r.flatMap {
        case Successful(value, _, _, _) => IO.pure(value)
        case v: Unauthorized            => IO.raiseError(Err.UnauthorizedErr(v.reason))
        case v: Forbidden               => IO.raiseError(Err.ForbiddenErr(v.reason))
        case v: Unknown                 => IO.raiseError(Err.UnsuccessfulResponseErr(v))
      }
    def retryfor(condition: Unknown => Boolean, delay: FiniteDuration, term: Terminal): IO[A] =
      r.flatMap {
        case Successful(value, _, _, _) => IO.pure(value)
        case v: Unauthorized            => IO.raiseError(Err.UnauthorizedErr(v.reason))
        case v: Forbidden               => IO.raiseError(Err.ForbiddenErr(v.reason))
        case v: Unknown                 =>
          if (condition(v))
            term.writeLn(s"Unsuccessful api response, status '${v.status}', retrying...") >> IO
              .sleep(delay) >> retryfor(
              condition,
              delay,
              term
            )
          else IO.raiseError(Err.UnsuccessfulResponseErr(v))
      }
  }
  private[api] case class ErrorResponse(`@type`: String, reason: String)
  object ErrorResponse {
    implicit val errorResponseDecoder: Decoder[ErrorResponse] =
      Decoder.forProduct2("@type", "reason")(ErrorResponse.apply)
  }
}
