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

"""Functions that produce, consume, and modify Imagecat :ref:`images<images>`.
"""

import logging

import numpy

import imagecat.data
import imagecat.operator.util

log = logging.getLogger(__name__)


def fill(graph, name, inputs):
    """Generate a :ref:`image<images>` with a single solid-color layer.

    Parameters
    ----------
    graph: :ref:`graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :ref:`named-inputs`, required
        Inputs for this function, containing:

        :"components": sequence of :class:`str`, optional. Component names for the new layer.  Defaults to `["r", "g", "b"]`.  The number of component names must match the number of values.
        :"layer": :class:`str`, optional. New layer name.  Default: `"C"`.
        :"res": (width, height) tuple, optional.  Resolution of the new image.  Default: [256, 256].
        :"role": :class:`imagecat.data.Role`, optional.  Semantic role of the new layer.  Default: :class:`imagecat.data.Role.RGB`.
        :"values": sequence of values, optional.  Solid color values for the new layer.  Default: [1, 1, 1].

    Returns
    -------
    image: :class:`imagecat.data.Image`
        New image with a single solid-color layer.
    """
    components = imagecat.operator.util.optional_input(name, inputs, "components", default=["r", "g", "b"])
    layer = imagecat.operator.util.optional_input(name, inputs, "layer", type=str, default="C")
    res = imagecat.operator.util.optional_input(name, inputs, "res", type=imagecat.operator.util.array(shape=(2,), dtype=int), default=[256, 256])
    role = imagecat.operator.util.optional_input(name, inputs, "role", type=imagecat.data.Role, default=imagecat.data.Role.RGB)
    values = imagecat.operator.util.optional_input(name, inputs, "values", type=numpy.array, default=[1, 1, 1])

    if components and len(components) != len(values):
        raise ValueError("Number of components and number of values must match.") # pragma: no cover

    data = numpy.full((res[1], res[0], len(values)), values, dtype=numpy.float16)
    output = imagecat.data.Image(layers={layer: imagecat.data.Layer(data=data, components=components, role=role)})
    imagecat.operator.util.log_result(log, name, "fill", output, components=components, layer=layer, role=role, res=res, values=values)
    return output

