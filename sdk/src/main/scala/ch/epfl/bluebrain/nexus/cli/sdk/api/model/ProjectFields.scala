package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import cats.data.NonEmptyList
import io.circe.Encoder
import io.circe.generic.semiauto.deriveEncoder
import org.http4s.circe._
import org.http4s.Uri

case class ProjectFields(
    apiMappings: Option[NonEmptyList[ApiMapping]],
    base: Option[Uri],
    description: Option[String],
    vocab: Option[Uri]
)

object ProjectFields {

  val empty: ProjectFields = ProjectFields(None, None, None, None)

  implicit val projectFieldsEncoder: Encoder[ProjectFields] =
    deriveEncoder[ProjectFields]

}
