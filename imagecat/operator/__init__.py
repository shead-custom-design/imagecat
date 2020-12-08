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

import imagecat.data
import imagecat.io
import imagecat.operator.util
import imagecat.units

log = logging.getLogger(__name__)


def colormap(graph, name, inputs):
    """Convert single-component layers to RGB layers using a colormap.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["image"][0]: :class:`imagecat.data.Image`, required. Image with layers to be color mapped.
        :["layers"][0]: :class:`str`, optional. Pattern matching the image layers to be color mapped.  Default: `"*"`, which maps all single-component layers.
        :["colormap"][0]: Python callable, optional.  Mapping function that accepts a (rows, columns, 1) array as input and produces an RGB (rows, columns, 3) array as output.  If :any:`None` (the default), a linear map with a Color Brewer 2 Blue-Red palette will be used.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image with some layers mapped.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    layers = imagecat.operator.util.optional_input(name, inputs, "layers", type=str, default="*")
    mapping = imagecat.operator.util.optional_input(name, inputs, "mapping", default=None)

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
        output.layers[layer_name] = imagecat.data.Layer(data=data, components=["r", "g", "b"], role=imagecat.data.Role.RGB)
    imagecat.operator.util.log_result(log, name, "colormap", output, layers=layers, mapping=mapping)
    return output


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


def delete(graph, name, inputs):
    """Delete layers from an :ref:`image<images>`.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["image"][0]: :class:`imagecat.data.Image`, required. Image with layers to be deleted.
        :["layers"][0]: :class:`str`, optional. Pattern matching the image layers are deleted.  Default: `"*"`, which deletes all layers.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image with some layers deleted.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    layers = imagecat.operator.util.optional_input(name, inputs, "layers", type=str, default="*")

    remove = image.match_layer_names(layers)
    output = imagecat.data.Image(layers={name: layer for name, layer in image.layers.items() if name not in remove})
    imagecat.operator.util.log_result(log, name, "delete", output, layers=layers)
    return output


def load(graph, name, inputs):
    """Load an :ref:`image<images>` from a file.

    The file loader plugins in :mod:`imagecat.io` are used to load specific
    file formats.  See that module for details, and to write loaders of your
    own.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :class:`dict`, required
        Inputs for this function, including:

        :["path"][0]: :class:`str`, required. Filesystem path of the file to be loaded.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        Image loaded from the file.
    """
    layers = imagecat.operator.util.optional_input(name, inputs, "layers", type=str, default="*")
    path = imagecat.operator.util.require_input(name, inputs, "path", type=str)

    for loader in imagecat.io.loaders:
        output = loader(name, path, layers)
        if output is not None:
            imagecat.operator.util.log_result(log, name, "load", output, layers=layers, path=path)
            return output
    raise RuntimeError(f"Task {task} could not load {path} from disk.") # pragma: no cover


def merge(graph, name, inputs):
    """Merge multiple :ref:`images<images>` into one.

    This operator merges the layers from multiple images into a single image.
    The images must all have the same resolution.  Upstream inputs are merged
    in order, sorted by input name.  Later image layers with duplicate names
    will overwrite earlier layers.  Callers can prevent this by renaming layers
    upstream with the :func:`rename` operator.

    See Also
    --------
    :func:`composite`
        Composites one image over another using a mask.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :[...][...]: :class:`imagecat.data.Image`, optional. Images to be merged.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        New image containing the union of all input layers.
    """
    output = imagecat.data.Image()
    for input, value in sorted(inputs.items()):
        image = value()
        if isinstance(image, imagecat.data.Image):
            output.layers.update(image.layers)
    imagecat.operator.util.log_result(log, name, "merge", output)
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


