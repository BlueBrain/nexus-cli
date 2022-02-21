package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import ch.epfl.bluebrain.nexus.cli.sdk.api.model._
import io.circe.Json
import io.circe.syntax.EncoderOps
import org.http4s.Method.{GET, PUT}
import org.http4s.{Headers, Request, ServerSentEvent, Uri}
import org.http4s.circe._
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.{`Last-Event-Id`, Authorization}
import fs2.Stream
import org.http4s.ServerSentEvent.EventId

class Projects(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {

  def list(from: Option[Int], size: Option[Int], deprecated: Option[Boolean]): IO[ApiResponse[Listing[Project]]] = {
    val req = GET(endpoint / "projects" +?? ("from" -> from) +?? ("size" -> size) +?? ("deprecated", deprecated))
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decode[Listing[Project]]
    }
  }

  def get(ref: ProjectRef): IO[Option[Project]] =
    client.run(GET(endpoint / "projects" / ref.org.value / ref.project.value).withAuthOpt(auth)).use { resp =>
      resp.decodeOpt[Project].raiseIfUnsuccessful
    }

  def save(ref: ProjectRef, fields: ProjectFields, rev: Option[Long] = None): IO[Unit] = {
    val req = PUT(
      fields.asJson,
      endpoint / "projects" / ref.org.value / ref.project.value +?? ("rev" -> rev),
      Api.accept,
      contentTypeJsonLd
    )
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decodeOpt[Json].raiseIfUnsuccessful.void
    }
  }

  def ensureExists(ref: ProjectRef, fields: ProjectFields): IO[Unit] =
    get(ref).flatMap {
      case Some(_) => IO.unit
      case None    => save(ref, fields)
    }

  def events(ref: ProjectRef, offset: Option[String]): Stream[IO, Event] = {
    val req = Request[IO](
      uri = endpoint / "resources" / ref.org.value / ref.project.value / "events",
      headers = Headers(auth.toList) ++ Headers(offset.map(str => `Last-Event-Id`(EventId(str))).toList)
    )
    client
      .stream(req)
      .flatMap(_.body.through(ServerSentEvent.decoder[IO]))
      .evalMapFilter {
        // TODO: add logging
        case ServerSentEvent(Some(data), Some(eventType), Some(offset), _, _) =>
          IO.print('.') >> IO.pure(Event.from(offset.value, eventType, data).toOption)
        case _                                                                => IO.none
      }
  }
}
