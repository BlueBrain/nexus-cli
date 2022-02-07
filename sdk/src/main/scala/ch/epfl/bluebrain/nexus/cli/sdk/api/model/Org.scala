package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import ch.epfl.bluebrain.nexus.cli.sdk.Label
import io.circe.Decoder
import io.circe.generic.semiauto.deriveDecoder
import org.http4s.Uri
import org.http4s.circe._

import java.time.Instant
import java.util.UUID

case class Org(
    `@id`: Uri,
    `@type`: String,
    description: String,
    _constrainedBy: Uri,
    _createdAt: Instant,
    _createdBy: Uri,
    _deprecated: Boolean,
    _label: Label,
    _rev: Long,
    _self: Uri,
    _updatedAt: Instant,
    _updatedBy: Uri,
    _uuid: UUID
)

object Org {

  implicit val orgDecoder: Decoder[Org] =
    deriveDecoder[Org]

}
