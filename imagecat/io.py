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

import logging
import os
import sys

import numpy
import skimage

import imagecat.color as color

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

def openexr_loader(task, path, planes):
    if "OpenEXR" not in sys.modules:
        return None

    extension = os.path.splitext(path)[1].lower()
    if extension != ".exr":
        return None

    reader = OpenEXR.InputFile(path)
    header = reader.header()
    width = header["dataWindow"].max.x - header["dataWindow"].min.x + 1
    height = header["dataWindow"].max.y - header["dataWindow"].min.y + 1

    image = {}
    for name, dtype in header["channels"].items():
        if dtype.type.v == Imath.PixelType.HALF:
            image[name] = numpy.frombuffer(reader.channel(name), dtype=numpy.float16).reshape((height, width, 1))
    return image


def pil_loader(task, path, planes):
    if "PIL.Image" not in sys.modules:
        return None

    if planes != "*":
        raise NotImplementedError()

    pil_image = PIL.Image.open(path)
    log.debug(pil_image.info)

    image = {}
    if pil_image.mode == "L":
        image["L"] = numpy.array(pil_image, dtype=numpy.float16) / 255.0
    if pil_image.mode == "RGB":
        image["C"] = color.srgb_to_linear(numpy.array(pil_image, dtype=numpy.float16) / 255.0)
    if pil_image.mode == "RGBA":
        image["C"] = color.srgb_to_linear(numpy.array(pil_image, dtype=numpy.float16)[:,:,0:3] / 255.0)
        image["A"] = numpy.array(pil_image, dtype=numpy.float16)[:,:,3:4] / 255.0
    return image


#####################################################################################33
# Savers

def openexr_saver(task, image, planes, path):
    if "OpenEXR" not in sys.modules:
        return False

    extension = os.path.splitext(path)[1].lower()
    if extension != ".exr":
        return False

    channels = {}
    pixels = {}
    for plane in planes:
        dtype = image[plane].dtype
        if dtype != numpy.float16:
            raise RuntimeError(f"Unexpected dtype: {dtype}")
        shape = image[plane].shape
        if shape[2] == 1:
            channels[f"{plane}"] = Imath.Channel(Imath.PixelType(Imath.PixelType.HALF))
            pixels[f"{plane}"] = image[plane][:,:,0].tobytes()
        elif shape[2] == 2:
            channels[f"{plane}.x"] = Imath.Channel(Imath.PixelType(Imath.PixelType.HALF))
            channels[f"{plane}.y"] = Imath.Channel(Imath.PixelType(Imath.PixelType.HALF))
            pixels[f"{plane}.x"] = image[plane][:,:,0].tobytes()
            pixels[f"{plane}.y"] = image[plane][:,:,1].tobytes()
        elif shape[2] == 3:
            channels[f"{plane}.r"] = Imath.Channel(Imath.PixelType(Imath.PixelType.HALF))
            channels[f"{plane}.g"] = Imath.Channel(Imath.PixelType(Imath.PixelType.HALF))
            channels[f"{plane}.b"] = Imath.Channel(Imath.PixelType(Imath.PixelType.HALF))
            pixels[f"{plane}.r"] = image[plane][:,:,0].tobytes()
            pixels[f"{plane}.g"] = image[plane][:,:,1].tobytes()
            pixels[f"{plane}.b"] = image[plane][:,:,2].tobytes()
        else:
            raise RuntimeError(f"Unexpected image plane depth: {shape[2]}")

    header = OpenEXR.Header(shape[1], shape[0])
    header["channels"] = channels
    log.debug(header)
    writer = OpenEXR.OutputFile(path, header)
    writer.writePixels(pixels)

    return True


def pil_saver(task, image, planes, path):
    if "PIL.Image" not in sys.modules:
        return False

    if len(planes) == 1:
        plane = image[planes[0]]
        if plane.shape[2] == 1:
            pil_image = PIL.Image.fromarray(skimage.img_as_ubyte(plane), mode="L")
        elif plane.shape[2] == 3:
            pil_image = PIL.Image.fromarray(skimage.img_as_ubyte(color.linear_to_srgb(plane)), mode="RGB")
        else:
            return False

    elif len(planes) == 2 and "C" in planes and "A" in planes:
        C = color.linear_to_srgb(image["C"])
        A = image["A"]
        pil_image = PIL.Image.fromarray(skimage.img_as_ubyte(numpy.depth_stack((C, A))), mode="RGBA")
    else:
        return False

    pil_image.save(path)
    return True


loaders = [
    openexr_loader,
    pil_loader,
]


savers = [
    openexr_saver,
    pil_saver,
]
