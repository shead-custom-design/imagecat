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

from setuptools import setup, find_packages
import re

setup(
    name="imagecat",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Artistic Software",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    description="Flexible, high-quality tools for procedural image editing.",
    install_requires=[
        "Pillow>=8.0.0",
        "graphcat>=1.0.0",
        "mmh3",
        "numpy>=1.17",
        "scikit-image",
    ],
    long_description="""Imagecat provides flexible, high-quality tools for procedural image editing.
    See the Imagecat documentation at http://imagecat.readthedocs.io, and the Imagecat sources at http://github.com/shead-custom-design/imagecat""",
    maintainer="Timothy M. Shead",
    maintainer_email="tim@shead-custom-design.com",
    packages=find_packages(),
    package_data={
        "imagecat": ["LeagueSpartan-SemiBold.ttf"],
    },
    scripts=[
    ],
    url="http://imagecat.readthedocs.io",
    version=re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        open(
            "imagecat/__init__.py",
            "r").read(),
        re.M).group(1),
)
