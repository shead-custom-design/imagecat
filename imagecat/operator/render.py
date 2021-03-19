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

"""Functions that generate new :ref:`image<images>` data.
"""

import logging

import numpy

import imagecat.data
import imagecat.operator.util
import imagecat.units

log = logging.getLogger(__name__)


def text(graph, name, inputs):
    """Generate an image containing text.

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
    anchor: :class:`str`, optional
        Anchor point for text placement, defined at https://pillow.readthedocs.io/en/latest/handbook/text-anchors.html#text-anchors. Defaults to `"mm"`.
    fontindex: integer, optional
        Index of the font to use within a multi-font file.  Defaults to `0`.
    fontname: :class:`str`, optional
        Path to a font file.  Defaults to :func:`imagecat.data.default_font`.
    fontsize: Size of the rendered font, optional
        Default: `"0.33h"`, which is one-third the height of the output image.
    layer: :class:`str`, optional
        Name of the generated layer.  Default: `["A"]`.
    position: (x, y) tuple, optional
        Position of the text anchor relative to the output image.  Default:
        `["0.5w", "0.5h"]`, which is centered vertically and horizontally.
    res: (width, height) tuple, optional
        Resolution of the output image.  Default: [256, 256].
    string: :class:`str`, optional
        String to be rendered.  Default: `"Text!"`.

    Returns
    -------
    image: :class:`imagecat.data.Image`
        New image containing rendered text.
    """
    import PIL.Image
    import PIL.ImageDraw
    import PIL.ImageFont

    anchor = imagecat.operator.util.optional_input(name, inputs, "anchor", type=str, default="mm")
    fontindex = imagecat.operator.util.optional_input(name, inputs, "fontindex", type=int, default=0)
    fontname = imagecat.operator.util.optional_input(name, inputs, "fontname", type=str, default=imagecat.data.default_font())
    fontsize = imagecat.operator.util.optional_input(name, inputs, "fontsize", default="0.33h")
    layer = imagecat.operator.util.optional_input(name, inputs, "layer", type=str, default="A")
    position = imagecat.operator.util.optional_input(name, inputs, "position", default=("0.5w", "0.5h"))
    res = imagecat.operator.util.optional_input(name, inputs, "res", type=imagecat.operator.util.array(shape=(2,), dtype=int), default=[256, 256])
    string = imagecat.operator.util.optional_input(name, inputs, "string", type=str, default="Text!")

    fontsize_px = int(imagecat.units.length(fontsize, res))
    x = imagecat.units.length(position[0], res)
    y = res[1] - imagecat.units.length(position[1], res) # +Y = up

    pil_image = PIL.Image.new("L", (res[0], res[1]), 0)
    font = PIL.ImageFont.truetype(fontname, fontsize_px, fontindex)
    draw = PIL.ImageDraw.Draw(pil_image)
    draw.text((x, y), string, font=font, fill=255, anchor=anchor)

    data = numpy.array(pil_image, dtype=numpy.float16)[:,:,None] / 255.0
    output = imagecat.data.Image({layer: imagecat.data.Layer(data=data, role=imagecat.data.Role.ALPHA)})
    imagecat.operator.util.log_result(log, name, "text", output, anchor=anchor, fontindex=fontindex, fontname=fontname, fontsize=fontsize, layer=layer, position=position, res=res, string=string)
    return output


