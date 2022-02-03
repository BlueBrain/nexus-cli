package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.{ExitCode, IO}
import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.sdk.{BuildInfo, Terminal}
import fansi.Color.Green
import fansi.Str
import fs2.io.file.Path

object ListPlugins {

  def apply(term: Terminal): IO[ExitCode] =
    Plugins.pluginsOnPath
      .flatMap { plugins =>
        if (plugins.isEmpty) term.writeLn("No plugins found on the PATH.")
        else
          term.writeLn("Available plugins:") >>
            plugins.traverse { p => writePluginEntry(term, p) }
      }
      .as(ExitCode.Success)

  private def writePluginEntry(term: Terminal, p: Path): IO[Unit] =
    term.writeLn(
      Green(s"- ${p.fileName.toString.drop(BuildInfo.cliName.length + 1)}") ++ Str(s" (${p.absolute.toString})")
    )

}
