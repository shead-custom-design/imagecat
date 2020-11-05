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


"""Helpers for implementing Imagecat operations.
"""

import collections
import itertools
import fnmatch
import logging

import numpy
import skimage.transform

import imagecat
import imagecat.units as units


log = logging.getLogger(__name__)


def array(shape, dtype=numpy.float16):
    def implementation(value):
        value = numpy.array(value, dtype=dtype)
        if value.shape != shape:
            raise ValueError(f"Expected array with shape {shape}, received {value.shape}.") # pragma: no cover
        return value
    return implementation


def channels_to_layers(channels):
     layers = [channel.rsplit(".", 1) for channel in channels]
     #log.debug(f"layers: {layers}")
     layers = [layer if len(layer) > 1 else ["", layer[0]] for layer in layers]
     #log.debug(f"layers: {layers}")
     layers = [(channel, layer, component) for channel, (layer, component) in zip(channels, layers)]
     #log.debug(f"layers: {layers}")
     groups = collections.defaultdict(list)
     for channel, layer, component in layers:
         groups[layer].append((channel, component))
     layers = list(groups.items())
     #log.debug(f"layers: {layers}")

 #    def split_layers(layers):
 #        for layer, channels in layers:
 #            if layer:
 #                yield (layer, channels)
 #                continue
 #            ci_components = [component.lower() for component, channel in channels]
 #            if "r" in ci_components and "g" in ci_components and "b" in ci_components:
 #                yield (layer, [channels[ci_components.index("r")], channels[ci_components.index("g")], channels[ci_components.index("b")]])
 #            channels = [channel for channel, ci_component in zip(channels, ci_components) if ci_component not in "rgb"]
 #            for channel in channels:
 #                yield layer, [channel]
 #    layers = list(split_layers(layers))

     def organize_layers(layers):
         for layer, components in layers:
             ci_components = [component.lower() for channel, component in components]
             for collection in ["rgb", "hsv", "hsb", "xy", "xyz", "uv", "uvw"]:
                 if sorted(ci_components) == sorted(collection):
                     components = [components[ci_components.index(component)] for component in collection]
             yield layer, components
     layers = list(organize_layers(layers))
     #log.debug(f"layers: {layers}")

     def categorize_layers(layers):
         for layer, components in layers:
             ci_components = [component.lower() for channel, component in components]
             if ci_components == ["r", "g", "b"]:
                 yield layer, components, imagecat.Role.RGB
             else:
                 yield layer, components, imagecat.Role.NONE
     layers = list(categorize_layers(layers))
     #log.debug(f"layers: {layers}")

     return layers


def match_layers(layers, patterns):
    """Match image layers against a pattern.

    Use this function implementing tasks that can operate on multiple image
    layers.  `patterns` is a :class:`str` that can contain multiple whitespace
    delimited patterns.  Patterns can include ``"*"`` which matches everything, ``"?"``
    to match a single character, ``"[seq]"`` to match any character in seq, and ``"[!seq]"``
    to match any character not in seq.

    Parameters
    ----------
    layers: sequence of :class:`str`, required
        The :ref:`image<images>` layer names to be matched.
    pattern: :class:`str`, required
        Whitespace delimited collection of patterns to match against layer names.

    Yields
    ------
    layers: sequence of :class:`str` layer names that match `patterns`.
    """
    for layer in layers:
        for pattern in patterns.split():
            if fnmatch.fnmatchcase(layer, pattern):
                yield layer
                break


def optional_input(name, inputs, input, *, index=0, type=None, default=None):
    """Extract an optional parameter from task inputs.

    Parameters
    ----------
    name: hashable object, required
        The name of the task being executed.
    inputs: :class:`dict`, required
        Input dict containing task function arguments.
    input: hashable object, required
        Name of the input parameter.
    index: integer, required
        Integer index of the input parameter.
    type: callable, optional
        Function for testing / converting the parameter value.
    default: Any python object, optional.
        Default value that will be returned if `input` or `index` aren't matched from the `inputs` :class:`dict`.

    Returns
    -------
    parameter: Any python object.
        The request parameter from `inputs`, or the `default` value.
    """
    value = default
    if input in inputs and 0 <= index and index < len(inputs[input]):
        value = inputs[input][index]
    if type is not None:
        value = type(value)
    return value


