package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import ch.epfl.bluebrain.nexus.cli.sdk.Label
import io.circe.Decoder
import io.circe.generic.semiauto._
import org.http4s.Uri
import org.http4s.circe._

import java.time.Instant
import java.util.UUID

case class Project(
    `@id`: Uri,
    `@type`: String,
    apiMappings: List[ApiMapping],
    base: Uri,
    description: Option[String],
    vocab: Uri,
    _constrainedBy: Uri,
    _createdAt: Instant,
    _createdBy: Uri,
    _deprecated: Boolean,
    _effectiveApiMappings: List[EffectiveApiMapping],
    _label: Label,
    _markedForDeletion: Boolean,
    _organizationLabel: Label,
    _organizationUuid: UUID,
    _rev: Long,
    _self: Uri,
    _updatedAt: Instant,
    _updatedBy: Uri,
    _uuid: UUID
) {
  def ref: ProjectRef = ProjectRef(_organizationLabel, _label)
}

object Project {

  implicit val projectDecoder: Decoder[Project] =
    deriveDecoder[Project]

}
