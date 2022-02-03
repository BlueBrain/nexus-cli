package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import ch.epfl.bluebrain.nexus.cli.sdk.Label
import io.circe.Decoder
import io.circe.generic.semiauto._
import org.http4s.Uri
import org.http4s.circe._

case class EffectiveApiMapping(
    _prefix: Label,
    _namespace: Uri
)

object EffectiveApiMapping {

  implicit val effectiveApiMappingDecoder: Decoder[EffectiveApiMapping] =
    deriveDecoder[EffectiveApiMapping]

}
