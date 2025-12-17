import importlib
import importlib.util
import os
import sgtk


plugin_widgets = []

def launch_integration():
    bootstrap = os.environ.get("SGTK_SUBSTANCEPAINTER_ENGINE_STARTUP")
    if not bootstrap:
        raise sgtk.TankError("No bootstrap file in environment!")
    name, ext = os.path.splitext(os.path.basename(bootstrap))
    spec = importlib.util.spec_from_file_location(name, bootstrap)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.launch()

def start_plugin():
    launch_integration()

def close_plugin():
    engine = sgtk.platform.current_engine()
    if engine and engine.menu_generator:
        engine.menu_generator.destroy_menu()

if __name__ == "__main__":
    start_plugin()