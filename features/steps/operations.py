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

from behave import *

import logging
import os
import tempfile

import graphcat
import numpy
import skimage.data

import imagecat
import imagecat.notebook
import imagecat.operator
import test

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
artwork_dir = os.path.join(root_dir, "artwork")
failed_dir = os.path.join(root_dir, "features", "failed")
reference_dir = os.path.join(root_dir, "features", "reference")
temp_dir = tempfile.mkdtemp()


@given(u'an empty graph')
def step_impl(context):
    context.graph = graphcat.Graph()


@given(u'links {links}')
def step_impl(context, links):
    links = eval(links)
    for source, targets in links:
        imagecat.set_links(context.graph, source, targets)


@given(u'a task {task} which outputs the chelsea sample image')
def step_impl(context, task):
    task = eval(task)

    data = skimage.img_as_float(skimage.data.chelsea()).astype(numpy.float16)
    layer = imagecat.Layer(data=imagecat.color.srgb_to_linear(data), components=["r", "g", "b"], role=imagecat.Role.RGB)
    image = imagecat.Image({"C": layer})
    context.graph.set_task(task, graphcat.constant(image))

@given(u'a task {task} with operator composite position {position} orientation {orientation}')
def step_impl(context, task, position, orientation):
    task = eval(task)
    position = eval(position)
    orientation = eval(orientation)
    imagecat.add_task(context.graph, task, imagecat.operator.composite, position=position, orientation=orientation)


@given(u'a task {task} with operator delete layers {layers}')
def step_impl(context, task, layers):
    task = eval(task)
    layers = eval(layers)
    imagecat.add_task(context.graph, task, imagecat.operator.delete, layers=layers)


@given(u'a task {task} with operator fill layer {layer} size {size} values {values} components {components} role {role}')
def step_impl(context, components, layer, size, role, task, values):
    components = eval(components)
    layer = eval(layer)
    role = eval(role)
    size = eval(size)
    task = eval(task)
    values = eval(values)
    imagecat.add_task(context.graph, task, imagecat.operator.fill, components=components, layer=layer, size=size, values=values, role=role)


@given(u'a task {task} with operator gaussian radius {radius}')
def step_impl(context, task, radius):
    task = eval(task)
    radius = eval(radius)
    imagecat.add_task(context.graph, task, imagecat.operator.gaussian, radius=radius)


@given(u'a task {task} with operator load path {path}')
def step_impl(context, task, path):
    task = eval(task)
    path = eval(path)
    path = os.path.join(temp_dir, path)
    imagecat.add_task(context.graph, task, imagecat.operator.load, path=path)


@given(u'a task {task} with operator merge')
def step_impl(context, task):
    task = eval(task)
    imagecat.add_task(context.graph, task, imagecat.operator.merge)


@given(u'a task {task} with operator offset layers {layers} offset {offset}')
def step_impl(context, task, layers, offset):
    task = eval(task)
    layers = eval(layers)
    offset = eval(offset)
    imagecat.add_task(context.graph, task, imagecat.operator.offset, layers=layers, offset=offset)


@given(u'a task {task} with operator rename changes {changes}')
def step_impl(context, task, changes):
    task = eval(task)
    changes = eval(changes)
    imagecat.add_task(context.graph, task, imagecat.operator.rename, changes=changes)


@given(u'a task {task} with operator rgb2gray layers {layers} weights {weights}')
def step_impl(context, task, layers, weights):
    task = eval(task)
    layers = eval(layers)
    weights = eval(weights)
    imagecat.add_task(context.graph, task, imagecat.operator.rgb2gray, layers=layers, weights=weights)


@given(u'a task {task} with operator save path {path}')
def step_impl(context, task, path):
    task = eval(task)
    path = eval(path)
    path = os.path.join(temp_dir, path)
    imagecat.add_task(context.graph, task, imagecat.operator.save, path=path)


@given(u'a task {task} with operator scale order {order} size {size}')
def step_impl(context, task, order, size):
    order = eval(order)
    size = eval(size)
    task = eval(task)
    imagecat.add_task(context.graph, task, imagecat.operator.scale, order=order, size=size)


@given(u'a task {task} with operator text anchor {anchor} fontindex {fontindex} fontname {fontname} fontsize {fontsize} layer {layer} position {position} size {size} text {text}')
def step_impl(context, task, anchor, fontindex, fontname, fontsize, layer, position, size, text):
    anchor = eval(anchor)
    fontindex = eval(fontindex)
    fontname = eval(fontname)
    fontsize = eval(fontsize)
    layer = eval(layer)
    position = eval(position)
    size = eval(size)
    task = eval(task)
    text = eval(text)

    fontname = os.path.join(artwork_dir, fontname)
    imagecat.add_task(context.graph, task, imagecat.operator.text, anchor=anchor, fontindex=fontindex, fontname=fontname, fontsize=fontsize, layer=layer, position=position, size=size, text=text)


@when(u'updating the task {task}')
def step_impl(context, task):
    task = eval(task)
    context.graph.update(task)


@when(u'retrieving the output image from task {task}')
def step_impl(context, task):
    task = eval(task)
    context.image = context.graph.output(task)


@then(u'displaying the image in a notebook should produce a visualization')
def step_impl(context):
    imagecat.notebook.display(context.image)


@then(u'the image should match the {name} reference image')
def step_impl(context, name):
    reference_file = os.path.join(reference_dir, f"{name}.icp")
    failed_file = os.path.join(failed_dir, f"{name}.icp")

    # Get rid of past failures.
    if os.path.exists(failed_file):
        os.remove(failed_file)

    # If the reference for this test doesn't exist, create it.
    if not os.path.exists(reference_file):
        if not os.path.exists(reference_dir):
            os.mkdir(reference_dir)

        graph = graphcat.Graph()
        graph.set_task("/image", graphcat.constant(context.image))
        imagecat.add_task(graph, "/save", imagecat.save, path=reference_file)
        imagecat.set_links(graph, "/image", ("/save", "image"))
        graph.update("/save")

        raise AssertionError(f"Created new reference file {reference_file} ... verify its contents before re-running the test.")

    # Load the reference for comparison.
    graph = graphcat.Graph()
    imagecat.add_task(graph, "/load", imagecat.operator.load, path=reference_file)
    reference_image = graph.output("/load")

    try:
        test.assert_image_equal(context.image, reference_image)
    except Exception as e:
        # Save the failed file for later examination.
        if not os.path.exists(failed_dir):
            os.mkdir(failed_dir)

        graph = graphcat.Graph()
        graph.set_task("/image", graphcat.constant(context.image))
        imagecat.add_task(graph, "/save", imagecat.save, path=failed_file)
        imagecat.set_links(graph, "/image", ("/save", "image"))
        graph.update("/save")

        raise e


