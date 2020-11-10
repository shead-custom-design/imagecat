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


################################################################################################
# Helper functions for implementing operators


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
    return image.layers[layer].modify()


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


################################################################################################
# Operators


def colormap(graph, name, inputs):
    image = require_image(name, inputs, "image", index=0)
    layers = optional_input(name, inputs, "layers", type=str, default="*")
    mapping = optional_input(name, inputs, "mapping", default=None)

    if mapping is None:
        palette = imagecat.color.brewer.palette("BlueRed")
        mapping = functools.partial(imagecat.color.linear_map, palette=palette)

    output = imagecat.data.Image()
    for layer_name in image.match_layer_names(layers):
        layer = image.layers[layer_name]
        data = layer.data
        if data.shape[2] != 1:
            continue
        data = mapping(data[:,:,0])
        output.layers[layer_name] = imagecat.data.Layer(data=data)
    log_result(log, name, "colormap", output, layers=layers, mapping=mapping)
    return output


def composite(graph, name, inputs):
    bglayer = optional_input(name, inputs, "bglayer", index=0, type=str, default="C")
    fglayer = optional_input(name, inputs, "fglayer", index=0, type=str, default="C")
    masklayer = optional_input(name, inputs, "masklayer", index=0, type=str, default="A")
    orientation = optional_input(name, inputs, "orientation", index=0, type=float, default=0)
    pivot = optional_input(name, inputs, "pivot", index=0, default=["0.5w", "0.5h"])
    position = optional_input(name, inputs, "position", index=0, default=["0.5w", "0.5h"])

    background = require_layer(name, inputs, "background", index=0, layer=bglayer)
    foreground = require_layer(name, inputs, "foreground", index=0, layer=fglayer)
    mask = require_layer(name, inputs, "mask", index=0, layer=masklayer, components=1)

    transformed_foreground = transform(foreground.data, background.data.shape, pivot=pivot, orientation=orientation, position=position)
    transformed_mask = transform(mask.data, background.data.shape, pivot=pivot, orientation=orientation, position=position)
    alpha = transformed_mask
    one_minus_alpha = 1 - alpha
    data = transformed_foreground * alpha + background.data * one_minus_alpha

    output = imagecat.data.Image(layers={"C": imagecat.data.Layer(data=data, components=background.components, role=background.role)})
    log_result(log, name, "composite", output, bglayer=bglayer, fglayer=fglayer, masklayer=masklayer, orientation=orientation, pivot=pivot, position=position)
    return output


def delete(graph, name, inputs):
    """Delete layers from an :ref:`image<images>`.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["image"][0]: :class:`dict`, required. :ref:`Image<images>` containing image planes to be deleted.
        :["layers"][0]: :class:`str`, optional. Controls which image layers are deleted.  Default: '*', which deletes all layers.

    Returns
    -------
    image: :class:`dict`
        A copy of the input :ref:`image<images>` with some image planes deleted.
    """
    image = require_image(name, inputs, "image", index=0)
    layers = optional_input(name, inputs, "layers", type=str, default="*")

    remove = image.match_layer_names(layers)
    output = imagecat.data.Image(layers={name: layer for name, layer in image.layers.items() if name not in remove})
    log_result(log, name, "delete", output, layers=layers)
    return output


def fill(graph, name, inputs):
    components = optional_input(name, inputs, "components", default=["r", "g", "b"])
    layer = optional_input(name, inputs, "layer", type=str, default="C")
    res = optional_input(name, inputs, "res", type=array(shape=(2,), dtype=int), default=[256, 256])
    role = optional_input(name, inputs, "role", type=imagecat.data.Role, default=imagecat.data.Role.RGB)
    values = optional_input(name, inputs, "values", type=numpy.array, default=[1, 1, 1])

    if components and len(components) != len(values):
        raise ValueError("Number of components and number of values must match.") # pragma: no cover

    data = numpy.full((res[1], res[0], len(values)), values, dtype=numpy.float16)
    output = imagecat.data.Image(layers={layer: imagecat.data.Layer(data=data, components=components, role=role)})
    log_result(log, name, "fill", output, components=components, layer=layer, role=role, res=res, values=values)
    return output


