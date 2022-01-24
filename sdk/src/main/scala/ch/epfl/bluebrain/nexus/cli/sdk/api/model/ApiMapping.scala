package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import ch.epfl.bluebrain.nexus.cli.sdk.Label
import io.circe.Codec
import org.http4s.Uri
import org.http4s.circe.*

case class ApiMapping(
    prefix: Label,
    namespace: Uri
) derives Codec.AsObject
