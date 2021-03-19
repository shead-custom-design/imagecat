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

"""Operators that generate :ref:`images<images>` containing noise.
"""

import logging

import numpy

import imagecat.data
import imagecat.operator.util

log = logging.getLogger(__name__)


def uniform(graph, name, inputs):
    """Generate an :ref:`image<images>` containing random values drawn from a uniform distribution.

    Parameters
    ----------
    graph: :ref:`graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :ref:`named-inputs`, required
        Inputs for this operator.

    Named Inputs
    ------------
    high: number, optional
        Highest value in the generated noise.  Default: 1.
    layer: :class:`str`, optional
        Name of the layer to be created.  Default: 'Y'.
    low: number, optional
        Lowest value for the generated noise.  Default: 0.
    role: :class:`imagecat.data.Role`, optional
        Role for the layer to be created. Default: :class:`imagecat.data.Role.LUMINANCE`.
    seed: :any:`int`, optional
        Random seed for the random noise function. Default: 1234.
    res: (width, height) tuple, optional
        Resolution of the new image along each dimension.  Default: [256, 256].

    Returns
    -------
    image: :class:`imagecat.data.Image`
        New image with one layer containing uniform noise.
    """
    high = imagecat.operator.util.optional_input(name, inputs, "high", type=float, default=1)
    layer = imagecat.operator.util.optional_input(name, inputs, "layer", type=str, default="Y")
    low = imagecat.operator.util.optional_input(name, inputs, "low", type=float, default=0)
    role = imagecat.operator.util.optional_input(name, inputs, "role", type=imagecat.data.Role, default=imagecat.data.Role.LUMINANCE)
    seed = imagecat.operator.util.optional_input(name, inputs, "seed", type=int, default=1234)
    res = imagecat.operator.util.optional_input(name, inputs, "res", type=imagecat.operator.util.array(shape=(2,), dtype=int), default=[256, 256])

    depth = imagecat.data.depth(role)

    generator = numpy.random.default_rng(seed=seed)
    data = generator.uniform(low=low, high=high, size=(res[1], res[0], depth)).astype(numpy.float16)
    output = imagecat.data.Image(layers={layer: imagecat.data.Layer(data=data, role=role)})
    imagecat.operator.util.log_result(log, name, "uniform", output, low=low, high=high, layer=layer, role=role, seed=seed, res=res)
    return output

