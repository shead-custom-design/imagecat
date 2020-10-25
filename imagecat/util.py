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

import itertools
import fnmatch

import numpy
import skimage.transform


def array(shape, dtype=float):
    def implementation(value):
        value = numpy.array(value, dtype=dtype)
        if value.shape != shape:
            raise ValueError(f"Expected array with shape {shape}, received {value.shape}.")
        return value
    return implementation


def match_planes(planes, patterns):
    """Match image planes against a pattern.

    Use this function implementing tasks that can operate on multiple image
    planes.  `patterns` is a :class:`str` that can contain multiple whitespace
    delimited patterns.  Patterns can include ``"*"`` which matches everything, ``"?"``
    to match a single character, ``"[seq]"`` to match any character in seq, and ``"[!seq]"``
    to match any character not in seq.

    Parameters
    ----------
    planes: sequence of :class:`str`, required
        The :ref:`image<images>` plane names to be matched.
    pattern: :class:`str`, required
        Whitespace delimited collection of patterns to match against image names.

    Yields
    ------
    planes: sequence of :class:`str` image names that match `patterns`.
    """
    for plane in planes:
        for pattern in patterns.split():
            if fnmatch.fnmatchcase(plane, pattern):
                yield plane
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


def is_plane(plane, channels=None, dtype=None):
    if not isinstance(plane, numpy.ndarray):
        return False
    if plane.ndim != 3:
        return False
    if channels is not None and plane.shape[2] != channels:
        return False
    if dtype is not None and plane.dtype != dtype:
        return False
    return True


def is_image(image):
    if not isinstance(image, dict):
        return False
    planes = list(images.values())
    for plane in planes:
        if not is_plane(plane):
            return False
        # All planes must have the same resolution
        if plane.shape[:2] != planes[0].shape[:2]:
            return False
    return True


def require_plane(name, inputs, input, *, index=0, plane="C", channels=None, dtype=None):
    image = require_input(name, inputs, input, index=index, type=dict)
    if plane not in image:
        raise RuntimeError(f"Task {name} input {input!r} index {index} missing plane {plane}.")
    if not is_plane(image[plane], channels=channels, dtype=dtype):
        raise RuntimeError(f"Task {name} input {input!r} index {index} plane {plane} is not an image plane with {channels} channels and dtype {dtype}.")
    return image[plane]


def require_image(name, inputs, input, *, index=0):
    image = require_input(name, inputs, input, index=index, type=dict)
    planes = list(image.items())
    for name, plane in planes:
        if not is_plane(plane):
            raise ValueError(f"Task {name} input {input!r} index {index} {plane} is not an image plane.")
        if plane.shape[:2] != planes[0][1].shape[:2]:
            raise ValueError(f"Task {name} input {input!r} index {index} not all planes are the same resolution.")
    return image


def transform(source, target_shape, *, rotation=None, translation=None):
    """Transform an image using an affine transformation.

    Parameters
    ----------
    source: :class:`numpy.ndarray`, required
        Image to be transformed.
    target_shape: 2-tuple of integers, required
        Desired output image size, as a ``(rows, cols)`` tuple.  Note that this does not have to
        match the size of the `source` image.  By default, the `source` image will be centered in
        the output, cropped if necessary.
    rotation: number, optional
        Rotation of the image around its center, in degrees.
    translation: 2-tuple of numbers, optional
        Translation of the image relative to `target_shape`, in relative coordinates.

    Returns
    -------
    image: :class:`numpy.ndarray`
        The transformed image.
    """
    sy, sx = source.shape[:2]
    ty, tx = target_shape[:2]

    # Start with an identity matrix.
    matrix = skimage.transform.AffineTransform(matrix=numpy.identity(3))

    # Optionally rotate the image around its center.
    if rotation is not None:
        offset = skimage.transform.AffineTransform(translation=(-sx / 2, -sy / 2))
        matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

        # Positive rotation is counter-clockwise in my book.
        rotation = skimage.transform.AffineTransform(rotation=numpy.radians(-rotation))
        matrix = skimage.transform.AffineTransform(matrix=numpy.dot(rotation.params, matrix.params))

        offset = skimage.transform.AffineTransform(translation=(sx / 2, sy / 2))
        matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    # Center the result.
    offset = skimage.transform.AffineTransform(translation=((tx - sx) / 2, (ty - sy) / 2))
    matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    # Optionally transform the image relative to the target.
    if translation is not None:
        # +Y is up in my book.
        offset = skimage.transform.AffineTransform(translation=(translation[0] * tx, -translation[1] * ty))
        matrix = skimage.transform.AffineTransform(matrix=numpy.dot(offset.params, matrix.params))

    # Transform the image.
    return skimage.transform.warp(source, matrix.inverse, output_shape=target_shape, order=3, mode="constant", cval=0)


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
