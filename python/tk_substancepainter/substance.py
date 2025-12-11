"""
Module that encapsulates access to the actual application

"""
import time
import traceback

import substance_painter as sp
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QUrl

__author__ = "Diego Garcia Huerta"
__email__ = "diegogh2000@gmail.com"


class Substance:
    def __init__(self, engine):
        self.engine = engine

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
        sp.project.create(mesh_file_path=path, template_file_path=template, settings=self._dict_to_proj_settings(settings))

    def open_project(self, path):
        sp.project.open(path)

    def save_project_as(self, path):
        try:
            sp.project.save_as(path)
        except sp.exception.ProjectError as e:
            self.log_error(f"Cannot save project file as {path} due to exception:\n{traceback.format_exception(e)}")
            return False
        return True

    def save_project_as_action(self):
        return self.open_save_dialog()

    def save_project(self):
        try:
            sp.project.save()
        except sp.exception.ProjectError as e:
            self.log_error(f"Cannot save project file due to exception:\n{traceback.format_exception(e)}")
            return False
        return True

    def close_project(self):
        if sp.project.is_open():
            sp.project.close()

    def execute(self, statement_str):
        #TODO Rethink whether that is a feature that is still required, or should even be implemented in the first place.
        return exec(statement_str)

    def extract_thumbnail(self, filename):
        raise NotImplementedError("This feature is currently not implemented.")

    def import_project_resource(self, filename, usage, destination):
        return sp.resource.import_project_resource(file_path=filename, resource_usage=usage, name=destination)

    def get_project_settings(self, key):
        raise NotImplementedError("This feature is currently not implemented.")

    def get_resource_info(self, resource_url):
        return sp.resource.ResourceID.from_url(resource_url)

    def get_project_export_path(self):
        raise NotImplementedError("This feature is currently not implemented.")

    def get_map_export_information(self):
        raise NotImplementedError("This feature is currently not implemented.")

    def export_document_maps(self, destination):
        self.log_debug("Starting map export...")
        #result = self.send_and_receive("EXPORT_DOCUMENT_MAPS", destination=destination)

        export_options = sp.js.evaluate("alg.mapexport.getProjectExportOptions()")
        export_preset = sp.js.evaluate("alg.mapexport.getProjectExportPreset()")

        # TODO working command below
        #   vvvvvvvvvvvvvvvvvvvvvvvvv
        # result = sp.js.evaluate(
        #     'alg.mapexport.exportDocumentMaps('
        #     '"resource://davos/LAVA PBRMR?version=11006380353236710736.spexp", '
        #     '"S:/projects/210823_workflow3d/production/assets/Prop/pr_bench/Surface/work/substancepainter/textures/jpk.v003.textures", '
        #     '"exr", '
        #     '{bitDepth: 32, dilation: 16, exportShaderParams: false, exportUSD: false, fileFormat: "exr", padding: "Infinite"}, '
        #     '[]);' # ["bench_body", "bench_metal"]
        # )
        # TODO ^^^^^^^^^^^^^^^^^^^^^^
        # TODO destination backslashes auf forward slahes wechseln

        result = sp.js.evaluate(f"alg.mapexport.exportDocumentMaps({export_preset}, {destination}, {export_options.get('fileFormat')}, {export_options})")

        self.log_debug("Map export ended.")
        return result

    def update_document_resources(self, old_url, new_url):
        old_id = sp.resource.ResourceID.from_url(old_url)
        new_id = sp.resource.ResourceID.from_url(new_url)
        return sp.resource.replace_project_resources({old_id: new_id})

    def document_resources(self):
        return sp.resource.list_project_resources()

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
            "Substance Painter files (*.spp)"  # file filter
        )
        if file_path:
            sp.project.save_as(file_path, mode=sp.project.ProjectSaveMode.Full)
            return True
        return False