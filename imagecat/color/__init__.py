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


"""Functionality for color mapping and colorspace conversion.
"""

import numpy

class Palette(object):
    """Storage for an ordered collection of colors.

    A palette is an ordered collection of colors.  Typically, palettes are
    used to define color mappings.

    See Also
    --------
    :func:`srgb_to_linear`
        Useful for converting colors from other sources into linear space.

    Parameters
    ----------
    colors: :class:`numpy.ndarray`, required
        :math:`M \\times N` matrix containing :math:`M` colors with :math:`N`
        channels each.  Note that while three channels for colors is
        typical, any number of channels is allowed.  The color channels
        *must* be in linear space, not sRGB.
    reverse: boolean, optional
        If `True`, reverse the order of `colors`.
    """
    def __init__(self, colors, reverse=False):
        colors = numpy.array(colors)
        if reverse:
            colors = colors[::-1]
        self._colors = colors

    @property
    def colors(self):
        """Color data stored by this palette.

        Returns
        -------
        :class:`numpy.ndarray`
            :math:`M \\times N` matrix containing :math:`M` colors with :math:`N`
            channels each.
        """
        return self._colors


def categorical_map(data, palette):
    """Convert scalar data to color data using a categorical map.

    Integer input values will be used to lookup colors in `palette`.  Modulo
    arithmetic ensures that colors are repeated for negative or out-of-bound
    colors.  Floating point values are truncated using "floor" prior to lookup.

    Parameters
    ----------
    data: :class:`numpy.ndarray`, required
        The data to be mapped.
    palette: :class:`Palette`, required
        The palette of colors to use for the categorical mapping.

    Returns
    -------
    mapped: :class:`numpy.ndarray`
        Mapped data with the same shape as `data`, but an extra dimension
        added.
    """
    data = numpy.array(data)
    if not numpy.issubdtype(data.dtype, numpy.integer):
        data = numpy.floor(data).astype(numpy.int64)

    colors = palette.colors
    flat = numpy.reshape(data, -1) % len(colors)
    mapped = numpy.empty((len(flat), colors.shape[1]), dtype=numpy.float)
    for index, channel in enumerate(colors.T):
        mapped[:,index] = colors[flat][:,index]
    return mapped.reshape((*data.shape, colors.shape[1]))


def linear_map(data, palette, min=None, max=None):
    """Convert scalar data to color data using a linear map.

    Input values from `min` and `max` will be linearly mapped
    to the colors in `palette`.  If `min` or `max` are :any:`None`,
    the corresponding value will be computed from the data.

    Parameters
    ----------
    data: :class:`numpy.ndarray`, required
        The data to be mapped.
    palette: :class:`Palette`, required
        The palette of colors to use for the linear mapping.
    min: number, optional
        If :any:`None` (the default) uses the minimum value in `data`.
    max: number, optional
        If :any:`None` (the default) uses the maximum value in `data`.

    Returns
    -------
    mapped: :class:`numpy.ndarray`
        Mapped data with the same shape as `data`, but an extra dimension
        added.
    """
    data = numpy.array(data)
    if min is None:
        min = data.min()
    if max is None:
        max = data.max()

    colors = palette.colors
    stops = numpy.linspace(min, max, len(colors))

    flat = numpy.reshape(data, -1)
    mapped = numpy.empty((len(flat), colors.shape[1]), dtype=numpy.float)
    for index, channel in enumerate(colors.T):
        mapped[:,index] = numpy.interp(flat, stops, channel)
    return mapped.reshape((*data.shape, colors.shape[1]))


def linear_to_srgb(data):
    """Convert linear color data to sRGB.

    Acessed from https://entropymine.com/imageworsener/srgbformula

    Parameters
    ----------
    data: :class:`numpy.ndarray`, required
        Array of any shape containing linear data to be converted to sRGB.

    Returns
    -------
    converted: :class:`numpy.ndarray`
        Array with the same shape as `data` containing values in sRGB space.
    """
    return numpy.where(data <= 0.0031308, data * 12.92, 1.055 * numpy.power(data, 1 / 2.4) - 0.055)


def srgb_to_linear(data):
    """Convert sRGB data to linear color.

    Acessed from https://entropymine.com/imageworsener/srgbformula

    Parameters
    ----------
    data: :class:`numpy.ndarray`, required
        Array of any shape containing sRGB data to be converted to linear.

    Returns
    -------
    converted: :class:`numpy.ndarray`
        Array with the same shape as `data` containing values in linear space.
    """
    return numpy.where(data <= 0.04045, data / 12.92, numpy.power((data + 0.055) / 1.055, 2.4))


# Generated using https://www.colour-science.org:8010/apps/rgb_colourspace_transformation_matrix
#transformation_matrix = {
#    "sRGB/CAT02/ACEScg": numpy.array([
#        [ 0.6131178129,  0.3411819959,  0.0457873443],
#        [ 0.0699340823,  0.9181030375,  0.0119327755],
#        [ 0.0204629926,  0.1067686634,  0.8727159106],
#        ]),
#    "ACEScg/CAT02/sRGB": numpy.array([
#        [ 1.7048873310, -0.6241572745, -0.0808867739],
#        [-0.1295209353,  1.1383993260, -0.0087792418],
#        [-0.0241270599, -0.1246206123,  1.1488221099],
#        ]),
#}


