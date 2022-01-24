package ch.epfl.bluebrain.nexus.cli.sdk

import cats.effect.*
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal.lineSep
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse
import fansi.{Color, Str}
import fs2.io.file.Path
import org.http4s.headers.`Content-Type`

import scala.util.Try

trait Err extends Throwable:

  override def fillInStackTrace(): Throwable = this

  /**
    * @return
    *   a short descriptive message as to why the error occurred
    */
  def message: String

  /**
    * @return
    *   a (possibly multi-line) description of the error
    */
  def description: String

  /**
    * @return
    *   and optional solution to solve this error
    */
  def solution: Option[String]

  /**
    * Renders the error as a String.
    */
  def render(term: Terminal): IO[String]

  /**
    * Prints the error as a String.
    */
  def println(term: Terminal): IO[Unit] =
    render(term).flatMap { str =>
      term.writeLn(str)
    }

object Err:
  val padding: Str = Str("🔥  ")

  case class UnknownErr(th: Throwable) extends Err:
    override val message: String                    =
      Try(th.getClass.getCanonicalName + ": " + th.getMessage).getOrElse(th.getClass.getCanonicalName)
    override val description: String                = th.getStackTrace.map(_.toString).mkString("\n")
    override val solution: Option[String]           = None
    override def render(term: Terminal): IO[String] =
      for
        msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
        desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
      yield msg + lineSep + desc

  case class IllegalLabelErr(provided: String) extends Err:
    override val message: String                    = "Illegal Label format"
    override val description: String                =
      s"The provided value ('$provided') does not match the label format constraints ('${Label.regex.regex}')."
    override val solution: Option[String]           = None
    override def render(term: Terminal): IO[String] =
      for
        msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
        desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
      yield msg + lineSep + desc

  case class ParseErr(cause: String) extends Err:
    override val message: String                    = "Failed to parse a response from the server."
    override val description: String                = s"The underlying parsing failure message is: '$cause'."
    override val solution: Option[String]           = None
    override def render(term: Terminal): IO[String] =
      for
        msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
        desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
      yield msg + lineSep + desc

  case class UnsupportedContentTypeErr(ct: Option[`Content-Type`]) extends Err:
    override val message: String                    = "Unsupported Content-Type header."
    override val description: String                =
      "The server did not respond with the expected Content-Type 'application/json' or 'application/ld+json'." +
        (ct match {
          case Some(value) => s"The provided header was '${value.mediaType.mainType}/${value.mediaType.subType}'."
          case None        => "No value was provided for the Content-Type header."
        })
    override val solution: Option[String]           = None
    override def render(term: Terminal): IO[String] =
      for
        msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
        desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
      yield msg + lineSep + desc

  case object UnconfiguredErr extends Err:
    override val message: String = "Endpoint and/or credentials were not configured."

    override val description: String =
      """The plugin requires NEXUS_ENDPOINT and NEXUS_TOKEN environment variables to be provided
        |in order to execute the chosen action.""".stripMargin

    private val sol: String = s"Login with the CLI by calling the login subcommand (${BuildInfo.cliName} login ...)"

    override val solution: Option[String] = Some(sol)

    override def render(term: Terminal): IO[String] =
      for
        msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
        desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
        sol  <- term.render(Color.Green("Solution: ") ++ Str(sol), Err.padding)
      yield msg + lineSep + desc + lineSep + sol

  case class UnauthorizedErr(reason: String) extends Err:
    override val message: String = "The request resulted in a 401 Unauthorized response."

    override val description: String =
      s"""A 401 Unauthorized response is usually caused by an invalid token. The following reason was provided by
         |the server: '$reason'.""".stripMargin

    private val sol = s"Login again with the CLI by calling the login subcommand (${BuildInfo.cliName} login ...)"

    override val solution: Option[String] = Some(sol)

    override def render(term: Terminal): IO[String] =
      for
        msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
        desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
        sol  <- term.render(Color.Green("Solution: ") ++ Str(sol), Err.padding)
      yield msg + lineSep + desc + lineSep + sol

  case class ForbiddenErr(reason: String) extends Err:
    override val message: String = "The request resulted in a 403 Forbidden response."

    override val description: String =
      s"""A 403 Forbidden response is usually returned when the caller does not have the required permission to
         |execute the intended action. The following reason was provided by the server: '$reason'.""".stripMargin

    override val solution: Option[String] = None

    override def render(term: Terminal): IO[String] =
      for
        msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
        desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
      yield msg + lineSep + desc

  case class UnsuccessfulResponseErr(resp: ApiResponse.Unsuccessful) extends Err:
    override val message: String = "The request was unsuccessful."

    override val description: String =
      s"""A request is considered unsuccessful when either the status code is not in the 2xx range or the
         |response body could not be decoded as the expected type.""".stripMargin

    override val solution: Option[String] = None

    override def render(term: Terminal): IO[String] =
      for
        msg    <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
        desc   <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
        status <- term.render(Color.Cyan("Status: ") ++ Str(s"${resp.status.code} ${resp.status.reason}"), Err.padding)
        body   <- term.render(Color.Cyan("Response body:"), Err.padding)
        json   <- term.renderJson(resp.raw, Err.padding)
      yield msg + lineSep + desc + lineSep + status + lineSep + body + lineSep + json

  case class PathIsNotReadableErr(path: Path) extends Err:
    override val message: String = "Could not read provided path."

    override val description: String =
      s"The provided path '${path.absolute.toString}' does not exit or it is not readable."

    private val sol =
      s"""Verify that the path '${path.absolute.toString}' exists, that it is a file
         |and that the current user can open it for reading.""".stripMargin

    override val solution: Option[String] = Some(sol)

    override def render(term: Terminal): IO[String] =
      for
        msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
        desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
        sol  <- term.render(Color.Green("Solution: ") ++ Str(sol), Err.padding)
      yield msg + lineSep + desc + lineSep + sol

  case class FileParseErr(path: Path, cause: String) extends Err:
    override val message: String = "Failed to parse content of provided path."

    override val description: String =
      s"""The provided path '${path.absolute.toString}' was successfully read, but its contents could
         | not be parsed as a JSON document.
         | The underlying parsing failure message is: '$cause'.""".stripMargin

    override val solution: Option[String] = None

    override def render(term: Terminal): IO[String] =
      for
        msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
        desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
      yield msg + lineSep + desc
