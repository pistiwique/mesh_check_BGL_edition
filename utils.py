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

import bgl
from gpu_extras.batch import batch_for_shader


class MeshCheckObject:

    def __init__(self, name):

        self.name = name
        self._bm_object = None

        self._verts = 0
        self._edges = 0
        self._faces = 0

        self._non_manifold = set()
        self._triangles = set()
        self._ngons = set()

        self.init_object()

    def init_object(self):
        if bpy.context.object.mode == "EDIT":
            bm = self.set_bm_object()
            self.update_datas(bm)

    def get_bm_object(self):
        return self._bm_object

    def set_bm_object(self):
        obj = bpy.data.objects.get(self.name)
        if obj.data.is_editmode:
            me = obj.data
            self._bm_object = bmesh.from_edit_mesh(me)
            return self._bm_object

    def update_bm_object(self):
        bm = self.set_bm_object()
        self.update_datas(bm)
        return bm

    def update_datas(self, bm):
        self._verts = len(bm.verts)
        self._edges = len(bm.edges)
        self._faces = len(bm.faces)

        self.set_non_manifold(bm)
        self.set_triangles(bm)
        self.set_ngons(bm)


    def clear_datas(self):
        self._verts = self._edges = self._faces = 0

    def is_updated_datas(self, bm):
        datas = ("verts", "edges", "faces")
        return any([getattr(self, f"_{data}") != len(getattr(bm, data))
                    for data in datas])

    def get_non_manifold(self):
        return self._non_manifold

    def set_non_manifold(self, bm):
        if bm is not None:
            self._non_manifold.clear()
            self._non_manifold.update(
                    edge.index for edge in bm.edges if not edge.is_manifold)
        else:
            raise ValueError("Invalid bmesh object")

    def get_triangles(self):
        return self._triangles

    def set_triangles(self, bm):
        if bm is not None:
            self._triangles.clear()
            self._triangles.update(edge.index for face in bm.faces for edge in
                   face.edges if len(face.edges) == 3)
        else:
            raise ValueError("Invalid bmesh object")

    def get_ngons(self):
        return self._ngons

    def set_ngons(self, bm):
        if bm is not None:
            self._ngons.clear()
            self._ngons.update(edge.index for face in bm.faces for edge in
                   face.edges if len(face.edges) > 4)
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
    def draw_edges(cls, mc_object, idx, line_width, color):
        obj = bpy.data.objects.get(mc_object.name)
        bm = mc_object.get_bm_object()
        if not bm.is_valid:
            bm = mc_object.update_bm_object()
        coords = [obj.matrix_world @ vert.co for vert in bm.edges[idx].verts]

        bgl.glLineWidth(line_width)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

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

            if any([getattr(mesh_check, data) for data in ("non_manifold",
                                                           "triangles",
                                                           "ngons")]):
                for id, mc_object in MeshCheck.objects.items():
                    if mesh_check.non_manifold:
                        for edge_idx in mc_object.get_non_manifold():
                            cls.draw_edges(mc_object,
                                           edge_idx,
                                           addon_prefs.line_width,
                                           addon_prefs.non_manifold_color)

                    if mesh_check.triangles:
                        for edge_idx in mc_object.get_triangles():
                            cls.draw_edges(mc_object,
                                           edge_idx,
                                           addon_prefs.line_width,
                                           addon_prefs.triangles_color)

                    if mesh_check.ngons:
                        for edge_idx in mc_object.get_ngons():
                            cls.draw_edges(mc_object,
                                           edge_idx,
                                           addon_prefs.line_width,
                                           addon_prefs.ngons_color)


class MeshCheck:

    _mode = ""
    objects = {}

    @staticmethod
    def poll():
        mesh_check = bpy.context.window_manager.mesh_check_props
        props = ("non_manifold", "triangles", "ngons")
        return mesh_check.display_mesh_check and \
               any([getattr(mesh_check, prop) for prop in props])

    @classmethod
    def reset_mesh_check(cls):
        cls.set_mode("")
        for mc_object in cls.objects.values():
            del mc_object
        cls.objects.clear()

    @classmethod
    def mode(cls):
        return cls._mode

    @classmethod
    def set_mode(cls, states):
        cls._mode = states

    @classmethod
    def add_mesh_check_object(cls):
        for obj in bpy.context.selected_objects:
            if obj.type != "MESH":
                continue
            cls.objects[obj.name] = MeshCheckObject(obj.name)

    @classmethod
    def reset_mc_objects(cls):
        for mc_object in cls.objects.values():
            del mc_object
        cls.objects.clear()
        cls.add_mesh_check_object()

    @classmethod
    def add_callback(cls):
        if cls.callback not in bpy.app.handlers.depsgraph_update_post:
            cls.add_mesh_check_object()
            bpy.app.handlers.depsgraph_update_post.append(cls.callback)
            MeshCheckBGL.setup_handler()

    @classmethod
    def remove_callback(cls):
        if cls.callback in bpy.app.handlers.depsgraph_update_post:
            MeshCheckBGL.remove_handler()
            bpy.app.handlers.depsgraph_update_post.remove(cls.callback)
            cls.reset_mesh_check()

    @classmethod
    def update_mc_object_datas(cls, datas):
        for mc_object in cls.objects.values():
            getattr(mc_object, f"set_{datas}")(mc_object.get_bm_object())

    @staticmethod
    def callback(scene):
        """
        Before doing anything, we check that the mode haven't change.
        If it's the case and we are in EDIT mode, we check the  validity
        of registered MeshCheckObject instances. For each instance,
        we update its bmesh representation.
        """
        if bpy.context.object is not None:
            object_mode = bpy.context.object.mode
            if object_mode != MeshCheck.mode():
                MeshCheck.set_mode(object_mode)
                if object_mode == "EDIT":
                    MeshCheck.reset_mc_objects()

            if object_mode == "EDIT" and MeshCheck.poll():
                depsgraph = bpy.context.evaluated_depsgraph_get()
                for id, object in MeshCheck.objects.items():
                    bm = object.get_bm_object()
                    if bm is None or not bm.is_valid:
                        bm = object.set_bm_object()
                    for update in depsgraph.updates:
                        if update.id.original == bpy.data.objects[id] and \
                                object.is_updated_datas(bm):
                            object.update_datas(bm)