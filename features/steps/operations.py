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

import graphcat
import numpy
import skimage.data

import imagecat.color
import test

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
artwork_dir = os.path.join(root_dir, "artwork")
failed_dir = os.path.join(root_dir, "features", "failed")
reference_dir = os.path.join(root_dir, "features", "reference")


@given(u'an empty graph')
def step_impl(context):
    context.graph = graphcat.Graph()


@given(u'links {links}')
def step_impl(context, links):
    links = eval(links)
    for source, targets in links:
        context.graph.set_links(source, targets)


@given(u'a task {task} which outputs the chelsea sample image')
def step_impl(context, task):
    task = eval(task)

    data = skimage.img_as_float(skimage.data.chelsea()).astype(numpy.float16)
    layer = imagecat.Layer(data=imagecat.color.srgb_to_linear(data), components=["r", "g", "b"], role=imagecat.Role.RGB)
    image = imagecat.Image({"C": layer})
    context.graph.set_task(task, graphcat.constant(image))


@given(u'a task {task} with operator scale order {order} size {size}')
def step_impl(context, task, order, size):
    order = eval(order)
    size = eval(size)
    task = eval(task)
    imagecat.add_operation(context.graph, task, imagecat.scale, order=order, size=size)


@given(u'a task {task} with operator solid layer {layer} size {size} values {values} components {components} role {role}')
def step_impl(context, components, layer, size, role, task, values):
    components = eval(components)
    layer = eval(layer)
    role = eval(role)
    size = eval(size)
    task = eval(task)
    values = eval(values)
    imagecat.add_operation(context.graph, task, imagecat.solid, components=components, layer=layer, size=size, values=values, role=role)


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
    imagecat.add_operation(context.graph, task, imagecat.text, anchor=anchor, fontindex=fontindex, fontname=fontname, fontsize=fontsize, layer=layer, position=position, size=size, text=text)


@when(u'retrieving the output image from task {task}')
def step_impl(context, task):
    task = eval(task)
    context.image = context.graph.output(task)


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
        imagecat.add_operation(graph, "/save", imagecat.save, path=reference_file)
        graph.set_links("/image", ("/save", "image"))
        graph.update("/save")

        raise AssertionError(f"Created new reference file {reference_file} ... verify its contents before re-running the test.")

    # Load the reference for comparison.
    graph = graphcat.Graph()
    imagecat.add_operation(graph, "/load", imagecat.load, path=reference_file)
    reference_image = graph.output("/load")

    try:
        test.assert_image_equal(context.image, reference_image)
    except Exception as e:
        # Save the failed file for later examination.
        if not os.path.exists(failed_dir):
            os.mkdir(failed_dir)

        graph = graphcat.Graph()
        graph.set_task("/image", graphcat.constant(context.image))
        imagecat.add_operation(graph, "/save", imagecat.save, path=failed_file)
        graph.set_links("/image", ("/save", "image"))
        graph.update("/save")

        raise e


