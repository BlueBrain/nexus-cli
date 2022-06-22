package ch.epfl.bluebrain.nexus.cli.migrate.ns

import java.time.Instant

sealed trait Intent extends Product with Serializable

object Intent {

  case class MigrateNs(lastUpdate: Instant, pageSize: Int, concurrency: Int) extends Intent

}
