package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import ch.epfl.bluebrain.nexus.cli.sdk.Label
import io.circe.Codec
import io.circe.generic.semiauto._
import org.http4s.Uri
import org.http4s.circe._

case class ApiMapping(
    prefix: Label,
    namespace: Uri
)

object ApiMapping {

  implicit val apiMappingCodec: Codec[ApiMapping] = deriveCodec[ApiMapping]

}
