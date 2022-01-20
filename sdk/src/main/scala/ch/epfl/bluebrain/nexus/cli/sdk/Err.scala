package ch.epfl.bluebrain.nexus.cli.sdk

import cats.effect.*
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal.lineSep
import fansi.{Color, Str}
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

  case class UnsupportedContentType(ct: Option[`Content-Type`]) extends Err:
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
