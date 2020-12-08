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

"""Functionality for manipulating images by merging and splitting layers."""

import logging

import numpy

import imagecat.data
import imagecat.operator.util

log = logging.getLogger(__name__)


def remap(graph, name, inputs):
    """Merge and split layers from an :ref:`image<images>`.

    Parameters
    ----------
    graph: :ref:`graph`, required
        Graphcat graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :ref:`named-inputs`, required
        Inputs for this function, containing:

        :"image": :class:`imagecat.data.Image`, required. :ref:`Image<images>` containing image layers and components to be remapped.
        :"mapping": :class:`dict`, optional. Maps existing layers and components to the output.  Default: {}, which returns an empty image.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image with remapped layers and components.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    mapping = imagecat.operator.util.optional_input(name, inputs, "mapping", type=dict, default={})

    layers = {}
    for name, spec in mapping.items():
        data = []
        for layer in spec.get("selection"):
            if isinstance(layer, str):
                data.append(image.layers[layer].data)
            elif isinstance(layer, tuple):
                layer, component = layer
                index = image.layers[layer].components.index(component)
                data.append(image.layers[layer].data[:,:,index])
        data=numpy.dstack(data)
        components = spec.get("components", None)
        role = spec.get("role", None)
        layers[name] = imagecat.data.Layer(data=data, components=components, role=role)

    output = imagecat.data.Image(layers=layers)
    imagecat.operator.util.log_result(log, name, "remap", output, mapping=mapping)
    return output

