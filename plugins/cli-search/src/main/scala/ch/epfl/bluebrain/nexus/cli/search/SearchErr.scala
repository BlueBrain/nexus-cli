package ch.epfl.bluebrain.nexus.cli.search

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal.lineSep
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, Terminal}
import ch.epfl.bluebrain.nexus.cli.search.SearchErr.ArgErr
import com.monovore.decline.Help

sealed abstract class SearchErr(val message: String, val description: String, val solution: Option[String])
    extends Err {

  override def render(term: Terminal): IO[String] =
    this match {
      case ArgErr(help) => IO.delay(help.toString)
      // case _: SearchErr => renderHeader(term)
    }

}

object SearchErr {

  case class ArgErr(help: Help)
      extends SearchErr(
        help.errors.mkString(", "),
        lineSep + "Usage: " + lineSep + help.usage.mkString(lineSep) + help.body.mkString(lineSep),
        None
      )

}
