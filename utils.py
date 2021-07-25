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

from mathutils.geometry import tessellate_polygon as tessellate


class MeshCheckObject:

    def __init__(self, name):

        self.name = name
        self._bm_object = None

        self._verts = 0
        self._edges = 0
        self._faces = 0

        self._non_manifold = set()  # storage for edges
        self._triangles = set()  # storage for faces
        self._triangles_vertices = []  # nested list
        self._triangles_indices = []

        self._ngons = set()  # storage for faces
        self._ngons_vertices = []
        self._ngons_indices = []

        self.init_object()

    def init_object(self):
        if bpy.context.object.mode == "EDIT":
            mesh_check = bpy.context.window_manager.mesh_check_props
            check_types = ("non_manifold", "triangles", "ngons")

            if any(getattr(mesh_check, check) for check in check_types):
                bm = self.set_bm_object()
                self.update_datas(bm)

    def get_object_data(self):
        obj = bpy.data.objects.get(self.name)  # if doesn't exist no error
        return obj.data

    def get_bm_object(self):
        return self._bm_object

    def set_bm_object(self):
        me = self.get_object_data()
        if me.is_editmode:
            self._bm_object = bmesh.from_edit_mesh(me)
            return self._bm_object

    def update_bm_object(self):
        bm = self.set_bm_object()
        self.update_datas(bm)
        return bm

    def update_datas(self, bm):

        me = self.get_object_data()
        bmesh.update_edit_mesh(me)

        mesh_check = bpy.context.window_manager.mesh_check_props
        check_types = ("non_manifold", "triangles", "ngons")

        for check in check_types:
            if getattr(mesh_check, check):  # to not exe all each time
                exec(f"self.set_{check}(bm)")

    def is_updated_datas(self, bm):
        datas = ("verts", "edges", "faces")
        return any(
            getattr(self, f"_{data}") != len(getattr(bm, data)) for data in datas
        )

    def set_non_manifold(self, bm):
        if bm is None or not bm.is_valid:
            bm = self.update_bm_object()

        self._non_manifold = [
            edge for edge in bm.edges if not edge.is_manifold]

    def get_triangles(self):
        return self._triangles

    def set_triangles(self, bm):
        if bm is None or not bm.is_valid:
            bm = self.update_bm_object()

        self._triangles = [face for face in bm.faces if len(face.edges) == 3]

        bm.faces.ensure_lookup_table()

        self._triangles_vertices = [
            vert for f in bm.faces if len(f.edges) == 3 for vert in f.verts]

        index = list(range(len(self._triangles_vertices)))
        self._triangles_indices = [
            index[i:i+3] for i in range(0, len(self._triangles_vertices), 3)]  # trés habile

    def get_ngons(self):
        return self._ngons

    def set_ngons(self, bm):
        self._ngons.clear()
        self._ngons_vertices.clear()
        self._ngons_indices.clear()

        if bm is None or not bm.is_valid:
            bm = self.update_bm_object()

        self._ngons = [face for face in bm.faces if len(face.edges) > 4]

        bm.faces.ensure_lookup_table()
        for face in self.get_ngons():
            coords = [vert.co for vert in face.verts]
            verts = [vert for vert in face.verts]
            tessellated = tessellate([coords])
            remapped_verts = [verts[idx] for tris in
                              tessellated for idx in tris]
            self._ngons_vertices.extend(remapped_verts)

        index = list(range(len(self._ngons_vertices)))
        self._ngons_indices.extend(
            index[i:i + 3] for i in
            range(0, len(self._ngons_vertices), 3)
        )

    def get_edges(self, bm, check_type):

        if check_type == "non_manifold":
            return self._non_manifold

        faces = getattr(self, f"get_{check_type}")()
        return (edge for face in faces for edge in face.edges)

    def get_faces(self, check_type):
        verts = getattr(self, f"_{check_type}_vertices")
        indices = getattr(self, f"_{check_type}_indices")
        return verts, indices


