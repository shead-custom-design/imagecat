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
import graphcat
import numpy
import skimage.color
import skimage.filters

log = logging.getLogger(__name__)

logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)


################################################################################################
# Helper functions

def match_planes(planes, patterns):
    for plane in planes:
        for pattern in patterns.split():
            if fnmatch.fnmatchcase(plane, pattern):
                yield plane
                break


def require_input(name, inputs, input, *, index=0, type=None, default=None):
    if input not in inputs:
        if default is not None:
            return default
        raise RuntimeError(f"Task {name} missing required input {input!r}.")
    if len(inputs[input]) <= index:
        if default is not None:
            return default
        raise RuntimeError(f"Task {name} missing required input {input!r} index {index}.")
    if type is not None and not isinstance(inputs[input][index], type):
        raise RuntimeError(f"Task {name} required input {input!r} index {index} is not a {type}.")
    return inputs[input][index]


def require_images(name, inputs, *, input=0, index=0):
    return dict(require_input(name, inputs, input=input, index=index, type=dict))


################################################################################################
# Task functions


def constant(name, inputs):
    plane = require_input(name, inputs, "plane", type=str, default="C")
    size = require_input(name, inputs, "size", type=tuple)
    value = require_input(name, inputs, "value", type=numpy.ndarray, default=numpy.ones(3, dtype=float))
    log.info(f"Task {name} generating constant plane {plane} size {size} value {value}")

    images = {}
    images[plane] = numpy.empty((size[1], size[0], len(value)))
    images[plane][:,:] = value
    return images


def file(name, inputs):
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
    images = require_images(name, inputs)
    patterns = require_input(name, inputs, "planes", type=str, default="*")
    sigma = require_input(name, inputs, "sigma", type=float)
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


def rgb2gray(name, inputs):
    images = require_images(name, inputs)
    patterns = require_input(name, inputs, "planes", type=str, default="*")
    for plane in match_planes(images.keys(), patterns):
        log.info(f"Task {name} rgb2gray plane {plane}")
        images[plane] = numpy.atleast_3d(skimage.color.rgb2gray(images[plane]))
    return images


def scale(name, inputs):
    images = require_images(name, inputs)
    patterns = require_input(name, inputs, "planes", type=str, default="*")
    order = require_input(name, inputs, "order", type=int, default=3)
    scale = require_input(name, inputs, "scale", type=tuple)
    for plane in match_planes(images.keys(), patterns):
        log.info(f"Task {name} resizing plane {plane} scale {scale} order {order}")
        images[plane] = skimage.transform.rescale(images[plane], (scale[0], scale[1], 1), anti_aliasing=True, order=order)
    return images

