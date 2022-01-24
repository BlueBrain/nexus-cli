package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.*
import cats.implicits.*
import ch.epfl.bluebrain.nexus.cli.sdk.BuildInfo
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal
import fansi.Color.*
import fansi.Str

import java.io.File

object ListPlugins:
  def apply(term: Terminal): IO[ExitCode] =
    Plugins.pluginsOnPath
      .flatMap { plugins =>
        if (plugins.isEmpty) term.writeLn("No plugins found on the PATH.")
        else
          term.writeLn("Available plugins:") >>
            plugins.map { p =>
              term.writeLn(
                Green(s"- ${p.fileName.toString.drop(BuildInfo.cliName.length + 1)}") ++ Str(
                  s" (${p.absolute.toString})"
                )
              )
            }.sequence
      }
      .as(ExitCode.Success)
