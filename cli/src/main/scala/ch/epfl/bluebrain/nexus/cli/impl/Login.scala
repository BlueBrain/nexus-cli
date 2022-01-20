package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.*
import ch.epfl.bluebrain.nexus.cli.CliErr
import ch.epfl.bluebrain.nexus.cli.impl.Config.LoginConfig
import ch.epfl.bluebrain.nexus.cli.impl.Login.getAndValidateRealm
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api.*
import ch.epfl.bluebrain.nexus.cli.sdk.api.{Identities, Realms}
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, Realm}
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, Label, Terminal}
import io.circe.*
import org.http4s.Method.*
import org.http4s.blaze.client.BlazeClientBuilder
import org.http4s.circe.*
import org.http4s.client.Client
import org.http4s.client.dsl.io.*
import org.http4s.{Status, Uri, UrlForm}

object Login:
  def apply(
      endpoint: Option[Uri],
      realm: Option[Label],
      token: Option[BearerToken],
      clientId: String,
      term: Terminal
  ): IO[ExitCode] =
    (endpoint, realm, token) match
      // no args, show login information
      case (None, None, None)          =>
        Config.load.flatMap {
          case Some(cfg) =>
            term.writeLn(s"Logged in to '${cfg.endpoint}' on realm '${cfg.realm}'.").as(ExitCode.Success)
          case None      =>
            term
              .writeLn("Currently not logged in, use the 'login' command options to specify target.")
              .as(ExitCode.Success)
        }
      // provided token login, check realm and identities
      case (Some(e), Some(r), Some(t)) =>
        BlazeClientBuilder[IO].resource.use { client =>
          getAndValidateRealm(e, r, client).flatMap { realm =>
            val identities = new Identities(e, client, Some(t.toAuthorization))
            identities.list.flatMap {
              case ApiResponse.Successful(_, _, _, _)             =>
                Config.save(LoginConfig(e, r, t, clientId)).as(ExitCode.Success)
              case ApiResponse.Unauthorized(tpe, reason, _, _, _) =>
                IO.raiseError(CliErr.InvalidTokenErr(tpe, reason))
              case ApiResponse.Forbidden(tpe, reason, _, _, _)    =>
                IO.raiseError(CliErr.InvalidTokenErr(tpe, reason))
              case ApiResponse.Unsuccessful(status, raw, _)       =>
                IO.raiseError(CliErr.UnableToDecodeIdentitiesErr(status, raw))
            }
          }
        }
      // initiate login
      case (Some(e), Some(r), None)    =>
        BlazeClientBuilder[IO].resource.use { client =>
          getAndValidateRealm(e, r, client).flatMap { realm =>
            readUsernameAndPassword(term).flatMap { case (username, password) =>
              val req = POST(
                UrlForm(
                  "grant_type" -> "password",
                  "username"   -> username,
                  "password"   -> password,
                  "client_id"  -> clientId,
                  "scope"      -> "openid"
                ),
                realm._tokenEndpoint
              )
              client.run(req).use { resp =>
                resp.decode[AuthResponse].flatMap {
                  case ApiResponse.Successful(value, _, _, _) =>
                    Config.save(LoginConfig(e, r, value.access_token, clientId)).as(ExitCode.Success)
                  case ar: ApiResponse[_]                     =>
                    ar.raw.as[ErrorAuthResponse] match
                      case Right(value) => IO.raiseError(CliErr.UnableToLoginErr(value.error)).as(ExitCode.Error)
                      case Left(_)      => IO.raiseError(CliErr.UnableToDecodeLoginErr(ar.status, ar.raw)).as(ExitCode.Error)
                }
              }
            }
          }
        }
      case (_, _, _)                   =>
        IO.raiseError(CliErr.IncorrectLoginFlagsErr)

  private def getAndValidateRealm(endpoint: Uri, realm: Label, client: Client[IO]): IO[Realm] =
    val realms = new Realms(endpoint, client, None)
    realms.get(realm).flatMap {
      case ApiResponse.Successful(Some(r), _, _, _) if r._deprecated => IO.raiseError(CliErr.RealmIsDeprecatedErr)
      case ApiResponse.Successful(Some(r), _, _, _)                  => IO.pure(r)
      case ApiResponse.Successful(None, _, _, _)                     => IO.raiseError(CliErr.RealmNotFoundErr)
      case r: ApiResponse[_]                                         => IO.raiseError(CliErr.UnableToRetrieveRealmErr(r.status, r.raw))
    }

  private def readUsernameAndPassword(term: Terminal): IO[(String, String)] =
    for
      _        <- term.write("Username: ")
      username <- term.readLn(masked = false)
      _        <- term.write("Password: ")
      password <- term.readLn(masked = true)
    yield (username, password)

  private case class AuthResponse(
      access_token: BearerToken,
      expires_in: Int,
      refresh_expires_in: Int,
      refresh_token: String,
      token_type: String,
      scope: String
  ) derives Codec.AsObject

  private case class ErrorAuthResponse(
      error: String,
      error_description: String
  ) derives Codec.AsObject
