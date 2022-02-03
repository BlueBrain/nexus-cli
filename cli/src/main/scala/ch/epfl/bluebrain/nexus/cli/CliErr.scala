package ch.epfl.bluebrain.nexus.cli

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.CliErr._
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal.lineSep
import ch.epfl.bluebrain.nexus.cli.sdk.{BuildInfo, Err, Terminal}
import com.monovore.decline.Help
import fs2.io.file.Path
import io.circe.Json
import org.http4s.Status

sealed abstract class CliErr(val message: String, val description: String, val solution: Option[String]) extends Err {

  override def render(term: Terminal): IO[String] =
    this match {
      case ArgErr(help)                                  => IO.delay(help.toString)
      case UnableToRetrieveRealmErr(status, response)    => renderWithResponse(term, status, response)
      case UnableToDecodeLoginErr(status, response)      => renderWithResponse(term, status, response)
      case UnableToDecodeIdentitiesErr(status, response) => renderWithResponse(term, status, response)
      case InvalidTokenErr(tpe, reason)                  => renderGeneric(term, Some(tpe + ": " + reason))
      case _: CliErr                                     => renderGeneric(term)
    }

}

object CliErr {

  case object UserHomeNotFoundErr
      extends CliErr(
        "The 'user.home' system property was not defined.",
        s"""The 'user.home' property is required for determining where the application
         |configuration needs to be stored or read from. The JVM automatically detects
         |the appropriate value from the provided environment, but in this case it could not.""".stripMargin,
        Some("run the tool again forcing a value ('-Duser.home=') to the expected system property.")
      )

  case class IncorrectUserHomeErr(userHome: String)
      extends CliErr(
        s"The 'user.home' system property ('$userHome') cannot be parsed as a correct path.",
        s"""The 'user.home' property is required for determining where the application
         |configuration needs to be stored or read from.""".stripMargin,
        Some("run the tool again forcing a correct value ('-Duser.home=') to the expected system property.")
      )

  case class InaccessibleConfigFileErr(path: Path)
      extends CliErr(
        s"The config file '${path.absolute.toString}' is cannot be read.",
        s"""Attempting to access the config file '${path.absolute.toString}' failed.
         |The path either does not represent a file or the file could not be read.""".stripMargin,
        Some(
          "Update the permission mask or remove the current file and issue another 'login' command to regenerate it."
        )
      )

  case class UnwritableConfigFileErr(path: Path)
      extends CliErr(
        s"The config file '${path.absolute.toString}' is cannot be written.",
        s"""Attempting to write login configuration to '${path.absolute.toString}' failed.
         |The issue is most likely caused by an incorrect permission mask on the file itself
         |or parent directory.""".stripMargin,
        Some("Update the permission mask to the file or parent directory and issue another 'login' command.")
      )

  case class IncorrectConfigFileFormatErr(path: Path, reason: String)
      extends CliErr(
        s"The config file '${path.absolute.toString}' is malformed.",
        s"""Attempting to parse the config file '${path.absolute.toString}' failed with the following error:
         |'$reason'.
         |The config file must be a valid json with 3 optional fields 'endpoint', 'realm' and 'token'.""".stripMargin,
        Some("Issue another 'login' command to regenerate it or manually correct the error in the file.")
      )

  case object IncorrectLoginFlagsErr
      extends CliErr(
        "Incorrect login command options.",
        s"""In order to be able to login to a Nexus instance both 'endpoint' and 'realm' options must be provided along
         |with an optional 'token'. When a 'token' is provided it will be saved automatically, otherwise
         |credentials will be requested to be exchanged for a token.""".stripMargin,
        Some("Issue another 'login' command with correct options.")
      )

  case object RealmIsDeprecatedErr
      extends CliErr(
        "The provided realm is deprecated.",
        """In order to be able to login to a Nexus instance both 'endpoint' and 'realm' options must be provided along
        |with an optional 'token'. When a 'token' is provided it will be saved automatically, otherwise
        |credentials will be requested to be exchanged for a token.
        |The provided realm must not be deprecated, otherwise the Nexus instance will reject any token issued for
        |that realm.""".stripMargin,
        Some("Issue another 'login' command providing a realm that is NOT deprecated.")
      )

  case object RealmNotFoundErr
      extends CliErr(
        "The provided realm could not be found.",
        """In order to be able to login to a Nexus instance both 'endpoint' and 'realm' options must be provided along
        |with an optional 'token'. When a 'token' is provided it will be saved automatically, otherwise
        |credentials will be requested to be exchanged for a token.
        |The provided realm must exist such that the tokenEndpoint is collected to execute the
        |authentication.""".stripMargin,
        Some("Issue another 'login' command providing a realm that exists.")
      )

  case class UnableToRetrieveRealmErr(status: Status, response: Json)
      extends CliErr(
        "The provided realm could not be retrieved.",
        s"""In order to be able to login to a Nexus instance the provided realm must be read to collect the
         |tokenEndpoint for executing the authentication.
         |The Nexus instance returned an unexpected response.""".stripMargin,
        None
      )

  case class UnableToDecodeLoginErr(status: Status, response: Json)
      extends CliErr(
        "Unable to retrieve an access token from IdP.",
        """While attempting to exchange the provided credentials with an access token the IdP
        |returned an unknown error response.""".stripMargin,
        None
      )

  case class UnableToLoginErr(reason: String)
      extends CliErr(
        "Unable to retrieve an access token from IdP.",
        s"""While attempting to exchange the provided credentials with an access token the IdP
         |returned an error response: '$reason'""".stripMargin,
        None
      )

  case class InvalidTokenErr(`type`: String, reason: String)
      extends CliErr(
        "Unable to confirm that the provided token is valid.",
        s"""When logging in with a token, the token is verified against the Nexus instance by fetching the
         |corresponding list of identities for that token. The server responded with an error when
         |attempting to get the list of identities.""".stripMargin,
        None
      )

  case class UnableToDecodeIdentitiesErr(status: Status, response: Json)
      extends CliErr(
        "Unable to confirm that the provided token is valid.",
        s"""When logging in with a token, the token is verified against the Nexus instance by fetching the
         |corresponding list of identities for that token. The server returned an unknown response when
         |attempting to get the list of identities.""".stripMargin,
        None
      )

  case class ArgErr(help: Help)
      extends CliErr(
        help.errors.mkString(", "),
        lineSep + "Usage: " + lineSep + help.usage.mkString(lineSep) + help.body.mkString(lineSep),
        None
      )

  case class UnknownPluginErr(pluginName: String)
      extends CliErr(
        s"No plugin with name '$pluginName' was found.",
        s"""When the subcommand provided does not match one of the supported subcommands, the ${BuildInfo.cliName}
       |tool attempts to find a plugin executable with the name '${BuildInfo.cliName}-<plugin-name>' on the PATH.
       |For this execution the '${BuildInfo.cliName}-$pluginName' was searched but wasn't found.""".stripMargin,
        Some(s"run '${BuildInfo.cliName} list-plugins' to list the available plugins")
      )
}
