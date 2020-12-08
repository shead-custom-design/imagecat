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

"""Operators for blurring :ref:`images<images>`.
"""

import logging

import numpy

import imagecat.data
import imagecat.operator.util
import imagecat.units

log = logging.getLogger(__name__)


def gaussian(graph, name, inputs):
    """Blur an :ref:`image<images>` using a Gaussian kernel.

    Parameters
    ----------
    graph: :ref:`graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :ref:`named-inputs`, required
        Inputs for this function, containing:

        :"image": :class:`imagecat.data.Image`, required. Image containing layers to be blurred.
        :"layers": :class:`str`, optional. Pattern matching the layers to be blurred.  Default: '*', which blurs all layers.
        :"sigma": (x, y) tuple, required. Width of the gaussian kernel in pixels along each dimension.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image with some layers blurred.
    """
    import skimage.filters

    image = imagecat.operator.util.require_image(name, inputs, "image")
    layers = imagecat.operator.util.optional_input(name, inputs, "layers", type=str, default="*")
    radius = imagecat.operator.util.optional_input(name, inputs, "radius", default=["5px", "5px"])

    output = imagecat.data.Image()
    for layer_name in image.match_layer_names(layers):
        layer = image.layers[layer_name]
        data = layer.data
        sigma = [
            imagecat.units.length(radius[1], layer.res),
            imagecat.units.length(radius[0], layer.res),
            ]
        data = numpy.atleast_3d(skimage.filters.gaussian(data, sigma=sigma, multichannel=True, preserve_range=True).astype(data.dtype))
        output.layers[layer_name] = layer.copy(data=data)
    imagecat.operator.util.log_result(log, name, "gaussian", output, layers=layers, radius=radius)
    return output

