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

val catsEffectVersion = "3.3.1"
val circeVersion      = "0.15.0-M1"
val declineVersion    = "2.2.0"
val fansiVersion      = "0.3.0"
val fs2Version        = "3.2.4"
val http4sVersion     = "1.0.0-M30"
val jlineVersion      = "3.21.0"
val logbackVersion    = "1.2.10"
val munitVersion      = "0.7.29"

lazy val catsEffect    = "org.typelevel" %% "cats-effect"         % catsEffectVersion
lazy val circeCore     = "io.circe"      %% "circe-core"          % circeVersion
lazy val circeParser   = "io.circe"      %% "circe-parser"        % circeVersion
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
  .settings(compilationSettings)
  .settings(
    name                 := "cli-sdk",
    moduleName           := "cli-sdk",
    libraryDependencies ++= Seq(
      catsEffect,
      circeCore,
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
    )
  )

lazy val cli = project
  .in(file("cli"))
  .dependsOn(sdk)
  .enablePlugins(NativeImagePlugin, BuildInfoPlugin)
  .settings(compilationSettings, nativeImageSettings)
  .settings(
    name                 := "cli",
    moduleName           := "cli",
    libraryDependencies ++= Seq(
      munit % Test
    ),
    Compile / mainClass  := Some("ch.epfl.bluebrain.nexus.cli.Main"),
    cliName              := {
      sys.env.get("CLI_NAME") match {
        case Some(value) => value
        case None        => "nexusctl"
      }
    },
    buildInfoKeys        := Seq[BuildInfoKey](version, cliName),
    buildInfoPackage     := "ch.epfl.bluebrain.nexus.cli"
  )

lazy val cliSearch = project
  .in(file("cli-search"))
  .enablePlugins(NativeImagePlugin)
  .dependsOn(cli)
  .settings(compilationSettings, nativeImageSettings)
  .settings(
    name                 := "cli-search",
    moduleName           := "cli-search",
    libraryDependencies ++= Seq(
      munit % Test
    ),
    Compile / mainClass  := Some("ch.epfl.bluebrain.nexus.cli.search.Main")
  )

lazy val root = project
  .in(file("."))
  .aggregate(sdk, cli, cliSearch)
  .settings(compilationSettings)
  .settings(
    publish / skip := true
  )

val compilationSettings = Seq(
  scalaVersion := "3.1.0"
)

val nativeImageSettings = Seq(
  nativeImageVersion  := "21.1.0",
  nativeImageJvm      := "graalvm-ce-java16",
  nativeImageJvmIndex := "jabba",
  nativeImageOptions ++= {
    val configDir = (Compile / resourceDirectory).value / "native-image"
    List(
      "--verbose",
      "--no-server",
      "--no-fallback",
      "--install-exit-handlers",
      "--allow-incomplete-classpath",
      // "--trace-class-initialization=scala.package$",
      // due to org.http4s.client.package$defaults$
      "--initialize-at-build-time=scala.math,scala.collection,scala.collection.immutable,scala.reflect,scala.concurrent.duration,scala.package$,scala.Predef$",
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
