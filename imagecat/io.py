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


"""Helpers for implementing Imagecat I/O.
"""

import bz2
import collections
import logging
import os
import pickle
import sys

import numpy
import skimage

from imagecat.color import linear_to_srgb, srgb_to_linear
from imagecat.data import Image, Layer, Role, channels_to_layers

try:
    import Imath
    import OpenEXR
except: # pragma: no cover
    pass

try:
    import PIL.Image
except: # pragma: no cover
    pass


log = logging.getLogger(__name__)

#####################################################################################33
# Loaders

def openexr_loader(task, path, layers):
    """Image loader plugin for OpenEXR (.exr) files.

    Implemented using https://www.excamera.com/sphinx/articles-openexr.html

    Use :func:`imagecat.operator.load` to load images in an Imagecat workflow.
    """
    if "OpenEXR" not in sys.modules:
        return None # pragma: no cover

    extension = os.path.splitext(path)[1].lower()
    if extension != ".exr":
        return None

    if layers != "*":
        raise NotImplementedError("Layer matching not implemented.")

    reader = OpenEXR.InputFile(path)
    header = reader.header()
    width = header["dataWindow"].max.x - header["dataWindow"].min.x + 1
    height = header["dataWindow"].max.y - header["dataWindow"].min.y + 1

    image = Image()
    layers = channels_to_layers(header["channels"].keys())
    for name, components, role in layers:
        data = []
        for channel, component in components:
            dtype = header["channels"][channel]
            if dtype.type.v == Imath.PixelType.HALF:
                data.append(numpy.frombuffer(reader.channel(channel), dtype=numpy.float16).reshape((height, width)))
            elif dtype.type.v == Imath.PixelType.FLOAT:
                data.append(numpy.frombuffer(reader.channel(channel), dtype=numpy.float32).reshape((height, width)))
            elif dtype.type.v == Imath.PixelType.INT:
                data.append(numpy.frombuffer(reader.channel(channel), dtype=numpy.int32).reshape((height, width)))
        data = numpy.dstack(data)
        image.layers[name] = Layer(data=data, components=[component for channel, component in components], role=role)
    return image


def pickle_loader(task, path, layers):
    """Image loader plugin for Imagecat Pickle (.icp) files.

    The .icp format serializes an Imagecat image as a gzip2-compressed Python
    pickle object.  It is primarily used in testing, and is **not** recommended
    for general use.

    Use :func:`imagecat.operator.load` to load images in an Imagecat workflow.
    """
    extension = os.path.splitext(path)[1].lower()
    if extension != ".icp":
        return None

    if layers != "*":
        raise NotImplementedError("Layer matching not implemented.")

    with bz2.open(path, "rb") as stream:
        image = pickle.load(stream)
    if not isinstance(image, Image):
        raise RuntimeError("Not an Imagecat Pickle (*.icp) file.") # pragma: no cover
    return image


def pil_loader(task, path, layers):
    """Image loader plugin that uses Pillow for file I/O.

    Loads any file format supported by Pillow, https://pillow.readthedocs.io.

    Use :func:`imagecat.operator.load` to load images in an Imagecat workflow.
    """
    if "PIL.Image" not in sys.modules:
        return None # pragma: no cover

    if layers != "*":
        raise NotImplementedError("Layer matching not implemented.")

    pil_image = PIL.Image.open(path)
    log.debug(pil_image.info)

    image = Image()
    if pil_image.mode == "L":
        image.layers["Y"] = Layer(data=numpy.array(pil_image, dtype=numpy.float16) / 255.0)
    if pil_image.mode == "RGB":
        image.layers["C"] = Layer(data=srgb_to_linear(numpy.array(pil_image, dtype=numpy.float16) / 255.0), role=Role.RGB)
    if pil_image.mode == "RGBA":
        image.layers["C"] = Layer(data=srgb_to_linear(numpy.array(pil_image, dtype=numpy.float16)[:,:,0:3] / 255.0), role=Role.RGB)
        image.layers["A"] = Layer(data=numpy.array(pil_image, dtype=numpy.float16)[:,:,3:4] / 255.0)
    return image


#####################################################################################33
# Savers

def openexr_saver(task, image, layers, path):
    """Image saver plugin for OpenEXR (.exr) files.

    Implemented using https://www.excamera.com/sphinx/articles-openexr.html

    Use :func:`imagecat.operator.save` to save images in an Imagecat workflow.
    """
    if "OpenEXR" not in sys.modules:
        return False # pragma: no cover

    extension = os.path.splitext(path)[1].lower()
    if extension != ".exr":
        return False

    channels = {}
    pixels = {}
    for layer_name in layers:
        layer = image.layers[layer_name]
        dtype = layer.data.dtype
        shape = layer.data.shape
        for index, component in enumerate(layer.components):
            channel_name = f"{layer_name}.{component}" if component else f"{layer_name}"
            if dtype == numpy.float16:
                channels[channel_name] = Imath.Channel(Imath.PixelType(Imath.PixelType.HALF))
            elif dtype == numpy.float32:
                channels[channel_name] = Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT))
            elif dtype == numpy.int32:
                channels[channel_name] = Imath.Channel(Imath.PixelType(Imath.PixelType.INT))
            else:
                raise ValueError(f"Unsupported dtype: {dtype}")
            pixels[channel_name] = layer.data[:,:,index].tobytes()

    header = OpenEXR.Header(shape[1], shape[0])
    header["channels"] = channels
    writer = OpenEXR.OutputFile(path, header)
    writer.writePixels(pixels)

    return True


def pickle_saver(task, image, layers, path):
    """Image saver plugin for Imagecat Pickle (.icp) files.

    The .icp format serializes an Imagecat image as a gzip2-compressed Python
    pickle object.  It is primarily used in testing, and is **not** recommended
    for general use.

    Use :func:`imagecat.operator.save` to save images in an Imagecat workflow.
    """
    extension = os.path.splitext(path)[1].lower()
    if extension != ".icp":
        return False

    with bz2.open(path, "wb") as stream:
        pickle.dump(image, stream)
    return True


def pil_saver(task, image, layers, path):
    """Image saver plugin that uses Pillow for file I/O.

    Saves any file format supported by Pillow, https://pillow.readthedocs.io.

    Use :func:`imagecat.operator.save` to save images in an Imagecat workflow.
    """
    if "PIL.Image" not in sys.modules:
        return False # pragma: no cover

    if len(layers) == 1:
        layer = image.layers[layers[0]]
        if layer.data.shape[2] == 1:
            pil_image = PIL.Image.fromarray(skimage.img_as_ubyte(layer.data[:,:,0]), mode="L")
        elif layer.data.shape[2] == 3 and layer.role == Role.RGB:
            pil_image = PIL.Image.fromarray(skimage.img_as_ubyte(linear_to_srgb(layer.data)), mode="RGB")
        else:
            return False
    elif len(layers) == 2 and "C" in layers and "A" in layers:
        C = linear_to_srgb(image.layers["C"].data)
        A = image.layers["A"].data
        pil_image = PIL.Image.fromarray(skimage.img_as_ubyte(numpy.dstack((C, A))), mode="RGBA")
    else:
        return False

    pil_image.save(path)
    return True


loaders = [
    openexr_loader,
    pickle_loader,
    pil_loader,
]
"""List of available loader plugins.  In-house plugins may be prepended to this list for use with :func:`imagecat.operator.load`."""


savers = [
    openexr_saver,
    pickle_saver,
    pil_saver,
]
"""List of available saver plugins.  In-house plugins may be prepended to this list for use with :func:`imagecat.operator.save`."""
