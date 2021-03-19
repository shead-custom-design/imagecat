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


"""Image processing functionality based on Graphcat computational graphs, http://graphcat.readthedocs.io.
"""

__version__ = "0.5.0"

import itertools
import logging

import imagecat.expression

log = logging.getLogger(__name__)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)


def add_links(graph, *args, **kwargs):
    """Add links between tasks in a :class:`graphcat.Graph`.

    This function calls-through to :meth:`graphcat.Graph.add_links`,
    and is provided for symmetry with :func:`add_task`.
    """
    return graph.add_links(*args, **kwargs)


def add_task(graph, name, fn, **parameters):
    """Simplify setting-up graphcat tasks with parameters.

    Virtually all non-trivial Imagecat operations have parameters that affect
    their operation.  Because individually creating parameter tasks and linking
    them with the main task is tiresome and verbose, use this function instead.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        The Graphcat graph where the new task will be created.
    name: :class:`str`, required
        The name of the new task.
    fn: callable, required
        The Imagecat operation to use for the new task.
    parameters: additional keyword arguments, optional
        Each extra keyword argument will be turned into a parameter
        task and linked with the main task.  Each parameter name
        is created by concatenating `name` with the keyword name,
        separated by a slash "/".

    Returns
    -------
    name: :class:`str`
        Name of the newly-created operation, which may be different than `name`.
    """
    name = unique_name(graph, name)
    graph.add_task(name, fn)
    for pname, pvalue in parameters.items():
        ptname = unique_name(graph, f"{name}/{pname}")
        graph.set_parameter(name, pname, ptname, pvalue)
    return name


def set_links(graph, *args, **kwargs):
    """Set links between tasks in a :class:`graphcat.Graph`.

    This function calls-through to :meth:`graphcat.Graph.set_links`,
    and is provided for symmetry with :func:`add_task`.
    """
    return graph.set_links(*args, **kwargs)


def set_expression(graph, name, expression, locals={}):
    """Setup an expression task in a :class:`graphcat.Graph`.

    This function calls-through to :meth:`graphcat.Graph.set_expression`,
    but provides a library of Imagecat-specific functionality that can
    be used by expressions.
    """
    builtins = imagecat.expression.builtins(graph)
    builtins.update(locals)
    graph.set_expression(name, expression, builtins)


def unique_name(graph, name):
    """Return `name`, modified to be unique within `graph`.

    Parameters
    ----------
    graph: :class:`graphcat.Graph`, required
        The graph where `name` will be used.
    name: :class:`str`, required
        Task name to be adjusted.
    """
    if name not in graph:
        return name
    for index in itertools.count(start=1):
        if f"{name}{index}" not in graph:
            return f"{name}{index}"


import imagecat.operator as operator
