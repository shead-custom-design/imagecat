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

import functools
import logging
import os
import tempfile

import graphcat
import numpy
import skimage.data

import imagecat
import imagecat.color
import imagecat.color.basic
import imagecat.color.brewer
import imagecat.notebook
import imagecat.operator
import test

# As a special-case to make scenarios less wordy
from imagecat.data import Role

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
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
    layer = imagecat.data.Layer(data=imagecat.color.srgb_to_linear(data), components=["r", "g", "b"], role=imagecat.data.Role.RGB)
    image = imagecat.data.Image({"C": layer})
    context.graph.set_task(task, graphcat.constant(image))


@given(u'a task {task} with constant value {value}')
def step_impl(context, task, value):
    task = eval(task)
    value = eval(value)
    imagecat.add_task(context.graph, task, graphcat.constant(value))


@then(u'the graph should contain task {task}')
def step_impl(context, task):
    task = eval(task)
    test.assert_true(task in context.graph)


@then(u'the output from {task} should be {value}')
def step_impl(context, task, value):
    task = eval(task)
    value = eval(value)
    test.assert_equal(context.graph.output(task), value)


@given(u'a basic {name} palette reversed: {reverse}')
def step_impl(context, name, reverse):
    name = eval(name)
    reverse = eval(reverse)
    context.palette = imagecat.color.basic.palette(name, reverse=reverse)


@given(u'a brewer {name} palette reversed: {reverse}')
def step_impl(context, name, reverse):
    name = eval(name)
    reverse = eval(reverse)
    context.palette = imagecat.color.brewer.palette(name, reverse=reverse)


@given(u'a linear colormap')
def step_impl(context):
	context.mapping = functools.partial(imagecat.color.linear_map, palette=context.palette)


@given(u'a task {task} with operator colormap layers {layers} and default mapping')
def step_impl(context, task, layers):
    layers = eval(layers)
    task = eval(task)
    imagecat.add_task(context.graph, task, imagecat.operator.colormap, layers=layers)


@given(u'a task {task} with operator colormap layers {layers}')
def step_impl(context, task, layers):
    layers = eval(layers)
    task = eval(task)
    imagecat.add_task(context.graph, task, imagecat.operator.colormap, layers=layers, mapping=context.mapping)


@given(u'a task {task} with operator composite pivot {pivot} position {position} orientation {orientation}')
def step_impl(context, task, pivot, position, orientation):
    task = eval(task)
    pivot = eval(pivot)
    position = eval(position)
    orientation = eval(orientation)
    imagecat.add_task(context.graph, task, imagecat.operator.composite, pivot=pivot, position=position, orientation=orientation)


@given(u'a task {task} with operator delete layers {layers}')
def step_impl(context, task, layers):
    task = eval(task)
    layers = eval(layers)
    imagecat.add_task(context.graph, task, imagecat.operator.delete, layers=layers)


@given(u'a task {task} with operator fill layer {layer} res {res} values {values} components {components} role {role}')
def step_impl(context, components, layer, res, role, task, values):
    components = eval(components)
    layer = eval(layer)
    role = eval(role)
    res = eval(res)
    task = eval(task)
    values = eval(values)
    imagecat.add_task(context.graph, task, imagecat.operator.fill, components=components, layer=layer, res=res, values=values, role=role)


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


@given(u'a task {task} with operator resize order {order} res {res}')
def step_impl(context, task, order, res):
    order = eval(order)
    res = eval(res)
    task = eval(task)
    imagecat.add_task(context.graph, task, imagecat.operator.resize, order=order, res=res)


@given(u'a task {task} with operator text anchor {anchor} fontsize {fontsize} layer {layer} position {position} res {res} text {text}')
def step_impl(context, task, anchor, fontsize, layer, position, res, text):
    anchor = eval(anchor)
    fontsize = eval(fontsize)
    layer = eval(layer)
    position = eval(position)
    res = eval(res)
    task = eval(task)
    text = eval(text)

    imagecat.add_task(context.graph, task, imagecat.operator.text, anchor=anchor, fontsize=fontsize, layer=layer, position=position, res=res, text=text)


@given(u'a task {task} with operator uniform layer {layer} res {res} components {components} role {role} seed {seed}')
def step_impl(context, task, layer, res, components, role, seed):
    components = eval(components)
    layer = eval(layer)
    role = eval(role)
    seed = eval(seed)
    res = eval(res)
    task = eval(task)
    imagecat.add_task(context.graph, task, imagecat.operator.uniform, components=components, layer=layer, role=role, seed=seed, res=res)


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
        imagecat.add_task(graph, "/save", imagecat.operator.save, path=reference_file)
        imagecat.set_links(graph, "/image", ("/save", "image"))
        graph.update("/save")

        raise AssertionError(f"Created new reference file {reference_file} ... verify its contents before re-running the test.")


    try:
        # Load the reference for comparison
        graph = graphcat.Graph()
        imagecat.add_task(graph, "/load", imagecat.operator.load, path=reference_file)
        try:
            reference_image = graph.output("/load")
        except Exception as e:
            raise AssertionError(f"Unable to load reference file {reference_file} ... verify its contents and replace as-needed.")

        test.assert_image_equal(context.image, reference_image)
    except Exception as e:
        # Save the failed file for later examination.
        if not os.path.exists(failed_dir):
            os.mkdir(failed_dir)

        graph = graphcat.Graph()
        graph.set_task("/image", graphcat.constant(context.image))
        imagecat.add_task(graph, "/save", imagecat.operator.save, path=failed_file)
        imagecat.set_links(graph, "/image", ("/save", "image"))
        graph.update("/save")

        raise e

