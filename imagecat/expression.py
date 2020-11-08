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


import imagecat.data


def _graph(graph):
    def implementation():
        return graph
    return implementation


def _out(graph):
    def implementation(name):
        return graph.output(name)
    return implementation


def _res(graph):
    def implementation(name):
        image = graph.output(name)
        if not isinstance(image, imagecat.data.Image):
            raise ValueError(f"Not an image: {name}")
        for layer in image.layers.values():
            return layer.res
    return implementation

def _shape(graph):
    def implementation(name):
        image = graph.output(name)
        if not isinstance(image, imagecat.data.Image):
            raise ValueError(f"Not an image: {name}")
        for layer in image.layers.values():
            return layer.shape
    return implementation


def builtins(graph):
    return {
        "graph": _graph(graph),
        "out": _out(graph),
        "res": _res(graph),
        "shape": _shape(graph),
    }
