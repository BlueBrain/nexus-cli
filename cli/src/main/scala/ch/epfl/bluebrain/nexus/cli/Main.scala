package ch.epfl.bluebrain.nexus.cli

import cats.effect.{ExitCode, IO, IOApp}
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, Terminal}
import com.monovore.decline.Help

object Main extends IOApp {
  override def run(args: List[String]): IO[ExitCode] =
    Terminal()
      .use { terminal =>
        val io: IO[ExitCode] = CliOpts.command.parse(args) match {
          case Left(help)    =>
            pluginInvocation(args, help) match {
              case None                         => CliOpts.printHelp(terminal, help).as(ExitCode.Success)
              case Some((pluginName, restArgs)) =>
                impl.Plugins
                  .resolvePlugin(pluginName)
                  .flatMap {
                    case Some(path) => evaluate(Intent.InvokePlugin(path, restArgs), terminal)
                    case None       => IO.raiseError(CliErr.UnknownPluginErr(pluginName))
                  }
            }
          case Right(intent) => evaluate(intent, terminal)
        }

        io.handleErrorWith {
          case e: Err => e.println(terminal).as(ExitCode.Error)
          case th     => Err.UnknownErr(th).println(terminal).as(ExitCode.Error)
        }
      }

  private def evaluate(intent: Intent, term: Terminal): IO[ExitCode] =
    intent match {
      case Intent.ListPlugins                             => impl.ListPlugins(term)
      case Intent.InvokePlugin(path, args)                => impl.InvokePlugin(path, args)
      case Intent.Login(endpoint, realm, token, clientId) => impl.Login(term, endpoint, realm, token, clientId)
      case Intent.ShowLogin                               => impl.ShowLogin(term)
      case Intent.RemoveLogin                             => impl.RemoveLogin()
    }

  private def pluginInvocation(args: List[String], help: Help): Option[(String, List[String])] =
    (args, help.errors.headOption) match {
      case (head :: rest, Some(err)) if err == s"Unexpected argument: $head" => Some((head, rest))
      case _                                                                 => None
    }
}
