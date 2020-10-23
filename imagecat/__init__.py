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
    backgrounds = util.required_images(name, inputs, "background", index=0)
    fgplane = util.optional_input(name, inputs, "fgplane", index=0, type=str, default="C")
    foregrounds = util.required_images(name, inputs, "foreground", index=0)
    maskplane = util.optional_input(name, inputs, "maskplane", index=0, type=str, default="A")
    masks = util.required_images(name, inputs, "mask", index=0)
    rotation = util.optional_input(name, inputs, "rotation", index=0, type=float, default=None)
    translation = util.optional_input(name, inputs, "translation", index=0, default=None)

    foreground = foregrounds[fgplane]
    background = backgrounds[bgplane]
    mask = masks[maskplane]

    log.info(f"Task {name} comp foreground {fgplane} over background {bgplane} with mask {maskplane} rotation {rotation} translation {translation}")

    foreground = util.transform(foreground, background.shape, rotation=rotation, translation=translation)
    mask = util.transform(mask, background.shape, rotation=rotation, translation=translation)

    alpha = mask
    one_minus_alpha = 1 - alpha

    merged = {}
    merged["C"] = foreground * alpha + background * one_minus_alpha
    return merged


def delete(name, inputs):
    """Delete image planes from an :ref:`image collection<image-collections>`.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["images"][0]: :class:`dict`, required. :ref:`Image collection<image-collections>` containing image planes to be deleted.
        :["planes"][0]: :class:`str`, optional. Controls which image planes are deleted.  Default: '*', which deletes all images.

    Returns
    -------
    images: :class:`dict`
        A copy of the input :ref:`image collection<image-collections>` with some image planes deleted.
    """
    images = util.required_images(name, inputs, "images", index=0)
    patterns = util.optional_input(name, inputs, "planes", type=str, default="*")

    remove = set(util.match_planes(images.keys(), patterns))
    remaining = {key: value for key, value in images.items() if key not in remove}
    return remaining


