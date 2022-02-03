package ch.epfl.bluebrain.nexus.cli.sdk

import cats.effect.IO
import cats.implicits._
import fs2.io.file.{Files, Path}
import fs2.text
import io.circe.Json
import io.circe.parser._

object PathUtils {

  def loadPath(path: Path): IO[String] =
    for {
      cr      <- canRead(path)
      _       <- IO.raiseUnless(cr)(Err.PathIsNotReadableErr(path))
      content <- Files[IO]
                   .readAll(path)
                   .through(text.utf8.decode)
                   .compile
                   .toList
                   .map {
                     _.foldLeft("")(_ + _)
                   }
    } yield content

  def canRead(path: Path): IO[Boolean] =
    for {
      exists  <- Files[IO].exists(path)
      isFile  <- Files[IO].isRegularFile(path)
      canRead <- Files[IO].isReadable(path)
    } yield exists && isFile && canRead

  def loadPathAsJson(path: Path): IO[Json] =
    loadPath(path).flatMap { str =>
      IO.fromEither(parse(str).leftMap(pf => Err.FileParseErr(path, pf.getMessage)))
    }
}
