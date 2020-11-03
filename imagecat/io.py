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

import imagecat
import imagecat.color as color
import imagecat.util as util

try:
    import Imath
    import OpenEXR
except:
    pass

try:
    import PIL.Image
except:
    pass


log = logging.getLogger(__name__)

#####################################################################################33
# Loaders

def openexr_loader(task, path, layers):
    if "OpenEXR" not in sys.modules:
        return None

    extension = os.path.splitext(path)[1].lower()
    if extension != ".exr":
        return None

    if layers != "*":
        raise NotImplementedError("Layer matching not implemented.")

    reader = OpenEXR.InputFile(path)
    header = reader.header()
    width = header["dataWindow"].max.x - header["dataWindow"].min.x + 1
    height = header["dataWindow"].max.y - header["dataWindow"].min.y + 1

    image = imagecat.Image()
    layers = util.channels_to_layers(header["channels"].keys())
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
        image.layers[name] = imagecat.Layer(data=data, components=[component for channel, component in components], role=role)
    return image


def pickle_loader(task, path, layers):
    extension = os.path.splitext(path)[1].lower()
    if extension != ".icp":
        return None

    if layers != "*":
        raise NotImplementedError("Layer matching not implemented.")

    with bz2.open(path, "rb") as stream:
        image = pickle.load(stream)
    if not isinstance(image, imagecat.Image):
        raise RuntimeError("Not an Imagecat Pickle (*.icp) file.")
    return image


def pil_loader(task, path, layers):
    if "PIL.Image" not in sys.modules:
        return None

    if layers != "*":
        raise NotImplementedError("Layer matching not implemented.")

    pil_image = PIL.Image.open(path)
    log.debug(pil_image.info)

    image = imagecat.Image()
    if pil_image.mode == "L":
        image.layers["Y"] = imagecat.Layer(data=numpy.array(pil_image, dtype=numpy.float16) / 255.0)
    if pil_image.mode == "RGB":
        image.layers["C"] = imagecat.Layer(data=color.srgb_to_linear(numpy.array(pil_image, dtype=numpy.float16) / 255.0), role=imagecat.Role.RGB)
    if pil_image.mode == "RGBA":
        image.layers["C"] = imagecat.Layer(data=color.srgb_to_linear(numpy.array(pil_image, dtype=numpy.float16)[:,:,0:3] / 255.0), role=imagecat.Role.RGB)
        image.layers["A"] = imagecat.Layer(data=numpy.array(pil_image, dtype=numpy.float16)[:,:,3:4] / 255.0)
    return image


#####################################################################################33
# Savers

def openexr_saver(task, image, layers, path):
    if "OpenEXR" not in sys.modules:
        return False

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
    extension = os.path.splitext(path)[1].lower()
    if extension != ".icp":
        return False

    with bz2.open(path, "wb") as stream:
        pickle.dump(image, stream)
    return True


def pil_saver(task, image, layers, path):
    if "PIL.Image" not in sys.modules:
        return False

    if len(layers) == 1:
        layer = image.layers[layers[0]]
        if layer.data.shape[2] == 1:
            pil_image = PIL.Image.fromarray(skimage.img_as_ubyte(layer.data), mode="L")
        elif layer.data.shape[2] == 3 and layer.role == imagecat.Role.RGB:
            pil_image = PIL.Image.fromarray(skimage.img_as_ubyte(color.linear_to_srgb(layer.data)), mode="RGB")
        else:
            return False
    elif len(layers) == 2 and "C" in layers and "A" in layers:
        C = color.linear_to_srgb(image.layers["C"].data)
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


savers = [
    openexr_saver,
    pickle_saver,
    pil_saver,
]
