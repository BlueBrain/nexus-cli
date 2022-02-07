package ch.epfl.bluebrain.nexus.cli.copy

import cats.effect.{ExitCode, IO, IOApp}
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, Terminal}

object Main extends IOApp {
  override def run(args: List[String]): IO[ExitCode] =
    Terminal()
      .use { terminal =>
        val io: IO[ExitCode] = CliOpts.command.parse(args) match {
          case Left(help)    => CliOpts.printHelp(terminal, help).as(ExitCode.Success)
          case Right(intent) => evaluate(intent, terminal)
        }
        io.handleErrorWith {
          case e: Err => e.println(terminal).as(ExitCode.Error)
          case th     => Err.UnknownErr(th).println(terminal).as(ExitCode.Error)
        }
      }

  private def evaluate(intent: Intent, term: Terminal): IO[ExitCode] =
    intent match {
      case Intent.Copy(source, target, offset, concurrency, preload) =>
        impl.CopyProject(term, source, target, offset, concurrency, preload)
    }
}
