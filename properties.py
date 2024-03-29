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

from bpy.types import PropertyGroup

from bpy.props import (BoolProperty,
                       PointerProperty
                       )

from .utils import MeshCheck


def enable_depsgraph_handler(self, context):
    if self.display_mesh_check:
        MeshCheck.set_mode(context.object.mode)
        MeshCheck.add_callback()
    else:
        MeshCheck.remove_callback()


def mc_object_datas_updater(attr):
    def updater(self, context):
        if context.object.mode == "EDIT" and getattr(self, attr):
            MeshCheck.update_mc_object_datas(attr)

    return updater


class MeshCheckProperties(PropertyGroup):

    display_mesh_check: BoolProperty(
        name="Mesh Check",
        default=False,
        update=enable_depsgraph_handler
    )

    non_manifold: BoolProperty(
        name="Non manifold",
        default=False,
        description="Draw non manifold edges",
        update=mc_object_datas_updater("non_manifold")
    )

    triangles: BoolProperty(
        name="Triangles",
        default=False,
        description="Draw triangles",
        update=mc_object_datas_updater("triangles")
    )

    ngons: BoolProperty(
        name="Ngons",
        default=False,
        description="Draw ngons",
        update=mc_object_datas_updater("ngons")
    )

    def split_template(self, layout):
        row = layout.row(align=True)
        split = row.split(factor=0.2)
        split.separator()  # créé un décalage verticale
        return split

    def draw_options(self, layout):
        layout.active = self.display_mesh_check and bpy.context.object.mode == "EDIT"
        split = self.split_template(layout)
        split.prop(self, "non_manifold")
        split = self.split_template(layout)
        split.prop(self, "triangles")
        split = self.split_template(layout)
        split.prop(self, "ngons")


def register():

    bpy.utils.register_class(MeshCheckProperties)
    bpy.types.WindowManager.mesh_check_props = PointerProperty(
        type=MeshCheckProperties)


def unregister():

    del bpy.types.WindowManager.mesh_check_props
    bpy.utils.unregister_class(MeshCheckProperties)
