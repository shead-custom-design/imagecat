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

"""Operators that modify :ref:`images<images>` by transforming content.
"""

import logging

import numpy

import imagecat.data
import imagecat.operator.util
import imagecat.units

log = logging.getLogger(__name__)


def composite(graph, name, inputs):
    """Composite foreground and background layers using a mask and optional transformation.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["bglayer"][0]: :class:`str`, optional. Name of the background layer.  Defaults to `"C"`.
        :["fglayer"][0]: :class:`str`, optional. Name of the foreground layer.  Defaults to `"C"`.
        :["layer"][0]: :class:`str`, optional. Name of the output image layer.  Defaults to the value of `bglayer`.
        :["masklayer"][0]: :class:`str`, optional. Name of the mask layer.  Defaults to `"A"`.
        :["orientation"][0]: number, optional. Rotation of the foreground layer for the composition.  Default: `0`.
        :["pivot"][0]: (x, y) tuple, optional.  Position of the foreground pivot point.  All rotation and positioning is relative to this point.  Default: `["0.5w", "0.5h"]`, which is centered on the foreground.
        :["position"][0]: (x, y) tuple, optional.  Position of the foreground layer over the background layer.  All rotation and positioning is relative to the pivot point.  Default: `["0.5w", "0.5h"]`, which is centered on the background.

        :["foreground"][0]: :class:`imagecat.data.Image`, required. Image containing the foreground layer.
        :["background"][0]: :class:`imagecat.data.Image`, required. Image containing the background layer.
        :["mask"][0]: :class:`imagecat.data.Image`, optional. Image containing the foreground layer mask.  If omitted, the foreground layer is assumed to be 100% opaque.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        New image with a single solid-color layer.
    """
    bglayer = imagecat.operator.util.optional_input(name, inputs, "bglayer", type=str, default="C")
    fglayer = imagecat.operator.util.optional_input(name, inputs, "fglayer", type=str, default="C")
    layer = imagecat.operator.util.optional_input(name, inputs, "layer", type=str, default=bglayer)
    masklayer = imagecat.operator.util.optional_input(name, inputs, "masklayer", type=str, default="A")
    order = imagecat.operator.util.optional_input(name, inputs, "order", type=int, default=3)
    orientation = imagecat.operator.util.optional_input(name, inputs, "orientation", type=float, default=0)
    pivot = imagecat.operator.util.optional_input(name, inputs, "pivot", default=["0.5w", "0.5h"])
    position = imagecat.operator.util.optional_input(name, inputs, "position", default=["0.5w", "0.5h"])
    scale = imagecat.operator.util.optional_input(name, inputs, "scale", default=[1, 1])

    background = imagecat.operator.util.require_layer(name, inputs, "background", layer=bglayer)
    foreground = imagecat.operator.util.require_layer(name, inputs, "foreground", layer=fglayer)
    mask = imagecat.operator.util.optional_layer(name, inputs, "mask", layer=masklayer, components=1)

    if mask is None:
        mask = numpy.ones((foreground.shape[0], foreground.shape[1], 1), dtype=numpy.float16)
    else:
        mask = mask.data

    i1, i2, j1, j2, transformed_foreground = imagecat.operator.util.transform(foreground.data, background.data.shape, pivot=pivot, orientation=orientation, position=position, scale=scale, order=order)
    i1, i2, j1, j2, transformed_mask = imagecat.operator.util.transform(mask, background.data.shape, pivot=pivot, orientation=orientation, position=position, scale=scale, order=order)
    alpha = transformed_mask
    one_minus_alpha = 1 - alpha
    data = background.data.copy()
    data[i1:i2, j1:j2] = transformed_foreground * alpha + data[i1:i2, j1:j2] * one_minus_alpha

    output = imagecat.data.Image(layers={layer: imagecat.data.Layer(data=data, components=background.components, role=background.role)})
    imagecat.operator.util.log_result(log, name, "composite", output, bglayer=bglayer, fglayer=fglayer, masklayer=masklayer, layer=layer, order=order, orientation=orientation, pivot=pivot, position=position, scale=scale)
    return output


def offset(graph, name, inputs):
    """Offset layers in an :ref:`image<images>`.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["image"][0]: :class:`imagecat.data.Image`, required. Image containing layers to be offset.
        :["layers"][0]: :class:`str`, optional. Pattern matching the layers to be offset.  Default: '*', which offsets all layers.
        :["offset"][0]: (x, y) tuple, required. Distance to offset layers along each dimension.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image with some layers offset.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    layers = imagecat.operator.util.optional_input(name, inputs, "layers", type=str, default="*")
    offset = imagecat.operator.util.optional_input(name, inputs, "offset", default=["0.5w", "0.5h"])

    output = imagecat.data.Image()
    for layer_name in image.match_layer_names(layers):
        layer = image.layers[layer_name]
        data = layer.data
        xoffset = int(imagecat.units.length(offset[0], layer.res))
        yoffset = -int(imagecat.units.length(offset[1], layer.res)) # We always treat +Y as "up"
        data = numpy.roll(data, shift=(xoffset, yoffset), axis=(1, 0))
        output.layers[layer_name] = layer.copy(data=data)
    imagecat.operator.util.log_result(log, name, "offset", output, layers=layers, offset=offset)
    return output
