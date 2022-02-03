package ch.epfl.bluebrain.nexus.cli.impl

import cats.effect.{ExitCode, IO}
import ch.epfl.bluebrain.nexus.cli.CliErr
import ch.epfl.bluebrain.nexus.cli.impl.LoginConfig.{AnonymousLoginConfig, UserLoginConfig}
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api.RichResponseIO
import ch.epfl.bluebrain.nexus.cli.sdk.api.{Identities, Realms}
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, Realm}
import ch.epfl.bluebrain.nexus.cli.sdk.{BearerToken, Err, Label, Terminal}
import io.circe.Decoder
import io.circe.generic.semiauto._
import org.http4s.client.dsl.io._
import org.http4s.Method.POST
import org.http4s.{Uri, UrlForm}
import org.http4s.blaze.client.BlazeClientBuilder
import org.http4s.client.Client

object Login {

  def apply(
      term: Terminal,
      endpoint: Option[Uri],
      realm: Option[Label],
      token: Option[BearerToken],
      clientId: String
  ): IO[ExitCode] =
    (endpoint, realm, token) match {
      // no info provided, attempt to login with previous config
      case (None, None, None)          =>
        Config.load.flatMap {
          case Some(AnonymousLoginConfig(endpoint))             =>
            term
              .writeLn(
                s"""Currently logged in as Anonymous to '${endpoint.renderString}'.
                   |Specify at least a realm to start the authentication flow.""".stripMargin,
                Err.padding
              )
              .as(ExitCode.Error)
          case Some(UserLoginConfig(e, r, _, existingClientId)) => initiateLogin(term, e, r, existingClientId)
          case None                                             =>
            term
              .writeLn("Currently not logged in, use the 'login' command options to specify target.", Err.padding)
              .as(ExitCode.Error)
        }
      case (Some(e), Some(r), None)    => initiateLogin(term, e, r, clientId)
      case (Some(e), Some(r), Some(t)) => initiateLoginWithToken(e, r, t, clientId)
      case (Some(e), None, None)       => Config.save(AnonymousLoginConfig(e)).as(ExitCode.Success)
      case _                           => IO.raiseError(CliErr.IncorrectLoginFlagsErr)
    }

  private def initiateLogin(term: Terminal, e: Uri, r: Label, clientId: String): IO[ExitCode] =
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
                Config.save(UserLoginConfig(e, r, value.access_token, clientId)).as(ExitCode.Success)
              case ar: ApiResponse[_]                     =>
                ar.raw.as[ErrorAuthResponse] match {
                  case Right(value) => IO.raiseError(CliErr.UnableToLoginErr(value.error)).as(ExitCode.Error)
                  case Left(_)      => IO.raiseError(CliErr.UnableToDecodeLoginErr(ar.status, ar.raw)).as(ExitCode.Error)
                }
            }
          }
        }
      }
    }

  private def initiateLoginWithToken(e: Uri, r: Label, t: BearerToken, clientId: String): IO[ExitCode] =
    BlazeClientBuilder[IO].resource.use { client =>
      getAndValidateRealm(e, r, client).flatMap { _ =>
        val identities = new Identities(client, e, Some(t.toAuthorization))
        identities.list.flatMap {
          case ApiResponse.Successful(_, _, _, _)                          =>
            Config.save(UserLoginConfig(e, r, t, clientId)).as(ExitCode.Success)
          case ApiResponse.Unsuccessful.Unauthorized(tpe, reason, _, _, _) =>
            IO.raiseError(CliErr.InvalidTokenErr(tpe, reason))
          case ApiResponse.Unsuccessful.Forbidden(tpe, reason, _, _, _)    =>
            IO.raiseError(CliErr.InvalidTokenErr(tpe, reason))
          case ApiResponse.Unsuccessful.Unknown(status, raw, _)            =>
            IO.raiseError(CliErr.UnableToDecodeIdentitiesErr(status, raw))
        }
      }
    }

  private def getAndValidateRealm(endpoint: Uri, realm: Label, client: Client[IO]): IO[Realm] = {
    val realms = new Realms(client, endpoint, None)
    realms.get(realm).flatMap {
      case ApiResponse.Successful(Some(r), _, _, _) if r._deprecated => IO.raiseError(CliErr.RealmIsDeprecatedErr)
      case ApiResponse.Successful(Some(r), _, _, _)                  => IO.pure(r)
      case ApiResponse.Successful(None, _, _, _)                     => IO.raiseError(CliErr.RealmNotFoundErr)
      case r: ApiResponse[_]                                         => IO.raiseError(CliErr.UnableToRetrieveRealmErr(r.status, r.raw))
    }
  }

  private def readUsernameAndPassword(term: Terminal): IO[(String, String)] =
    for {
      _        <- term.write("Username: ")
      username <- term.readLn(masked = false)
      _        <- term.write("Password: ")
      password <- term.readLn(masked = true)
    } yield (username, password)

  private[Login] case class AuthResponse(
      access_token: BearerToken,
      expires_in: Int,
      refresh_expires_in: Int,
      refresh_token: String,
      token_type: String,
      scope: String
  )
  object AuthResponse {
    implicit val authResponseDecoder: Decoder[AuthResponse] = deriveDecoder[AuthResponse]
  }

  private[Login] case class ErrorAuthResponse(
      error: String,
      error_description: String
  )
  object ErrorAuthResponse {
    implicit val errorAuthResponseDecoder: Decoder[ErrorAuthResponse] = deriveDecoder[ErrorAuthResponse]
  }

}
