import sbtbuildinfo.BuildInfoPlugin.autoImport.buildInfoKeys

/*
scalafmt: {
  maxColumn = 150
  align.tokens.add = [
    { code = ":=", owner = "Term.ApplyInfix" }
    { code = "+=", owner = "Term.ApplyInfix" }
    { code = "++=", owner = "Term.ApplyInfix" }
    { code = "~=", owner = "Term.ApplyInfix" }
    { code = "cross", owner = "Term.ApplyInfix" }
  ]
}
 */

val catsEffectVersion = "3.3.12"
val circeVersion      = "0.15.0-M1"
val declineVersion    = "2.2.0"
val fansiVersion      = "0.3.1"
val fs2Version        = "3.2.8"
val http4sVersion     = "1.0.0-M33"
val jlineVersion      = "3.21.0"
val logbackVersion    = "1.2.11"
val munitVersion      = "0.7.29"

lazy val catsEffect    = "org.typelevel" %% "cats-effect"         % catsEffectVersion
lazy val circeCore     = "io.circe"      %% "circe-core"          % circeVersion
lazy val circeLiteral  = "io.circe"      %% "circe-literal"       % circeVersion
lazy val circeParser   = "io.circe"      %% "circe-parser"        % circeVersion
lazy val circeGeneric  = "io.circe"      %% "circe-generic"       % circeVersion
lazy val decline       = "com.monovore"  %% "decline"             % declineVersion
lazy val fansi         = "com.lihaoyi"   %% "fansi"               % fansiVersion
lazy val fs2Core       = "co.fs2"        %% "fs2-core"            % fs2Version
lazy val fs2IO         = "co.fs2"        %% "fs2-io"              % fs2Version
lazy val http4sClient  = "org.http4s"    %% "http4s-blaze-client" % http4sVersion
lazy val http4sCirce   = "org.http4s"    %% "http4s-circe"        % http4sVersion
lazy val jlineTerminal = "org.jline"      % "jline-terminal"      % jlineVersion
lazy val jlineReader   = "org.jline"      % "jline-reader"        % jlineVersion
lazy val logback       = "ch.qos.logback" % "logback-classic"     % logbackVersion
lazy val munit         = "org.scalameta" %% "munit"               % munitVersion

lazy val sdk = project
  .in(file("sdk"))
  .enablePlugins(BuildInfoPlugin)
  .settings(compilationSettings)
  .settings(
    name                 := "cli-sdk",
    moduleName           := "cli-sdk",
    libraryDependencies ++= Seq(
      catsEffect,
      circeCore,
      circeLiteral,
      circeGeneric,
      circeParser,
      decline,
      fansi,
      fs2Core,
      fs2IO,
      http4sClient,
      http4sCirce,
      jlineReader,
      jlineTerminal,
      logback,
      munit % Test
    ),
    buildInfoKeys        := Seq[BuildInfoKey](version, cliName),
    buildInfoPackage     := "ch.epfl.bluebrain.nexus.cli.sdk"
  )

lazy val cli = project
  .in(file("cli"))
  .dependsOn(sdk)
  .enablePlugins(NativeImagePlugin)
  .settings(compilationSettings, nativeImageSettings)
  .settings(
    name                 := cliName.value,
    moduleName           := cliName.value,
    libraryDependencies ++= Seq(
      munit % Test
    ),
    Compile / mainClass  := Some("ch.epfl.bluebrain.nexus.cli.Main")
  )

lazy val cliSearch = project
  .in(file("plugins/cli-search"))
  .enablePlugins(NativeImagePlugin)
  .dependsOn(sdk)
  .settings(compilationSettings, nativeImageSettings)
  .settings(
    name                 := cliName.value + "-search",
    moduleName           := cliName.value + "-search",
    libraryDependencies ++= Seq(
      munit % Test
    ),
    Compile / mainClass  := Some("ch.epfl.bluebrain.nexus.cli.search.Main")
  )

lazy val cliCopy = project
  .in(file("plugins/cli-copy"))
  .enablePlugins(NativeImagePlugin)
  .dependsOn(sdk)
  .settings(compilationSettings, nativeImageSettings)
  .settings(
    name                 := cliName.value + "-copy",
    moduleName           := cliName.value + "-copy",
    libraryDependencies ++= Seq(
      munit % Test
    ),
    Compile / mainClass  := Some("ch.epfl.bluebrain.nexus.cli.copy.Main")
  )

lazy val cliMigrateNs = project
  .in(file("plugins/cli-migrate-ns"))
  .enablePlugins(NativeImagePlugin)
  .dependsOn(sdk)
  .settings(compilationSettings, nativeImageSettings)
  .settings(
    name                 := cliName.value + "-migrate-ns",
    moduleName           := cliName.value + "-migrate-ns",
    libraryDependencies ++= Seq(
      munit % Test
    ),
    Compile / mainClass  := Some("ch.epfl.bluebrain.nexus.cli.migrate.ns.Main")
  )

lazy val plugins = project
  .in(file("plugins"))
  .aggregate(cliSearch, cliCopy, cliMigrateNs)
  .settings(compilationSettings, noPublish)

lazy val root = project
  .in(file("."))
  .aggregate(sdk, cli, plugins)
  .settings(compilationSettings, noPublish)

lazy val compilationSettings = Seq(
  scalaVersion := "2.13.8", // scala 3 native image compilation requires manual config, see https://github.com/lampepfl/dotty/issues/13985
  cliName      := {
    sys.env.get("CLI_NAME") match {
      case Some(value) => value
      case None        => "nexusctl"
    }
  }
)

lazy val noPublish = Seq(
  publish / skip := true
)

val nativeImageSettings = Seq(
  nativeImageVersion  := "22.1.0",
  nativeImageJvm      := "graalvm-java17",
  nativeImageJvmIndex := "https://raw.githubusercontent.com/coursier/jvm-index/master/index.json",
  nativeImageOptions ++= {
    val configDir = (Compile / sourceDirectory).value / "native-image"
    List(
      "--verbose",
      "--no-server",
      "--no-fallback",
      "--install-exit-handlers",
      "--allow-incomplete-classpath",
      "--enable-http",
      "--enable-https",
      "--enable-all-security-services",
      // "--trace-class-initialization=scala.package$",
      // due to org.http4s.client.package$defaults$
      // "--initialize-at-build-time=scala.math,scala.collection,scala.collection.immutable,scala.reflect,scala.concurrent.duration,scala.package$,scala.Predef$",
      "-H:+ReportExceptionStackTraces",
      s"-H:ResourceConfigurationFiles=${configDir / "resource-config.json"}",
      s"-H:ReflectionConfigurationFiles=${configDir / "reflect-config.json"}",
      s"-H:JNIConfigurationFiles=${configDir / "jni-config.json"}",
      s"-H:DynamicProxyConfigurationFiles=${configDir / "proxy-config.json"}"
    )
  },
  nativeImageReady    := { () => () }
)

val cliName = SettingKey[String]("cliName", "The name of the command line utility to be used in help.")

ThisBuild / evictionErrorLevel := Level.Info

Global / excludeLintKeys ++= Set(
  cliName,
  nativeImageVersion,
  nativeImageJvm,
  nativeImageJvmIndex
)
