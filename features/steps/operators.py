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
import glob
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
    context.graph = graphcat.DynamicGraph()


@given(u'links {links}')
def step_impl(context, links):
    links = eval(links)
    for source, targets in links:
        imagecat.set_links(context.graph, source, targets)


@given(u'a task {task} which outputs the chelsea sample image')
def step_impl(context, task):
    task = eval(task)

    data = skimage.img_as_float(skimage.data.chelsea()).astype(numpy.float16)
    layer = imagecat.data.Layer(data=imagecat.color.srgb_to_linear(data), role=imagecat.data.Role.RGB)
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


@given(u'a task {task} with operator colormap inlayer {inlayer} and default mapping')
def step_impl(context, task, inlayer):
    inlayer = eval(inlayer)
    task = eval(task)
    imagecat.add_task(context.graph, task, imagecat.operator.color.colormap, inlayer=inlayer)


@given(u'a task {task} with operator colormap inlayer {inlayer} outlayer {outlayer}')
def step_impl(context, task, inlayer, outlayer):
    inlayer = eval(inlayer)
    outlayer = eval(outlayer)
    task = eval(task)
    imagecat.add_task(context.graph, task, imagecat.operator.color.colormap, inlayer=inlayer, outlayer=outlayer, mapping=context.mapping)


@given(u'a task {task} with operator composite pivot {pivot} position {position} orientation {orientation}')
def step_impl(context, task, pivot, position, orientation):
    task = eval(task)
    pivot = eval(pivot)
    position = eval(position)
    orientation = eval(orientation)
    imagecat.add_task(context.graph, task, imagecat.operator.transform.composite, pivot=pivot, position=position, orientation=orientation)


@given(u'a task {task} with operator delete layers {layers}')
def step_impl(context, task, layers):
    task = eval(task)
    layers = eval(layers)
    imagecat.add_task(context.graph, task, imagecat.operator.delete, layers=layers)


@given(u'a task {task} with operator fill layer {layer} res {res} values {values} role {role}')
def step_impl(context, layer, res, role, task, values):
    layer = eval(layer)
    role = eval(role)
    res = eval(res)
    task = eval(task)
    values = eval(values)
    imagecat.add_task(context.graph, task, imagecat.operator.color.fill, layer=layer, res=res, values=values, role=role)


@given(u'a task {task} with operator gaussian radius {radius}')
def step_impl(context, task, radius):
    task = eval(task)
    radius = eval(radius)
    imagecat.add_task(context.graph, task, imagecat.operator.blur.gaussian, radius=radius)


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
    imagecat.add_task(context.graph, task, imagecat.operator.transform.offset, layers=layers, offset=offset)


@given(u'a task {task} with operator rename changes {changes}')
def step_impl(context, task, changes):
    task = eval(task)
    changes = eval(changes)
    imagecat.add_task(context.graph, task, imagecat.operator.rename, changes=changes)


@given(u'a task {task} with operator dot inlayer {inlayer} outlayer {outlayer} outrole {outrole} matrix {matrix}')
def step_impl(context, task, inlayer, outlayer, outrole, matrix):
    task = eval(task)
    inlayer = eval(inlayer)
    outlayer = eval(outlayer)
    outrole = eval(outrole)
    matrix = eval(matrix)
    imagecat.add_task(context.graph, task, imagecat.operator.color.dot, inlayer=inlayer, outlayer=outlayer, outrole=outrole, matrix=matrix)


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
    imagecat.add_task(context.graph, task, imagecat.operator.transform.resize, order=order, res=res)


@given(u'a task {task} with operator text anchor {anchor} fontsize {fontsize} layer {layer} position {position} res {res} string {string}')
def step_impl(context, task, anchor, fontsize, layer, position, res, string):
    anchor = eval(anchor)
    fontsize = eval(fontsize)
    layer = eval(layer)
    position = eval(position)
    res = eval(res)
    task = eval(task)
    string = eval(string)

    imagecat.add_task(context.graph, task, imagecat.operator.render.text, anchor=anchor, fontsize=fontsize, layer=layer, position=position, res=res, string=string)


@given(u'a task {task} with operator uniform layer {layer} res {res} role {role} seed {seed}')
def step_impl(context, task, layer, res, role, seed):
    layer = eval(layer)
    res = eval(res)
    role = eval(role)
    seed = eval(seed)
    task = eval(task)
    imagecat.add_task(context.graph, task, imagecat.operator.noise.uniform, layer=layer, role=role, seed=seed, res=res)


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
    reference_files = glob.glob(os.path.join(reference_dir, f"{name}.icp"))
    reference_files += glob.glob(os.path.join(reference_dir, "**", f"{name}.icp"))

    new_reference_file = os.path.join(reference_dir, f"{name}.icp")
    failed_file = os.path.join(failed_dir, f"{name}.icp")

    # Get rid of past failures.
    if os.path.exists(failed_file):
        os.remove(failed_file)

    # If a reference for this test doesn't exist, create it.
    if not reference_files:
        if not os.path.exists(reference_dir):
            os.mkdir(reference_dir)

        graph = graphcat.DynamicGraph()
        graph.set_task("/image", graphcat.constant(context.image))
        imagecat.add_task(graph, "/save", imagecat.operator.save, path=new_reference_file)
        imagecat.set_links(graph, "/image", ("/save", "image"))
        graph.update("/save")

        raise AssertionError(f"Created new reference file {new_reference_file} ... verify its contents before re-running the test.")


    # The context image should match at least one reference.
    try:
        matched = False
        for reference_file in reference_files:
            # Load a reference for comparison
            graph = graphcat.DynamicGraph()
            imagecat.add_task(graph, "/load", imagecat.operator.load, path=reference_file)
            try:
                reference_image = graph.output("/load")
            except Exception as e:
                raise AssertionError(f"Unable to load reference file {reference_file} ... verify its contents and replace as-needed.")

            try:
                test.assert_image_equal(context.image, reference_image)
                matched = True
                break
            except Exception as e:
                pass
        if not matched:
            raise AssertionError(f"Test image did not match reference files {reference_files}.")

    except Exception as e:
        # Save the failed file for later examination.
        if not os.path.exists(failed_dir):
            os.mkdir(failed_dir)

        graph = graphcat.DynamicGraph()
        graph.set_task("/image", graphcat.constant(context.image))
        imagecat.add_task(graph, "/save", imagecat.operator.save, path=failed_file)
        imagecat.set_links(graph, "/image", ("/save", "image"))
        graph.update("/save")

        raise e


