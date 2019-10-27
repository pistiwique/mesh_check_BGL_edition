# Copyright (C) 2018 Legigan Jeremy AKA Pistiwique and Pitiwazou
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# <pep8 compliant>

import bpy
import bmesh
import gpu

from gpu_extras.batch import batch_for_shader


class MeshCheckObject:

    def __init__(self, name):

        self.name = name
        self._bm_object = None
        self._verts = 0
        self._edges = 0
        self._faces = 0
        self._non_manifold = set()

    def init_object(self):
        self.set_bm_object()
        self.update_datas()

    def get_bm_object(self):
        return self._bm_object

    def set_bm_object(self):
        obj = bpy.data.objects.get(self.name)
        if obj.data.is_editmode:
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            self._bm_object = bm
            return bm

    def update_bm_object(self):
        bm = self.get_bm_object()
        if not bm:
            self.init_object()
        else:
            self.set_bm_object()

        self.update_datas()

    def update_datas(self):
        bm = self.get_bm_object()
        if bm is not None:
            self._verts = len(bm.verts)
            self._edges = len(bm.edges)
            self._faces = len(bm.faces)
            self.set_non_manifold_edges(bm)
        else:
            raise ValueError("Invalid bmesh object")

    def clear_datas(self):
        self._verts = self._edges = self._faces = 0

    def is_updated_datas(self):
        datas = ("verts", "edges", "faces")
        bm = self.get_bm_object()
        if bm:
            return any([getattr(self, f"_{data}") != len(getattr(bm, data))
                        for data in datas])

        raise ValueError("Invalid bmesh object")

    def get_non_manifold_edges(self):
        return self._non_manifold

    def set_non_manifold_edges(self, bm):
        if bm is not None:
            self._non_manifold.clear()
            self._non_manifold.update(
                    [edge.index for edge in bm.edges if not edge.is_manifold])
        else:
            raise ValueError("Invalid bmesh object")



class MeshCheckBGL:

    _handler = None

    @classmethod
    def setup_handler(cls):
        cls._handler = bpy.types.SpaceView3D.draw_handler_add(
                cls.draw, (), 'WINDOW', 'POST_VIEW'
                )

    @classmethod
    def remove_handler(cls):
        bpy.types.SpaceView3D.draw_handler_remove(cls._handler, 'WINDOW')

    @classmethod
    def draw_edges(cls, obj, bm, edge_idx, color):
        coords = [obj.matrix_world@vert.co for vert in bm.edges[
            edge_idx].verts]
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": coords})
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)

    @classmethod
    def draw(cls):
        C = bpy.context
        if C.object is not None and C.object.data.is_editmode:
            mesh_check = bpy.context.window_manager.mesh_check_props
            addon_prefs = bpy.context.preferences.addons[
                __name__.split(".")[0]].preferences
            if mesh_check.non_manifold:
                for id, mc_object in MeshCheck.objects.items():
                    for idx in mc_object.get_non_manifold_edges():
                        bm = mc_object.get_bm_object()
                        obj = bpy.data.objects.get(mc_object.name)
                        cls.draw_edges(obj,
                                       bm,
                                       idx,
                                       addon_prefs.non_manifold_color)

class MeshCheck:

    _mode = ""
    objects = {}

    @staticmethod
    def poll(mesh_check):
        props = ("non_manifold", "triangles", "ngons")
        return mesh_check.display_mesh_check and \
               any([getattr(mesh_check, prop) for prop in props])

    @classmethod
    def reset_mesh_check(cls):
        cls._mode = ""
        cls.clear_objects()
        cls.remove_callback()

    @classmethod
    def clear_objects(cls):
        cls.objects.clear()

    @classmethod
    def mode(cls):
        return cls._mode

    @classmethod
    def set_mode(cls, states):
        cls._mode = states

    @classmethod
    def add_mesh_check_object(cls, obj):
        cls.objects[obj.name] = MeshCheckObject(obj.name)
        if bpy.context.object.mode == "EDIT":
            cls.objects[obj.name].update_bm_object()

    @classmethod
    def reset_mc_objects(cls):
        for mc_object in cls.objects.values():
            del mc_object
        cls.objects.clear()

        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                cls.add_mesh_check_object(obj)


    @classmethod
    def add_callback(cls):
        if cls.callback not in bpy.app.handlers.depsgraph_update_post:
            for obj in bpy.context.selected_objects:
                if obj.type != "MESH":
                    continue
                cls.add_mesh_check_object(obj)

            bpy.app.handlers.depsgraph_update_post.append(cls.callback)
            MeshCheckBGL.setup_handler()

    @classmethod
    def remove_callback(cls):
        if cls.callback in bpy.app.handlers.depsgraph_update_post:
            MeshCheckBGL.remove_handler()
            for mc_object in cls.objects.values():
                del mc_object
            cls.objects.clear()

            bpy.app.handlers.depsgraph_update_post.remove(cls.callback)

    @staticmethod
    def callback(scene):
        """
        Before doing anything, we check that the mode haven't change.
        If it's the case and we are in EDIT mode, we check the  validity
        of registered MeshCheckObject instances. For each instance,
        we update its bmesh representation.
        """
        # ne detecte pas le changement de mode apres un undo
        object_mode = bpy.context.object.mode
        if object_mode != MeshCheck.mode():
            MeshCheck.set_mode(object_mode)
            print("updated")
            if object_mode == "EDIT":
                MeshCheck.reset_mc_objects()

        if bpy.context.object.mode == "EDIT":
            depsgraph = bpy.context.evaluated_depsgraph_get()
            for id, object in MeshCheck.objects.items():
                bm = object.get_bm_object()
                if bm is None or not bm.is_valid:
                    object.set_bm_object()
                for update in depsgraph.updates:
                    if update.id.original == bpy.data.objects[id] and \
                            object.is_updated_datas():
                        object.update_datas()