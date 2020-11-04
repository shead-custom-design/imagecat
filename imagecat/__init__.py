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


"""Image processing functionality based on Graphcat computational graphs, http://graphcat.readthedocs.io.
"""

__version__ = "0.1.0-dev"

import enum
import logging

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import graphcat
import numpy
import skimage.filters

import imagecat.io as io
import imagecat.units as units
import imagecat.util as util

log = logging.getLogger(__name__)

logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)


class Role(enum.Enum):
    NONE = 0
    RGB = 1


class Layer(object):
    def __init__(self, *, data, components=None, role=None):
        if not isinstance(data, numpy.ndarray):
            raise ValueError("Layer data must be an instance of numpy.ndarray.")
        if data.ndim != 3:
            raise ValueError("Layer data must have three dimensions.")

        if role is None:
            if data.shape[2] == 3:
                role = Role.RGB
            else:
                role = Role.NONE
        if not isinstance(role, Role):
            raise ValueError("Layer role must be an instance of imagecat.util.Role.")

        if components is None:
            if data.shape[2] == 1:
                components = [""]
            elif data.shape[2] == 3 and role == Role.RGB:
                components = ["r", "g", "b"]
            else:
                components = []
        if len(components) != data.shape[2]:
            raise ValueError(f"Expected {data.shape[2]} layer components, received {len(components)}.")

        self.data = data
        self.components = components
        self.role = role

    def __repr__(self):
        return f"Layer({self.data.shape[1]}x{self.data.shape[0]}x{self.data.shape[2]} {self.data.dtype} {self.components} {self.role})"

    @property
    def res(self):
        return self.data.shape[1], self.data.shape[0]

    @property
    def shape(self):
        return self.data.shape

    def modify(self, data=None, components=None, role=None):
        data = self.data if data is None else data
        components = self.components if components is None else components
        role = self.role if role is None else role
        return Layer(data=data, components=components, role=role)



class Image(object):
    def __init__(self, layers={}):
        first_layer = None
        for key, layer in layers.items():
            if not isinstance(key, str):
                raise ValueError(f"{key} is not a valid layer name.")
            if not isinstance(layer, Layer):
                raise ValueError(f"{layer} is not a valid Layer instance.")
            if first_layer is None:
                first_layer = layer
            else:
                if layer.data.shape[:2] != first_layer.data.shape[:2]:
                    raise ValueError("All layers must have the same resolution.")
        self._layers = layers

    def __repr__(self):
        layers = (f"{k}: {v!r}" for k, v in self._layers.items())
        return f"Image({','.join(layers)})"

    @property
    def layers(self):
        return self._layers


################################################################################################
# Helper functions


def add_operation(graph, name, fn, **parameters):
    """Simplify setting-up tasks with parameters.

    Virtually all non-trivial Imagecat operations have parameters that affect
    their operation.  Because individually creating parameter tasks and linking
    them with the main task is tiresome and verbose, use this function instead.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        The Graphcat graph where the new task will be created.
    name: :class:`str`, required
        The name of the new task.
    fn: callable, required
        The Imagecat operation to use for the new task.
    parameters: additional keyword arguments, optional
        Each extra keyword argument will be turned into a parameter
        task and linked with the main task.  Each parameter name
        is created by concatenating `name` with the keyword name,
        separated by a slash "/".

    Returns
    -------
    name: :class:`str`
        Name of the newly-created operation, which may be different than `name`.
    """
    name = util.unique_name(graph, name)
    graph.add_task(name, fn)
    for pname, pvalue in parameters.items():
        ptname = util.unique_name(graph, f"{name}/{pname}")
        graph.set_parameter(name, pname, ptname, pvalue)
    return name


def set_expression(graph, name, expression, locals={}):
    def res(graph, dimension):
        def implementation(name):
            image = graph.output(name)
            if not util.is_image(image):
                raise ValueError(f"Not an image: {name}")
            for plane in image.values():
                return plane.shape[dimension]
        return implementation

    builtins = {
        "xres": res(graph, 1),
        "yres": res(graph, 0),
        }
    builtins.update(locals)
    graph.set_expression(name, expression, builtins)


################################################################################################
# Task functions


