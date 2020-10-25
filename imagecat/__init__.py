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
import skimage.color
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


################################################################################################
# Task functions


def composite(name, inputs):
    bgplane = util.optional_input(name, inputs, "bgplane", index=0, type=str, default="C")
    background = util.require_plane(name, inputs, "background", index=0, plane=bgplane)
    fgplane = util.optional_input(name, inputs, "fgplane", index=0, type=str, default="C")
    foreground = util.require_plane(name, inputs, "foreground", index=0, plane=fgplane)
    maskplane = util.optional_input(name, inputs, "maskplane", index=0, type=str, default="A")
    mask = util.require_plane(name, inputs, "mask", index=0, plane=maskplane, channels=1, dtype=float)
    rotation = util.optional_input(name, inputs, "rotation", index=0, type=float, default=None)
    translation = util.optional_input(name, inputs, "translation", index=0, default=None)

    log.info(f"Task {name} comp foreground {fgplane} {foreground.shape} over background {bgplane} {background.shape} with mask {maskplane} {mask.shape}  rotation {rotation} translation {translation}")

    foreground = util.transform(foreground, background.shape, rotation=rotation, translation=translation)
    mask = util.transform(mask, background.shape, rotation=rotation, translation=translation)

    alpha = mask
    one_minus_alpha = 1 - alpha

    merged = {}
    merged["C"] = foreground * alpha + background * one_minus_alpha
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
    patterns = util.optional_input(name, inputs, "planes", type=str, default="*")

    remove = set(util.match_planes(image.keys(), patterns))
    remaining = {name: plane for name, plane in image.items() if name not in remove}
    return remaining


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

    pil_image = PIL.Image.open(path)
    log.info(f"Task {name} loaded {path} mode {pil_image.mode} {pil_image.size[0]}x{pil_image.size[1]}")

    image = {}
    if pil_image.mode == "L":
        image["C"] = numpy.array(pil_image) / 255.0
    if pil_image.mode == "RGB":
        image["C"] = numpy.array(pil_image) / 255.0
    if pil_image.mode == "RGBA":
        image["C"] = numpy.array(pil_image)[:,:,0:3] / 255.0
        image["A"] = numpy.array(pil_image)[:,:,3:4] / 255.0
    return image


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
    patterns = util.optional_input(name, inputs, "planes", type=str, default="*")
    sigma = util.require_input(name, inputs, "sigma", type=float)
    for plane in util.match_planes(image.keys(), patterns):
        log.info(f"Task {name} gaussian blurring plane {plane} sigma {sigma}")
        image[plane] = numpy.atleast_3d(skimage.filters.gaussian(image[plane], sigma=sigma, multichannel=True, preserve_range=True))
    return image


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
            if is_image(image):
                log.info(f"Task {name} merging input {input} index {index} planes {list(image.keys())}")
                merged.update(image)
    return merged


def offset(name, inputs):
    image = util.require_image(name, inputs, "image", index=0)
    offset = util.optional_input(name, inputs, "offset", index=0, type=numpy.array, default=[0, 0])
    patterns = util.optional_input(name, inputs, "planes", index=0, type=str, default="*")

    for plane in util.match_planes(image.keys(), patterns):
        log.info(f"Task {name} offset {offset} plane {plane}")
        image[plane] = numpy.roll(image[plane], shift=offset, axis=(1, 0))
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
    patterns = util.optional_input(name, inputs, "planes", type=str, default="*")
    weights = util.optional_input(name, inputs, "weights", type=util.array(shape=(3,)), default=[0.2125, 0.7154, 0.0721])
    for plane in util.match_planes(image.keys(), patterns):
        if util.is_plane(image[plane], channels=3, dtype=float):
            log.info(f"Task {name} rgb2gray plane {plane} weights {weights}")
            image[plane] = numpy.dot(image[plane], weights)[:,:,None]
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
    patterns = util.optional_input(name, inputs, "planes", type=str, default="*")

    planes = list(util.match_planes(image.keys(), patterns))

    for saver in io.savers:
        if saver(name, image, planes, path):
            return
    raise RuntimeError(f"Task {task} could not save 'image' to disk.")


def scale(name, inputs):
    image = util.require_image(name, inputs, "image", index=0)
    order = util.optional_input(name, inputs, "order", type=int, default=3)
    scale = util.require_input(name, inputs, "scale", type=util.array(shape=(2,)))
    for plane in image.keys():
        log.info(f"Task {name} resizing plane {plane} scale {scale} order {order}")
        image[plane] = skimage.transform.rescale(image[plane], (scale[0], scale[1], 1), anti_aliasing=True, order=order)
    return image


def solid(name, inputs):
    plane = util.optional_input(name, inputs, "plane", type=str, default="C")
    size = util.require_input(name, inputs, "size")
    value = util.optional_input(name, inputs, "value", type=numpy.array, default=[1, 1, 1])
    log.info(f"Task {name} generating solid plane {plane} size {size} value {value}")

    image = {
        plane: numpy.full((size[1], size[0], len(value)), value, dtype=float),
    }

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

    log.info(f"Task {name} generating text anchor {anchor} fontindex {fontindex} fontname {fontname} fontsize {fontsize} plane {plane} position {position} size {size}")

    image = PIL.Image.new("L", size, 0)
    font = PIL.ImageFont.truetype(fontname, fontsize, fontindex)
    draw = PIL.ImageDraw.Draw(image)
    draw.text(position, text, font=font, fill=255, anchor=anchor)

    image = {
        plane: numpy.array(image)[:,:,None] / 255.0,
    }
    return image


