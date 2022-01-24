package ch.epfl.bluebrain.nexus.cli.search

import cats.effect.*
import cats.implicits.*
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, Err, Terminal}
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api
import com.monovore.decline.Help
import fs2.*
import fs2.io.file.{Files, Path}
import org.http4s.Uri
import org.http4s.blaze.client.BlazeClientBuilder

import java.io.File

object Main extends IOApp:

  override def run(args: List[String]): IO[ExitCode] =
    Terminal()
      .use { terminal =>
        val io: IO[ExitCode] = Cli.command.parse(args) match
          case Left(help)    => Cli.printHelp(terminal, help).as(ExitCode.Success)
          case Right(intent) =>
            val endpoint = sys.env.get("NEXUS_ENDPOINT").map(str => Uri.unsafeFromString(str))
            val token    = sys.env.get("NEXUS_TOKEN").map(str => BearerToken.unsafe(str))
            for
              e    <- IO.fromOption(endpoint)(Err.UnconfiguredErr)
              t    <- IO.fromOption(token)(Err.UnconfiguredErr)
              code <- evaluate(intent, terminal, e, t)
            yield code

        io.handleErrorWith {
          case e: Err => e.println(terminal).as(ExitCode.Error)
          case th     => Err.UnknownErr(th).println(terminal).as(ExitCode.Error)
        }
      }

  private def evaluate(intent: Intent, term: Terminal, endpoint: Uri, token: BearerToken): IO[ExitCode] =
    BlazeClientBuilder[IO].resource.use { client =>
      val api = Api(client, endpoint, token)
      intent match
        case Intent.UpdateConfig(compositeViewPath) => impl.UpdateConfig(compositeViewPath, term, api)
    }
