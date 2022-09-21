package ch.epfl.bluebrain.nexus.cli.migrate.ns

import ch.epfl.bluebrain.nexus.cli.sdk.api.model.ProjectRef

import java.time.Instant

sealed trait Intent extends Product with Serializable

object Intent {

  final case class MigrateNs(lastUpdate: Instant, pageSize: Int, concurrency: Int, projects: List[ProjectRef])
      extends Intent {
    def filter(input: List[ProjectRef]): List[ProjectRef] =
      if (projects.isEmpty)
        input
      else
        input.intersect(projects)
  }

}
