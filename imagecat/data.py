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

"""Functionality for manipulating images and related data structures.
"""

import collections
import enum
import fnmatch
import os

import numpy


# Warning!  Moving this to another module will break *.icp file loading.
class Image(object):
    """Storage for a multi-layer bitmap image.

    An Imagecat :class:`Image` is composed of zero-to-many layers, which are
    instances of :class:`Layer`.  Each layer is named, and all layer names must
    be unique.

    Parameters
    ----------
    layers: :class:`dict`, required
        Dictionary mapping :class:`str` layer names to :class:`Layer` instances that
        contain the data for each layer.  If :any:`None` (the default), creates
        an empty (no layers) image.

    See Also
    --------
    :ref:`images`
        For an in-depth discussion of how images are stored in Imagecat.
    """
    def __init__(self, layers=None):
        if layers is None:
            layers = {}
        first_layer = None
        for key, layer in layers.items():
            if not isinstance(key, str):
                raise ValueError(f"{key} is not a valid layer name.") # pragma: no cover
            if not isinstance(layer, Layer):
                raise ValueError(f"{layer} is not a valid Layer instance.") # pragma: no cover
            if first_layer is None:
                first_layer = layer
            else:
                if layer.data.shape[:2] != first_layer.data.shape[:2]:
                    raise ValueError("All layers must have the same resolution.") # pragma: no cover
        self._layers = layers

    def __repr__(self):
        layers = (f"{k}: {v!r}" for k, v in self._layers.items())
        return f"Image({', '.join(layers)})"

    @property
    def layers(self):
        """Access the :class:`dict` containing layers.

        Returns
        -------
        layers: :class:`dict`
            Dictionary mapping :class:`str` layer names to :class:`Layer` instances that
            contain the data for each layer.
        """
        return self._layers


    def match_layer_names(self, patterns):
        """Return layer names in this image that match the given patterns.

        See :func:`match_layer_names` for a description of the pattern syntax.

        Parameters
        ----------
        patterns: :class:`str`, required
            Patterns to match against this image's layer names.

        Returns
        -------
        layers: sequence of :class:`str`
            Layer names in this image that match `patterns`.
        """
        return match_layer_names(self.layers.keys(), patterns)


# Warning!  Moving this to another module will break *.icp file loading.
class Layer(object):
    """Storage for one layer in a bitmap image.

    An Imagecat :class:`Layer` contains the data and metadata that describe
    a single layer in an Imagecat :class:`Image`.  This includes the raw
    data itself, a set of names for each component in the data, and a role
    enumeration that describes the semantic purpose of the layer.

    Parameters
    ----------
    data: :class:`numpy.ndarray`, required
        A three dimensional :math:`M \\times N \\times C` array containing the
        layer data, organized into :math:`M` rows in top-to-bottom order,
        :math:`N` columns in left-to-right order, and :math:`C` components or
        channels.  The array dtype should be `numpy.float16` for most data,
        with `numpy.float32` and `numpy.int32` reserved for special cases such
        as depth maps and object id maps, respectively.
    components: sequence of :class:`str`, optional
        Component names for each of the :math:`C` components in the data.  If
        :any:`None` (the default), a set of component names will be inferred
        from context, but this process may fail.  Component names can be any
        strings, but good choices are `["r", "g", "b"]` for RGB color data,
        `["x", "y", "z"]` for vector / normal information, `["u", "v"]` for
        texture coordinates, and `[""]` for single-component layers like
        alphas or masks.
    role: :class:`Role`, optional
        Semantic purpose of the layer.  If :any:`None` (the default), an
        attempt will be made to infer the role from context.

    See Also
    --------
    :ref:`images`
        For an in-depth discussion of how images are stored in Imagecat.
    """
    def __init__(self, *, data, components=None, role=None):
        if not isinstance(data, numpy.ndarray):
            raise ValueError("Layer data must be an instance of numpy.ndarray.") # pragma: no cover
        if data.ndim != 3:
            raise ValueError("Layer data must have three dimensions.") # pragma: no cover

        if role is None:
            if data.shape[2] == 3:
                role = Role.RGB
            else:
                role = Role.NONE
        if not isinstance(role, Role):
            raise ValueError("Layer role must be an instance of imagecat.storage.Role.") # pragma: no cover

        if components is None:
            if data.shape[2] == 1:
                components = [""]
            elif data.shape[2] == 3 and role == Role.RGB:
                components = ["r", "g", "b"]
            else:
                components = []
        if len(components) != data.shape[2]:
            raise ValueError(f"Expected {data.shape[2]} layer components, received {len(components)}.") # pragma: no cover

        self.data = data
        self.components = components
        self.role = role

    def __repr__(self):
        return f"Layer({self.data.shape[1]}x{self.data.shape[0]}x{self.data.shape[2]} {self.data.dtype} {self.components} {self.role})"

    @property
    def res(self):
        """Layer resolution in x and y.

        Returns
        -------
        res: (width, height) :any:`tuple`
            The resolution of the layer, ignoring the number of components.
        """
        return self.data.shape[1], self.data.shape[0]

    @property
    def shape(self):
        """Shape of the underlying data array.

        Returns
        -------
        shape: (rows, columns, components) :any:`tuple`
        """
        return self.data.shape

    def copy(self, data=None, components=None, role=None):
        """Return a shallow copy of the layer, with optional modifications.

        This method returns a new instance of :class:`Layer` that can be altered
        without modifying the original.  Note that the new layer still references
        the same `data` as the original, unless a new data array is supplied as
        an argument.

        Parameters
        ----------
        data: :class:`numpy.ndarray`, optional
            Replaces the existing data array in the new layer, if not :any:`None` (the default).
        components: list of :class:`str`, optional
            Replaces the existing component names in the new layer, if not :any:`None` (the default).
        role: :class:`Role`, optional
            Replaces the existing role in the new layer, if not :any:`None` (the default).

        Returns
        -------
        layer: :class:`Layer`
            The new layer instance with modifications.
        """
        data = self.data if data is None else data
        components = self.components if components is None else components
        role = self.role if role is None else role
        return Layer(data=data, components=components, role=role)


