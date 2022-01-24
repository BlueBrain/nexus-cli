package ch.epfl.bluebrain.nexus.cli.search

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.Terminal.lineSep
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, Terminal}
import com.monovore.decline.Help
import fansi.{Color, Str}

enum CliErr(val message: String, val description: String, val solution: Option[String]) extends Err:
  case ArgErr(help: Help)
      extends CliErr(
        help.errors.mkString(", "),
        lineSep + "Usage: " + lineSep + help.usage.mkString(lineSep) + help.body.mkString(lineSep),
        None
      )

  override def render(term: Terminal): IO[String] =
    this match
      case ArgErr(help) => IO.delay(help.toString)
      case err: CliErr  =>
        for
          msg  <- term.render(Color.Red("An error occurred: ") ++ Str(message), Err.padding)
          desc <- term.render(Color.Cyan("Description: ") ++ Str(description), Err.padding)
          sol  <- term.render(
                    solution match
                      case Some(sol) => Color.Green("Solution: ") ++ Str(sol)
                      case None      => Str("")
                    ,
                    Err.padding
                  )
        yield msg + lineSep + desc + lineSep + sol
