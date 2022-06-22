package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.{IO, Resource}
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api.{acceptAll, RichRequestIO, RichResourceApiResponse, RichResponseIO}
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse.{Successful, Unsuccessful}
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, ProjectRef}
import fs2.Stream
import fs2.io.file
import fs2.io.file.Path
import org.http4s.Method.{GET, PUT}
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.{`Content-Type`, Authorization}
import org.http4s.multipart.{Multiparts, Part}
import org.http4s.{Entity, MediaType, Uri}

class Files(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {

  def download(
      ref: ProjectRef,
      id: Uri,
      rev: Option[Long]
  ): Resource[IO, ApiResponse[(Stream[IO, Byte], Option[Long])]] = {
    val req =
      GET(endpoint / "files" / ref.org.value / ref.project.value / id.renderString +?? ("rev" -> rev), acceptAll)
    client.run(req.withAuthOpt(auth)).decodeAsStream
  }

  def downloadAsTemp(ref: ProjectRef, id: Uri, rev: Option[Long]): Resource[IO, ApiResponse[(Path, Long)]] =
    download(ref, id, rev).flatMap {
      case v @ Successful((stream, lengthOpt), _, _, _) =>
        file.Files[IO].tempFile.evalMap { tmp =>
          stream.through(file.Files[IO].writeAll(tmp)).compile.drain >> {
            lengthOpt match {
              case Some(length) => IO.pure(v.copy(value = (tmp, length)))
              case None         => file.Files[IO].size(tmp).map(length => v.copy(value = (tmp, length)))
            }
          }
        }
      case v: Unsuccessful                              => Resource.pure(v)
    }

  def upload(
      ref: ProjectRef,
      id: Uri,
      bytes: Stream[IO, Byte],
      length: Option[Long],
      fileName: String,
      mediaType: MediaType,
      rev: Option[Long]
  ): IO[ApiResponse[Unit]] = {
    val multipart = for {
      multiparts <- Multiparts.forSync[IO]
      multipart  <- multiparts.multipart(
                      Vector(
                        Part.fileData(
                          name = "file",
                          filename = fileName,
                          entity = Entity(bytes, length),
                          `Content-Type`(mediaType)
                        )
                      )
                    )

    } yield multipart

    multipart.flatMap { mp =>
      val req = PUT(mp, endpoint / "files" / ref.org.value / ref.project.value / id.renderString +?? ("rev" -> rev))
        .withHeaders(mp.headers)
        .withAuthOpt(auth)
      client.run(req).use { resp =>
        resp.discard
      }
    }
  }

  def uploadFromPath(
      path: Path,
      ref: ProjectRef,
      id: Uri,
      length: Long,
      fileName: String,
      mediaType: MediaType,
      rev: Option[Long]
  ): IO[ApiResponse[Unit]] =
    upload(ref, id, file.Files[IO].readAll(path), Some(length), fileName, mediaType, rev)

}
