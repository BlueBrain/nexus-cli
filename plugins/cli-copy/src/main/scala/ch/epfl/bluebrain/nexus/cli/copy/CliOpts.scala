package ch.epfl.bluebrain.nexus.cli.copy

import cats.data.{NonEmptyList, Validated}
import cats.effect.IO
import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.copy.impl.CopyRef
import ch.epfl.bluebrain.nexus.cli.sdk.Args.{pathArgument, uriArgument}
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ProjectRef
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, BuildInfo, Terminal}
import com.monovore.decline.{Command, Help, Opts}
import fs2.io.file.Path
import org.http4s.Uri

object CliOpts {
  def command: Command[Intent] =
    Command(name, s"Nexus Project Copy CLI (version ${BuildInfo.version})") {
      (sourceRef, targetRef, offset.orNone, concurrency.withDefault(5), preload.orNone).mapN(Intent.Copy)
    }

  val sourceEnv: Opts[Uri]              = Opts.option[Uri]("source-env", "The source Nexus env base api URI.")
  val targetEnv: Opts[Uri]              = Opts.option[Uri]("target-env", "The target Nexus env base api URI.")
  val sourceProj: Opts[ProjectRef]      = Opts.option[ProjectRef]("source-proj", "The source Nexus project.")
  val targetProj: Opts[ProjectRef]      = Opts.option[ProjectRef]("target-proj", "The target Nexus project.")
  val sourceToken: Opts[BearerToken]    = Opts.option[BearerToken]("source-token", "The source token.")
  val targetToken: Opts[BearerToken]    = Opts.option[BearerToken]("target-token", "The target token.")
  val offset: Opts[String]              = Opts.option[String]("offset", "The starting offset.")
  val preload: Opts[NonEmptyList[Path]] = Opts.arguments[Path]("preload-path")
  val concurrency: Opts[Int]            =
    Opts.option[Int]("concurrency", "The maximum level of concurrency to use.").mapValidated { value =>
      if (value > 0 && value <= 100) Validated.validNel(value)
      else Validated.invalidNel("Invalid concurrency, value must be in the [1, 100] range.")
    }

  val sourceRef: Opts[CopyRef] = (sourceEnv, sourceProj, sourceToken.orNone).mapN(CopyRef.apply)
  val targetRef: Opts[CopyRef] = (targetEnv, targetProj, targetToken.orNone).mapN(CopyRef.apply)

  def name: String = BuildInfo.cliName + " copy"

  def printHelp(terminal: Terminal, help: Help): IO[Unit] =
    if (help.errors.isEmpty) terminal.writeLn(help.toString)
    else IO.raiseError(CopyErr.ArgErr(help))
}
