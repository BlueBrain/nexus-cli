package ch.epfl.bluebrain.nexus.cli.copy.impl

import cats.data.NonEmptyList
import cats.effect.{ExitCode, IO}
import cats.implicits.toTraverseOps
import ch.epfl.bluebrain.nexus.cli.copy.CopyErr
import ch.epfl.bluebrain.nexus.cli.copy.impl.EvaluationResult.{Conflict, Discarded, Error, Ok}
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, Event, ProjectFields}
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, PathUtils, Terminal}
import fansi.{Color, Str}
import fs2.io.file.Path
import io.circe.Json
import org.http4s.blaze.client.BlazeClientBuilder
import org.http4s.client.Client
import org.http4s.{MediaType, Status}

import java.util.concurrent.TimeoutException
import scala.concurrent.duration.{Duration, DurationInt}

object CopyProject {

  def apply(
      term: Terminal,
      source: CopyRef,
      target: CopyRef,
      offset: Option[String],
      concurrency: Int,
      preload: Option[NonEmptyList[Path]]
  ): IO[ExitCode] =
    BlazeClientBuilder[IO]
      .withMaxTotalConnections(2 * concurrency + 1)
      .withRequestTimeout(Duration.Inf)
      .resource
      .use { client =>
        for {
          _                  <- verifyEnvRef(client, source)
          _                  <- verifyEnvRef(client, target)
          resourcesToPreload <- loadPreloadPaths(preload)
          confirmed          <- confirmation(term, source, target, offset, concurrency, preload)
          _                  <- IO.raiseUnless(confirmed)(CopyErr.ConfirmationNotReceivedErr)
          _                  <- createOrgProj(client, target)
          _                  <- term.writeLn("Preloading default resources")
          _                  <- preloadResources(client, target, resourcesToPreload)
          _                  <- term.writeLn("Starting copy stream")
          _                  <- streamProject(term, client, source, target, offset, concurrency)
        } yield ExitCode.Success
      }

  def streamProject(
      term: Terminal,
      client: Client[IO],
      source: CopyRef,
      target: CopyRef,
      offset: Option[String],
      concurrency: Int
  ): IO[Unit] = {
    val sourceApi = Api(client, source.endpoint, source.token)
    sourceApi.projects
      .events(source.project, offset)
      .chunkN(concurrency)
      .flatMap { chunk =>
        val hasDuplicates = chunk.map(_.resourceId).toList.toSet.size != chunk.size
        if (hasDuplicates) fs2.Stream.iterable(chunk.toList).map(ev => List(ev))
        else fs2.Stream.apply(chunk.toList)
      }
      .evalTap(_ => IO.print('c'))
      .evalMap { chunk => evalChunk(chunk, client, source, target) }
      .flatMap(results => fs2.Stream.iterable(results))
      .evalTap {
        case Error(_, status, error) => term.writeLn(s"Status: $status\n$error")
        case _                       => IO.unit
      }
      .mapAccumulate(CopyStatus(0L, 0L, 0L, 0L)) {
        case (status, Ok(offset))          => (status.incrementSuccesses, offset)
        case (status, Conflict(offset))    => (status.incrementConflicts, offset)
        case (status, Discarded(offset))   => (status.incrementDiscarded, offset)
        case (status, Error(offset, _, _)) => (status.incrementErrors, offset)
      }
      .debounce(5.seconds)
      .evalMap { case (CopyStatus(successes, conflicts, discarded, errors), offset) =>
        term.writeLn(
          s"\nWritten $successes events, conflicts $conflicts, discarded $discarded, errors $errors, current offset: '$offset'"
        )
      }
      .compile
      .drain
  }

  private def evalChunk(
      chunk: List[Event],
      client: Client[IO],
      source: CopyRef,
      target: CopyRef
  ): IO[List[EvaluationResult]] =
    fs2.Stream
      .iterable(chunk)
      .covary[IO]
      .parEvalMapUnordered(chunk.size) { event =>
        evalEvent(client, source, target, event)
          .timeout(2.minutes)
          .handleErrorWith {
            case _: TimeoutException => IO.pure(Error(event.offset, Status.RequestTimeout, "Client Timeout"))
            case th                  => IO.raiseError(th)
          }
      }
      .compile
      .toList