def composite(name, inputs):
    bglayer = util.optional_input(name, inputs, "bglayer", index=0, type=str, default="C")
    fglayer = util.optional_input(name, inputs, "fglayer", index=0, type=str, default="C")
    masklayer = util.optional_input(name, inputs, "masklayer", index=0, type=str, default="A")
    orientation = util.optional_input(name, inputs, "orientation", index=0, type=float, default=0)
    position = util.optional_input(name, inputs, "position", index=0, default=["0.5vw", "0.5vh"])

    background = util.require_layer(name, inputs, "background", index=0, layer=bglayer)
    foreground = util.require_layer(name, inputs, "foreground", index=0, layer=fglayer)
    mask = util.require_layer(name, inputs, "mask", index=0, layer=masklayer, components=1)

    transformed_foreground = util.transform(foreground.data, background.data.shape, orientation=orientation, position=position)
    transformed_mask = util.transform(mask.data, background.data.shape, orientation=orientation, position=position)
    alpha = transformed_mask
    one_minus_alpha = 1 - alpha
    data = transformed_foreground * alpha + background.data * one_minus_alpha

    image = Image({"C": Layer(data=data, components=background.components, role=background.role)})
    util.log_operation(log, name, "composite", image, bglayer=bglayer, fglayer=fglayer, masklayer=masklayer, orientation=orientation, position=position)
    return image


def delete(name, inputs):
    """Delete image planes from an :ref:`image<images>`.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["image"][0]: :class:`dict`, required. :ref:`Image<images>` containing image planes to be deleted.
        :["planes"][0]: :class:`str`, optional. Controls which image planes are deleted.  Default: '*', which deletes all planes.

    Returns
    -------
    image: :class:`dict`
        A copy of the input :ref:`image<images>` with some image planes deleted.
    """
    image = util.require_image(name, inputs, "image", index=0)
    planes = util.optional_input(name, inputs, "planes", type=str, default="*")

    remove = set(util.match_planes(image.keys(), planes))
    remaining = {name: plane for name, plane in image.items() if name not in remove}
    return remaining


def gaussian(name, inputs):
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
    image = util.require_image(name, inputs, "image", index=0)
    layers = util.optional_input(name, inputs, "layers", type=str, default="*")
    radius = util.optional_input(name, inputs, "radius", default=["5px", "5px"])

    layer_names = list(util.match_layers(image.layers.keys(), layers))
    for layer_name in layer_names:
        layer = image.layers[layer_name]
        data = layer.data
        sigma = [
            units.length(radius[1], layer.res),
            units.length(radius[0], layer.res),
            ]
        data = numpy.atleast_3d(skimage.filters.gaussian(data, sigma=sigma, multichannel=True, preserve_range=True).astype(data.dtype))
        image.layers[layer_name] = layer.modify(data=data)
    util.log_operation(log, name, "gaussian", image, layers=layers, radius=radius)
    return image


def load(name, inputs):
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
    layers = util.optional_input(name, inputs, "layers", type=str, default="*")
    path = util.require_input(name, inputs, "path", type=str)

    for loader in io.loaders:
        image = loader(name, path, layers)
        if image is not None:
            util.log_operation(log, name, "load", image, layers=layers, path=path)
            return image

    raise RuntimeError(f"Task {task} could not load {path} from disk.")



def merge(name, inputs):
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
    image: :class:`imagecat.Image`
        New :ref:`image<images>` containing the union of all input images.
    """
    merged = Image()
    for input in sorted(inputs.keys()):
        for index in range(len(inputs[input])):
            image = inputs[input][index]
            if isinstance(image, Image):
                merged.layers.update(image.layers)
    util.log_operation(log, name, "merge", merged)
    return merged


def offset(name, inputs):
    image = util.require_image(name, inputs, "image", index=0)
    layers = util.optional_input(name, inputs, "layers", index=0, type=str, default="*")
    offset = util.optional_input(name, inputs, "offset", index=0, default=["0.5vw", "0.5vh"])

    layer_names = list(util.match_layers(image.layers.keys(), layers))
    for layer_name in layer_names:
        layer = image.layers[layer_name]
        data = layer.data
        xoffset = int(units.length(offset[0], layer.res))
        yoffset = -int(units.length(offset[1], layer.res)) # We always treat +Y as "up"
        data = numpy.roll(data, shift=(xoffset, yoffset), axis=(1, 0))
        image.layers[layer_name] = layer.modify(data=data)

    util.log_operation(log, name, "offset", image, layers=layers, offset=offset)
    return image


def rename(name, inputs):
    """Rename image planes within an :ref:`image<images>`.

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
    image = util.require_image(name, inputs, "image")
    changes = util.optional_input(name, inputs, "changes", type=dict, default={})

    renamed = {changes.get(name, name): plane for name, plane in image.items()}
    return renamed