def gaussian(graph, name, inputs):
    """Blur image using a Gaussian kernel.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["image"][0]: :class:`dict`, required. :ref:`Image<images>` containing planes to be blurred.
        :["planes"][0]: :class:`str`, optional. Controls which image planes are blurred.  Default: '*', which blurs all planes.
        :["sigma"][0]: number, required. Width of the gaussian kernel in pixels.

    Returns
    -------
    image: :class:`dict`
        A copy of the input :ref:`image<images>` with some or all planes blurred.
    """
    image = require_image(name, inputs, "image", index=0)
    layers = optional_input(name, inputs, "layers", type=str, default="*")
    radius = optional_input(name, inputs, "radius", default=["5px", "5px"])

    output = imagecat.data.Image()
    for layer_name in image.match_layer_names(layers):
        layer = image.layers[layer_name]
        data = layer.data
        sigma = [
            imagecat.units.length(radius[1], layer.res),
            imagecat.units.length(radius[0], layer.res),
            ]
        data = numpy.atleast_3d(skimage.filters.gaussian(data, sigma=sigma, multichannel=True, preserve_range=True).astype(data.dtype))
        output.layers[layer_name] = layer.modify(data=data)
    log_result(log, name, "gaussian", output, layers=layers, radius=radius)
    return output


def load(graph, name, inputs):
    """Load a file into memory.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :class:`dict`, required
        Inputs for this function, including:

        :["path"][0]: :class:`str`, required. Filesystem path of the file to be loaded.

    Returns
    -------
    image: :class:`dict`
        :ref:`Image <images>` containing image planes loaded from the file.
    """
    layers = optional_input(name, inputs, "layers", type=str, default="*")
    path = require_input(name, inputs, "path", type=str)

    for loader in imagecat.io.loaders:
        output = loader(name, path, layers)
        if output is not None:
            log_result(log, name, "load", output, layers=layers, path=path)
            return output
    raise RuntimeError(f"Task {task} could not load {path} from disk.") # pragma: no cover


def merge(graph, name, inputs):
    """Merge multiple :ref:`images<images>` into one.

    Inputs are merged in order, sorted by input name and index.  Image layers with duplicate
    names will overwrite earlier layers.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :[...][...]: :class:`dict`, optional. :ref:`Images<images>` to be merged.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        New :ref:`image<images>` containing the union of all input images.
    """
    output = imagecat.data.Image()
    for input in sorted(inputs.keys()):
        for index in range(len(inputs[input])):
            image = inputs[input][index]
            if isinstance(image, imagecat.data.Image):
                output.layers.update(image.layers)
    log_result(log, name, "merge", output)
    return output


def offset(graph, name, inputs):
    image = require_image(name, inputs, "image", index=0)
    layers = optional_input(name, inputs, "layers", index=0, type=str, default="*")
    offset = optional_input(name, inputs, "offset", index=0, default=["0.5w", "0.5h"])

    output = imagecat.data.Image()
    for layer_name in image.match_layer_names(layers):
        layer = image.layers[layer_name]
        data = layer.data
        xoffset = int(imagecat.units.length(offset[0], layer.res))
        yoffset = -int(imagecat.units.length(offset[1], layer.res)) # We always treat +Y as "up"
        data = numpy.roll(data, shift=(xoffset, yoffset), axis=(1, 0))
        output.layers[layer_name] = layer.modify(data=data)
    log_result(log, name, "offset", output, layers=layers, offset=offset)
    return output


def rename(graph, name, inputs):
    """Rename layers within an :ref:`image<images>`.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["image"][0]: :class:`dict`, required. :ref:`Image<images>` containing image planes to be renamed.
        :["changes"][0]: :class:`dict`, optional. Maps existing names to new names.  Default: {}, which does nothing.

    Returns
    -------
    image: :class:`dict`
        A copy of the input :ref:`image<images>` with some image planes renamed.
    """
    image = require_image(name, inputs, "image")
    changes = optional_input(name, inputs, "changes", type=dict, default={})

    output = imagecat.data.Image(layers={changes.get(name, name): layer for name, layer in image.layers.items()})
    log_result(log, name, "rename", output, changes=changes)
    return output


