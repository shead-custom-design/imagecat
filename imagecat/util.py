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
        The :ref:`image collection<image-collections>` image names to be matched.
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


def required_input(name, inputs, input, *, index=0, type=None):
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


def require_images(name, inputs, input, *, index=0):
    return dict(required_input(name, inputs, input, index=index, type=dict))


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
