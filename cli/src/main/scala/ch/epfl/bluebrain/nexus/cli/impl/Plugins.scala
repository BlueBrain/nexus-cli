package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.IO
import ch.epfl.bluebrain.nexus.cli.sdk.BuildInfo
import fs2.Stream
import fs2.io.file.{Files, Path}

import java.io.File

object Plugins:

  def pluginExists(name: String): IO[Boolean] =
    resolvePlugin(name).map(_.isDefined)

  def resolvePlugin(name: String): IO[Option[Path]] =
    pluginsOnPath.map(_.find(_.fileName.toString == s"${BuildInfo.cliName}-$name"))

  def pluginsOnPath: IO[Vector[Path]] =
    sys.env.get("PATH") match
      case None        => IO.pure(Vector.empty)
      case Some(value) =>
        val dirs = value.split(File.pathSeparator).toVector
        Stream
          .iterable(dirs)
          .map(str => Path(str))
          .evalFilter(p => Files[IO].exists(p))
          .evalMap { p =>
            Files[IO]
              .isDirectory(p)
              .ifM(
                IO.pure(Files[IO].list(p, s"${BuildInfo.cliName}-*")),
                IO.pure(Stream[IO, Path](p).filter(p => p.fileName.startsWith(s"${BuildInfo.cliName}-")))
              )
          }
          .flatten
          .evalFilter(p => Files[IO].isRegularFile(p, followLinks = true))
          .evalFilter(p => Files[IO].isExecutable(p))
          .compile
          .toVector
