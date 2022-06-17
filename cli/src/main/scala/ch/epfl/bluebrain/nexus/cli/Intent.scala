package ch.epfl.bluebrain.nexus.cli

import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ProjectRef
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, Label}
import fs2.io.file.Path
import io.circe.Json
import org.http4s.Uri

sealed trait Intent extends Product with Serializable

object Intent {
  case object ListPlugins                                 extends Intent
  case class InvokePlugin(path: Path, args: List[String]) extends Intent

  case object ShowLogin   extends Intent
  case object RemoveLogin extends Intent
  case class Login(
      endpoint: Option[Uri],
      realm: Option[Label],
      token: Option[BearerToken],
      clientId: String
  ) extends Intent

  case class ListResources(project: ProjectRef, includeAll: Boolean)    extends Intent
  case class GetResourceSource(project: ProjectRef, id: Uri)            extends Intent
  case class UpdateResource(project: ProjectRef, id: Uri, source: Json) extends Intent

  case class ListOrgs(from: Option[Int], size: Option[Int], deprecated: Option[Boolean]) extends Intent

  case class ListProjects(org: Option[Label], from: Option[Int], size: Option[Int], deprecated: Option[Boolean])
      extends Intent
}
