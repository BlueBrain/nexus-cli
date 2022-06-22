package ch.epfl.bluebrain.nexus.cli.migrate.ns

import cats.effect.{ExitCode, IO, IOApp}
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, Err, Terminal}
import org.http4s.Uri
import org.http4s.blaze.client.BlazeClientBuilder

object Main extends IOApp {

  override def run(args: List[String]): IO[ExitCode] =
    Terminal()
      .use { terminal =>
        val io: IO[ExitCode] = CliOpts.command.parse(args) match {
          case Left(help)    => CliOpts.printHelp(terminal, help).as(ExitCode.Success)
          case Right(intent) =>
            val endpoint = sys.env.get("NEXUS_ENDPOINT").map(str => Uri.unsafeFromString(str))
            val token    = sys.env.get("NEXUS_TOKEN").map(str => BearerToken.unsafe(str))
            for {
              e    <- IO.fromOption(endpoint)(Err.UnconfiguredErr)
              code <- evaluate(intent, terminal, e, token)
            } yield code
        }
        io.handleErrorWith {
          case e: Err => e.println(terminal).as(ExitCode.Error)
          case th     => Err.UnknownErr(th).println(terminal).as(ExitCode.Error)
        }
      }

  private def evaluate(intent: Intent, term: Terminal, endpoint: Uri, token: Option[BearerToken]): IO[ExitCode] =
    BlazeClientBuilder[IO].resource.use { client =>
      val api = Api(client, endpoint, token)
      intent match {
        case v: Intent.MigrateNs => impl.MigrateNs(v, term, api)
      }
    }
}
