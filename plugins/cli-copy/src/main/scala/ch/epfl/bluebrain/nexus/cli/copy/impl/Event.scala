package ch.epfl.bluebrain.nexus.cli.copy.impl

import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.copy.CopyErr
import ch.epfl.bluebrain.nexus.cli.copy.CopyErr.{UnableToDecodeEventErr, UnableToParseEventErr}
import io.circe.Json
import io.circe.parser.parse
import org.http4s.Uri

case class Event(
    offset: String,
    eventType: String,
    resourceId: Uri,
    rev: Long,
    source: Option[Json]
)

object Event {

  def from(offset: String, eventType: String, data: String): Either[CopyErr, Event] =
    parse(data).leftMap(err => UnableToParseEventErr(data, err)).flatMap(from(offset, eventType, _))

  def from(offset: String, eventType: String, json: Json): Either[UnableToDecodeEventErr, Event] = {
    val either = for {
      resourceId <- json.hcursor.downField("_resourceId").as[String].map(str => Uri.unsafeFromString(str))
      rev        <- json.hcursor.downField("_rev").as[Option[Long]].map(_.getOrElse(1L))
      source     <- json.hcursor.downField("_source").as[Option[Json]]
    } yield Event(offset, eventType, resourceId, rev, source)
    either.leftMap(df => UnableToDecodeEventErr(json, df))
  }

}
