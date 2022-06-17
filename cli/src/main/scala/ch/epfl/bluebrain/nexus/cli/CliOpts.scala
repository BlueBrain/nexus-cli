package ch.epfl.bluebrain.nexus.cli

import cats.effect.IO
import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.sdk.Args._
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ProjectRef
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, BuildInfo, Label, Terminal}
import com.monovore.decline.{Command, Help, Opts}
import io.circe.Json
import org.http4s.Uri

object CliOpts {

  def command: Command[Intent] =
    Command(BuildInfo.cliName, s"Nexus CLI (version ${BuildInfo.version})", helpFlag = true) {
      listPlugins orElse login orElse resources orElse orgs orElse projects
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

  private val listResources = Opts.subcommand(
    "list",
    "Lists resources"
  ) {
    (
      Opts.option[ProjectRef]("project", "The project where resources should be listed"),
      Opts.flag("include-all", "Include all supported resource types (e.g. Schemas)").orNone
    ).mapN {
      case (project, Some(_)) => Intent.ListResources(project, includeAll = true)
      case (project, None)    => Intent.ListResources(project, includeAll = false)
    }
  }

  private val getResourceSource = Opts.subcommand(
    "get-source",
    "Prints the json representation of the resource as provided by the client"
  ) {
    (
      Opts.option[ProjectRef]("project", "The resource project"),
      Opts.option[Uri]("id", "The resource id")
    ).mapN(Intent.GetResourceSource.apply)
  }

  private val updateResource = Opts.subcommand(
    "update",
    "Performs a resource update"
  ) {
    (
      Opts.option[ProjectRef]("project", "The resource project"),
      Opts.option[Uri]("id", "The resource id"),
      Opts.option[Json]("source", "The resource representation")
    ).mapN(Intent.UpdateResource.apply)
  }

  private val resources = Opts.subcommand(
    "resources",
    "Operations on resources"
  ) {
    listResources orElse getResourceSource orElse updateResource
  }

  private val orgs = Opts.subcommand(
    "orgs",
    "Operations on organizations"
  ) {
    (
      Opts.option[Int]("from", "The start page").orNone,
      Opts.option[Int]("size", "The max number of results").orNone,
      Opts.option[Boolean]("deprecated", "The deprecation status of the organization").orNone
    ).mapN(Intent.ListOrgs.apply)
  }

  private val projects = Opts.subcommand(
    "projects",
    "Operations on projects"
  ) {
    (
      Opts.option[Label]("org", "The parent organization").orNone,
      Opts.option[Int]("from", "The start page").orNone,
      Opts.option[Int]("size", "The max number of results").orNone,
      Opts.option[Boolean]("deprecated", "The deprecation status of the organization").orNone
    ).mapN(Intent.ListProjects.apply)
  }

  def printHelp(term: Terminal, help: Help): IO[Unit] =
    if (help.errors.isEmpty) term.writeLn(help.toString)
    else IO.raiseError(CliErr.ArgErr(help))

}