# Warning!  Moving this to another module will break *.icp file loading.
class Role(enum.Enum):
    """Semantic description of how :class:`Layer` data should be interpreted.

    Because Imagecat allows an image to contain many types of data - not just
    colors - :class:`Role` is used to indicate how a given layer should be
    treated for operations such as visualization and file IO.

    See Also
    --------
    :ref:`images`
        For an in-depth discussion of how images are stored in Imagecat.
    """
    NONE = 0
    """General purpose catch-all for layers with no specific role."""
    RGB = 1
    """Indicates that a layer contains RGB information that e.g. should be
    converted to sRGB for display."""


def default_font():
    """Path to a default font file included with Imagecat.

    Returns
    -------
    path: :class:`str`
        Absolute path to the default Imagecat font.
    """
    data_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(data_dir, "LeagueSpartan-SemiBold.ttf")


def channels_to_layers(channels):
    """Convert a flat list of channel names into grouped layers compatible with Imagecat's data model.

    Some file formats such as OpenEXR split an image into a flat collection of named `channels`, where
    each channel is a 2D array and channels are implicitly grouped together by naming conventions, i.e.
    the channel name "C.r" represents the red component of layer "C".  This function converts a collection
    of channel names into layers with component names suitable for use in Imagecat, and also attempts to
    infer a :class:`Role` for each layer.

    Parameters
    ----------
    channels: sequence of :class:`str`, required
        Sequence of string channel names to be grouped into layers.

    Returns
    -------
    layers: sequence of (layer name, layer components, layer role) tuples
    """
    layers = [channel.rsplit(".", 1) for channel in channels]
    layers = [layer if len(layer) > 1 else ["", layer[0]] for layer in layers]
    layers = [(channel, layer, component) for channel, (layer, component) in zip(channels, layers)]
    groups = collections.defaultdict(list)
    for channel, layer, component in layers:
        groups[layer].append((channel, component))
    layers = list(groups.items())

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

    def categorize_layers(layers):
        for layer, components in layers:
            ci_components = [component.lower() for channel, component in components]
            if ci_components == ["r", "g", "b"]:
                yield layer, components, Role.RGB
            else:
                yield layer, components, Role.NONE
    layers = list(categorize_layers(layers))

    return layers


def match_layer_names(names, patterns):
    """Match image layer names against a pattern.

    Use this function to implement operators that operate on multiple image
    layers.  `patterns` is a :class:`str` that can contain multiple whitespace
    delimited patterns.  Patterns can include ``"*"`` which matches everything, ``"?"``
    to match a single character, ``"[seq]"`` to match any character in seq, and ``"[!seq]"``
    to match any character not in seq.

    Parameters
    ----------
    names: Sequence of :class:`str`, required
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

