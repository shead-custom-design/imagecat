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

import numpy
import skimage

log = logging.getLogger(__name__)


def openexr_saver(task, image, planes, path):
    extension = os.path.splitext(path)[1].lower()
    if extension != ".exr":
        return False

    try:
        import Imath
        import OpenEXR
    except:
        return False

    shape = image[planes[0]].shape
    header = OpenEXR.Header(shape[1], shape[0])
    header["channels"] = {channel: Imath.Channel(Imath.PixelType(Imath.PixelType.HALF)) for channel in "RGB"}
    writer = OpenEXR.OutputFile(path, header)
    writer.writePixels({
        "R": image[planes[0]][:,:,0].astype(numpy.float16).tobytes(),
        "G": image[planes[0]][:,:,1].astype(numpy.float16).tobytes(),
        "B": image[planes[0]][:,:,2].astype(numpy.float16).tobytes(),
    })

    return True

    return False


def pil_saver(task, image, planes, path):
    try:
        import PIL.Image
    except:
        return False

    if len(planes) == 1:
        plane = planes[0]
        image = image[plane]
        image = PIL.Image.fromarray(skimage.img_as_ubyte(image))
        image.save(path)
        log.info(f"Task {task} saved planes {planes} to {path}")
        return True

    if len(planes) == 2 and "C" in planes and "A" in planes:
        raise NotImplementedError()

    return False


savers = [
    openexr_saver,
    pil_saver,
    ]
