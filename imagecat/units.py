"""Functionality for performing unit conversions.
"""

import numbers
import re


def length(value, width, height, default="px"):
    """Convert a length value to pixels.

    Supported unit abbreviations include: px, pixel, pixels, vw, vh, vmin,
    and vmax.

    Parameters
    ----------
    value: number, :any:`str` or (number, :any:`str`) tuple, required
        Value to be converted.  The value may be a number (in which case the
        `default` parameter will specify the unit of measure), a :any:`str`
        containing a number and unit abbreviation, or a (value, units) tuple.
    width: number, required
        Reference width for use when the caller specifies a relative unit of measure.
        Note that the width *must* be specified in pixels.
    height: number, required
        Reference height for use when the caller specifies a relative unit of measure.
        Note that the height *must* be specified in pixels.
    default: :any:`str`, optional
        Default unit of measure to use when `value` is a plain number.

    Returns
    -------
    value: number
        `value` converted to pixel units.  Note that the result is a
        floating-point number, so callers may need to convert to an int if they
        are e.g. specifying the size of an image.
    """
    if isinstance(value, numbers.Number):
        value = (value, default)
    elif isinstance(value, str):
        value, units = re.match(r"([^a-zA-Z%]+)([a-zA-Z%]+)\Z", value).groups()
        value = (float(value), units)

    if not isinstance(value, tuple):
        raise ValueError("Value must be a number, string or (number, string) tuple.")
    if not len(value) == 2:
        raise ValueError("Value must be a number, string or (number, string) tuple.")
    if not isinstance(value[0], numbers.Number):
        raise ValueError("Value must be a number, string or (number, string) tuple.")
    if not isinstance(value[1], str):
        raise ValueError("Value must be a number, string or (number, string) tuple.")

    value, units = value
    units = units.lower()
    if units in ["px", "pixel", "pixels"]:
        return value
    if units == "vw":
        return value * width
    if units == "vh":
        return value * height
    if units == "vmin":
        return value * min(width, height)
    if units == "vmax":
        return value * max(width, height)
    raise ValueError("Unknown unit of measure: %s" % units)

