package ch.epfl.bluebrain.nexus.cli.migrate.ns

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.migrate.ns.MigrateErr.{ArgErr, DecodingErr, UpdateErr}
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal.lineSep
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, Terminal}
import com.monovore.decline.Help
import io.circe.Json
import org.http4s.ParseFailure

sealed abstract class MigrateErr(val message: String, val description: String, val solution: Option[String])
    extends Err {

  override def render(term: Terminal): IO[String] =
    this match {
      case ArgErr(help)   => IO.delay(help.toString)
      case e: DecodingErr => renderWithJson(term, e.description, e.json)
      case e: UpdateErr   => renderWithResponse(term, e.response.status, e.response.raw)
      case _: MigrateErr  => renderHeader(term)
    }
}

object MigrateErr {
  case class ArgErr(help: Help)
      extends MigrateErr(
        help.errors.mkString(", "),
        lineSep + "Usage: " + lineSep + help.usage.mkString(lineSep) + help.body.mkString(lineSep),
        None
      )

  case class DecodingErr(reason: String, json: Json)
      extends MigrateErr(
        "Json decoding failure",
        reason,
        None
      )

  case class UpdateErr(response: ApiResponse.Unsuccessful.Unknown)
      extends MigrateErr(
        "Failed to update resource",
        "The resource could not be updated due to a client error.",
        None
      )

  case class CouldNotParseIdAsUriErr(id: String, pf: ParseFailure)
      extends MigrateErr(
        "Could not parse id as uri",
        s"Could not parse id '$id' as an Uri because '${pf.message}'",
        None
      )
}
