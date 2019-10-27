# -*- coding:utf-8 -*-

# Blender ASSET MANAGEMENT Add-on
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

from bpy.types import Panel


class ObjectButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"


class OBJECT_PT_display_mesh_check(ObjectButtonsPanel, Panel):
    bl_label = "Mesh Check"
    bl_parent_id = "OBJECT_PT_display"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        mesh_check = context.window_manager.mesh_check_props
        layout = self.layout
        layout.active = context.object.mode == "EDIT"
        layout.prop(mesh_check, "display_mesh_check", text="")

    def draw(self, context):
        mesh_check = context.window_manager.mesh_check_props
        layout = self.layout
        mesh_check.draw_options(layout)
        # obj = context.object
        # layout.use_property_split = True
        #
        # layout.active = obj.show_bounds or (obj.display_type == 'BOUNDS')
        # layout.prop(obj, "display_bounds_type", text="Shape")

def register():
    bpy.utils.register_class(OBJECT_PT_display_mesh_check)

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_display_mesh_check)