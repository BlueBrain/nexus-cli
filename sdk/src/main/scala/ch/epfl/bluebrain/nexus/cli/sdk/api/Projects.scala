package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api.*
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, Listing, Project}
import org.http4s.Method.GET
import org.http4s.Uri
import org.http4s.client.Client
import org.http4s.client.dsl.io.*
import org.http4s.headers.Authorization

class Projects(client: Client[IO], endpoint: Uri, auth: Option[Authorization]):

  def list(from: Option[Int], size: Option[Int], deprecated: Option[Boolean]): IO[ApiResponse[Listing[Project]]] =
    val req = GET(endpoint / "projects" +?? ("from" -> from) +?? ("size" -> size) +?? ("deprecated", deprecated))
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decode[Listing[Project]]
    }
