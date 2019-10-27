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
import re
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader


class MeshCheckObject:

    def __init__(self):

        self._bm_object = None
        self._verts_count = 0
        self._edges_count = 0
        self._faces_count = 0

    @property
    def bm_object(self):
        return self._bm_object

    @bm_object.setter
    def bm_object(self, obj):
        if obj.data.is_editmode:
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            self._bm_object = bm
            return bm

    def update_bm_object(self, obj):
        self._bm_object.clear()
        self.bm_object(obj)


class MeshCheck:

    _mode = ""
    _objects = {}

    @classmethod
    def mode(cls):
        return cls._mode

    @classmethod
    def set_mode(cls, states):
        cls._mode = states

    @staticmethod
    def poll(mesh_check):
        props = ("non_manifold", "triangles", "ngons")
        return mesh_check.display_mesh_check and \
               any([getattr(mesh_check, prop) for prop in props])

    @classmethod
    def add_callback(cls):
        if cls.callback not in bpy.app.handlers.depsgraph_update_post:
            for obj in bpy.context.selected_objects:
                if obj.type != "MESH":
                    continue

            bpy.app.handlers.depsgraph_update_post.append(cls.callback)

    @classmethod
    def remove_callback(cls):
        if cls.callback in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(cls.callback)

    @staticmethod
    def callback(scene):
        object_mode = bpy.context.object.mode
        if object_mode != MeshCheck.mode():
            MeshCheck.set_mode(object_mode)
            if object_mode == "EDIT":
                print("update_datas")

