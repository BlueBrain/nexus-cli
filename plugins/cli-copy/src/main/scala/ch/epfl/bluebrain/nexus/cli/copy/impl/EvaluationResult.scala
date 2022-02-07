package ch.epfl.bluebrain.nexus.cli.copy.impl

import org.http4s.Status

sealed trait EvaluationResult extends Product with Serializable {
  def offset: String
}

object EvaluationResult {

  case class Ok(offset: String)                                   extends EvaluationResult
  case class Conflict(offset: String)                             extends EvaluationResult
  case class Discarded(offset: String)                            extends EvaluationResult
  case class Error(offset: String, status: Status, error: String) extends EvaluationResult
}