def rename(graph, name, inputs):
    """Rename layers within an :ref:`image<images>`.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["image"][0]: :class:`imagecat.data.Image`, required. :ref:`Image<images>` containing image planes to be renamed.
        :["changes"][0]: :class:`dict`, optional. Maps existing names to new names.  Default: {}, which does nothing.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image with some layers renamed.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    changes = imagecat.operator.util.optional_input(name, inputs, "changes", type=dict, default={})

    output = imagecat.data.Image(layers={changes.get(name, name): layer for name, layer in image.layers.items()})
    imagecat.operator.util.log_result(log, name, "rename", output, changes=changes)
    return output


def rgb2gray(graph, name, inputs):
    """Convert :ref:`image<images>` layers from RGB color to grayscale.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["image"][0]: :class:`imagecat.data.Image`, required. Image containing layers to be converted.
        :["layers"][0]: :class:`str`, optional. Pattern matching the layers to be converted.  Default: '*', which converts all layers.
        :["weights"][0]: (red weight, green weight, blue weight) tuple, optional. Weights controlling how much each RGB component in a layer contributes to the output.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image with some layers converted to grayscale.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    layers = imagecat.operator.util.optional_input(name, inputs, "layers", type=str, default="*")
    weights = imagecat.operator.util.optional_input(name, inputs, "weights", type=imagecat.operator.util.array(shape=(3,)), default=[0.2125, 0.7154, 0.0721])

    output = imagecat.data.Image()
    for layer_name in image.match_layer_names(layers):
        layer = image.layers[layer_name]
        if layer.data.shape[2] != 3:
            continue
        output.layers[layer_name] = imagecat.data.Layer(data=numpy.dot(layer.data, weights)[:,:,None])
    imagecat.operator.util.log_result(log, name, "rgb2gray", output, layers=layers, weights=weights)
    return output


