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

import fnmatch
import logging

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import graphcat
import numpy
import skimage.filters

import imagecat.io as io
import imagecat.util as util

log = logging.getLogger(__name__)

logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)


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
    bgplane = util.optional_input(name, inputs, "bgplane", index=0, type=str, default="C")
    background = util.require_plane(name, inputs, "background", index=0, plane=bgplane)
    fgplane = util.optional_input(name, inputs, "fgplane", index=0, type=str, default="C")
    foreground = util.require_plane(name, inputs, "foreground", index=0, plane=fgplane)
    maskplane = util.optional_input(name, inputs, "maskplane", index=0, type=str, default="A")
    mask = util.require_plane(name, inputs, "mask", index=0, plane=maskplane, channels=1)
    rotation = util.optional_input(name, inputs, "rotation", index=0, type=float, default=None)
    translation = util.optional_input(name, inputs, "translation", index=0, default=None)

    transformed_foreground = util.transform(foreground, background.shape, rotation=rotation, translation=translation)
    transformed_mask = util.transform(mask, background.shape, rotation=rotation, translation=translation)

    alpha = transformed_mask
    one_minus_alpha = 1 - alpha

    merged = {}
    merged["C"] = transformed_foreground * alpha + background * one_minus_alpha

    log.info(f"Task {name} comp {util.plane_repr(fgplane, foreground)} over {util.plane_repr(bgplane, background)} mask {util.plane_repr(maskplane, mask)} rotation {rotation} translation {translation} result {util.image_repr(merged)}")

    return merged


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
    planes = util.optional_input(name, inputs, "planes", type=str, default="*")
    sigma = util.require_input(name, inputs, "sigma", type=float)
    for plane in util.match_planes(image.keys(), planes):
        image[plane] = numpy.atleast_3d(skimage.filters.gaussian(image[plane], sigma=sigma, multichannel=True, preserve_range=True).astype(image[plane].dtype))
    log.info(f"Task {name} gaussian {planes} {sigma} result {util.image_repr(image)}")
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
    path = util.require_input(name, inputs, "path", type=str)
    planes = util.optional_input(name, inputs, "planes", type=str, default="*")
    for loader in io.loaders:
        image = loader(name, path, planes)
        if image is not None:
            log.info(f"Task {name} load {path} result {util.image_repr(image)}")
            return image
    raise RuntimeError(f"Task {task} could not load {path} from disk.")



def merge(name, inputs):
    """Merge multiple :ref:`images<images>` into one.

    Inputs are merged in order, sorted by input name and index.  Images with duplicate
    names will overwrite earlier images.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :[...][...]: :class:`dict`, optional. :ref:`Images<images>` to be merged.

    Returns
    -------
    image: :class:`dict`
        New :ref:`image<images>` containing the union of all input images.
    """
    merged = {}
    for input in sorted(inputs.keys()):
        for index in range(len(inputs[input])):
            image = inputs[input][index]
            if util.is_image(image):
                merged.update(image)
    log.info(f"Task {name} merge result {util.image_repr(merged)}")
    return merged


def offset(name, inputs):
    image = util.require_image(name, inputs, "image", index=0)
    offset = util.optional_input(name, inputs, "offset", index=0, type=numpy.array, default=[0, 0])
    planes = util.optional_input(name, inputs, "planes", index=0, type=str, default="*")

    for plane in util.match_planes(image.keys(), planes):
        image[plane] = numpy.roll(image[plane], shift=offset, axis=(1, 0))

    log.info(f"Task {name} offset {offset} {planes} result {util.image_repr(image)}")
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
    planes = util.optional_input(name, inputs, "planes", type=str, default="*")
    weights = util.optional_input(name, inputs, "weights", type=util.array(shape=(3,)), default=[0.2125, 0.7154, 0.0721])
    for plane in util.match_planes(image.keys(), planes):
        if util.is_plane(image[plane], channels=3):
            image[plane] = numpy.dot(image[plane], weights)[:,:,None]
    log.info(f"Task {name} rgb2gray {planes} {weights} result {util.image_repr(image)}")
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
    planes = util.optional_input(name, inputs, "planes", type=str, default="*")
    planes = list(util.match_planes(image.keys(), planes))
    for saver in io.savers:
        if saver(name, image, planes, path):
            return
    raise RuntimeError(f"Task {task} could not save 'image' to disk.")


def scale(name, inputs):
    image = util.require_image(name, inputs, "image", index=0)
    mode = util.optional_input(name, inputs, "mode", type=str, default="absolute")
    order = util.optional_input(name, inputs, "order", type=int, default=3)
    size = util.require_input(name, inputs, "size", type=util.array(shape=(2,)))
    for plane in image.keys():
        if mode == "absolute":
            image[plane] = skimage.transform.resize(image[plane].astype(numpy.float32), (size[1], size[0]), anti_aliasing=True, order=order).astype(numpy.float16)
        elif mode == "relative":
            image[plane] = skimage.transform.rescale(image[plane].astype(numpy.float32), (size[1], size[0], 1), anti_aliasing=True, order=order).astype(numpy.float16)
        else:
            raise RuntimeError(f"Task {task} unknown mode: {mode}")
    log.info(f"Task {name} scale mode {mode} order {order} plane {plane} size {size} result {util.image_repr(image)}")
    return image


def solid(name, inputs):
    plane = util.optional_input(name, inputs, "plane", type=str, default="C")
    size = util.require_input(name, inputs, "size")
    value = util.optional_input(name, inputs, "value", type=numpy.array, default=[1, 1, 1])

    image = {
        plane: numpy.full((size[1], size[0], len(value)), value, dtype=numpy.float16),
    }

    log.info(f"Task {name} solid {plane} {size} {value} result {util.image_repr(image)}")
    return image


def text(name, inputs):
    anchor = util.optional_input(name, inputs, "anchor", type=str, default="mm")
    fontindex = util.optional_input(name, inputs, "fontindex", type=int, default=0)
    fontname = util.optional_input(name, inputs, "fontname", type=str, default="Helvetica")
    fontsize = util.optional_input(name, inputs, "fontsize", type=int, default=32)
    plane = util.optional_input(name, inputs, "plane", type=str, default="A")
    position = util.optional_input(name, inputs, "position", default=None)
    size = util.require_input(name, inputs, "size")
    text = util.optional_input(name, inputs, "text", type=str, default="Text!")

    if position is None:
        position = (size[0] / 2, size[1] / 2)

    image = PIL.Image.new("L", size, 0)
    font = PIL.ImageFont.truetype(fontname, fontsize, fontindex)
    draw = PIL.ImageDraw.Draw(image)
    draw.text(position, text, font=font, fill=255, anchor=anchor)

    image = {
        plane: numpy.array(image, dtype=numpy.float16)[:,:,None] / 255.0,
    }

    log.info(f"Task {name} text anchor {anchor} fontindex {fontindex} fontname {fontname} fontsize {fontsize} plane {plane} position {position} size {size} result {util.image_repr(image)}")

    return image


