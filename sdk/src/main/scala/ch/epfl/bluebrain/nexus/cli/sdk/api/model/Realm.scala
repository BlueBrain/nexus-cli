package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import cats.effect.*
import ch.epfl.bluebrain.nexus.cli.sdk.Label
import io.circe.Codec
import org.http4s.Uri
import org.http4s.circe.*

import java.time.Instant

case class Realm(
    `@id`: Uri,
    `@type`: String,
    name: String,
    openIdConfig: Uri,
    logo: Option[Uri],
    _authorizationEndpoint: Uri,
    _constrainedBy: Uri,
    _createdAt: Instant,
    _createdBy: Uri,
    _deprecated: Boolean,
    _endSessionEndpoint: Uri,
    _grantTypes: Option[List[String]],
    _issuer: Uri,
    _label: Label,
    _rev: Int,
    _self: Uri,
    _tokenEndpoint: Uri,
    _updatedAt: Instant,
    _updatedBy: Uri,
    _userInfoEndpoint: Uri
) derives Codec.AsObject
