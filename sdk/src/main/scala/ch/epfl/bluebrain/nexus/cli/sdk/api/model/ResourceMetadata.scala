package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import io.circe.Decoder
import org.http4s.Uri
import org.http4s.circe._

case class ResourceMetadata(
    `@id`: Uri,
    `@type`: Set[String],
    _rev: Long,
    _deprecated: Boolean
)

object ResourceMetadata {

  implicit val resourceMetadataDecoder: Decoder[ResourceMetadata] =
    Decoder.instance { cursor =>
      for {
        id         <- cursor.get[Uri]("@id")
        tpe        <- cursor.get[Option[String]]("@type").map(_.toSet) orElse cursor.get[Set[String]]("@type")
        rev        <- cursor.get[Long]("_rev")
        deprecated <- cursor.get[Boolean]("_deprecated")
      } yield ResourceMetadata(id, tpe, rev, deprecated)
    }
}
