# Copyright 2020 Timothy M. Shead
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Functionality for performing unit conversions.
"""

import numbers
import re


def length(value, size, default="px"):
    """Convert a length value to pixels.

    Supported unit abbreviations include:

    :"px", "pixel", "pixels": absolute length in pixels
    :"w", "width": relative length, as a fraction of the width of an image
    :"h", "height": relative length, as a fraction of the height of an image
    :"min": relative length, as a fraction of the smaller of width and height
    :"max": relative length, as a fraction of the larger of width and height

    Relative lengths will be relative to some reference that is
    context-specific and documented.  For example: the text operator fontsize
    is relative to the size of the output image.

    Parameters
    ----------
    value: number, :any:`str` or (number, :any:`str`) tuple, required
        Value to be converted.  The value may be a number (in which case the
        `default` parameter will specify the unit of measure), a :any:`str`
        containing a number and unit abbreviation, or a (value, units) tuple.
    size: (width, height) tuple, required
        Reference width and height for use when the caller specifies a relative unit of measure.
        Note that width and height *must* be specified in pixels.
    default: :any:`str`, optional
        Default unit of measure to use when `value` is a plain number.

    Returns
    -------
    value: number
        `value` converted to pixel units.  Note that the result is a
        floating-point number, so callers may need to convert to an int if they
        are intend to e.g. specifying the resolution of an image.
    """
    if isinstance(value, numbers.Number):
        value = (value, default)
    elif isinstance(value, str):
        value, units = re.match(r"([^a-zA-Z%]+)([a-zA-Z%]+)\Z", value).groups()
        value = (float(value), units)

    if not isinstance(value, tuple):
        raise ValueError("Value must be a number, string or (number, string) tuple.") # pragma: no cover
    if not len(value) == 2:
        raise ValueError("Value must be a number, string or (number, string) tuple.") # pragma: no cover
    if not isinstance(value[0], numbers.Number):
        raise ValueError("Value must be a number, string or (number, string) tuple.") # pragma: no cover
    if not isinstance(value[1], str):
        raise ValueError("Value must be a number, string or (number, string) tuple.") # pragma: no cover

    value, units = value
    units = units.lower()
    if units in {"px", "pixel", "pixels"}:
        return value
    if units in {"w", "width"}:
        return value * size[0]
    if units in {"h", "height"}:
        return value * size[1]
    if units in {"min"}:
        return value * min(size[0], size[1])
    if units in {"max"}:
        return value * max(size[0], size[1])
    raise ValueError("Unknown unit of measure: %s" % units) # pragma: no cover

