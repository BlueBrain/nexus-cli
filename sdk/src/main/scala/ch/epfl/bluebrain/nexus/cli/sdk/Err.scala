package ch.epfl.bluebrain.nexus.cli.sdk

import cats.effect._
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal.lineSep
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse
import fansi.{Color, Str}
import fs2.io.file.Path
import io.circe.Json
import org.http4s.Status
import org.http4s.headers.`Content-Type`

import scala.util.Try

trait Err extends Throwable {

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

  protected def renderGeneric(term: Terminal, additional: Option[String] = None): IO[String] =
    for {
      header <- renderHeader(term)
      err    <- additional match {
                  case Some(value) => term.render(Color.Red("Details: ") ++ Str(value), Err.padding)
                  case None        => IO.pure("")
                }
    } yield header + err

  protected def renderWithResponse(term: Terminal, status: Status, body: Json): IO[String] =
    for {
      header    <- renderHeader(term)
      details   <- term.render(Color.Red("Details: "), Err.padding).map(_ + lineSep)
      st        <- term.render(Color.Red("Status: ") ++ Str(status.code.toString), Err.padding).map(_ + lineSep)
      respTitle <- term.render(Color.Red("Response body:")).map(_ + lineSep)
      resp      <- term.renderJson(body, Err.padding)
    } yield header + details + st + respTitle + resp

  protected def renderWithJson(term: Terminal, description: String, json: Json): IO[String] =
    for {
      header  <- renderHeader(term)
      desc    <- term.render(Color.Red(description), Err.padding).map(_ + lineSep)
      jsonStr <- term.renderJson(json, Err.padding)
    } yield header + desc + jsonStr

  protected def renderHeader(term: Terminal): IO[String] =
    for {
      msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding).map(_ + lineSep)
      desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding).map(_ + lineSep)
      sol  <- solution match {
                case Some(sol) => term.render(Color.Green("Solution: ") ++ Str(sol), Err.padding).map(_ + lineSep)
                case None      => IO.pure("")
              }
    } yield msg + desc + sol
}

object Err {
  val padding: Str = Str("🔥  ")

  case class UnknownErr(th: Throwable) extends Err {
    override val message: String                    =
      Try(th.getClass.getCanonicalName + ": " + th.getMessage).getOrElse(th.getClass.getCanonicalName)
    override val description: String                = th.getStackTrace.map(_.toString).mkString("\n")
    override val solution: Option[String]           = None
    override def render(term: Terminal): IO[String] = renderHeader(term)
  }

  case class IllegalLabelErr(provided: String) extends Err {
    override val message: String                    = "Illegal Label format"
    override val description: String                =
      s"The provided value ('$provided') does not match the label format constraints ('${Label.regex.regex}')."
    override val solution: Option[String]           = None
    override def render(term: Terminal): IO[String] = renderHeader(term)
  }

  case class ParseErr(cause: String) extends Err {
    override val message: String                    = "Failed to parse a response from the server."
    override val description: String                = s"The underlying parsing failure message is: '$cause'."
    override val solution: Option[String]           = None
    override def render(term: Terminal): IO[String] = renderHeader(term)
  }

  case class UnsupportedContentTypeErr(ct: Option[`Content-Type`]) extends Err {
    override val message: String                    = "Unsupported Content-Type header."
    override val description: String                =
      "The server did not respond with the expected Content-Type 'application/json' or 'application/ld+json'." +
        (ct match {
          case Some(value) => s"The provided header was '${value.mediaType.mainType}/${value.mediaType.subType}'."
          case None        => "No value was provided for the Content-Type header."
        })
    override val solution: Option[String]           = None
    override def render(term: Terminal): IO[String] = renderHeader(term)
  }

  case object UnconfiguredErr extends Err {
    override val message: String = "Endpoint and/or credentials were not configured."

    override val description: String =
      """The plugin requires NEXUS_ENDPOINT and NEXUS_TOKEN environment variables to be provided
        |in order to execute the chosen action.""".stripMargin

    override val solution: Option[String] = Some(
      s"Login with the CLI by calling the login subcommand (${BuildInfo.cliName} login ...)"
    )

    override def render(term: Terminal): IO[String] = renderHeader(term)
  }

  case class UnauthorizedErr(reason: String) extends Err {
    override val message: String = "The request resulted in a 401 Unauthorized response."

    override val description: String =
      s"""A 401 Unauthorized response is usually caused by an invalid token. The following reason was provided by
         |the server: '$reason'.""".stripMargin

    override val solution: Option[String] = Some(
      s"Login again with the CLI by calling the login subcommand (${BuildInfo.cliName} login ...)"
    )

    override def render(term: Terminal): IO[String] = renderHeader(term)
  }

  case class ForbiddenErr(reason: String) extends Err {
    override val message: String = "The request resulted in a 403 Forbidden response."

    override val description: String =
      s"""A 403 Forbidden response is usually returned when the caller does not have the required permission to
         |execute the intended action. The following reason was provided by the server: '$reason'.""".stripMargin

    override val solution: Option[String] = None

    override def render(term: Terminal): IO[String] = renderHeader(term)
  }

  case class UnsuccessfulResponseErr(resp: ApiResponse.Unsuccessful) extends Err {
    override val message: String = "The request was unsuccessful."

    override val description: String =
      s"""A request is considered unsuccessful when either the status code is not in the 2xx range or the
         |response body could not be decoded as the expected type.""".stripMargin

    override val solution: Option[String] = None

    override def render(term: Terminal): IO[String] = renderWithResponse(term, resp.status, resp.raw)
  }

  case class PathIsNotReadableErr(path: Path) extends Err {
    override val message: String = "Could not read provided path."

    override val description: String =
      s"The provided path '${path.absolute.toString}' does not exit or it is not readable."

    override val solution: Option[String] = Some(
      s"""Verify that the path '${path.absolute.toString}' exists, that it is a file
         |and that the current user can open it for reading.""".stripMargin
    )

    override def render(term: Terminal): IO[String] = renderHeader(term)
  }

  case class FileParseErr(path: Path, cause: String) extends Err {
    override val message: String = "Failed to parse content of provided path."

    override val description: String =
      s"""The provided path '${path.absolute.toString}' was successfully read, but its contents could
         | not be parsed as a JSON document.
         | The underlying parsing failure message is: '$cause'.""".stripMargin

    override val solution: Option[String] = None

    override def render(term: Terminal): IO[String] = renderHeader(term)
  }
}