def rgb2gray(graph, name, inputs):
    image = require_image(name, inputs, "image", index=0)
    layers = optional_input(name, inputs, "layers", type=str, default="*")
    weights = optional_input(name, inputs, "weights", type=array(shape=(3,)), default=[0.2125, 0.7154, 0.0721])

    output = imagecat.data.Image()
    for layer_name in image.match_layer_names(layers):
        layer = image.layers[layer_name]
        if layer.data.shape[2] != 3:
            continue
        output.layers[layer_name] = imagecat.data.Layer(data=numpy.dot(layer.data, weights)[:,:,None])
    log_result(log, name, "rgb2gray", output, layers=layers, weights=weights)
    return output


def save(graph, name, inputs):
    """Save a file to disk.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :class:`dict`, required
        Inputs for this function, including:

        :["path"][0]: :class:`str`, required. Filesystem path of the file to be saved.
        :["planes"][0]: :class:`str`, optional. Controls which image planes are to be saved.  Default: '*', which saves all planes.
    """
    image = require_image(name, inputs, "image", index=0)
    path = require_input(name, inputs, "path", type=str)
    layers = optional_input(name, inputs, "layers", type=str, default="*")

    layer_names = image.match_layer_names(layers)
    for saver in imagecat.io.savers:
        if saver(name, image, layer_names, path):
            return
    raise RuntimeError(f"Task {task} could not save 'image' to disk.") # pragma: no cover


def resize(graph, name, inputs):
    image = require_image(name, inputs, "image", index=0)
    order = optional_input(name, inputs, "order", type=int, default=3)
    res = optional_input(name, inputs, "res", default=("1w", "1h"))

    output = imagecat.data.Image()
    for layername, layer in image.layers.items():
        width = int(imagecat.units.length(res[0], layer.res))
        height = int(imagecat.units.length(res[1], layer.res))
        data = skimage.transform.resize(layer.data.astype(numpy.float32), (height, width), anti_aliasing=True, order=order).astype(layer.data.dtype)
        output.layers[layername] = layer.modify(data=data)
    log_result(log, name, "resize", output, order=order, res=res)
    return output


def text(graph, name, inputs):
    anchor = optional_input(name, inputs, "anchor", type=str, default="mm")
    fontindex = optional_input(name, inputs, "fontindex", type=int, default=0)
    fontname = optional_input(name, inputs, "fontname", type=str, default="Helvetica")
    fontsize = optional_input(name, inputs, "fontsize", default="32px")
    layer = optional_input(name, inputs, "layer", type=str, default="A")
    position = optional_input(name, inputs, "position", default=("0.5w", "0.5h"))
    res = optional_input(name, inputs, "res", type=array(shape=(2,), dtype=int), default=[256, 256])
    text = optional_input(name, inputs, "text", type=str, default="Text!")

    fontsize_px = int(imagecat.units.length(fontsize, res))
    x = imagecat.units.length(position[0], res)
    y = imagecat.units.length(position[1], res)

    pil_image = PIL.Image.new("L", (res[0], res[1]), 0)
    font = PIL.ImageFont.truetype(fontname, fontsize_px, fontindex)
    draw = PIL.ImageDraw.Draw(pil_image)
    draw.text((x, y), text, font=font, fill=255, anchor=anchor)

    data = numpy.array(pil_image, dtype=numpy.float16)[:,:,None] / 255.0
    output = imagecat.data.Image({layer: imagecat.data.Layer(data=data)})
    log_result(log, name, "text", output, anchor=anchor, fontindex=fontindex, fontname=fontname, fontsize=fontsize, layer=layer, position=position, res=res, text=text)
    return output


def uniform(graph, name, inputs):
    components = optional_input(name, inputs, "components", default=None)
    layer = optional_input(name, inputs, "layer", type=str, default="C")
    role = optional_input(name, inputs, "role", type=imagecat.data.Role, default=imagecat.data.Role.RGB)
    seed = optional_input(name, inputs, "seed", type=int, default=1234)
    res = optional_input(name, inputs, "res", type=array(shape=(2,), dtype=int), default=[256, 256])

    if components is None:
        components = [""]

    generator = numpy.random.default_rng(seed=seed)
    data = generator.uniform(size=(res[1], res[0], len(components))).astype(numpy.float16)
    output = imagecat.data.Image(layers={layer: imagecat.data.Layer(data=data, components=components, role=role)})
    log_result(log, name, "uniform", output, components=components, layer=layer, role=role, seed=seed, res=res)
    return output


