package ch.epfl.bluebrain.nexus.cli

import fs2.io.file.Path
import org.http4s.Uri
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, Label}

enum Intent:
  case ListPlugins
  case InvokePlugin(pluginName: String, path: Path, args: List[String])
  case Login(endpoint: Option[Uri], realm: Option[Label], token: Option[BearerToken], clientId: String)
//  case GetVersion
