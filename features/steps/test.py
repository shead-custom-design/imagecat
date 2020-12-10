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

import unittest

import numpy.testing

import imagecat.data


def assert_equal(first, second, msg=None):
    return unittest.TestCase().assertEqual(first, second, msg)


def assert_raises(exception, *, msg=None):
    return unittest.TestCase().assertRaises(exception, msg=msg)


def assert_true(expr, msg=None):
    return unittest.TestCase().assertTrue(expr, msg)


def assert_layer_equal(lhs, rhs):
    if not isinstance(lhs, imagecat.data.Layer):
        raise ValueError("Left operand must be an instance of imagecat.data.Layer.")
    if not isinstance(rhs, imagecat.data.Layer):
        raise ValueError("Right operand must be an instance of imagecat.data.Layer.")
    assert_equal(lhs.data.dtype, rhs.data.dtype)
    numpy.testing.assert_allclose(lhs.data, rhs.data, rtol=0, atol=0.0005)
    assert_equal(lhs.role, rhs.role)


def assert_image_equal(lhs, rhs):
    if not isinstance(lhs, imagecat.data.Image):
        raise ValueError("lhs must be an instance of imagecat.data.Image.")
    if not isinstance(rhs, imagecat.data.Image):
        raise ValueError("rhs must be an instance of imagecat.data.Image.")
    if sorted(lhs.layers.keys()) != sorted(rhs.layers.keys()):
        raise ValueError(f"lhs channel names {lhs.layers.keys()} != rhs channel names {rhs.layers.keys()}")
    for name in lhs.layers.keys():
        assert_layer_equal(lhs.layers[name], rhs.layers[name])
