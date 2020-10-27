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


"""Helpers for colorspace conversion.
"""

import numpy

def srgb_to_linear(image):
    """Convert an sRGB image to linear color.

    Acessed from https://entropymine.com/imageworsener/srgbformula
    """
    return numpy.where(image <= 0.04045, image / 12.92, numpy.power((image + 0.055) / 1.055, 2.4))


def linear_to_srgb(image):
    """Convert linear color image to sRGB.

    Acessed from https://entropymine.com/imageworsener/srgbformula
    """
    return numpy.where(image <= 0.0031308, image * 12.92, 1.055 * numpy.power(image, 1 / 2.4) - 0.055)


# Generated using https://www.colour-science.org:8010/apps/rgb_colourspace_transformation_matrix
#transformation_matrix = {
#    "sRGB/CAT02/ACEScg": numpy.array([
#        [ 0.6131178129,  0.3411819959,  0.0457873443],
#        [ 0.0699340823,  0.9181030375,  0.0119327755],
#        [ 0.0204629926,  0.1067686634,  0.8727159106],
#        ]),
#    "ACEScg/CAT02/sRGB": numpy.array([
#        [ 1.7048873310, -0.6241572745, -0.0808867739],
#        [-0.1295209353,  1.1383993260, -0.0087792418],
#        [-0.0241270599, -0.1246206123,  1.1488221099],
#        ]),
#}
