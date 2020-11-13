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

"""Functions that produce, consume, and modify Imagecat :ref:`images<images>`.
"""

import functools
import logging

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import numpy
import skimage.filters
import skimage.transform

import imagecat.data
import imagecat.io
import imagecat.units

log = logging.getLogger(__name__)


def array(shape, dtype=numpy.float16):
    def implementation(value):
        value = numpy.array(value, dtype=dtype)
        if value.shape != shape:
            raise ValueError(f"Expected array with shape {shape}, received {value.shape}.") # pragma: no cover
        return value
    return implementation


def log_result(log, name, operation, output, **parameters):
     log.info(f"Task {name} {operation}:")
     for name, parameter in sorted(parameters.items()):
         log.info(f"  {name}: {parameter}")
     log.info(f"  output: {output!r}")


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
        raise RuntimeError(f"Task {name} missing required input {input!r} index {index}.") # pragma: no cover
    if type is not None:
        value = type(value)
    return value


def require_layer(name, inputs, input, *, index=0, layer="C", components=None, dtype=None):
    image = require_image(name, inputs, input, index=index)
    if layer not in image.layers:
        raise RuntimeError(f"Task {name} input {input!r} index {index} missing layer {layer}.") # pragma: no cover
    if components is not None and image.layers[layer].data.shape[2] != components:
        raise RuntimeError(f"Expected a layer with {components} components.") # pragma: no cover
    if dtype is not None and image.layers[layer].data.dtype != dtype:
        raise RuntimeError(f"Expected a layer with dtype {dtype}.") # pragma: no cover
    return image.layers[layer].copy()


def require_image(name, inputs, input, *, index=0):
    image = require_input(name, inputs, input, index=index)
    if not isinstance(image, imagecat.data.Image):
        raise ValueError(f"Task {name} input {input!r} index {index} is not an image.") # pragma: no cover
    # This ensures that we don't accidentally our inputs.
    return imagecat.data.Image(layers=dict(image.layers))


def transform(source, target_shape, *, pivot, position, orientation):
    """Transform an image using an affine transformation.

    Parameters
    ----------
    source: :class:`numpy.ndarray`, required
        Image to be transformed.
    target_shape: 2-tuple of integers, required
        Desired output image size, as a ``(rows, cols)`` tuple.  Note that this does not have to
        match the size of the `source` image.  By default, the `source` image will be centered in
        the output, cropped if necessary.
    pivot: 2-tuple of numbers, required
        Location of the point on the source image around which scaling and rotation takes place.
    orientation: number, optional
        Rotation of the source around its pivot point, in degrees.  Positive
        angles lead to counter-clockwise rotation.
    position: 2-tuple of numbers, optional
        Position of the image pivot point relative to `target_shape`.

    Returns
    -------
    image: :class:`numpy.ndarray`
        The transformed image.
    """
    # Get the source resolution.
    sourcey, sourcex = source.shape[:2]
    # Get the target resolution
    targety, targetx = target_shape[:2]

    # Start with an identity matrix.
    matrix = skimage.transform.AffineTransform(matrix=numpy.identity(3))

    # Position the source image relative to its pivot.
    pivotx = imagecat.units.length(pivot[0], (sourcex, sourcey))
    pivoty = imagecat.units.length(pivot[1], (sourcex, sourcey))

    offset = skimage.transform.AffineTransform(translation=(0, -sourcey))
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    offset = skimage.transform.AffineTransform(translation=(-pivotx, pivoty))
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    # Rotate the source.
    rotation = skimage.transform.AffineTransform(rotation=numpy.radians(-orientation)) # Positive = counter-clockwise
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(rotation.params, matrix.params))

    # Position the pivot relative to the target.
    offset = skimage.transform.AffineTransform(translation=(0, targety))
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    # Position the image relative to the target shape.
    positionx = imagecat.units.length(position[0], (targetx, targety))
    positiony = imagecat.units.length(position[1], (targetx, targety))

    offset = skimage.transform.AffineTransform(translation=(positionx, -positiony))
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    # Transform the image.
    return skimage.transform.warp(skimage.img_as_float64(source), matrix.inverse, output_shape=target_shape, order=3, mode="constant", cval=0).astype(numpy.float16)


