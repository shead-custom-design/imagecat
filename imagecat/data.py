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

import collections
import enum
import fnmatch

import numpy


# Warning!  Moving this to another module will break *.icp file loading.
class Image(object):
    def __init__(self, layers=None):
        if layers is None:
            layers = {}
        first_layer = None
        for key, layer in layers.items():
            if not isinstance(key, str):
                raise ValueError(f"{key} is not a valid layer name.")
            if not isinstance(layer, Layer):
                raise ValueError(f"{layer} is not a valid Layer instance.")
            if first_layer is None:
                first_layer = layer
            else:
                if layer.data.shape[:2] != first_layer.data.shape[:2]:
                    raise ValueError("All layers must have the same resolution.")
        self._layers = layers

    def __repr__(self):
        layers = (f"{k}: {v!r}" for k, v in self._layers.items())
        return f"Image({', '.join(layers)})"

    @property
    def layers(self):
        return self._layers


    def match_layer_names(self, patterns):
        return match_layer_names(self.layers.keys(), patterns)


# Warning!  Moving this to another module will break *.icp file loading.
class Layer(object):
    def __init__(self, *, data, components=None, role=None):
        if not isinstance(data, numpy.ndarray):
            raise ValueError("Layer data must be an instance of numpy.ndarray.")
        if data.ndim != 3:
            raise ValueError("Layer data must have three dimensions.")

        if role is None:
            if data.shape[2] == 3:
                role = Role.RGB
            else:
                role = Role.NONE
        if not isinstance(role, Role):
            raise ValueError("Layer role must be an instance of imagecat.storage.Role.")

        if components is None:
            if data.shape[2] == 1:
                components = [""]
            elif data.shape[2] == 3 and role == Role.RGB:
                components = ["r", "g", "b"]
            else:
                components = []
        if len(components) != data.shape[2]:
            raise ValueError(f"Expected {data.shape[2]} layer components, received {len(components)}.")

        self.data = data
        self.components = components
        self.role = role

    def __repr__(self):
        return f"Layer({self.data.shape[1]}x{self.data.shape[0]}x{self.data.shape[2]} {self.data.dtype} {self.components} {self.role})"

    @property
    def res(self):
        return self.data.shape[1], self.data.shape[0]

    @property
    def shape(self):
        return self.data.shape

    def modify(self, data=None, components=None, role=None):
        data = self.data if data is None else data
        components = self.components if components is None else components
        role = self.role if role is None else role
        return Layer(data=data, components=components, role=role)


# Warning!  Moving this to another module will break *.icp file loading.
class Role(enum.Enum):
    NONE = 0
    RGB = 1


def channels_to_layers(channels):
     layers = [channel.rsplit(".", 1) for channel in channels]
     #log.debug(f"layers: {layers}")
     layers = [layer if len(layer) > 1 else ["", layer[0]] for layer in layers]
     #log.debug(f"layers: {layers}")
     layers = [(channel, layer, component) for channel, (layer, component) in zip(channels, layers)]
     #log.debug(f"layers: {layers}")
     groups = collections.defaultdict(list)
     for channel, layer, component in layers:
         groups[layer].append((channel, component))
     layers = list(groups.items())
     #log.debug(f"layers: {layers}")

 #    def split_layers(layers):
 #        for layer, channels in layers:
 #            if layer:
 #                yield (layer, channels)
 #                continue
 #            ci_components = [component.lower() for component, channel in channels]
 #            if "r" in ci_components and "g" in ci_components and "b" in ci_components:
 #                yield (layer, [channels[ci_components.index("r")], channels[ci_components.index("g")], channels[ci_components.index("b")]])
 #            channels = [channel for channel, ci_component in zip(channels, ci_components) if ci_component not in "rgb"]
 #            for channel in channels:
 #                yield layer, [channel]
 #    layers = list(split_layers(layers))

     def organize_layers(layers):
         for layer, components in layers:
             ci_components = [component.lower() for channel, component in components]
             for collection in ["rgb", "hsv", "hsb", "xy", "xyz", "uv", "uvw"]:
                 if sorted(ci_components) == sorted(collection):
                     components = [components[ci_components.index(component)] for component in collection]
             yield layer, components
     layers = list(organize_layers(layers))
     #log.debug(f"layers: {layers}")

     def categorize_layers(layers):
         for layer, components in layers:
             ci_components = [component.lower() for channel, component in components]
             if ci_components == ["r", "g", "b"]:
                 yield layer, components, Role.RGB
             else:
                 yield layer, components, Role.NONE
     layers = list(categorize_layers(layers))
     #log.debug(f"layers: {layers}")

     return layers


def match_layer_names(names, patterns):
    """Match image layers against a pattern.

    Use this function implementing tasks that can operate on multiple image
    layers.  `patterns` is a :class:`str` that can contain multiple whitespace
    delimited patterns.  Patterns can include ``"*"`` which matches everything, ``"?"``
    to match a single character, ``"[seq]"`` to match any character in seq, and ``"[!seq]"``
    to match any character not in seq.

    Parameters
    ----------
    names: :class:`Image` or sequence of :class:`str`, required
        The :ref:`image<images>` layer names to be matched.
    pattern: :class:`str`, required
        Whitespace delimited collection of patterns to match against layer names.

    Returns
    -------
    names: sequence of :class:`str` layer names that match `patterns`.
    """
    output = []
    for name in names:
        for pattern in patterns.split():
            if fnmatch.fnmatchcase(name, pattern):
                output.append(name)
                break
    return output

