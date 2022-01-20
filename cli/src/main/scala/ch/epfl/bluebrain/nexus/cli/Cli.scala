package ch.epfl.bluebrain.nexus.cli

import cats.effect.*
import cats.implicits.*
import ch.epfl.bluebrain.nexus.cli.Intent
import ch.epfl.bluebrain.nexus.cli.sdk.*
import ch.epfl.bluebrain.nexus.cli.sdk.Args.given
import com.monovore.decline.{Command, Help, Opts}
import org.http4s.Uri

object Cli:

  def command: Command[Intent] =
    Command(BuildInfo.cliName, s"Nexus CLI (version ${BuildInfo.version})", helpFlag = true) {
      listPlugins orElse login
    }

  private val listPlugins =
    Opts.subcommand("list-plugins", "Detect and list available cli plugins from the PATH") {
      Opts(Intent.ListPlugins)
    }

  private val login =
    Opts.subcommand(
      "login",
      "Authenticate to a Nexus Delta instance with a configured Identity Provider via Password Grant or explicit token"
    ) {
      (
        Opts.option[Uri]("endpoint", "The Nexus Delta api endpoint").orNone,
        Opts.option[Label]("realm", "The realm to authenticate against").orNone,
        Opts.option[BearerToken]("token", "A user provided token to be used for future commands").orNone,
        Opts
          .option[String]("client-id", "The client id to be used in the credentials exchange for a token")
          .withDefault("nexus-cli")
      ).mapN(Intent.Login.apply)
    }

  def printHelp(terminal: Terminal, help: Help): IO[Unit] =
    if (help.errors.isEmpty) terminal.writeLn(help.toString)
    else IO.raiseError(CliErr.ArgErr(help))
