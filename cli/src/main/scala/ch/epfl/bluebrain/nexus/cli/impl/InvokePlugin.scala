package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.*
import cats.effect.Outcome.*
import fs2.io.file.Path

object InvokePlugin:
  def apply(pluginName: String, path: Path, args: List[String]): IO[ExitCode] =
    val acquire: Poll[IO] => IO[Process] =
      _ =>
        Config.load.flatMap {
          case Some(value) =>
            IO.blocking {
              val builder = new ProcessBuilder(path.absolute.toString :: args: _*)
              builder.environment().put("NEXUS_ENDPOINT", value.endpoint.toString)
              builder.environment().put("NEXUS_TOKEN", value.token.value)
              builder.inheritIO().start()
            }
          case None        =>
            IO.blocking {
              new ProcessBuilder(path.absolute.toString :: args: _*).inheritIO().start()
            }
        }

    val use: Process => IO[ExitCode] =
      process => IO.blocking(process.waitFor()).map(ExitCode.apply)

    val release: (Process, OutcomeIO[ExitCode]) => IO[Unit] = {
      case (_, Succeeded(_))     => IO.unit
      case (process, Errored(_)) => IO.blocking(process.destroy())
      case (process, Canceled()) => IO.blocking(process.destroy())
    }

    IO.bracketFull(acquire)(use)(release)
