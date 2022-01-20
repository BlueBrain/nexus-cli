package ch.epfl.bluebrain.nexus.cli.sdk

import cats.implicits.*
import io.circe.*

import scala.util.matching.Regex

/**
  * A safe representation of a name or label that can be positioned as a segment in an Uri without the need to escape
  * it.
  */
opaque type Label = String

object Label:
  extension (label: Label) def value: String = label

  private val allowedChars: String = "a-zA-Z0-9_-"
  private[sdk] val regex: Regex    = s"[$allowedChars]{1,64}".r

  /**
    * Attempts to construct a label from its string representation.
    *
    * @param value
    *   the string representation of the Label
    */
  def apply(value: String): Either[Err.IllegalLabelErr, Label] =
    value match {
      case regex() => Right(value)
      case _       => Left(Err.IllegalLabelErr(value))
    }

  /**
    * Constructs a Label from its string representation without validation in terms of allowed characters or size.
    *
    * @param value
    *   the string representation of the label
    */
  def unsafe(value: String): Label = value

  /**
    * Attempts to construct a label from its string representation. It will remove all invalid characters and truncate
    * to max length of 64 characters. It will return [[Err.IllegalLabelErr]] when `value` contains only invalid
    * characters.
    *
    * @param value
    *   the string representation of the Label
    */
  def sanitized(value: String): Either[Err.IllegalLabelErr, Label] =
    apply(value.replaceAll(s"[^$allowedChars]", "").take(64))

  given Encoder[Label] = Encoder.encodeString.contramap(_.value)
  given Decoder[Label] = Decoder.decodeString.emap(str => apply(str).leftMap(_.message))