def file(name, inputs):
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
    images: :class:`dict`
        :ref:`Image collection <image-collections>` containing image planes loaded from the file.
    """
    path = util.required_input(name, inputs, "path", type=str)

    path = inputs["path"][0]
    image = PIL.Image.open(path)
    log.info(f"Task {name} loaded {path} {image.mode} {image.size[0]}x{image.size[1]}")

    images = {}
    if image.mode == "L":
        images["C"] = numpy.array(image) / 255.0
    if image.mode == "RGB":
        images["C"] = numpy.array(image) / 255.0
    if image.mode == "RGBA":
        images["C"] = numpy.array(image)[:,:,0:3] / 255.0
        images["A"] = numpy.array(image)[:,:,3:4] / 255.0
    return images


def gaussian(name, inputs):
    """Blur images using a Gaussian kernel.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["images"][0]: :class:`dict`, required. :ref:`Image collection<image-collections>` containing images to be blurred.
        :["planes"][0]: :class:`str`, optional. Controls which image planes are blurred.  Default: '*', which blurs all images.
        :["sigma"][0]: number, required. Width of the gaussian kernel in pixels.

    Returns
    -------
    images: :class:`dict`
        A copy of the input :ref:`image collection<image-collections>` with some image planes blurred.
    """
    images = util.required_images(name, inputs, "images", index=0)
    patterns = util.optional_input(name, inputs, "planes", type=str, default="*")
    sigma = util.required_input(name, inputs, "sigma", type=float)
    for plane in util.match_planes(images.keys(), patterns):
        log.info(f"Task {name} gaussian blurring plane {plane} sigma {sigma}")
        images[plane] = numpy.atleast_3d(skimage.filters.gaussian(images[plane], sigma=sigma, multichannel=True, preserve_range=True))
    return images


def merge(name, inputs):
    """Merge multiple :ref:`image collections<image-collections>` into one.

    Inputs are merged in order, sorted by input name.  Images with duplicate
    names will overwrite earlier images.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :[...][...]: :class:`dict`, optional. :ref:`Image collections<image-collections>` to be merged.

    Returns
    -------
    images: :class:`dict`
        New :ref:`image collection<image-collections>` containing the union of all input images.
    """
    merged = {}
    for input in sorted(inputs.keys()):
        for index in range(len(inputs[input])):
            images = inputs[input][index]
            if isinstance(images, dict):
                log.info(f"Task {name} merging input {input} index {index} planes {list(images.keys())}")
                merged.update(images)
    return merged


def offset(name, inputs):
    images = util.required_images(name, inputs, "images", index=0)
    offset = util.optional_input(name, inputs, "offset", index=0, type=numpy.array, default=[0, 0])
    patterns = util.optional_input(name, inputs, "planes", index=0, type=str, default="*")

    for plane in util.match_planes(images.keys(), patterns):
        log.info(f"Task {name} offset {offset} plane {plane}")
        images[plane] = numpy.roll(images[plane], shift=offset, axis=(1, 0))
    return images


def rename(name, inputs):
    """Rename image planes within an :ref:`image collection<image-collections>`.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["images"][0]: :class:`dict`, required. :ref:`Image collection<image-collections>` containing image planes to be renamed.
        :["changes"][0]: :class:`dict`, optional. Maps existing names to new names.  Default: {}, which does nothing.

    Returns
    -------
    images: :class:`dict`
        A copy of the input :ref:`image collection<image-collections>` with some image planes renamed.
    """
    images = util.required_images(name, inputs, "images")
    changes = util.optional_input(name, inputs, "changes", type=dict, default={})

    renamed = {changes.get(key, key): value for key, value in images.items()}
    return renamed


def rgb2gray(name, inputs):
    images = util.required_images(name, inputs, "images", index=0)
    patterns = util.optional_input(name, inputs, "planes", type=str, default="*")
    for plane in util.match_planes(images.keys(), patterns):
        log.info(f"Task {name} rgb2gray plane {plane}")
        images[plane] = numpy.atleast_3d(skimage.color.rgb2gray(images[plane]))
    return images


def scale(name, inputs):
    images = util.required_images(name, inputs, "images", index=0)
    patterns = util.optional_input(name, inputs, "planes", type=str, default="*")
    order = util.optional_input(name, inputs, "order", type=int, default=3)
    scale = util.required_input(name, inputs, "scale", type=tuple)
    for plane in util.match_planes(images.keys(), patterns):
        log.info(f"Task {name} resizing plane {plane} scale {scale} order {order}")
        images[plane] = skimage.transform.rescale(images[plane], (scale[0], scale[1], 1), anti_aliasing=True, order=order)
    return images


def solid(name, inputs):
    plane = util.optional_input(name, inputs, "plane", type=str, default="C")
    size = util.required_input(name, inputs, "size")
    value = util.optional_input(name, inputs, "value", default=numpy.ones(3, dtype=float))
    log.info(f"Task {name} generating solid plane {plane} size {size} value {value}")

    images = {}
    images[plane] = numpy.full((size[1], size[0], len(value)), value, dtype=float)
    return images


def text(name, inputs):
    anchor = util.optional_input(name, inputs, "anchor", type=str, default="mm")
    fontindex = util.optional_input(name, inputs, "fontindex", type=int, default=0)
    fontname = util.optional_input(name, inputs, "fontname", type=str, default="Helvetica")
    fontsize = util.optional_input(name, inputs, "fontsize", type=int, default=32)
    plane = util.optional_input(name, inputs, "plane", type=str, default="A")
    position = util.optional_input(name, inputs, "position", default=None)
    size = util.required_input(name, inputs, "size")
    text = util.optional_input(name, inputs, "text", type=str, default="Text!")

    if position is None:
        position = (size[0] / 2, size[1] / 2)

    log.info(f"Task {name} generating text anchor {anchor} fontindex {fontindex} fontname {fontname} fontsize {fontsize} plane {plane} position {position} size {size}")

    image = PIL.Image.new("L", size, 0)
    font = PIL.ImageFont.truetype(fontname, fontsize, fontindex)
    draw = PIL.ImageDraw.Draw(image)
    draw.text(position, text, font=font, fill=255, anchor=anchor)

    images = {}
    images[plane] = numpy.array(image)[:,:,None] / 255.0
    return images


