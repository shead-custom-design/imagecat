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
import imagecat.io
import imagecat.operator.util
import imagecat.units

log = logging.getLogger(__name__)


def delete(graph, name, inputs):
    """Delete layers from an :ref:`image<images>`.

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
        Image with layers to be deleted.
    layers: :class:`str`, optional
        Pattern matching the image layers are deleted.  Default: `"*"`, which
        deletes all layers.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image with some layers deleted.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    layers = imagecat.operator.util.optional_input(name, inputs, "layers", type=str, default="*")

    remove = image.match_layer_names(layers)
    output = imagecat.data.Image(layers={name: layer for name, layer in image.layers.items() if name not in remove})
    imagecat.operator.util.log_result(log, name, "delete", output, layers=layers)
    return output


def load(graph, name, inputs):
    """Load an :ref:`image<images>` from a file.

    The file loader plugins in :mod:`imagecat.io` are used to load specific
    file formats.  See that module for details, and to write loaders of your
    own.

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
    path: :class:`str`, required
        Filesystem path of the file to be loaded.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        Image loaded from the file.
    """
    layers = imagecat.operator.util.optional_input(name, inputs, "layers", type=str, default="*")
    path = imagecat.operator.util.require_input(name, inputs, "path", type=str)

    for loader in imagecat.io.loaders:
        output = loader(name, path, layers)
        if output is not None:
            imagecat.operator.util.log_result(log, name, "load", output, layers=layers, path=path)
            return output
    raise RuntimeError(f"Task {task} could not load {path} from disk.") # pragma: no cover


def merge(graph, name, inputs):
    """Merge multiple :ref:`images<images>` into one.

    This operator merges the layers from multiple images into a single image.
    The images must all have the same resolution.  Upstream inputs are merged
    in order, sorted by input name.  Later image layers with duplicate names
    will overwrite earlier layers.  Callers can prevent this by renaming layers
    upstream with the :func:`rename` operator.

    See Also
    --------
    :func:`imagecat.operator.transform.composite`
        Composites one image over another using a mask.

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
    every input: :class:`imagecat.data.Image`, optional
        Images to be merged.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        New image containing the union of all input layers.
    """
    output = imagecat.data.Image()
    for input, value in sorted(inputs.items()):
        image = value()
        if isinstance(image, imagecat.data.Image):
            output.layers.update(image.layers)
    imagecat.operator.util.log_result(log, name, "merge", output)
    return output


def remap(graph, name, inputs):
    """Merge and split layers from an :ref:`image<images>`.

    Parameters
    ----------
    graph: :ref:`graph`, required
        Graphcat graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :ref:`named-inputs`, required
        Inputs for this operator.

    Named Inputs
    ------------
    image: :class:`imagecat.data.Image`, required
        :ref:`Image<images>` containing image layers and channels to be mapped.
    mapping: :class:`dict`, optional
        Maps existing layers and channels to the output.  Default: {}, which returns an empty image.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A new image containing only the mapped layers and channels.
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
                layer, channel = layer
                data.append(image.layers[layer].data[:,:,channel])
        data=numpy.dstack(data)
        role = spec.get("role", None)
        layers[name] = imagecat.data.Layer(data=data, role=role)

    output = imagecat.data.Image(layers=layers)
    imagecat.operator.util.log_result(log, name, "remap", output, mapping=mapping)
    return output


def rename(graph, name, inputs):
    """Rename layers within an :ref:`image<images>`.

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
        :ref:`Image<images>` containing layers to be renamed.
    changes: :class:`dict`, optional
        Maps existing names to new names.  Default: {}, which does nothing.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        A copy of the input image with some layers renamed.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    changes = imagecat.operator.util.optional_input(name, inputs, "changes", type=dict, default={})

    output = imagecat.data.Image(layers={changes.get(name, name): layer for name, layer in image.layers.items()})
    imagecat.operator.util.log_result(log, name, "rename", output, changes=changes)
    return output


def save(graph, name, inputs):
    """Save an :ref:`image<images>` to a file.

    The file saver plugins in :mod:`imagecat.io` are used to save specific
    file formats.  See that module for details, and to write savers of your
    own.

    Parameters
    ----------
    graph: :ref:`graph`, required
        Graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :ref:`named-inputs`, required
        Inputs for this function, including:

    Named Inputs
    ------------
    image: :class:`imagecat.data.Image`, required
        Image to be saved.
    path": :class:`str`, required
        Filesystem path of the file to be saved.
    layers: :class:`str`, optional
        Pattern matching the layers to be saved.  Default: '*', which saves all layers.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    path = imagecat.operator.util.require_input(name, inputs, "path", type=str)
    layers = imagecat.operator.util.optional_input(name, inputs, "layers", type=str, default="*")

    layer_names = image.match_layer_names(layers)
    for saver in imagecat.io.savers:
        if saver(name, image, layer_names, path):
            return
    raise RuntimeError(f"Task {task} could not save 'image' to disk.") # pragma: no cover


import imagecat.operator.blur as blur
import imagecat.operator.color as color
import imagecat.operator.cryptomatte as cryptomatte
import imagecat.operator.noise as noise
import imagecat.operator.render as render
import imagecat.operator.transform as transform

