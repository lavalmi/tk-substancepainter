import os
import sgtk

from typing import TYPE_CHECKING

HookBaseClass = sgtk.get_hook_baseclass()

class Breakdown2SceneOperations(HookBaseClass):

    def scan_scene(self):
        if TYPE_CHECKING:
            from ...engine import SubstancePainterEngine
            engine:SubstancePainterEngine
        engine = sgtk.platform.current_engine()

        items = []
        mesh_path = engine.substance.get_current_project_mesh()
        if mesh_path:
            items.append(
                dict(
                    node_name=os.path.basename(mesh_path),
                    node_type='mesh',
                    path=mesh_path
                )
            )
        return items

    def update(self, item):

        old_path = self._norm_path(item.get('extra_data', {}).get('old_path', None) or item.get('sg_data', {}).get('path', {}).get('local_path', None))
        if not old_path:
            return False
        new_path = self._norm_path(item.get('path', None))
        if not new_path:
            return False

        if old_path == new_path:
            return False

        if TYPE_CHECKING:
            from ...engine import SubstancePainterEngine
            engine:SubstancePainterEngine
        engine = sgtk.platform.current_engine()
        engine.substance.update_document_mesh(new_path)

        return True

    @staticmethod
    def _norm_path(path):
        return os.path.normpath(os.path.normcase(path))