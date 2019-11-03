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

from bpy.types import AddonPreferences
from bpy.props import (
    FloatVectorProperty,
    FloatProperty)


class MeshCheckPreferences(AddonPreferences):
    bl_idname = __name__.split(".")[0]

    non_manifold_color: FloatVectorProperty(
            name="Non manifold",
            default=(0, 1.0, 0, 1.0),
            min=0.0, max=1.0, size=4,
            subtype="COLOR",
            description="Non manifold edges color"
            )

    line_width: FloatProperty(
            name="Line Width",
            default=3.0,
            min=1.0, max=10.0,
            subtype="PIXEL",
            description="Edge width in pixels"
            )

    triangles_color: FloatVectorProperty(
            name="Triangles",
            default=(1.0, 0.85, 0, 0.25),
            min=0.0, max=1.0, size=4,
            subtype="COLOR",
            description="Triangles color"
            )

    ngons_color: FloatVectorProperty(
            name="Triangles",
            default=(1.0, 0, 0, 0.25),
            min=0.0, max=1.0, size=4,
            subtype="COLOR",
            description="Ngons color"
            )

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        split = row.split(factor=0.3)
        col_names = split.column()
        col_props = split.column()

        col_names.label(text="Non Manifold:")
        col_names.label(text="Line Width:")
        col_names.separator()
        col_names.label(text="Triangles:")
        col_names.label(text="Ngons:")

        col_props.prop(self, "non_manifold_color", text="")
        col_props.prop(self, "line_width", text="")
        col_props.separator()
        col_props.prop(self, "triangles_color", text="")
        col_props.prop(self, "ngons_color", text="")


def register():
    bpy.utils.register_class(MeshCheckPreferences)

def unregister():
    bpy.utils.unregister_class(MeshCheckPreferences)