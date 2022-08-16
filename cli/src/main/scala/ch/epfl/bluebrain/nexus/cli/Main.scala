package ch.epfl.bluebrain.nexus.cli

import cats.effect.{ExitCode, IO, IOApp}

object Main extends IOApp:

  override def run(args: List[String]): IO[ExitCode] =
    IO.pure {
      val value = List(2, 4, 6)
      val result = value.forall(el => el % 2 == 0)
      println(result)
      ExitCode.Success
    }

