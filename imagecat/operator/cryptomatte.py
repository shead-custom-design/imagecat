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


def _float32_to_int32(value):
    packed = struct.pack("<f", value)
    return struct.unpack("<L", packed)[0]


def decoder(graph, name, inputs):
    """Extract matte(s) from an :ref:`image<images>` containing Cryptomatte data.

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
    clown: :class:`bool`, optional
        If :any:`True`, extract a clown matte containing a unique color for the
        ID that has the greatest coverage in a given pixel.  Default:
        :any:`False`
    image: :class:`imagecat.data.Image`, required
        :ref:`Image<images>` containing Cryptomatte data to be decoded.
    layer: :class:`str`, optional
        Output matte layer name.  Default: `"M"`.
    mattes: :class:`list` of :class:`str`, optional
        List of mattes to extract.  The output will contain the union of all
        the given mattes.  Default: [], which returns an empty matte.
    cryptomatte: :class:`str`, optional
        Name of the Cryptomatte to extract.  Use this parameter to control
        which Cryptomatte to use, for images that contain multiple
        Cryptomattes.  Default: :any:`None`, which will match one Cryptomatte
        or raise an exception if there is more than one.

    Returns
    -------
    matte: :class:`imagecat.data.Image`
        The extracted matte.
    """
    clown = imagecat.operator.util.optional_input(name, inputs, "clown", type=bool, default=False)
    image = imagecat.operator.util.require_image(name, inputs, "image")
    layer = imagecat.operator.util.optional_input(name, inputs, "layer", type=str, default="M")
    mattes = imagecat.operator.util.optional_input(name, inputs, "mattes", type=list, default=[])
    cryptomatte = imagecat.operator.util.optional_input(name, inputs, "cryptomatte", default=None)

    # Get the list of available Cryptomattes
    cryptomatte_names = []
    for key, value in image.metadata.items():
        match = re.fullmatch(r"cryptomatte/(.{7})/name", key)
        if match is not None:
            cryptomatte_names.append(value)

    # Filter the available Cryptomattes.
    if cryptomatte is not None:
        cryptomatte_names = [cryptomatte_name for cryptomatte_name in cryptomatte_names if cryptomatte_name == cryptomatte]
    if not cryptomatte_names:
        raise RuntimeError("No matching Cryptomattes were found.")
    if len(cryptomatte_names) > 1:
        raise ValueError("A specific Cryptomatte must be chosen.")
    cryptomatte_name = cryptomatte_names[0]

    # Identify and sort the layers containing Cryptomatte data.
    pattern = f"{cryptomatte_name}\\d{{2}}[.](red|green|blue|alpha|r|g|b|a)"
    cryptomatte_layers = []
    for cryptomatte_layer in image.layers.keys():
        match = re.match(pattern, cryptomatte_layer, re.IGNORECASE)
        if match is not None:
            cryptomatte_layers.append(cryptomatte_layer)

    def channel_key(channel):
        channel = channel.rsplit(".", 1)[1].lower()
        return {"red":0, "r":0, "green":1, "g":1, "blue":2, "b":2, "alpha":3, "a":3}.get(channel)

    def layer_key(channel):
        return channel.rsplit(".", 1)[0]

    cryptomatte_layers = sorted(cryptomatte_layers, key=channel_key)
    cryptomatte_layers = sorted(cryptomatte_layers, key=layer_key)

    if not cryptomatte_layers:
        raise RuntimeError("No matching Cryptomatte layers were found.")

    # Extract a clown matte.
    if clown:
        for rank_id_layer, rank_coverage_layer in zip(cryptomatte_layers[0::2], cryptomatte_layers[1::2]):
            rank_ids = image.layers[rank_id_layer].data

            data = numpy.zeros((rank_ids.shape[0], rank_ids.shape[1], 3), dtype=numpy.float32)

            for matte in mattes:
                selection = (rank_ids == _name_to_float32(matte))[:,:,0]
                color = numpy.random.default_rng(_float32_to_int32(_name_to_float32(matte))).uniform(size=3)
                data[selection] = color

            output = imagecat.data.Image(layers={layer: imagecat.data.Layer(data=data, role=imagecat.data.Role.RGB)})
            break

    # Extract a regular matte.
    else:
        data = None

        for rank_id_layer, rank_coverage_layer in zip(cryptomatte_layers[0::2], cryptomatte_layers[1::2]):
            rank_ids = image.layers[rank_id_layer].data
            rank_coverage = image.layers[rank_coverage_layer].data

            if data is None:
                data = numpy.zeros_like(rank_ids)

            for matte in mattes:
                selection = rank_ids == _name_to_float32(matte)
                data[selection] += rank_coverage[selection]

        output = imagecat.data.Image(layers={layer: imagecat.data.Layer(data=data, role=imagecat.data.Role.MATTE)})

    imagecat.operator.util.log_result(log, name, "cryptomatte.decode", output, clown=clown, layer=layer, mattes=mattes, cryptomatte=cryptomatte)
    return output

