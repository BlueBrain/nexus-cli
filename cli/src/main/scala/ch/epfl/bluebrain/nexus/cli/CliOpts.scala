package ch.epfl.bluebrain.nexus.cli

import cats.effect.IO
import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.sdk.Args.uriArgument
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, BuildInfo, Label, Terminal}
import com.monovore.decline.{Command, Help, Opts}
import org.http4s.Uri

object CliOpts {

  def command: Command[Intent] =
    Command(BuildInfo.cliName, s"Nexus CLI (version ${BuildInfo.version})", helpFlag = true) {
      listPlugins orElse login
    }

  private val listPlugins =
    Opts.subcommand("list-plugins", "Detect and list available cli plugins from the PATH") {
      Opts(Intent.ListPlugins)
    }

  private val loginShow =
    Opts.subcommand("show", "Show the current login information (Nexus instance endpoint, realm, token)") {
      Opts(Intent.ShowLogin)
    }

  private val loginRemove =
    Opts.subcommand("remove", "Removes the current login information (Nexus instance endpoint, realm, token)") {
      Opts(Intent.RemoveLogin)
    }

  private val login = Opts.subcommand(
    "login",
    "Authenticate to a Nexus Delta instance with a configured Identity Provider via Password Grant or explicit token"
  ) {
    loginShow orElse loginRemove orElse
      (
        Opts.option[Uri]("endpoint", "The Nexus Delta api endpoint").orNone,
        Opts.option[Label]("realm", "The realm to authenticate against").orNone,
        Opts.option[BearerToken]("token", "A user provided token to be used for future commands").orNone,
        Opts
          .option[String]("client-id", "The client id to be used in the credentials exchange for a token")
          .withDefault("nexus-cli")
      ).mapN(Intent.Login.apply)
  }

  def printHelp(term: Terminal, help: Help): IO[Unit] =
    if (help.errors.isEmpty) term.writeLn(help.toString)
    else IO.raiseError(CliErr.ArgErr(help))

}
