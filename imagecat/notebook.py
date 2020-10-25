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

import imagecat.util as util


def display(image, planes="*", width=None, height=None):
    """Display :ref:`image<images>` inline in a Jupyter notebook.

    Parameters
    ----------
    image: :class:`dict`, required
        :ref:`Image<images>` to be displayed.
    planes: :class:`str`, optional
        Names of the image planes to display.  Use "*" (the default) to display all planes.
    width: :class:`str`, optional
        Optional HTML width for each image.
    height: :class:`str`, optional
        Optional HTML height for each image.
    """
    markup = "<div style='display: flex; flex-flow: row wrap; text-align: center'>"
    for name in sorted(util.match_planes(image.keys(), planes)):
        plane = image[name]
        pil_image = skimage.img_as_ubyte(plane)
        pil_image = numpy.squeeze(pil_image, 2) if pil_image.shape[2] == 1 else pil_image
        pil_image = PIL.Image.fromarray(pil_image)
        stream = io.BytesIO()
        pil_image.save(stream, "PNG")
        uri = "data:image/png;base64," + base64.standard_b64encode(stream.getvalue()).decode("ascii")

        markup += f"<figure style='margin: 5px'>"
        markup += f"<image src='{uri}' style='width:{width}; height:{height}'/>"
        markup += f"<figcaption>{name} <small>{plane.shape[1]}&times;{plane.shape[0]}&times;{plane.shape[2]} {plane.dtype}</small></figcaption>"
        markup += f"</figure>"
    markup += "</div>"

    IPython.display.display(IPython.display.HTML(markup))

