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
import functools
import io
import os

import numpy

try:
    import PIL.Image
except:
    pass

import imagecat.color
import imagecat.require


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
    def __init__(self, layers=None, metadata=None):
        if layers is None:
            layers = {}
        if metadata is None:
            metadata = {}

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
        self._metadata = metadata


    def __repr__(self):
        layers = (f"{k}: {v!r}" for k, v in self._layers.items())
        return f"Image({', '.join(layers)})"


    def copy(self, layers=None, metadata=None):
        """return a shallow copy of the image, with optional modifications.

        Returns a new instance of :class:`Image` that can be altered without
        modifying the original.  Note that the new image will references the
        same `layers` as the original, unless a new set of layers are supplied
        as an argument.

        Parameters
        ----------
        layers: :class:`dict`, optional
            Dictionary mapping :class:`str` layer names to :class:`Layer` instances that
            contain the data for each layer.  Replaces the original layers if not :any:`None` (the default).

        Returns
        -------
        image: :class:`Image`
            The new image instance with optional modifications.
        """
        layers = dict(self.layers) if layers is None else layers
        metadata = dict(self.metadata) if metadata is None else metadata
        return Image(layers=layers, metadata=metadata)


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


    @property
    def metadata(self):
        return self._metadata


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
    role: :class:`Role`, optional
        Semantic purpose of the layer.  If :any:`None` (the default), an
        attempt will be made to infer the role from context.

    See Also
    --------
    :ref:`images`
        For an in-depth discussion of how images are stored in Imagecat.
    """
    def __init__(self, *, data, role=None):
        if not isinstance(data, numpy.ndarray):
            raise ValueError("Layer data must be an instance of numpy.ndarray.") # pragma: no cover
        if data.ndim != 3:
            raise ValueError("Layer data must have three dimensions.") # pragma: no cover

        if role is None:
            role = Role.NONE
        if not isinstance(role, Role):
            raise ValueError("Layer role must be an instance of imagecat.data.Role.") # pragma: no cover

        role_depth = depth(role)
        if role_depth is not None and data.shape[2] != role_depth:
            raise ValueError(f"Expected {role_depth} components, received {data.shape[2]}.")

        self.data = data
        self.role = role


    def __repr__(self):
        return f"Layer({self.role} {self.data.shape[1]}x{self.data.shape[0]}x{self.data.shape[2]} {self.data.dtype})"


    @property
    def components(self):
        if self.role == Role.RGB:
            return ["R", "G", "B"]
        elif self.role == Role.REDGREEN:
            return ["R", "G"]
        elif self.role == Role.GREENBLUE:
            return ["G", "B"]
        elif self.role == Role.REDBLUE:
            return ["R", "B"]
        elif self.role == Role.RED:
            return ["R"]
        elif self.role == Role.GREEN:
            return ["G"]
        elif self.role == Role.BLUE:
            return ["B"]
        elif self.role == Role.ALPHA:
            return ["A"]
        elif self.role == Role.MATTE:
            return ["M"]
        elif self.role == Role.LUMINANCE:
            return ["Y"]
        elif self.role == Role.DEPTH:
            return ["Z"]
        elif self.role == Role.NONE:
            return [str(index) for index in range(self.data.shape[2])]
        raise RuntimeError(f"Unknown role: {self.role}")


    def copy(self, data=None, role=None):
        """Return a shallow copy of the layer, with optional modifications.

        This method returns a new instance of :class:`Layer` that can be altered
        without modifying the original.  Note that the new layer still references
        the same `data` as the original, unless a new data array is supplied as
        an argument.

        Parameters
        ----------
        data: :class:`numpy.ndarray`, optional
            Replaces the existing data array in the new layer, if not :any:`None` (the default).
        role: :class:`Role`, optional
            Replaces the existing role in the new layer, if not :any:`None` (the default).

        Returns
        -------
        layer: :class:`Layer`
            The new layer instance with modifications.
        """
        data = self.data if data is None else data
        role = self.role if role is None else role
        return Layer(data=data, role=role)


    @property
    def dtype(self):
        return self.data.dtype


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


    def _repr_png_(self):
        stream = io.BytesIO()
        to_pil(self).save(stream, "PNG")
        return stream.getvalue()


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
    """Indicates that a layer contains red-green-blue color information."""
    REDGREEN = 2
    """Indicates that a layer contains red-green color information."""
    GREENBLUE = 3
    """Indicates that a layer contains green-blue color information."""
    REDBLUE = 4
    """Indicates that a layer contains red-blue color information."""
    RED = 5
    """Indicates that a layer contains red color information."""
    GREEN = 6
    """Indicates that a layer contains green color information."""
    BLUE = 7
    """Indicates that a layer contains blue color information."""
    ALPHA = 8
    """Indicates that a layer contains alpha (opacity) information."""
    MATTE = 9
    """Indicates that a layer contains matte (selection / mask) information."""
    LUMINANCE = 10
    """Indicates that a layer contains luminance (intensity) information."""
    DEPTH = 11
    """Indicates that a layer contains depth (distance from viewer) information."""


def depth(role):
    if role in [Role.RGB]:
        return 3
    elif role in [Role.REDGREEN, Role.GREENBLUE, Role.REDBLUE]:
        return 2
    elif role in [Role.RED, Role.GREEN, Role.BLUE, Role.ALPHA, Role.MATTE, Role.LUMINANCE, Role.DEPTH]:
        return 1
    return None


def default_font():
    """Path to a default font file included with Imagecat.

    Returns
    -------
    path: :class:`str`
        Absolute path to the default Imagecat font.
    """
    data_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(data_dir, "LeagueSpartan-SemiBold.ttf")


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


@imagecat.require.loaded_module("PIL.Image")
def to_pil(layer):
    if not isinstance(layer, Layer):
        raise ValueError("Input must be an instance of imagecat.layer.Layer.")

    data = layer.data
    if layer.role in [Role.RGB, Role.REDGREEN, Role.GREENBLUE, Role.REDBLUE, Role.RED, Role.GREEN, Role.BLUE]:
        data = imagecat.color.linear_to_srgb(data)
        if layer.role != Role.RGB:
            black = numpy.zeros(data.shape[:2] + (1,))
            if layer.role == Role.REDGREEN:
                data = numpy.dstack((data[:,:,0], data[:,:,1], black))
            elif layer.role == Role.GREENBLUE:
                data = numpy.dstack((black, data[:,:,0], data[:,:,1]))
            elif layer.role == Role.REDBLUE:
                data = numpy.dstack((data[:,:,0], black, data[:,:,1]))
            elif layer.role == Role.RED:
                data = numpy.dstack((data[:,:,0], black, black))
            elif layer.role == Role.GREEN:
                data = numpy.dstack((black, data[:,:,0], black))
            elif layer.role == Role.BLUE:
                data = numpy.dstack((black, black, data[:,:,0]))
        data = (numpy.clip(data, 0, 1) * 255.0).astype(numpy.ubyte)
        return PIL.Image.fromarray(data)

    elif layer.role in [Role.ALPHA, Role.MATTE]:
        data = data[:,:,0]
        data = (numpy.clip(data, 0, 1) * 255.0).astype(numpy.ubyte)
        return PIL.Image.fromarray(data)

    elif layer.role in [Role.LUMINANCE, Role.DEPTH]:
        data = data[:,:,0]
        data = (numpy.clip(data, 0, 1) * 255.0).astype(numpy.ubyte)
        return PIL.Image.fromarray(data)

    elif layer.role in [Role.NONE] and layer.data.shape[2] == 1:
        data = data[:,:,0]
        data = (numpy.clip(data, 0, 1) * 255.0).astype(numpy.ubyte)
        return PIL.Image.fromarray(data)

