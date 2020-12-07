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

"""Functionality for working with Cryptomattes, see https://github.com/Psyop/Cryptomatte."""

import itertools
import logging
import re
import struct

import mmh3
import numpy

import imagecat.data
import imagecat.operator.util

log = logging.getLogger(__name__)


# Adapted from the Cryptomatte 1.2 specification:
# https://github.com/Psyop/Cryptomatte/blob/master/specification/cryptomatte_specification.pdf
# Accessed December 5, 2020.
def _name_to_float32(name):
    """Convert a string to an 8-digit hexadecimal Cryptomatte ID."""
    hash_32 = mmh3.hash(name, signed=False)
    exp = hash_32 >> 23 & 255
    if (exp == 0) or (exp == 255):
        hash_32 ^= 1 << 23
    packed = struct.pack("<L", hash_32 & 0xffffffff)
    return struct.unpack("<f", packed)[0]


def decoder(graph, name, inputs):
    """Extract matte(s) from an :ref:`image<images>` containing Cryptomatte data.

    Parameters
    ----------
    graph: :ref:`graph`, required
        Graphcat graph that owns this task.
    name: hashable object, required
        Name of the task executing this function.
    inputs: :ref:`named-inputs`, required
        Inputs for this function, containing:

        :"image": :class:`imagecat.data.Image`, required. :ref:`Image<images>` containing Cryptomatte data to be decoded.
        :"layer": :class:`str`, optional.  Matte layer name.  Default: `"matte"`.
        :"mattes": :class:`list` of :class:`str`, optional.  List of mattes to extract.  The output will contain the union of all the given mattes.  Default: [], which returns an empty matte.
        :"typename": :class:`str`, optional.  Name of the Cryptomatte data to extract.  Use this parameter to control which Cryptomatte to use, for images that contain multiple Cryptomattes.  Default: :any:`None`, which works with any image that contains one Cryptomatte.

    Returns
    -------
    matte: :class:`imagecat.data.Image`
        The extracted matte.
    """
    image = imagecat.operator.util.require_image(name, inputs, "image")
    layer = imagecat.operator.util.optional_input(name, inputs, "layer", type=str, default="matte")
    mattes = imagecat.operator.util.optional_input(name, inputs, "mattes", type=list, default=[])
    cryptomatte = imagecat.operator.util.optional_input(name, inputs, "cryptomatte", default=None)

    # Get the list of available Cryptomattes
    image_cryptomattes = []
    for key, value in image.metadata.items():
        match = re.fullmatch(r"cryptomatte/(.{7})/name", key)
        if match is not None:
            image_cryptomattes.append(value)

    data = None

    # For each Cryptomatte:
    for image_cryptomatte in image_cryptomattes:
        # Skip Cryptomattes that don't match the caller's request.
        if cryptomatte is not None and cryptomatte != image_cryptomatte:
            continue

        # Identify and sort the layers containing Cryptomatte data.
        cryptomatte_layers = []
        pattern = f"{image_cryptomatte}\\d{{2}}[.](red|green|blue|alpha|r|g|b|a)"
        for cryptomatte_layer in image.layers.keys():
            match = re.match(pattern, cryptomatte_layer)
            if match is not None:
                cryptomatte_layers.append(cryptomatte_layer)

        def component_key(channel):
            component = channel.rsplit(".", 1)[1]
            return {"red": 0, "r": 0, "green": 1, "g": 1, "blue": 2, "b": 2, "alpha": 3, "a": 3}.get(component)

        def layer_key(channel):
            return channel.rsplit(".", 1)[0]

        cryptomatte_layers = sorted(cryptomatte_layers, key=component_key)
        cryptomatte_layers = sorted(cryptomatte_layers, key=layer_key)

        # Extract the matte(s).
        for rank_id_layer, rank_coverage_layer in zip(cryptomatte_layers[0::2], cryptomatte_layers[1::2]):
            rank_id = image.layers[rank_id_layer].data
            rank_coverage = image.layers[rank_coverage_layer].data

            if data is None:
                data = numpy.zeros_like(rank_id)

            for matte in mattes:
                selection = rank_id == _name_to_float32(matte)
                data[selection] += rank_coverage[selection]

    output = imagecat.data.Image(layers={layer: imagecat.data.Layer(data=data)})
    imagecat.operator.util.log_result(log, name, "cryptomatte.decode", output, layer=layer, mattes=mattes, cryptomatte=cryptomatte)
    return output

