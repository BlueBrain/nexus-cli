package ch.epfl.bluebrain.nexus.cli.migrate.ns.impl

import cats.data.NonEmptyList
import cats.effect.{ExitCode, IO}
import cats.implicits._
import ch.epfl.bluebrain.nexus.cli.migrate.ns.MigrateErr.CouldNotParseIdAsUriErr
import ch.epfl.bluebrain.nexus.cli.migrate.ns.{Intent, MigrateErr}
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api
import ch.epfl.bluebrain.nexus.cli.sdk.api.Api.RichIOAPIResponseA
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ApiResponse.Unsuccessful.{Forbidden, Unauthorized, Unknown}
import ch.epfl.bluebrain.nexus.cli.sdk.api.model.{ApiResponse, ProjectRef}
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, Terminal}
import fs2.Stream
import io.circe.Json
import io.circe.generic.auto._
import io.circe.literal._
import org.http4s.implicits._
import org.http4s.{Status, Uri}

import java.time.Instant
import scala.concurrent.duration.DurationInt

object MigrateNs {

  def apply(intent: Intent.MigrateNs, term: Terminal, api: Api): IO[ExitCode] = {
    val stream = for {
      projects <- Stream.eval(projects(api).map{ i => intent.filter(i)})
      project  <- Stream.iterable(projects).evalTap(p => term.writeLn(s"==> $p"))
      elems    <- resources(project, api, intent.lastUpdate, intent.pageSize, term)
                    .parEvalMap(intent.concurrency)(el =>
                      term.writeLn(s"${el.id}") >>
                        update(el, api, term).recoverWith {
                          case v: MigrateErr.CouldNotParseIdAsUriErr => v.println(term)
                          case v: MigrateErr.UpdateErr               => v.println(term)
                        }
                    )
    } yield elems
    stream.compile.drain.as(ExitCode.Success)
  }

  private def projects(api: Api): IO[List[ProjectRef]] =
    for {
      orgList  <- api.orgs.list(Some(0), Some(1000), Some(false)).map(_._results)
      projList <- orgList.traverse { org =>
                    api.projects.list(Some(org._label), Some(0), Some(1000), Some(false)).map(_._results)
                  }
      refs      = projList.flatten.map(_.ref).sortBy(_.toString)
    } yield refs

  private def resources(
      ref: ProjectRef,
      api: Api,
      instant: Instant,
      pageSize: Int,
      term: Terminal
  ): Stream[IO, Elem] = {
    val viewId = uri"https://bluebrain.github.io/nexus/vocabulary/defaultElasticSearchIndex"

    def page(query: Json): IO[Vector[Elem]] = {
      api.elasticSearchViews
        .canBeQueried(ref.org, ref.project, viewId)
        .ifM(
          for {
            json     <- api.elasticSearchViews
                          .query(ref.org, ref.project, viewId, query)
                          .retryfor(_.status.responseClass == Status.ServerError, 1.second, term)
            response <- IO.fromEither(json.as[Response].leftMap(df => MigrateErr.DecodingErr(df.getMessage(), json)))
            elems     = response.toElem(ref)
          } yield elems,
          term.writeLn("Default view is deprecated") >> IO.pure(Vector.empty)
        )
    }

    def stream(query: Json): Stream[IO, Elem] =
      Stream.eval(page(query)).flatMap {
        case elems if elems.isEmpty => Stream.empty
        case elems                  => Stream.iterable(elems) ++ stream(replaceSearchAfter(query, elems.last))
      }
    stream(query(instant, pageSize))
  }

  private def update(elem: Elem, api: Api, term: Terminal): IO[Unit] =
    IO.fromEither(Uri.fromString(elem.id).leftMap(pf => CouldNotParseIdAsUriErr(elem.id, pf))).flatMap { id =>
      api.resources.getSource(elem.ref, id).flatMap {
        case ApiResponse.Successful(source, _, _, _)   =>
          api.resources.update(elem.ref, id, elem.rev, source).flatMap {
            case _: ApiResponse.Successful[_]              => IO.unit
            case v: Unauthorized                           => IO.raiseError(Err.UnauthorizedErr(v.reason))
            case v: Forbidden                              => IO.raiseError(Err.ForbiddenErr(v.reason))
            case v: Unknown if v.status == Status.NotFound => IO.raiseError(MigrateErr.UpdateErr(v))
            case v: Unknown                                =>
              if (v.status.responseClass == Status.ClientError) IO.raiseError(MigrateErr.UpdateErr(v))
              else
                term.writeLn(s"Failed to update resource '${elem.id}', status '${v.status}', retrying...") >> IO
                  .sleep(1.second) >> update(elem, api, term)
          }
        case v: Unauthorized                           => IO.raiseError(Err.UnauthorizedErr(v.reason))
        case v: Forbidden                              => IO.raiseError(Err.ForbiddenErr(v.reason))
        case v: Unknown if v.status == Status.NotFound => IO.raiseError(MigrateErr.UpdateErr(v))
        case v: Unknown                                =>
          term.writeLn(s"Failed to read source for resource '${elem.id}', status '${v.status}', retrying...") >> IO
            .sleep(1.second) >> update(elem, api, term)
      }
    }

  private def query(instant: Instant, pageSize: Int): Json =
    json"""{
            "query": {
              "bool": {
                "must": [
                  { "term": { "_deprecated": false } },
                  { "exists": { "field": "@id" } },
                  { "exists": { "field": "_rev" } },
                  { "exists": { "field": "_original_source" } },
                  { "range": { "_updatedAt": { "lte": $instant } } }
                ],
                "must_not": [
                  { "term" : { "@type" : "https://bluebrain.github.io/nexus/vocabulary/View" } },
                  { "term" : { "@type" : "https://bluebrain.github.io/nexus/vocabulary/Schema" } },
                  { "term" : { "@type" : "https://bluebrain.github.io/nexus/vocabulary/Storage" } },
                  { "term" : { "@type" : "https://bluebrain.github.io/nexus/vocabulary/File" } },
                  { "term" : { "@type" : "https://bluebrain.github.io/nexus/vocabulary/Project" } },
                  { "term" : { "@type" : "https://bluebrain.github.io/nexus/vocabulary/Organization" } },
                  { "term" : { "@type" : "https://bluebrain.github.io/nexus/vocabulary/Resolver" } }
                ]
              }
            },
            "fields": [
              "@id",
              "@type",
              "_rev"
            ],
            "_source": false,
            "sort": [
              { "_updatedAt": { "order": "asc" } }
            ],
            "track_total_hits": true,
            "size": $pageSize
          }"""

  private def replaceSearchAfter(query: Json, elem: Elem): Json =
    query.mapObject(_.filterKeys(_ != "search_after")).deepMerge(Json.obj("search_after" -> elem.sort))

  private case class Fields(
      `@id`: NonEmptyList[String],
      _rev: NonEmptyList[Long]
  )
  private case class Hit(fields: Fields, sort: Json)
  private case class Total(value: Long)
  private case class Hits(hits: Vector[Hit], total: Total)
  private case class Response(hits: Hits) {
    def toElem(ref: ProjectRef): Vector[Elem] =
      hits.hits.map { hit =>
        Elem(ref, hit.fields.`@id`.head, hit.fields._rev.head, hit.sort)
      }
  }

  private case class Elem(ref: ProjectRef, id: String, rev: Long, sort: Json)
}
