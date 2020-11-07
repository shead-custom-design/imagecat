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

"""Integration with Jupyter notebooks, https://jupyter.org"""

import base64
import io

import IPython.display
import PIL.Image
import numpy
import skimage

from imagecat.color import linear_to_srgb
from imagecat.data import Image, Role, match_layer_names


def display(image, layers="*", width=None, height=None):
    """Display :ref:`image<images>` inline in a Jupyter notebook.

    Parameters
    ----------
    image: :class:`dict`, required
        :ref:`Image<images>` to be displayed.
    layers: :class:`str`, optional
        Names of the image layers to display.  Use "*" (the default) to display all layers.
    width: :class:`str`, optional
        Optional HTML width for each image.
    height: :class:`str`, optional
        Optional HTML height for each image.
    """
    if not isinstance(image, Image):
        raise ValueError("Expected an instance of imagecat.Image.") # pragma: no cover

    markup = "<div style='display: flex; flex-flow: row wrap; text-align: center'>"
    for name in sorted(image.match_layer_names(layers)):
        layer = image.layers[name]
        data = layer.data
        if layer.role == Role.RGB:
            data = linear_to_srgb(data)

        stream = io.BytesIO()
        pil_image = skimage.img_as_ubyte(data)
        pil_image = numpy.squeeze(pil_image, 2) if pil_image.shape[2] == 1 else pil_image
        pil_image = PIL.Image.fromarray(pil_image)
        pil_image.save(stream, "PNG")
        uri = "data:image/png;base64," + base64.standard_b64encode(stream.getvalue()).decode("ascii")

        markup += f"<figure style='margin: 5px'>"
        markup += f"<image src='{uri}' style='width:{width}; height:{height}; box-shadow: 4px 4px 6px rgba(0, 0, 0, 0.5)'/>"
        markup += f"<figcaption>{name} <small>{data.shape[1]}&times;{data.shape[0]}&times;{data.shape[2]} {data.dtype} {layer.role}</small></figcaption>"
        markup += f"</figure>"
    markup += "</div>"

    IPython.display.display(IPython.display.HTML(markup))

