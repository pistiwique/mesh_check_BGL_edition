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

bl_info = {
    "name": "Mesh Check BGL edition",
    "description": "",
    "author": "Legigan Jeremy AKA Pistiwique",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "View3D",
    "warning": "This addon is still in development.",
    "wiki_url": "",
    "category": "Object"}

if "bpy" in locals():
    import importlib

    reloadable_modules = [
        "preferences",
        "properties",
        "ui"
        ]

    for module in reloadable_modules:
        if module in locals():
            importlib.reload(locals()[module])

from . import (preferences,
               properties,
               ui
               )


def register():
    preferences.register()
    properties.register()
    ui.register()

def unregister():
    ui.unregister()
    properties.unregister()
    preferences.unregister()