def save(graph, name, inputs):
    """Save an :ref:`image<images>` to a file.

    The file saver plugins in :mod:`imagecat.io` are used to save specific
    file formats.  See that module for details, and to write savers of your
    own.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :class:`dict`, required
        Inputs for this function, including:

        :["image"][0]: :class:`imagecat.data.Image`, required. Image to be saved.
        :["path"][0]: :class:`str`, required. Filesystem path of the file to be saved.
        :["layers"][0]: :class:`str`, optional. Pattern matching the layers to be saved.  Default: '*', which saves all layers.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    path = imagecat.operator.util.require_input(name, inputs, "path", type=str)
    layers = imagecat.operator.util.optional_input(name, inputs, "layers", type=str, default="*")

    layer_names = image.match_layer_names(layers)
    for saver in imagecat.io.savers:
        if saver(name, image, layer_names, path):
            return
    raise RuntimeError(f"Task {task} could not save 'image' to disk.") # pragma: no cover


def resize(graph, name, inputs):
    """Resize an :ref:`image<images>` to a new resolution.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["image"][0]: :class:`imagecat.data.Image`, required. Image to be resized.
        :["order"][0]: :any:`int`, optional.  Resampling filter order.  Default: '3' for bicubic resampling.
        :["res"][0]: (width, height) tuple, optional. New resolution of the image along each dimension.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image that has been resized.
    """
    import skimage.transform

    image = imagecat.operator.util.require_image(name, inputs, "image")
    order = imagecat.operator.util.optional_input(name, inputs, "order", type=int, default=3)
    res = imagecat.operator.util.optional_input(name, inputs, "res", default=("1w", "1h"))

    output = imagecat.data.Image()
    for layername, layer in image.layers.items():
        width = int(imagecat.units.length(res[0], layer.res))
        height = int(imagecat.units.length(res[1], layer.res))
        data = skimage.transform.resize(layer.data.astype(numpy.float32), (height, width), anti_aliasing=True, order=order).astype(layer.data.dtype)
        output.layers[layername] = layer.copy(data=data)
    imagecat.operator.util.log_result(log, name, "resize", output, order=order, res=res)
    return output


def text(graph, name, inputs):
    """Generate an image containing text.

    Parameters
    ----------
    graph: :ref:`graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :ref:`named-inputs`, required
        Inputs for this function, containing:

        :"anchor": :class:`str`, optional. Anchor point for text placement, defined at https://pillow.readthedocs.io/en/latest/handbook/text-anchors.html#text-anchors. Defaults to `"mm"`.
        :"fontindex": integer, optional. Index of the font to use within a multi-font file.  Defaults to `0`.
        :"fontname": :class:`str`, optional. Path to a font file.  Defaults to :func:`imagecat.data.default_font`.
        :"fontsize": Size of the rendered font.  Default: `"0.33h"`, which is one-third the height of the output image.
        :"layer": :class:`str`, optional.  Name of the generated layer.  Default: `["A"]`.
        :"position": (x, y) tuple, optional.  Position of the text anchor relative to the output image.  Default: `["0.5w", "0.5h"]`, which is centered vertically and horizontally.
        :"res": (width, height) tuple, optional. Resolution of the output image.  Default: [256, 256].
        :"string": :class:`str`, optional. String to be rendered.  Default: `"Text!"`.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        New image containing rendered text.
    """
    import PIL.Image
    import PIL.ImageDraw
    import PIL.ImageFont

    anchor = imagecat.operator.util.optional_input(name, inputs, "anchor", type=str, default="mm")
    fontindex = imagecat.operator.util.optional_input(name, inputs, "fontindex", type=int, default=0)
    fontname = imagecat.operator.util.optional_input(name, inputs, "fontname", type=str, default=imagecat.data.default_font())
    fontsize = imagecat.operator.util.optional_input(name, inputs, "fontsize", default="0.33h")
    layer = imagecat.operator.util.optional_input(name, inputs, "layer", type=str, default="A")
    position = imagecat.operator.util.optional_input(name, inputs, "position", default=("0.5w", "0.5h"))
    res = imagecat.operator.util.optional_input(name, inputs, "res", type=imagecat.operator.util.array(shape=(2,), dtype=int), default=[256, 256])
    string = imagecat.operator.util.optional_input(name, inputs, "string", type=str, default="Text!")

    fontsize_px = int(imagecat.units.length(fontsize, res))
    x = imagecat.units.length(position[0], res)
    y = res[1] - imagecat.units.length(position[1], res) # +Y = up

    pil_image = PIL.Image.new("L", (res[0], res[1]), 0)
    font = PIL.ImageFont.truetype(fontname, fontsize_px, fontindex)
    draw = PIL.ImageDraw.Draw(pil_image)
    draw.text((x, y), string, font=font, fill=255, anchor=anchor)

    data = numpy.array(pil_image, dtype=numpy.float16)[:,:,None] / 255.0
    output = imagecat.data.Image({layer: imagecat.data.Layer(data=data)})
    imagecat.operator.util.log_result(log, name, "text", output, anchor=anchor, fontindex=fontindex, fontname=fontname, fontsize=fontsize, layer=layer, position=position, res=res, string=string)
    return output


def uniform(graph, name, inputs):
    """Generate an :ref:`image<images>` containing random values drawn from a uniform distribution.

    Parameters
    ----------
    graph: :ref:`graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :ref:`named-inputs`, required
        Inputs for this function, containing:

        :"components": sequence of :class:`str`, optional. Component names for the layer to be created, which also implicitly define the number of components.  Default: :any:`None`, which creates a single component named `""` (i.e. for use as a mask).
        :"high": number, optional.  Highest value in the generated noise.  Default: 1.
        :"layer": :class:`str`, optional. Name of the layer to be created.  Default: 'A'.
        :"low": number, optional.  Lowest value for the generated noise.  Default: 0.
        :"role": :class:`imagecat.data.Role`. Role for the layer to be created. Default: :class:`imagecat.data.Role.NONE`.
        :"seed": :any:`int`. Random seed for the random noise function. Default: 1234.
        :"res": (width, height) tuple, optional. Resolution of the new image along each dimension.  Default: [256, 256].

    Returns
    -------
    image: :class:`imagecat.data.Image`
        New image with one layer containing uniform noise.
    """
    components = imagecat.operator.util.optional_input(name, inputs, "components", default=None)
    high = imagecat.operator.util.optional_input(name, inputs, "high", type=float, default=1)
    layer = imagecat.operator.util.optional_input(name, inputs, "layer", type=str, default="A")
    low = imagecat.operator.util.optional_input(name, inputs, "low", type=float, default=0)
    role = imagecat.operator.util.optional_input(name, inputs, "role", type=imagecat.data.Role, default=imagecat.data.Role.NONE)
    seed = imagecat.operator.util.optional_input(name, inputs, "seed", type=int, default=1234)
    res = imagecat.operator.util.optional_input(name, inputs, "res", type=imagecat.operator.util.array(shape=(2,), dtype=int), default=[256, 256])

    if components is None:
        components = [""]

    generator = numpy.random.default_rng(seed=seed)
    data = generator.uniform(low=low, high=high, size=(res[1], res[0], len(components))).astype(numpy.float16)
    output = imagecat.data.Image(layers={layer: imagecat.data.Layer(data=data, components=components, role=role)})
    imagecat.operator.util.log_result(log, name, "uniform", output, components=components, low=low, high=high, layer=layer, role=role, seed=seed, res=res)
    return output


from imagecat.operator.fill import fill
from imagecat.operator.remap import remap

import imagecat.operator.blur as blur
import imagecat.operator.cryptomatte as cryptomatte

