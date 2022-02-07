package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.{IO, Resource}
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api.{acceptAll, RichRequestIO, RichResourceApiResponse, RichResponseIO}
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, ProjectRef}
import fs2.Stream
import io.circe.Json
import org.http4s.Method.{GET, PUT}
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.{`Content-Type`, Authorization}
import org.http4s.multipart.{Multipart, Part}
import org.http4s.{MediaType, Uri}

class Files(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {

  def download(ref: ProjectRef, id: Uri, rev: Option[Long]): Resource[IO, ApiResponse[Stream[IO, Byte]]] = {
    val req =
      GET(endpoint / "files" / ref.org.value / ref.project.value / id.renderString +?? ("rev" -> rev), acceptAll)
    client.run(req.withAuthOpt(auth)).decodeAsStream
  }

  def upload(
      ref: ProjectRef,
      id: Uri,
      bytes: Stream[IO, Byte],
      fileName: String,
      mediaType: MediaType,
      rev: Option[Long]
  ): IO[ApiResponse[Unit]] = {
    val multipart = Multipart[IO](
      Vector(
        Part.fileData(
          name = "file",
          filename = fileName,
          entityBody = bytes,
          `Content-Type`(mediaType)
        )
      )
    )
    val req       =
      PUT(multipart, endpoint / "files" / ref.org.value / ref.project.value / id.renderString +?? ("rev" -> rev))
        .withHeaders(multipart.headers)
        .withAuthOpt(auth)
    client.run(req).use { resp =>
      resp.decode[Json].map(_.map(_ => ()))
    }
  }

}