def require_input(name, inputs, input, *, index=0, type=None):
    """Extract a required parameter from task inputs.

    Parameters
    ----------
    name: hashable object, required
        The name of the task being executed.
    inputs: :class:`dict`, required
        Input dict containing task function arguments.
    input: hashable object, required
        Name of the input parameter.
    index: integer, required
        Integer index of the input parameter.
    type: callable, optional
        Function for testing / converting the input parameter value.

    Raises
    ------
    :class:`RuntimeError`
        If the `inputs` :class:`dict` doesn't contain the required `input`
        or `index`.

    Returns
    -------
    parameter: Any python object.
        The request parameter from `inputs`, or the `default` value.
    """
    if input in inputs and 0 <= index and index < len(inputs[input]):
        value = inputs[input][index]
    else:
        raise RuntimeError(f"Task {name} missing required input {input!r} index {index}.")
    if type is not None:
        value = type(value)
    return value


def require_layer(name, inputs, input, *, index=0, layer="C", components=None, dtype=None):
    image = require_image(name, inputs, input, index=index)
    if layer not in image.layers:
        raise RuntimeError(f"Task {name} input {input!r} index {index} missing layer {layer}.")
    if components is not None and image.layers[layer].data.shape[2] != components:
        raise RuntimeError(f"Expected a layer with {components} components.")
    if dtype is not None and image.layers[layer].data.dtype != dtype:
        raise RuntimeError(f"Expected a layer with dtype {dtype}.")
    return image.layers[layer].modify()


def require_image(name, inputs, input, *, index=0):
    image = require_input(name, inputs, input, index=index)
    if not isinstance(image, imagecat.Image):
        raise ValueError(f"Task {name} input {input!r} index {index} is not an image.") # pragma: no cover 
    # This ensures that we don't accidentally our inputs.
    return imagecat.Image(layers=dict(image.layers))


def transform(source, target_shape, *, position, orientation):
    """Transform an image using an affine transformation.

    Parameters
    ----------
    source: :class:`numpy.ndarray`, required
        Image to be transformed.
    target_shape: 2-tuple of integers, required
        Desired output image size, as a ``(rows, cols)`` tuple.  Note that this does not have to
        match the size of the `source` image.  By default, the `source` image will be centered in
        the output, cropped if necessary.
    orientation: number, optional
        Rotation of the image around its center, in degrees.
    position: 2-tuple of numbers, optional
        Position of the image center relative to `target_shape`.

    Returns
    -------
    image: :class:`numpy.ndarray`
        The transformed image.
    """
    sy, sx = source.shape[:2]
    ty, tx = target_shape[:2]

    # Start with an identity matrix.
    matrix = skimage.transform.AffineTransform(matrix=numpy.identity(3))

    # Orient the image around its center.
    offset = skimage.transform.AffineTransform(translation=(-sx / 2, -sy / 2))
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    rotation = skimage.transform.AffineTransform(rotation=numpy.radians(-orientation)) # Positive = counter-clockwise
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(rotation.params, matrix.params))

    offset = skimage.transform.AffineTransform(translation=(sx / 2, sy / 2))
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    # Center the image on the lower-left corner.
    offset = skimage.transform.AffineTransform(translation=(-sx / 2, (-sy / 2) + ty))
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    # Position the image relative to the target shape.
    xoffset = units.length(position[0], (tx, ty))
    yoffset = units.length(position[1], (tx, ty))
    offset = skimage.transform.AffineTransform(translation=(xoffset, -yoffset))
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    # Transform the image.
    return skimage.transform.warp(skimage.img_as_float64(source), matrix.inverse, output_shape=target_shape, order=3, mode="constant", cval=0).astype(numpy.float16)


def unique_name(graph, name):
    """Return `name`, modified to be unique within `graph`.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        The graph where `name` will be used.
    name: :class:`str`, required
        Task name to be adjusted.
    """
    if name not in graph:
        return name
    for index in itertools.count(start=1):
        if f"{name}{index}" not in graph:
            return f"{name}{index}"


def log_operation(log, name, operation, output, **parameters):
     log.info(f"Task {name} {operation}:")
     for name, parameter in sorted(parameters.items()):
         log.info(f"  {name}: {parameter}")
     log.info(f"  output: {output!r}")


