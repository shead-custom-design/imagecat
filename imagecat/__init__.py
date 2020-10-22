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

log = logging.getLogger(__name__)

logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)


################################################################################################
# Helper functions

def set_operation(graph, name, fn, **parameters):
    """Simplify setting-up tasks with parameters.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
    name: hashable object, required
    """
    graph.set_task(name, fn)
    for pname, pvalue in parameters.items():
        graph.set_parameter(name, pname, f"{name}/{pname}", pvalue)


def match_planes(planes, patterns):
    for plane in planes:
        for pattern in patterns.split():
            if fnmatch.fnmatchcase(plane, pattern):
                yield plane
                break


def optional_input(name, inputs, input, *, index=0, type=None, default=None):
    value = default
    if input in inputs and 0 <= index and index < len(inputs[input]):
        value = inputs[input][index]
    if type is not None:
        value = type(value)
    return value


def required_input(name, inputs, input, *, index=0, type=None):
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

################################################################################################
# Task functions


def composite(name, inputs):
    bgplane = optional_input(name, inputs, "bgplane", index=0, type=str, default="C")
    backgrounds = require_images(name, inputs, "background", index=0)
    fgplane = optional_input(name, inputs, "fgplane", index=0, type=str, default="C")
    foregrounds = require_images(name, inputs, "foreground", index=0)
    maskplane = optional_input(name, inputs, "maskplane", index=0, type=str, default="A")
    masks = require_images(name, inputs, "mask", index=0)
    rotation = optional_input(name, inputs, "rotation", index=0, type=float, default=None)
    translation = optional_input(name, inputs, "translation", index=0, default=None)

    foreground = foregrounds[fgplane]
    background = backgrounds[bgplane]
    mask = masks[maskplane]

    log.info(f"Task {name} comp foreground {fgplane} over background {bgplane} with mask {maskplane} rotation {rotation} translation {translation}")

    foreground = transform(foreground, background.shape, rotation=rotation, translation=translation)
    mask = transform(mask, background.shape, rotation=rotation, translation=translation)

    alpha = mask
    one_minus_alpha = 1 - alpha

    merged = {}
    merged["C"] = foreground * alpha + background * one_minus_alpha
    return merged


def file(name, inputs):
    """Load a file into memory.

    Parameters
    ----------
    name: hashable object, required
        Name of the task executing this function.
    inputs: :any:`dict`, required
        Inputs for this function, containing:

        :["path"][0]: Required. Filesystem path of the file to be loaded.
    """
    path = required_input(name, inputs, "path", type=str)

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

        :[0][0]: Required. Image collection containing images to be blurred.
        :["patterns"][0]: Optional. :any:`str` used to control which images are blurred.  Default: '*', which blurs all images.
        :["sigma"][0]: Required. Width of the gaussian kernel in pixels.
    """
    images = require_images(name, inputs, "image")
    patterns = optional_input(name, inputs, "planes", type=str, default="*")
    sigma = required_input(name, inputs, "sigma", type=float)
    for plane in match_planes(images.keys(), patterns):
        log.info(f"Task {name} gaussian blurring plane {plane} sigma {sigma}")
        images[plane] = numpy.atleast_3d(skimage.filters.gaussian(images[plane], sigma=sigma, multichannel=True, preserve_range=True))
    return images


def merge(name, inputs):
    merged = {}
    for input in sorted(inputs.keys()):
        if isinstance(input, int):
            images = require_images(name, inputs, input=input)
            log.info(f"Task {name} merging input {input} planes {list(images.keys())}")
            merged.update(images)
    return merged


def offset(name, inputs):
    images = require_images(name, inputs, "image", index=0)
    offset = optional_input(name, inputs, "offset", index=0, type=numpy.array, default=[0, 0])
    patterns = optional_input(name, inputs, "planes", index=0, type=str, default="*")

    for plane in match_planes(images.keys(), patterns):
        log.info(f"Task {name} offset {offset} plane {plane}")
        images[plane] = numpy.roll(images[plane], shift=offset, axis=(1, 0))
    return images


def rgb2gray(name, inputs):
    images = require_images(name, inputs)
    patterns = optional_input(name, inputs, "planes", type=str, default="*")
    for plane in match_planes(images.keys(), patterns):
        log.info(f"Task {name} rgb2gray plane {plane}")
        images[plane] = numpy.atleast_3d(skimage.color.rgb2gray(images[plane]))
    return images


def scale(name, inputs):
    images = require_images(name, inputs, "images", index=0)
    patterns = optional_input(name, inputs, "planes", type=str, default="*")
    order = optional_input(name, inputs, "order", type=int, default=3)
    scale = required_input(name, inputs, "scale", type=tuple)
    for plane in match_planes(images.keys(), patterns):
        log.info(f"Task {name} resizing plane {plane} scale {scale} order {order}")
        images[plane] = skimage.transform.rescale(images[plane], (scale[0], scale[1], 1), anti_aliasing=True, order=order)
    return images


def solid(name, inputs):
    plane = optional_input(name, inputs, "plane", type=str, default="C")
    size = required_input(name, inputs, "size")
    value = optional_input(name, inputs, "value", default=numpy.ones(3, dtype=float))
    log.info(f"Task {name} generating solid plane {plane} size {size} value {value}")

    images = {}
    images[plane] = numpy.full((size[1], size[0], len(value)), value, dtype=float)
    return images


def text(name, inputs):
    anchor = optional_input(name, inputs, "anchor", type=str, default="mm")
    fontindex = optional_input(name, inputs, "fontindex", type=int, default=0)
    fontname = optional_input(name, inputs, "fontname", type=str, default="Helvetica")
    fontsize = optional_input(name, inputs, "fontsize", type=int, default=32)
    plane = optional_input(name, inputs, "plane", type=str, default="A")
    position = optional_input(name, inputs, "position", default=None)
    size = required_input(name, inputs, "size")
    text = optional_input(name, inputs, "text", type=str, default="Text!")

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


