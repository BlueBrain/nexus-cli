package ch.epfl.bluebrain.nexus.cli.sdk

import cats.implicits.*
import com.monovore.decline.Argument
import org.http4s.Uri

import java.nio.file.{Path, Paths}
import scala.concurrent.duration.Duration.Infinite
import scala.concurrent.duration.{Duration, FiniteDuration}
import scala.util.{Failure, Success, Try}

trait Args:

  given Argument[Uri] =
    Argument.from("uri") { str =>
      Uri
        .fromString(str)
        .leftMap(_ => s"Invalid Uri: '$str'")
        .ensure(s"Invalid Uri: '$str'")(uri => uri.scheme.isDefined)
        .toValidatedNel
    }

  given Argument[BearerToken] =
    Argument.from("token") { str =>
      Either
        .cond(str.nonEmpty, str.trim, "Token must be a non empty string")
        .toValidatedNel
        .map(value => BearerToken.unsafe(value))
    }

  given Argument[Label] =
    Argument.from("label") { str =>
      Label(str).leftMap(_.message).toValidatedNel
    }

  given Argument[FiniteDuration] =
    Argument.from("duration") { str =>
      val either: Either[String, FiniteDuration] =
        Try(Duration.create(str)) match
          case Success(fd: FiniteDuration) => Right(fd)
          case Success(_: Infinite)        => Left("The duration must be finite")
          case Failure(_)                  => Left("Invalid duration, must be '<number><unit>'")
      either.toValidatedNel
    }

  given Argument[Path] =
    Argument.from("path") { str =>
      Try(Paths.get(str)).toEither
        .leftMap(_ => s"Invalid path: '$str'")
        .toValidatedNel
    }

object Args extends Args
