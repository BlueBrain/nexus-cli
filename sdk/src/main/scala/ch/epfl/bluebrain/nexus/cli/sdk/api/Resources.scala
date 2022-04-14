package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.IO
import cats.implicits.toBifunctorOps
import ch.epfl.bluebrain.nexus.cli.sdk.Err
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, Listing, ProjectRef, ResourceMetadata}
import fs2.Stream
import io.circe.Json
import org.http4s.Method.{GET, POST, PUT}
import org.http4s.circe._
import org.http4s.client.Client
import org.http4s.client.dsl.io._
import org.http4s.headers.Authorization
import org.http4s.{Status, Uri}

class Resources(client: Client[IO], endpoint: Uri, auth: Option[Authorization]) {

  def ensureExists(project: ProjectRef, json: Json): IO[Unit] = {
    val req = POST(json, endpoint / "resources" / project.org.value / project.project.value, accept, contentTypeJsonLd)
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decode[Json].flatMap {
        case _: ApiResponse.Successful[_]                                       => IO.unit
        case r: ApiResponse.Unsuccessful.Unknown if r.status == Status.Conflict => IO.unit
        case other                                                              => IO.pure(other).raiseIfUnsuccessful.void
      }
    }
  }

  def createOrUpdate(project: ProjectRef, resourceId: Uri, json: Json, rev: Option[Long]): IO[ApiResponse[Unit]] = {
    val uri =
      endpoint / "resources" / project.org.value / project.project.value / "_" / resourceId.renderString +?? ("rev" -> rev)
    val req = PUT(json, uri, accept, contentTypeJsonLd)
    client.run(req.withAuthOpt(auth)).use { resp =>
      resp.decode[Json].map(_.map(_ => ()))
    }
  }

  def listAll(project: ProjectRef): Stream[IO, ResourceMetadata] = {
    def page(uri: Uri): IO[Listing[ResourceMetadata]]  =
      client.run(GET(uri, accept).withAuthOpt(auth)).use { resp =>
        resp.decode[Listing[ResourceMetadata]].raiseIfUnsuccessful
      }
    def stream(uri: Uri): Stream[IO, ResourceMetadata] =
      Stream.eval(page(uri)).flatMap { listing =>
        listing._next match {
          case Some(nextUri) => Stream.iterable(listing._results).covary[IO] ++ stream(nextUri)
          case None          => Stream.iterable(listing._results).covary[IO]
        }
      }
    stream(endpoint / "resources" / project.org.value / project.project.value)
  }

  def list(project: ProjectRef): Stream[IO, ResourceMetadata] = {
    val exclusions = Set("Resolver", "File", "Schema", "View", "Storage", "Project", "Organization")
    listAll(project).filter(_.`@type`.intersect(exclusions).isEmpty)
  }

  def getSource(project: ProjectRef, id: Uri): IO[ApiResponse[Json]] = {
    val uri = endpoint / "resources" / project.org.value / project.project.value / "_" / id.renderString / "source"
    val req = GET(uri, accept).withAuthOpt(auth)
    client.run(req).use { resp =>
      resp.decode[Json]
    }
  }

  def get(project: ProjectRef, id: Uri): IO[ApiResponse[Option[Json]]] = {
    val uri = endpoint / "resources" / project.org.value / project.project.value / "_" / id.renderString
    val req = GET(uri, accept).withAuthOpt(auth)
    client.run(req).use { resp =>
      resp.decodeOpt[Json]
    }
  }

  def update(project: ProjectRef, id: Uri, json: Json): IO[ApiResponse[Unit]] = {
    get(project, id).raiseIfUnsuccessful.flatMap {
      case None        => IO.raiseError(Err.ResourceNotFoundErr(project, id))
      case Some(value) =>
        val rev = value.hcursor.get[Long]("_rev").leftMap(df => Err.UnableToDecodeResourceJsonErr(project, id, df))
        IO.fromEither(rev).flatMap { r =>
          createOrUpdate(project, id, json, Some(r))
        }
    }
  }

}
