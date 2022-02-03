package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.IO
import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.CliErr
import ch.epfl.bluebrain.nexus.cli.sdk.Err
import fs2.Stream
import fs2.io.file.{Files, Path}
import fs2.text.utf8
import io.circe.parser._
import io.circe.syntax._

import java.nio.file.InvalidPathException

object Config {

  def load: IO[Option[LoginConfig]] =
    for {
      cfgFile     <- nexusCfgFilePath
      asStringOpt <- loadFile(cfgFile)
      cfgOpt      <- asStringOpt.traverse(str => parseAndDecode(cfgFile, str))
    } yield cfgOpt

  def save(cfg: LoginConfig): IO[Unit] =
    for {
      cfgFile <- nexusCfgFilePath
      _       <- saveFile(cfgFile, cfg)
    } yield ()

  def remove: IO[Unit] =
    for {
      cfgFile <- nexusCfgFilePath
      _       <- Files[IO].deleteIfExists(cfgFile)
    } yield ()

  private def nexusCfgFilePath: IO[Path] =
    nexusDirPath.map(_ / "config.json")

  private def nexusDirPath: IO[Path] =
    IO.delay(sys.props.get("user.home")).flatMap {
      case Some(value) =>
        IO.delay(Path(value) / ".nexus").onError {
          case _: InvalidPathException =>
            IO.println(s"The path: '$value'") >> IO.raiseError(CliErr.IncorrectUserHomeErr(value))
          case th                      => IO.raiseError(Err.UnknownErr(th))
        }
      case None        => IO.raiseError(CliErr.UserHomeNotFoundErr)
    }

  private def loadFile(path: Path): IO[Option[String]] =
    (Files[IO].exists(path), Files[IO].isRegularFile(path), Files[IO].isReadable(path)).tupled.flatMap {
      case (true, true, true) => Files[IO].readAll(path).through(utf8.decode).fold("")(_ + _).head.compile.last
      case (false, _, _)      => IO.pure(None)
      case (true, _, _)       => IO.raiseError(CliErr.InaccessibleConfigFileErr(path))
    }

  private def parseAndDecode(path: Path, str: String): IO[LoginConfig] =
    decode[LoginConfig](str) match {
      case Left(err)    => IO.raiseError(CliErr.IncorrectConfigFileFormatErr(path, err.getMessage))
      case Right(value) => IO.pure(value)
    }

  private def saveFile(path: Path, cfg: LoginConfig): IO[Unit] =
    (
      Files[IO].exists(path),
      Files[IO].isRegularFile(path),
      Files[IO].isWritable(path),
      path.parent.map(Files[IO].exists).getOrElse(IO.pure(false)),
      path.parent.map(Files[IO].isDirectory).getOrElse(IO.pure(false)),
      path.parent.map(Files[IO].isWritable).getOrElse(IO.pure(false))
    ).tupled.flatMap {
      // file exits and is writable
      case (true, true, true, _, _, _)     => writeToFile(path, cfg)
      // does not exist and parent is not writeable
      case (false, _, _, true, _, false)   => IO.raiseError(CliErr.UnwritableConfigFileErr(path))
      // does not exist and parent is not a directory -> don't do anything
      case (false, _, _, true, false, _)   => IO.raiseError(CliErr.UnwritableConfigFileErr(path))
      // does not exist and parent does not exist
      case (false, _, _, false, _, _)      =>
        path.parent.map(Files[IO].createDirectories).getOrElse(IO.unit) >> writeToFile(path, cfg)
      // does not exist and parent is writeable
      case (false, _, _, true, true, true) => writeToFile(path, cfg)
      // exists but not a file or not writeable
      case (true, _, _, _, _, _)           => IO.raiseError(CliErr.UnwritableConfigFileErr(path))
    }

  private def writeToFile(path: Path, cfg: LoginConfig): IO[Unit] =
    Stream(cfg.asJson.spaces2)
      .through(utf8.encode)
      .through(Files[IO].writeAll(path))
      .compile
      .drain

}
