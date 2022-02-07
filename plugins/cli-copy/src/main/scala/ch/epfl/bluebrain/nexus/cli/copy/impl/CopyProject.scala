package ch.epfl.bluebrain.nexus.cli.copy.impl

import cats.data.NonEmptyList
import cats.effect.{ExitCode, IO}
import cats.implicits.toTraverseOps
import ch.epfl.bluebrain.nexus.cli.copy.CopyErr
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api._
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, PathUtils, Terminal}
import fansi.{Color, Str}
import fs2.io.file.Path
import io.circe.Json
import org.http4s.blaze.client.BlazeClientBuilder
import org.http4s.client.Client

object CopyProject {

  def apply(
      term: Terminal,
      source: CopyRef,
      target: CopyRef,
      offset: Option[String],
      concurrency: Int,
      preload: Option[NonEmptyList[Path]]
  ): IO[ExitCode] =
    BlazeClientBuilder[IO].resource.use { client =>
      for {
        _         <- verifyEnvRef(client, source)
        _         <- verifyEnvRef(client, target)
        _         <- loadPreloadPaths(preload)
        confirmed <- confirmation(term, source, target, offset, concurrency, preload)
        _         <- IO.raiseUnless(confirmed)(CopyErr.ConfirmationNotReceivedErr)
      } yield ExitCode.Success
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

}
