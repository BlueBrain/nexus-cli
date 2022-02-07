package ch.epfl.bluebrain.nexus.cli.copy

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.copy.CopyErr.ArgErr
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal.lineSep
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, Terminal}
import com.monovore.decline.Help
import io.circe.{DecodingFailure, Json, ParsingFailure}
import org.http4s.Uri

sealed abstract class CopyErr(val message: String, val description: String, val solution: Option[String]) extends Err {
  override def render(term: Terminal): IO[String] =
    this match {
      case ArgErr(help)                           => IO.delay(help.toString)
      case CopyErr.UnableToParseEventErr(raw, _)  => renderGeneric(term, Some(raw))
      case CopyErr.UnableToDecodeEventErr(raw, _) => renderWithJson(term, "Event:", raw)
      case _: CopyErr                             => renderHeader(term)
    }
}

object CopyErr {

  case class ArgErr(help: Help)
      extends CopyErr(
        help.errors.mkString(", "),
        lineSep + "Usage: " + lineSep + help.usage.mkString(lineSep) + help.body.mkString(lineSep),
        None
      )

  case class UnableToParseEventErr(body: String, cause: ParsingFailure)
      extends CopyErr(
        "Unable to parse event.",
        s"An event read from the source environment could not be parsed, reason: ${cause.getMessage}",
        None
      )

  case class UnableToDecodeEventErr(raw: Json, cause: DecodingFailure)
      extends CopyErr(
        "Unable to decode event.",
        s"An event read from the source environment could not be decoded, reason: ${cause.getMessage}",
        None
      )

  case object ConfirmationNotReceivedErr
      extends CopyErr(
        "Execution aborted.",
        "The user did not confirm the project copy configuration.",
        None
      )

  case class InvalidCredentialsErr(endpoint: Uri, reason: String)
      extends CopyErr(
        "Invalid token provided.",
        s"The token provided for the endpoint '${endpoint.renderString}' is invalid, reason: $reason.",
        Some("Run the copy command again with a valid token.")
      )

  case class InvalidEndpointErr(endpoint: Uri, reason: String)
      extends CopyErr(
        "Unable to validate environment.",
        s"""A request to the endpoint '${endpoint.renderString}' failed, most likely caused by an incorrect
           |endpoint value, reason: $reason.""".stripMargin,
        Some("Run the copy command again with a valid endpoint.")
      )
}
