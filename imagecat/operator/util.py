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

import numpy
try:
    import skimage.transform
except:
    pass

import imagecat.data
import imagecat.io
import imagecat.require
import imagecat.units

log = logging.getLogger(__name__)


def array(ndim=None, shape=None, dtype=None):
    """Factory for parameter converters that return arrays.

    Parameters
    ----------
    ndim: integer, optional
        Raise exceptions if the number of value dimensions don't match.
    shape: integer or tuple of integers, optional
        Raise exceptions if the value shape doesn't match.
    dtype: :class:`numpy.dtype`, optional
        If specified, the returned array will be coerced to the given dtype.

    Returns
    -------
    converter: callable
         Callable that takes a single value as input and produces a
         :class:`numpy.ndarray` as output.
    """
    def implementation(value):
        value = numpy.array(value)
        if ndim is not None and value.ndim != ndim:
            raise ValueError(f"Expected array with {ndim} dimensions, received {value.ndim}.") # pragma: no cover
        if shape is not None and value.shape != shape:
            raise ValueError(f"Expected array with shape {shape}, received {value.shape}.") # pragma: no cover
        if dtype is not None:
            value = value.astype(dtype)
        return value
    return implementation


def log_result(log, name, operation, output, **parameters):
    """Standard logging output for operators when they're executed."""
    log.info(f"Task {name} {operation}:")
    for name, parameter in sorted(parameters.items()):
        log.info(f"  {name}: {parameter}")
    log.info(f"  output: {output!r}")


def optional_image(name, inputs, input):
    """Extract an optional image from task inputs.

    Parameters
    ----------
    name: hashable object, required
        The name of the task being executed.
    inputs: :ref:`named-inputs`, required
        Named inputs containing task function arguments.
    input: hashable object, required
        Name of the optional input image.

    Raises
    ------
    :class:`RuntimeError`
        If `inputs` contains `input`, but it isn't a :class:`imagecat.data.Image`.

    Returns
    -------
    image: class:`imagecat.data.Image` or :any:`None`
        The optional image from `inputs`.
    """
    image = optional_input(name, inputs, input)
    if image is None:
        return None
    if not isinstance(image, imagecat.data.Image):
        raise ValueError(f"Task {name} input {input!r} is not an image.") # pragma: no cover
    # This ensures that we don't accidentally modify our inputs.
    return image.copy()


def optional_input(name, inputs, input, *, type=None, default=None):
    """Extract an optional parameter from task inputs.

    Parameters
    ----------
    name: hashable object, required
        The name of the task being executed.
    inputs: :ref:`named-inputs`, required
        Named inputs containing task function arguments.
    input: hashable object, required
        Name of the input parameter.
    type: callable, optional
        Function for testing / converting the parameter value.
    default: Any python object, optional
        Default value that will be returned if `inputs` doesn't contain `input`.

    Returns
    -------
    parameter: Any python object.
        The optional parameter from `inputs`, or the `default` value.
    """
    value = inputs.get(input, default=default)
    if type is not None:
        value = type(value)
    return value


def optional_layer(name, inputs, input, *, layer=None, role=None, depth=None, dtype=None):
    """Extract an optional layer from task inputs.

    Parameters
    ----------
    name: hashable object, required
        The name of the task being executed.
    inputs: :ref:`named-inputs`, required
        Named inputs containing task function arguments.
    input: hashable object, required
        Name of the optional input image.
    layer: :class:`str`, optional
        The name of the optional layer.  If :any:`None` (the default) and the image only
        contains one layer, use it.
    role: :class:`imagecat.data.Role`, optional
        If specified, the layer must have a matching role.
    depth: int, optional
        If specified, the layer must have a matching depth (number of channels).
    dtype: :class:`numpy.dtype`, optional
        If specified, the layer must have a matching dtype.

    Returns
    -------
    layername: :class:`str` or :any:`None`
        The name of the matching layer.
    layer: :class:`imagecat.data.Layer` or :any:`None`
        The matching layer.
    """
    image = optional_image(name, inputs, input)
    if image is None:
        return None, None
    if layer is None and len(image.layers) == 1:
        layer = next(iter(image.layers.keys()))
    if layer not in image.layers:
        return None, None
    if role is not None and image.layers[layer].role != role:
        return None, None
    if depth is not None and image.layers[layer].data.shape[2] != depth:
        return None, None
    if dtype is not None and image.layers[layer].data.dtype != dtype:
        return None, None
    return layer, image.layers[layer].copy() # This ensures that we don't modify our inputs.


