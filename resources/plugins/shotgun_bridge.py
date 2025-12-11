import importlib
import importlib.util
import os
import sgtk
import sys

# Substance 3D Painter modules
import substance_painter.ui

# PySide module to build custom UI
from PySide6 import QtGui


plugin_widgets = []


def launch_integration():
    bootstrap = os.environ.get("SGTK_SUBSTANCEPAINTER_ENGINE_STARTUP")
    if not bootstrap:
        raise sgtk.TankError("No bootstrap file in environment!")
    dir = os.path.dirname(bootstrap)
    name, ext = os.path.splitext(os.path.basename(bootstrap))
    spec = importlib.util.spec_from_file_location(name, bootstrap)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.launch()

def start_plugin():
    # Create a text widget for a menu
    # Action = QtGui.QAction("Custom Python Export", triggered=launch_integration)

    # Add this widget to the existing File menu of the application
    # substance_painter.ui.add_action(substance_painter.ui.ApplicationMenu.File, Action)

    # Store the widget for proper cleanup later when stopping the plugin
    # plugin_widgets.append(Action)
    ...
    launch_integration()

def close_plugin():
    # Remove all widgets that have been added to the UI
    # for widget in plugin_widgets:
    #     substance_painter.ui.delete_ui_element(widget)

    # plugin_widgets.clear()
    ...


if __name__ == "__main__":
    start_plugin()