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

"""Functions that generate and alter :ref:`image<images>` color.
"""

import functools
import logging

import numpy

import imagecat.data
import imagecat.operator.util
import imagecat.units

log = logging.getLogger(__name__)


def colormap(graph, name, inputs):
    """Convert single-channel layers to RGB layers using a colormap.

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
    image: :class:`imagecat.data.Image`, required
        Image with layer to be color mapped.
    inlayer: :class:`str`, optional
        `image` layer to be color mapped.  Default: :any:`None`.
    outlayer: :class:`str`, optional
        Name of the output image layer.  Default: ``"C"``.
    mapping: Python callable, optional
        Mapping function that accepts a shape `(rows, columns, 1)` array as input and
        produces an RGB `(rows, columns, 3)` shaped array as output.  If :any:`None`
        (the default), a linear map with a Color Brewer 2 Blue-Red palette will
        be used.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image with some layers mapped.
    """
    inlayer = imagecat.operator.util.optional_input(name, inputs, "inlayer", default=None)
    outlayer = imagecat.operator.util.optional_input(name, inputs, "outlayer", default="C")
    layer_name, layer = imagecat.operator.util.require_layer(name, inputs, "image", layer=inlayer, depth=1)
    mapping = imagecat.operator.util.optional_input(name, inputs, "mapping", default=None)

    if mapping is None:
        palette = imagecat.color.brewer.palette("BlueRed")
        mapping = functools.partial(imagecat.color.linear_map, palette=palette)

    data = mapping(layer.data[:,:,0])
    output = imagecat.data.Image(layers={outlayer: imagecat.data.Layer(data=data, role=imagecat.data.Role.RGB)})
    imagecat.operator.util.log_result(log, name, "colormap", output, inlayer=inlayer, outlayer=outlayer, mapping=mapping)
    return output


def dot(graph, name, inputs):
    """Compute the dot product of a :class:`image.data.Layer` and a matrix.

    This is most commonly used to convert an RGB layer to grayscale, but the
    operator is capable of converting any depth :math:`M` layer to depth
    :math:`N` using an :math:`M \\times N` matrix.  The values in each output
    channel will be a weighted sum of the input channels, using weights
    stored in the corresponding matrix column.

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
    image: :class:`imagecat.data.Image`, required
        Image containing layer to be converted.
    inlayer: :class:`str`, optional
        Layer to be converted.  Default: None.
    outlayer: :class:`str`, optional
        Output layer.  Default: "Y".
    outrole: :class:`imagecat.data.Role`, optional
        Role for the new layer.  Defaults to :class:`imagecat.data.role.LUMINANCE`.
    matrix: :math:`M \\times N` :class:`numpy.ndarray` matrix, optional
        Matrix controlling how much each input channel contributes to each output channel.
        Defaults to an RGB-to-grayscale matrix.  :math:`M` must match the depth of the
        input layer, and :math:`N` must match the expected depth of the output role.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        Image containing the new layer.
    """
    inlayer = imagecat.operator.util.optional_input(name, inputs, "inlayer", default=None)
    layer_name, layer = imagecat.operator.util.require_layer(name, inputs, "image", layer=inlayer)
    outdtype = imagecat.operator.util.optional_input(name, inputs, "outdtype", type=numpy.dtype, default=numpy.float16)
    outlayer = imagecat.operator.util.optional_input(name, inputs, "outlayer", type=str, default="Y")
    outrole = imagecat.operator.util.optional_input(name, inputs, "outrole", type=imagecat.data.Role, default=imagecat.data.Role.LUMINANCE)
    matrix = imagecat.operator.util.optional_input(name, inputs, "matrix", type=imagecat.operator.util.array(ndim=2), default=[[0.2125], [0.7154], [0.0721]])

    data = numpy.dot(layer.data, matrix).astype(outdtype)
    image = imagecat.data.Image(layers={outlayer: imagecat.data.Layer(data=data, role=outrole)})
    imagecat.operator.util.log_result(log, name, "dot", image, inlayer=inlayer, outdtype=outdtype, outlayer=outlayer, outrole=outrole, matrix=matrix)
    return image


def fill(graph, name, inputs):
    """Generate an :ref:`image<images>` with a single solid-color layer.

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

    layer: :class:`str`, optional
        New layer name.  Default: `"C"`.
    res: (width, height) tuple, optional
        Resolution of the new image.  Default: `(256, 256)`.
    role: :class:`imagecat.data.Role`, optional
        Semantic role of the new layer.  Default: :class:`imagecat.data.Role.RGB`.
    values: sequence of values, optional
        Values for the new layer.  The number of values must be appropriate for `role`.  Default: [1, 1, 1].

    Returns
    -------
    image: :class:`imagecat.data.Image`
        New image with a single solid-color layer.
    """
    layer = imagecat.operator.util.optional_input(name, inputs, "layer", type=str, default="C")
    res = imagecat.operator.util.optional_input(name, inputs, "res", type=imagecat.operator.util.array(shape=(2,), dtype=int), default=[256, 256])
    role = imagecat.operator.util.optional_input(name, inputs, "role", type=imagecat.data.Role, default=imagecat.data.Role.RGB)
    values = imagecat.operator.util.optional_input(name, inputs, "values", type=numpy.array, default=[1, 1, 1])

    data = numpy.full((res[1], res[0], len(values)), values, dtype=numpy.float16)
    output = imagecat.data.Image(layers={layer: imagecat.data.Layer(data=data, role=role)})
    imagecat.operator.util.log_result(log, name, "fill", output, layer=layer, role=role, res=res, values=values)
    return output