def rgb2gray(name, inputs):
    image = util.require_image(name, inputs, "image", index=0)
    layers = util.optional_input(name, inputs, "layers", type=str, default="*")
    weights = util.optional_input(name, inputs, "weights", type=util.array(shape=(3,)), default=[0.2125, 0.7154, 0.0721])
    for name in util.match_layers(image.layers.keys(), layers):
        layer = image.layers[name]
        if layer.data.shape[2] != 3:
            continue
        image.layers[name] = Layer(data=numpy.dot(layer.data, weights)[:,:,None])
    util.log_operation(log, name, "rgb2gray", image, layers=layers, weights=weights)
    return image


def save(name, inputs):
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
    image = util.require_image(name, inputs, "image", index=0)
    path = util.require_input(name, inputs, "path", type=str)
    layers = util.optional_input(name, inputs, "layers", type=str, default="*")
    layer_names = list(util.match_layers(image.layers.keys(), layers))
    for saver in io.savers:
        if saver(name, image, layer_names, path):
            return
    raise RuntimeError(f"Task {task} could not save 'image' to disk.")


def scale(name, inputs):
    image = util.require_image(name, inputs, "image", index=0)
    order = util.optional_input(name, inputs, "order", type=int, default=3)
    size = util.optional_input(name, inputs, "size", default=("1vw", "1vh"))

    for layername, layer in image.layers.items():
        width = int(units.length(size[0], layer.res))
        height = int(units.length(size[1], layer.res))
        data = skimage.transform.resize(layer.data.astype(numpy.float32), (height, width), anti_aliasing=True, order=order).astype(layer.data.dtype)
        image.layers[layername] = layer.modify(data=data)
    util.log_operation(log, name, "scale", image, order=order, size=size)
    return image


def solid(name, inputs):
    components = util.optional_input(name, inputs, "components", default=["r", "g", "b"])
    layer = util.optional_input(name, inputs, "layer", type=str, default="C")
    size = util.optional_input(name, inputs, "size", type=util.array(shape=(2,), dtype=int), default=[256, 256])
    role = util.optional_input(name, inputs, "role", type=Role, default=Role.RGB)
    values = util.optional_input(name, inputs, "values", type=numpy.array, default=[1, 1, 1])

    if components and len(components) != len(values):
        raise ValueError("Number of components and number of values must match.")

    data = numpy.full((size[1], size[0], len(values)), values, dtype=numpy.float16)
    image = Image({layer: Layer(data=data, components=components, role=role)})
    util.log_operation(log, name, "solid", image, components=components, layer=layer, role=role, size=size, values=values)
    return image


def text(name, inputs):
    anchor = util.optional_input(name, inputs, "anchor", type=str, default="mm")
    fontindex = util.optional_input(name, inputs, "fontindex", type=int, default=0)
    fontname = util.optional_input(name, inputs, "fontname", type=str, default="Helvetica")
    fontsize = util.optional_input(name, inputs, "fontsize", default="32px")
    layer = util.optional_input(name, inputs, "layer", type=str, default="A")
    position = util.optional_input(name, inputs, "position", default=("0.5vw", "0.5vh"))
    size = util.optional_input(name, inputs, "size", type=util.array(shape=(2,), dtype=int), default=[256, 256])
    text = util.optional_input(name, inputs, "text", type=str, default="Text!")

    fontsize_px = int(units.length(fontsize, size))
    x = units.length(position[0], size)
    y = units.length(position[1], size)

    pil_image = PIL.Image.new("L", (size[0], size[1]), 0)
    font = PIL.ImageFont.truetype(fontname, fontsize_px, fontindex)
    draw = PIL.ImageDraw.Draw(pil_image)
    draw.text((x, y), text, font=font, fill=255, anchor=anchor)

    data = numpy.array(pil_image, dtype=numpy.float16)[:,:,None] / 255.0
    image = Image({layer: Layer(data=data)})
    util.log_operation(log, name, "text", image, anchor=anchor, fontindex=fontindex, fontname=fontname, fontsize=fontsize, layer=layer, position=position, size=size, text=text)
    return image


