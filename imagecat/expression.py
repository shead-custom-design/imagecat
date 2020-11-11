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

"""Helper functions providing Imagecat-specific functionality for expression tasks.

The following builtin functions can be used in Imagecat expression tasks:

.. py:function:: graph()

.. py:function:: out(name)

.. py:function:: res(name)

.. py:function:: shape(name)

"""

import imagecat.data


def _graph(g):
    def graph():
        """Return the graph to which this task belongs."""
        return g
    return graph


def _out(graph):
    def out(name):
        """Return the output of task `name`."""
        return graph.output(name)
    return out


def _res(graph):
    def res(name):
        """Return a (width, height) tuple containing the resolution of the image output from task `name`."""
        image = graph.output(name)
        if not isinstance(image, imagecat.data.Image):
            raise ValueError(f"Not an image: {name}")
        for layer in image.layers.values():
            return layer.res
    return res

def _shape(graph):
    def shape(name):
        image = graph.output(name)
        if not isinstance(image, imagecat.data.Image):
            raise ValueError(f"Not an image: {name}")
        for layer in image.layers.values():
            return layer.shape
    return shape


def builtins(graph):
    """Return a dict containing functions that can be used in expressions.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        Graph that will contain the expression task to be executed.

    Returns
    -------
    builtins: dict
        Dict containing functions that can be used in expressions.
    """
    return {
        "graph": _graph(graph),
        "out": _out(graph),
        "res": _res(graph),
        "shape": _shape(graph),
    }
