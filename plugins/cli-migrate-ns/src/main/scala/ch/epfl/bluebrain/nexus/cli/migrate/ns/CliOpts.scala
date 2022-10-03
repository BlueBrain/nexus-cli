package ch.epfl.bluebrain.nexus.cli.migrate.ns

import cats.effect.IO
import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ProjectRef
import ch.epfl.bluebrain.nexus.cli.sdk.{BuildInfo, Terminal}
import com.monovore.decline.time.defaultInstant
import com.monovore.decline.{Command, Help, Opts}

import java.nio.file.{Files, Path, Paths}
import java.time.Instant

object CliOpts {

  def command: Command[Intent] =
    Command(name, s"Nexus Namespace Migration CLI (version ${BuildInfo.version})", helpFlag = true) {
      (
        Opts
          .option[Instant](
            "created-after",
            "Update only resources that have been created after the specified instant."
          )
          .withDefault(Instant.EPOCH),
        Opts
          .option[Instant](
            "last-update-before",
            "Update only resources that haven't been updated before the specified instant."
          )
          .withDefault(Instant.now()),
        Opts.option[Int]("page-size", "The page size when querying Elasticsearch").withDefault(20),
        Opts.option[Int]("concurrency", "How many updates to perform in parallel.").withDefault(1),
        Opts
          .options[ProjectRef](
            "project",
            "A project to include in the migration. Can be repeated to include several projects. If absent, all projects will be processed."
          )
          .map(_.toList)
          .withDefault(List.empty),
        Opts
          .option[Path]("logFile", "A path to write the log in a way that is easily parsable by a script.")
          .validate("Path must be writable.")(Files.isWritable)
          .withDefault(Paths.get("", s"errors_${System.currentTimeMillis()}"))
      ).mapN(Intent.MigrateNs.apply)
    }

  def name: String = BuildInfo.cliName + " migrate-ns"

  def printHelp(terminal: Terminal, help: Help): IO[Unit] =
    if (help.errors.isEmpty) terminal.writeLn(help.toString)
    else IO.raiseError(MigrateErr.ArgErr(help))

}
