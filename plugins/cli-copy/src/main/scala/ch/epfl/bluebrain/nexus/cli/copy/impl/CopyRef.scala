package ch.epfl.bluebrain.nexus.cli.copy.impl

import ch.epfl.bluebrain.nexus.cli.sdk.BearerToken
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ProjectRef
import org.http4s.Uri

case class CopyRef(
    endpoint: Uri,
    project: ProjectRef,
    token: Option[BearerToken]
)