def require_image(name, inputs, input):
    """Extract an image from task inputs.

    Parameters
    ----------
    name: hashable object, required
        The name of the task being executed.
    inputs: :ref:`named-inputs`, required
        Named inputs containing task function arguments.
    input: hashable object, required
        Name of the required input image.

    Raises
    ------
    :class:`RuntimeError`
        If `inputs` doesn't contain the required `input`.

    Returns
    -------
    image: class:`imagecat.data.Image`
        The required image from `inputs`.
    """
    image = require_input(name, inputs, input)
    if not isinstance(image, imagecat.data.Image):
        raise ValueError(f"Task {name} input {input!r} is not an image.") # pragma: no cover
    # This ensures that we don't accidentally modify our inputs.
    return image.copy()


def require_input(name, inputs, input, *, type=None):
    """Extract a parameter from task inputs.

    Parameters
    ----------
    name: hashable object, required
        The name of the task being executed.
    inputs: :ref:`named-inputs`, required
        Named inputs containing task function arguments.
    input: hashable object, required
        Name of the required input parameter.
    type: callable, optional
        Function for testing / converting the type of the input parameter value.

    Raises
    ------
    :class:`RuntimeError`
        If `inputs` doesn't contain the required `input`.

    Returns
    -------
    parameter: Any python object.
        The required parameter from `inputs`.
    """
    try:
        value = inputs.getone(input)
    except KeyError:
        raise KeyError(f"Task {name} missing required input {input!r}.") # pragma: no cover
    if type is not None:
        value = type(value)
    return value


def require_layer(name, inputs, input, *, layer=None, role=None, depth=None, dtype=None):
    """Extract a layer from task inputs.

    Parameters
    ----------
    name: hashable object, required
        The name of the task being executed.
    inputs: :ref:`named-inputs`, required
        Named inputs containing task function arguments.
    input: hashable object, required
        Name of the required input image.
    layer: :class:`str`, optional
        The name of the required layer.  If :any:`None` (the default) and the image only
        contains one layer, use it.
    role: :class:`imagecat.data.Role`, optional
        If specified, the layer must have a matching role.
    depth: int, optional
        If specified, the layer must have a matching depth (number of channels).
    dtype: :class:`numpy.dtype`, optional
        If specified, the layer must have a matching dtype.

    Raises
    ------
    :class:`RuntimeError`
        If a layer matching all of the criteria can't be found.

    Returns
    -------
    layername: :class:`str`
        The name of the matching layer.
    layer: :class:`imagecat.data.Layer`
        The matching layer.
    """
    image = require_image(name, inputs, input)
    if layer is None and len(image.layers) == 1:
        layer = next(iter(image.layers.keys()))
    if layer not in image.layers:
        raise RuntimeError(f"Task {name} input {input!r} missing layer {layer}.") # pragma: no cover
    if role is not None and image.layers[layer].role != role:
        raise RuntimeError(f"Task {name} input {input!r} layer {layer} expected role {role}.") # pragma: no cover
    if depth is not None and image.layers[layer].data.shape[2] != depth:
        raise RuntimeError(f"Task {name} input {input!r} layer {layer} expected {depth} channels.") # pragma: no cover
    if dtype is not None and image.layers[layer].data.dtype != dtype:
        raise RuntimeError(f"Task {name} input {input!r} layer {layer} expected dtype {dtype}.") # pragma: no cover
    return layer, image.layers[layer].copy() # This ensures that we don't modify our inputs.


@imagecat.require.loaded_module("skimage.transform")
def transform(source, target_shape, *, pivot, position, orientation, scale, order):
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
    orientation: number, required
        Rotation of the source around its pivot point, in degrees.  Positive
        angles lead to counter-clockwise rotation.
    position: 2-tuple of numbers, required
        Position of the image pivot point relative to `target_shape`.
    scale: 2-tuple of numbers, required
        Scale of the source image around its pivot point.

    Returns
    -------
    rowoffset: integer
        Vertical offset of the returned array relative to the upper-left corner of `target_shape`
    coloffset: integer
        Horizontal offset of the returned array relative to the upper-left corner of `target_shape`
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

    # Scale the source.
    scale = skimage.transform.AffineTransform(scale=scale)
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(scale.params, matrix.params))

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

    # Identify the smallest region in target space that will completely contain
    # the transformed source.  This will become "render space".
    coords = [[0, 0], [sourcex, 0], [sourcex, sourcey], [0, sourcey]]
    coords = matrix(coords)
    minx, miny = numpy.max(numpy.row_stack((numpy.floor(numpy.min(coords, axis=0)), [0, 0])), axis=0).astype(numpy.int32)
    maxx, maxy = numpy.min(numpy.row_stack((numpy.ceil(numpy.max(coords, axis=0)), [targetx, targety])), axis=0).astype(numpy.int32)

    # Position the image relative to render space.
    offset = skimage.transform.AffineTransform(translation=(-minx, -miny))
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    # Transform the image.
    render_shape = (maxy - miny, maxx - minx) + target_shape[2:]
    return miny, maxy, minx, maxx, skimage.transform.warp(skimage.img_as_float64(source), matrix.inverse, output_shape=render_shape, order=order, mode="constant", cval=0).astype(numpy.float16)


