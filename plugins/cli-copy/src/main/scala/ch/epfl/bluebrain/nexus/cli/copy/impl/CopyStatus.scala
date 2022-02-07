package ch.epfl.bluebrain.nexus.cli.copy.impl

case class CopyStatus(
    successes: Long,
    conflicts: Long,
    discarded: Long,
    errors: Long
) {
  def incrementSuccesses: CopyStatus = copy(successes = successes + 1L)
  def incrementConflicts: CopyStatus = copy(conflicts = conflicts + 1L)
  def incrementDiscarded: CopyStatus = copy(discarded = discarded + 1L)
  def incrementErrors: CopyStatus    = copy(errors = errors + 1L)
}