class MeshCheckBGL:

    _handler = None

    @classmethod
    def setup_handler(cls):
        cls._handler = bpy.types.SpaceView3D.draw_handler_add(
            cls.draw, (bpy.context,), 'WINDOW', 'POST_VIEW'
        )

    @classmethod
    def remove_handler(cls):
        bpy.types.SpaceView3D.draw_handler_remove(cls._handler, 'WINDOW')

    @staticmethod
    def draw_edges(id, mc_object, check_type, line_width, color):
        obj = bpy.data.objects.get(id)
        bm = mc_object.get_bm_object()
        if bm is None or not bm.is_valid:
            bm = mc_object.update_bm_object()

        edges = mc_object.get_edges(bm, check_type)

        coords = [obj.matrix_world @ vert.co for edge in edges for vert
                  in edge.verts]

        bgl.glLineWidth(line_width)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": coords})
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)

    @staticmethod
    def draw_faces(id, mc_object, check_type, color):
        obj = bpy.data.objects.get(id)
        bm = mc_object.get_bm_object()
        if bm is None or not bm.is_valid:
            bm = mc_object.update_bm_object()

        verts, indices = mc_object.get_faces(check_type)
        vertices = tuple(obj.matrix_world @ vert.co for vert in
                         verts)

        bgl.glEnable(bgl.GL_BLEND)
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch = batch_for_shader(
            shader, 'TRIS', {"pos": vertices}, indices=indices)

        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
        bgl.glDisable(bgl.GL_BLEND)

    @classmethod
    def draw(cls, context):
        if context.object is None or not context.object.data.is_editmode:
            return
        mesh_check = context.window_manager.mesh_check_props

        addon_prefs = context.preferences.addons[
            __name__.split(".")[0]].preferences

        check_types = ("non_manifold", "triangles", "ngons")

        for check in check_types:
            if getattr(mesh_check, check):
                for id, mc_object in MeshCheck.objects.items():
                    MeshCheckBGL.draw_edges(
                        id,
                        mc_object,
                        check,
                        addon_prefs.line_width,
                        getattr(addon_prefs, f"{check}_color")
                    )

                    if check != "non_manifold":
                        MeshCheckBGL.draw_faces(
                            id,
                            mc_object,
                            check,
                            getattr(addon_prefs, f"{check}_color")
                        )


class MeshCheck:

    _mode = ""
    objects = {}

    @staticmethod
    def poll():
        mesh_check = bpy.context.window_manager.mesh_check_props
        props = ("non_manifold", "triangles", "ngons")
        return mesh_check.display_mesh_check and any(
            getattr(mesh_check, prop) for prop in props
        )

    @classmethod
    def reset_mesh_check(cls):
        cls._mode = ""

        for mc_object in cls.objects.values():
            del mc_object
        cls.objects.clear()

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
            cls.add_mesh_check_object()  # adding MeshCheckObject instances to "objects"
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
            getattr(mc_object, f"set_{datas}")(
                mc_object.get_bm_object())  # method(bm)

    @staticmethod
    def callback(scene):
        """        
        Before doing anything, we check that the mode haven't change.
        If it's the case and we are in EDIT mode, we check the  validity
        of registered MeshCheckObject instances. For each instance,
        we update its bmesh representation.
        """
        if bpy.context.object is None:
            return
        object_mode = bpy.context.object.mode
        if object_mode != MeshCheck._mode:
            MeshCheck.set_mode(object_mode)
            if object_mode == "EDIT":  # situation where objs could have been added/rmv
                MeshCheck.reset_mc_objects()

        if object_mode == "EDIT" and MeshCheck.poll():
            depsgraph = bpy.context.evaluated_depsgraph_get()
            for id, object in MeshCheck.objects.items():  # id=obj.name
                bm = object.get_bm_object()  # instance method
                if bm is None or not bm.is_valid:
                    bm = object.set_bm_object()
                for update in depsgraph.updates:
                    if update.id.original == bpy.data.objects[id] and \
                            object.is_updated_datas(bm):
                        object.update_datas(bm)
