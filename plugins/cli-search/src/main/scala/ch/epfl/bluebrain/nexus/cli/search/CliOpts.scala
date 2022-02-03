package ch.epfl.bluebrain.nexus.cli.search

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.Args.pathArgument
import ch.epfl.bluebrain.nexus.cli.sdk.{BuildInfo, Terminal}
import com.monovore.decline.{Command, Help, Opts}
import fs2.io.file.Path

object CliOpts {

  def command: Command[Intent] =
    Command(name, s"Nexus Search CLI (version ${BuildInfo.version})", helpFlag = true) {
      Opts.subcommand("config", "Configuration options for global search configuration.") {
        Opts.subcommand("update", "Update the search configuration across all project for a Nexus instance.") {
          Opts
            .option[Path](
              "composite-view-file",
              "The path to the composite view definition file in JSON(-LD) format."
            )
            .map(p => Intent.UpdateConfig(p))
        }
      }
    }

  def name: String = BuildInfo.cliName + " search"

  def printHelp(terminal: Terminal, help: Help): IO[Unit] =
    if (help.errors.isEmpty) terminal.writeLn(help.toString)
    else IO.raiseError(SearchErr.ArgErr(help))

}
