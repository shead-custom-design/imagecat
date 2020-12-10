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

"""Functionality for manipulating images and related data structures.
"""

import functools
import sys


def loaded_module(modules):
    if isinstance(modules, str):
        modules = (modules,)
    def implementation(f):
        @functools.wraps(f)
        def implementation(*args, **kwargs):
            for module in modules:
                if module not in sys.modules:
                    raise RuntimeError(f"Module {module} could not be found.")
            return f(*args, **kwargs)
        return implementation
    return implementation
