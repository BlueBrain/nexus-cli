package ch.epfl.bluebrain.nexus.cli.migrate.ns

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.{BuildInfo, Terminal}
import com.monovore.decline.time.defaultInstant
import cats.implicits._
import com.monovore.decline.{Command, Help, Opts}

import java.time.Instant

object CliOpts {

  def command: Command[Intent] =
    Command(name, s"Nexus Namespace Migration CLI (version ${BuildInfo.version})", helpFlag = true) {
      (
        Opts
          .option[Instant](
            "last-update-before",
            "Update only resources that haven't been updated before the specified instant."
          )
          .withDefault(Instant.now()),
        Opts.option[Int]("page-size", "The page size when querying Elasticsearch").withDefault(20),
        Opts.option[Int]("concurrency", "How many updates to perform in parallel.").withDefault(1)
      ).mapN(Intent.MigrateNs.apply)
    }

  def name: String = BuildInfo.cliName + " migrate-ns"

  def printHelp(terminal: Terminal, help: Help): IO[Unit] =
    if (help.errors.isEmpty) terminal.writeLn(help.toString)
    else IO.raiseError(MigrateErr.ArgErr(help))

}
