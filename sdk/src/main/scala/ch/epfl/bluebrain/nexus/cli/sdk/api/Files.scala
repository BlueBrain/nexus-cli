package ch.epfl.bluebrain.nexus.cli.sdk.api

import cats.effect.IO
import org.http4s.Uri
import org.http4s.client.Client
import org.http4s.headers.Authorization

import scala.annotation.unused

class Files(@unused client: Client[IO], @unused endpoint: Uri, @unused auth: Option[Authorization]) {}
