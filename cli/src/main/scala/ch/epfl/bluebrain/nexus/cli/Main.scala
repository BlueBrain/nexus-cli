package ch.epfl.bluebrain.nexus.cli

import cats.effect.*
import cats.implicits.*
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, Terminal}
import com.monovore.decline.Help
import fs2.*
import fs2.io.file.{Files, Path}

import java.io.File

object Main extends IOApp:

  override def run(args: List[String]): IO[ExitCode] =
    Terminal()
      .use { terminal =>
        val io: IO[ExitCode] = Cli.command.parse(args) match
          case Left(help)    =>
            pluginInvocation(args, help) match
              case None                         => Cli.printHelp(terminal, help).as(ExitCode.Success)
              case Some((pluginName, restArgs)) =>
                impl.Plugins
                  .resolvePlugin(pluginName)
                  .flatMap {
                    case Some(path) => evaluate(Intent.InvokePlugin(pluginName, path, restArgs), terminal)
                    case None       => IO.raiseError(CliErr.UnknownPluginErr(pluginName))
                  }
          case Right(intent) => evaluate(intent, terminal)

        io.handleErrorWith {
          case e: Err => e.println(terminal).as(ExitCode.Error)
          case th     => Err.UnknownErr(th).println(terminal).as(ExitCode.Error)
        }
      }

  private def evaluate(intent: Intent, term: Terminal): IO[ExitCode] =
    intent match
      case Intent.ListPlugins                             => impl.ListPlugins(term)
      case Intent.InvokePlugin(name, path, args)          => impl.InvokePlugin(name, path, args)
      case Intent.Login(endpoint, realm, token, clientId) => impl.Login(endpoint, realm, token, clientId, term)

  private def pluginInvocation(args: List[String], help: Help): Option[(String, List[String])] =
    (args, help.errors.headOption) match
      case (head :: rest, Some(err)) if err == s"Unexpected argument: $head" => Some((head, rest))
      case _                                                                 => None