  private def evalEvent(client: Client[IO], source: CopyRef, target: CopyRef, event: Event): IO[EvaluationResult] = {
    val sourceApi = Api(client, source.endpoint, source.token)
    val targetApi = Api(client, target.endpoint, target.token)
    event.eventType match {
      case "ResourceCreated" | "ResourceUpdated" =>
        event.source match {
          case Some(source) =>
            val rev = if (event.rev == 1L) None else Some(event.rev - 1)
            targetApi.resources.createOrUpdate(target.project, event.resourceId, source, rev).map {
              case _: ApiResponse.Successful[_]                                       => Ok(event.offset)
              case r: ApiResponse.Unsuccessful.Unknown if r.status == Status.Conflict => Conflict(event.offset)
              case r                                                                  => Error(event.offset, r.status, s"Resource Error:\n${r.raw.spaces2}")
            }
          case None         => IO.pure(EvaluationResult.Discarded(event.offset))
        }

      case "FileCreated" | "FileUpdated" =>
        val rev = if (event.rev == 1L) None else Some(event.rev - 1)
        filenameAndMediaType(event) match {
          case Some((filename, mediaType)) =>
            sourceApi.files.downloadAsTemp(source.project, event.resourceId, Some(event.rev)).use {
              case ApiResponse.Successful((path, length), _, _, _) =>
                targetApi.files
                  .uploadFromPath(path, target.project, event.resourceId, length, filename, mediaType, rev)
                  .map {
                    case _: ApiResponse.Successful[_]                                       => Ok(event.offset)
                    case r: ApiResponse.Unsuccessful.Unknown if r.status == Status.Conflict => Conflict(event.offset)
                    case r                                                                  => Error(event.offset, r.status, s"Upload Error:\n${r.raw.spaces2}")
                  }
              case r: ApiResponse.Unsuccessful                     =>
                IO.pure(Error(event.offset, r.status, s"Download Error:\n${r.raw.spaces2}"))
            }
          case None                        => IO.pure(EvaluationResult.Discarded(event.offset))
        }
      case _                             => IO.pure(EvaluationResult.Discarded(event.offset))
    }
  }

  private def preloadResources(client: Client[IO], target: CopyRef, resources: Option[NonEmptyList[Json]]): IO[Unit] =
    resources match {
      case Some(value) =>
        val api = Api(client, target.endpoint, target.token)
        value.traverse(json => api.resources.ensureExists(target.project, json)).void
      case None        => IO.unit
    }

  private def createOrgProj(client: Client[IO], target: CopyRef): IO[Unit] = {
    val api = Api(client, target.endpoint, target.token)
    for {
      _ <- api.orgs.ensureExists(target.project.org)
      _ <- api.projects.ensureExists(target.project, ProjectFields.empty)
    } yield ()
  }

  private def loadPreloadPaths(preload: Option[NonEmptyList[Path]]): IO[Option[NonEmptyList[Json]]] =
    preload match {
      case Some(value) => value.traverse(p => PathUtils.loadPathAsJson(p)).map(Some.apply)
      case None        => IO.none
    }

  private def verifyEnvRef(client: Client[IO], ref: CopyRef): IO[Unit] = {
    val api = Api(client, ref.endpoint, ref.token)
    api.identities.list.raiseIfUnsuccessful.void.handleErrorWith {
      case e: Err.UnauthorizedErr         =>
        IO.raiseError(CopyErr.InvalidCredentialsErr(ref.endpoint, s"${e.message} ${e.description}"))
      case e: Err.ForbiddenErr            =>
        IO.raiseError(CopyErr.InvalidCredentialsErr(ref.endpoint, s"${e.message} ${e.description}"))
      case e: Err.UnsuccessfulResponseErr =>
        IO.raiseError(CopyErr.InvalidEndpointErr(ref.endpoint, s"${e.message} ${e.description}"))
      case e                              => IO.raiseError(e)
    }
  }

  private def confirmation(
      term: Terminal,
      source: CopyRef,
      target: CopyRef,
      offset: Option[String],
      concurrency: Int,
      preload: Option[NonEmptyList[Path]]
  ): IO[Boolean] =
    for {
      _        <- term.writeLn("")
      _        <- term.writeLn("The tool will execute a project copy with the following configuration:")
      _        <- term.writeLn("")
      _        <- term.writeLn(Color.Cyan("Source endpoint: ") ++ source.endpoint.renderString)
      _        <- term.writeLn(Color.Cyan("Source project: ") ++ source.project.toString)
      _        <- term.writeLn(Color.Cyan("Target endpoint: ") ++ target.endpoint.renderString)
      _        <- term.writeLn(Color.Cyan("Target project: ") ++ target.project.toString)
      _        <- offset match {
                    case Some(value) => term.writeLn(Color.Cyan("Start offset: ") ++ value)
                    case None        => IO.unit
                  }
      _        <- term.writeLn(Color.Cyan("Concurrency: ") ++ concurrency.toString)
      _        <- preload match {
                    case Some(value) =>
                      term.writeLn(Color.Cyan("Preload resources from files:")) >>
                        value.toList
                          .map(_.absolute.toString)
                          .distinct
                          .traverse(p => term.writeLn(Str(p), Color.Green(" - ")))
                          .void
                    case None        => IO.unit
                  }
      _        <- term.writeLn("")
      _        <- term.write("Are you sure you want to proceed? [Y/n]: ")
      txt      <- term.readLn(masked = false)
      confirmed = txt == "Y"
    } yield confirmed

  private def filenameAndMediaType(event: Event): Option[(String, MediaType)] = {
    val cursor = event.raw.hcursor
    for {
      fileName     <- cursor.downField("_attributes").get[String]("_filename").toOption
      mediaTypeStr <- cursor.downField("_attributes").get[String]("_mediaType").toOption
      mediaType    <- MediaType.parse(mediaTypeStr).toOption
    } yield (fileName, mediaType)
  }

}
