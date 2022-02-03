package ch.epfl.bluebrain.nexus.cli.sdk

import cats.effect.IO
import cats.effect.kernel.Resource
import fansi.Str
import io.circe.Json
import org.jline.reader.LineReaderBuilder
import org.jline.terminal.{Terminal => JTerminal, TerminalBuilder}

import scala.annotation.tailrec

class Terminal private (underlying: JTerminal) {

  def width: IO[Int] =
    IO.delay(underlying.getWidth)

  def height: IO[Int] =
    IO.delay(underlying.getHeight)

  def render(string: Str, padding: Str = Str("")): IO[String] = {
    @tailrec
    def inner(builder: StringBuilder, written: Int, remaining: Vector[Str], maxWidth: Int, paddingLength: Int): String =
      if (written == 0 && paddingLength != 0) {
        builder.append(padding.render)
        inner(builder, paddingLength, remaining, maxWidth, paddingLength)
      } else
        remaining match {
          case head +: tail =>
            if (head.length + written >= maxWidth && written != paddingLength) {
              builder.append(System.lineSeparator()).append(padding.render)
              inner(builder, paddingLength, remaining, maxWidth, paddingLength)
            } else {
              builder.append(head.render).append(' ')
              inner(builder, written + head.length + 1, tail, maxWidth, paddingLength)
            }
          case _            => builder.toString()
        }
    width.map { w =>
      val tokens        = tokenize(string)
      val paddingLength = padding.length
      inner(new StringBuilder, 0, tokens, w, paddingLength)
    }
  }

  def renderJson(json: Json, padding: Str = Str("")): IO[String] =
    IO.delay {
      json.spaces2
        .split('\n')
        .foldLeft(new StringBuilder) { case (builder, line) =>
          builder.append(padding.render).append(line).append(System.lineSeparator())
        }
        .toString()
    }

  def writeLn(string: Str, padding: Str = Str("")): IO[Unit] =
    render(string, padding).flatMap { str =>
      writeLn(str)
    }

  def writeLn(string: String): IO[Unit] =
    IO.delay {
      val writer = underlying.writer()
      writer.println(string)
      writer.flush()
    }

  def write(string: String): IO[Unit] =
    IO.delay {
      val writer = underlying.writer()
      writer.print(string)
      writer.flush()
    }

  def readLn(masked: Boolean): IO[String] =
    IO.delay {
      val reader = LineReaderBuilder.builder().terminal(underlying).build()
      if (masked) reader.readLine('*')
      else reader.readLine()
    }

  private def tokenize(string: Str): Vector[Str] = {
    @tailrec
    def inner(acc: Vector[Str], remaining: Str): Vector[Str] = {
      val nextIdx = remaining.plainText.indexWhere(c => c == ' ' || c == '\r' || c == '\n')
      if (nextIdx == -1)
        if (remaining.length == 0) acc
        else acc :+ remaining
      else if (nextIdx == 0) inner(acc, remaining.substring(1))
      else {
        val (left, right) = remaining.splitAt(nextIdx)
        inner(acc :+ left, right.substring(1))
      }
    }
    inner(Vector.empty, string)
  }
}

object Terminal {

  def apply(): Resource[IO, Terminal] =
    Resource.fromAutoCloseable(IO.delay(TerminalBuilder.terminal())).map(t => new Terminal(t))

  val lineSep: String = System.lineSeparator()
}
