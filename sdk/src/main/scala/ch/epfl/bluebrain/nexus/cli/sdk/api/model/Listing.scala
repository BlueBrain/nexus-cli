package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import io.circe.Codec
import org.http4s.Uri
import org.http4s.circe.*

case class Listing[A](
    `@context`: List[Uri],
    _total: Long,
    _results: List[A]
) derives Codec.AsObject
