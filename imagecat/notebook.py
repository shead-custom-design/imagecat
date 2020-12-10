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

"""Integration with Jupyter notebooks, https://jupyter.org"""

import base64
import io
import pprint

import IPython.display
import ipywidgets

import imagecat.data


def display(image, layers="*", width=None, height=None):
    """Display :ref:`image<images>` inline in a Jupyter notebook.

    Parameters
    ----------
    image: :class:`dict`, required
        :ref:`Image<images>` to be displayed.
    layers: :class:`str`, optional
        Names of the image layers to display.  Use "*" (the default) to display all layers.
    width: :class:`str`, optional
        Optional HTML width for each image.
    height: :class:`str`, optional
        Optional HTML height for each image.
    """
    if not isinstance(image, imagecat.data.Image):
        raise ValueError("Expected an instance of imagecat.Image.") # pragma: no cover

    matched_layers = image.match_layer_names(layers)

    # Setup a tab for each image layer.
    def layer_generator(image, name):
        def implementation():
            layer = image.layers[name]

            stream = io.BytesIO()
            imagecat.data.to_pil(layer).save(stream, "PNG")
            uri = "data:image/png;base64," + base64.standard_b64encode(stream.getvalue()).decode("ascii")

            markup = f"<figure style='margin: 5px; text-align: center'>"
            markup += f"<image src='{uri}' style='width:{width}; height:{height}; box-shadow: 4px 4px 6px rgba(0, 0, 0, 0.5)'/>"
            markup += f"<figcaption>{name} <small>role: {layer.role.name} {layer.shape[1]}&times;{layer.shape[0]}&times;{layer.shape[2]} {layer.dtype}</small></figcaption>"
            markup += f"</figure>"
            return markup
        return implementation

    tabs = []
    titles = []
    generators = []
    for layer in matched_layers:
        tabs.append(ipywidgets.HTML())
        titles.append(f"Layer: {layer}")
        generators.append(layer_generator(image, layer))

    # Setup a tab for metadata.
    def metadata_generator(image):
        def implementation():
            markup = "<pre>"
            for key, value in image.metadata.items():
                markup += f"{key}: {value!r}\n"
            markup += "</pre>"
            return markup
        return implementation

    if image.metadata:
        tabs.append(ipywidgets.HTML())
        titles.append("Metadata")
        generators.append(metadata_generator(image))


    def on_tab_changed(change):
        index = change["new"]
        if index is None:
            return
        widget = tabs[index]
        generator = generators[index]
        if not widget.value and generator is not None:
            widget.value = generator()

    # Display the UI.
    tab_widget = ipywidgets.Accordion(children=tabs)
    for index, title in enumerate(titles):
        tab_widget.set_title(index, title)
    tab_widget.observe(on_tab_changed, names='selected_index')

    IPython.display.display(tab_widget)

    # Generate content for the first tab.
    if tabs:
        on_tab_changed({"new": 0})
