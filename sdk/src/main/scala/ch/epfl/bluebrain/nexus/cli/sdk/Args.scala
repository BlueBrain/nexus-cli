package ch.epfl.bluebrain.nexus.cli.sdk

import cats.implicits._
import com.monovore.decline.Argument
import fs2.io.file.Path
import io.circe._
import org.http4s.Uri

import scala.concurrent.duration.Duration.Infinite
import scala.concurrent.duration.{Duration, FiniteDuration}
import scala.util.{Failure, Success, Try}

trait Args {

  implicit val uriArgument: Argument[Uri] =
    Argument.from("uri") { str =>
      Uri
        .fromString(str)
        .leftMap(_ => s"Invalid Uri: '$str'")
        .ensure(s"Invalid Uri: '$str'")(uri => uri.scheme.isDefined)
        .toValidatedNel
    }

  implicit val finiteDurationArgument: Argument[FiniteDuration] =
    Argument.from("duration") { str =>
      val either: Either[String, FiniteDuration] =
        Try(Duration.create(str)) match {
          case Success(fd: FiniteDuration) => Right(fd)
          case Success(_: Infinite)        => Left("The duration must be finite")
          case Failure(_)                  => Left("Invalid duration, must be '<number><unit>'")
        }
      either.toValidatedNel
    }

  implicit val pathArgument: Argument[Path] =
    Argument.from("path") { str =>
      Try(Path(str)).toEither
        .leftMap(_ => s"Invalid path: '$str'")
        .toValidatedNel
    }

  implicit val jsonArgument: Argument[Json] =
    Argument.from("json") { str =>
      parser
        .parse(str)
        .leftMap(pf => s"Invalid json: '${pf.getMessage()}'")
        .toValidatedNel
    }
}

object Args extends Args
