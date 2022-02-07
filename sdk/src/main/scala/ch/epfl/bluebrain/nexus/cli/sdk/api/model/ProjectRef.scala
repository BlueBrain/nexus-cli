package ch.epfl.bluebrain.nexus.cli.sdk.api.model

import cats.data.Validated
import ch.epfl.bluebrain.nexus.cli.sdk.{Err, Label}
import com.monovore.decline.Argument

case class ProjectRef(org: Label, project: Label) {
  override def toString: String = s"${org.value}/${project.value}"
}

object ProjectRef {

  def fromString(str: String): Either[Err.IllegalLabelErr, ProjectRef] =
    str.trim.split('/') match {
      case Array(org, proj) =>
        for {
          o <- Label(org)
          p <- Label(proj)
        } yield ProjectRef(o, p)
      case _                => Left(Err.IllegalLabelErr(str))
    }

  implicit val projectRefArgument: Argument[ProjectRef] =
    Argument.from("org/proj") { str =>
      ProjectRef.fromString(str) match {
        case Right(value) => Validated.validNel(value)
        case Left(err)    => Validated.invalidNel(err.description)
      }
    }
}
