"""
Module that encapsulates access to the actual application

"""
import traceback

import sgtk
import substance_painter as sp
from PySide6.QtWidgets import QFileDialog

__author__ = "Diego Garcia Huerta"
__email__ = "diegogh2000@gmail.com"


class Substance:
    class Resource:
        def __init__(self, resID:sp.resource.ResourceID):
            self.name = resID.name
            self.context = resID.context
            self.location = resID.location().name
            self.location_index = resID.location().value
            self.version = resID.version
            self.url = resID.url()

        @classmethod
        def from_url(cls, url):
            return cls(sp.resource.ResourceID.from_url(url))


    def __init__(self, engine):
        self.engine:sgtk.platform.Engine = engine

        # borrow the engine logger
        self.log_info = engine.log_info
        self.log_debug = engine.log_debug
        self.log_warning = engine.log_warning
        self.log_error = engine.log_error

        self.log_debug(f"Substance initialized for {engine.name}")

    @staticmethod
    def _dict_to_proj_settings(settings:dict):
        settings = settings.copy()

        specials = {
            'normal_map_format': sp.project.NormalMapFormat,
            'tangent_space_mode': sp.project.TangentSpace ,
            'project_workflow': sp.project.ProjectWorkflow,
            'mesh_settings': (sp.project.UsdSettings, sp.project.GltfSettings)
        }

        for k, t in specials.items():
            if k in settings:
                value = None
                if isinstance(t, (set, tuple, list)):
                    value = None
                    for ty in t:
                        value = getattr(ty, settings[k])
                        if value is not None:
                            break
                else:
                    value = getattr(t, settings[k])
                if value is None:
                    raise ValueError(f"The value '{settings[k]}' for key '{k}' is not valid for the expected type(s) '{t}'.")
                settings[k] = value

        return sp.project.Settings(**settings)

    @staticmethod
    def main_window():
        return sp.ui.get_main_window()

    def get_application_version(self):
        return sp.application.version()

    def get_current_project_path(self):
        if sp.project.is_open():
            return sp.project.file_path()
        return None

    def get_current_project_mesh(self):
        return sp.project.last_imported_mesh_path()

    def need_saving(self):
        if sp.project.is_open():
            return sp.project.needs_saving()
        return False

    def new_project(self, path, template, settings):
        sp.project.create(
            mesh_file_path=path,
            template_file_path=template,
            settings=self._dict_to_proj_settings(settings),
        )

    def open_project(self, path):
        # shelf_name = self.engine.context.project.name
        # shelf_path = self.engine.context
        # if not sp.resource.Shelves.exists(shelf_name):
        # sp.resource.Shelves.add(shelf_name, shelf_path)
        # TODO add path to shelves
        # TODO check whether the export presets are properly read this way
        sp.project.open(path)

    def save_project_as(self, path):
        try:
            sp.project.save_as(path)
        except sp.exception.ProjectError as e:
            self.log_error(
                f"Cannot save project file as {path} due to exception:\n{traceback.format_exception(e)}"
            )
            return False
        return True

    def save_project_as_action(self):
        return self.open_save_dialog()

    def save_project(self):
        try:
            sp.project.save()
        except sp.exception.ProjectError as e:
            self.log_error(
                f"Cannot save project file due to exception:\n{traceback.format_exception(e)}"
            )
            return False
        return True

    def close_project(self):
        if sp.project.is_open():
            sp.project.close()

    def execute(self, statement_str):
        # TODO Rethink whether that is a feature that is still required, or should even be implemented in the first place.
        return exec(statement_str)

    def extract_thumbnail(self, filename):
        raise NotImplementedError("This feature is currently not implemented.")

    def import_project_resource(self, filename, usage, destination):
        return sp.resource.import_project_resource(file_path=filename, resource_usage=usage, name=destination)

    def add_shelf(self, name, path):
        shelf = (
            sp.resource.Shelf(name)
            if sp.resource.Shelves.exists(name)
            else sp.resource.Shelves.add(name, path)
        )
        shelf.refresh()

    def get_project_settings(self, key):
        return sp.js.evaluate("alg.project.settings.value(data.key, {})")

    def get_resource_info(self, resource_url):
        return Substance.Resource.from_url(resource_url)

    def get_project_export_path(self):
        return sp.js.evaluate("alg.mapexport.exportPath()")

    def get_map_export_information(self):
        raise NotImplementedError("This feature is currently not implemented.")

    def export_document_maps(self, destination, size_log2):
        self.log_debug("Starting map export...")

        preset = next(
            (
                preset
                for preset in sp.export.list_resource_export_presets()
                if preset.resource_id.name == "Lava_EXR"
            ),
            None,
        )
        if preset is None:
            raise RuntimeError("The 'Lava_EXR' export preset is not available.")

        export_list = [
            {"rootPath": str(stack)}
            for texture_set in sp.textureset.all_texture_sets()
            for stack in texture_set.all_stacks()
        ]
        if not export_list:
            raise RuntimeError("The project has no texture sets to export.")

        result = sp.export.export_project_textures(
            {
                "exportShaderParams": False,
                "exportPath": destination.replace("\\", "/"),
                "defaultExportPreset": preset.resource_id.url(),
                "exportList": export_list,
                "exportParameters": [
                    {
                        "parameters": {
                            "paddingAlgorithm": "infinite",
                            "sizeLog2": size_log2,
                        }
                    }
                ],
            }
        )
        if result.status != sp.export.ExportStatus.Success:
            raise RuntimeError(result.message)

        self.log_debug("Map export ended.")
        return result.textures

    def update_document_mesh(self, url):
        def reload_mesh_callback(status:sp.project.ReloadMeshStatus):
            self.log_debug(status)
            self.engine.clear_busy()

        self.engine.show_busy("Reloading Mesh", "Substance is currrently reloading your mesh.\nPlease wait a moment.")
        sp.project.reload_mesh(url, sp.project.MeshReloadingSettings(), reload_mesh_callback)

    def update_document_resource(self, old_url, new_url):
        old_id = sp.resource.ResourceID.from_url(old_url)
        new_id = sp.resource.ResourceID.from_url(new_url)
        return sp.resource.replace_project_resources({old_id: new_id})

    def document_resources(self):
        return [Substance.Resource(res) for res in sp.resource.list_project_resources()]

    def open_save_dialog(self):
        """
        Opens a native file dialog for saving Substance Painter project files.
        Returns the selected file path or None if cancelled.
        """
        # Create a simple dialog (no parent needed for this use case)
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window(),  # parent widget
            "Save Project",  # dialog title
            "",  # initial directory
            "Substance Painter files (*.spp)",  # file filter
        )
        if file_path:
            sp.project.save_as(file_path, mode=sp.project.ProjectSaveMode.Full)
            return True
        return False
