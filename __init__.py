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
    "author": "Legigan Jeremy AKA Pistiwique/1COD",
    "version": (0, 1, 1),
    "blender": (2, 93, 0),
    "location": "View3D",
    "wiki_url": "",
    "category": "Object"}


debug = 0

modules = (
    "preferences",
    "properties",
    "ui"
)


for mod in modules:
    exec(f"from . import {mod}")


def register():

    import importlib

    for mod in modules:
        if debug:
            exec(f"importlib.reload({mod})")
 
        exec(f"{mod}.register()")


def unregister():
    for mod in modules:
        exec(f"{mod}.unregister()")
