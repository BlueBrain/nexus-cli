package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.sdk.Err
import io.circe.Json
import io.circe.parser.parse
import org.http4s.Uri

case class Event(
    offset: String,
    eventType: String,
    resourceId: Uri,
    rev: Long,
    raw: Json,
    source: Option[Json]
)

object Event {

  def from(offset: String, eventType: String, data: String): Either[Err, Event] =
    parse(data).leftMap(err => Err.UnableToParseEventErr(data, err)).flatMap(from(offset, eventType, _))

  def from(offset: String, eventType: String, json: Json): Either[Err, Event] = {
    val either = for {
      resourceId <- json.hcursor.downField("_resourceId").as[String].map(str => Uri.unsafeFromString(str))
      rev        <- json.hcursor.downField("_rev").as[Option[Long]].map(_.getOrElse(1L))
      source     <- json.hcursor.downField("_source").as[Option[Json]]
    } yield Event(offset, eventType, resourceId, rev, json, source)
    either.leftMap(df => Err.UnableToDecodeEventErr(json, df))
  }

}
