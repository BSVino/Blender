# Paul "BrikBot" Marshall
# Created: July 1, 2011
# Last Modified: November 17, 2011
# Homepage (blog): http://post.darkarsenic.com/
#                       //blog.darkarsenic.com/
# Thanks to Meta-Androco, RickyBlender, Ace Dragon, and PKHG for ideas
#   and testing.
#
# Coded in IDLE, tested in Blender 2.59.  NumPy Recommended.
# Search for "@todo" to quickly find sections that need work.
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  The Blender Rock Creation tool is for rapid generation of
#  mesh rocks in Blender.
#  Copyright (C) 2011  Paul Marshall
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

bl_info = {
    "name": "Rock Generator",
    "author": "Paul Marshall (brikbot)",
    "version": (1, 3),
    "blender": (2, 6, 0),
    "api": 41875,
    "location": "View3D > Add > Rock Generator",
    "description": "Adds a mesh rock to the Add Mesh menu",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5"\
        "/Py/Scripts/Add_Mesh/Rock_Generator",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=27314",
    "category": "Add Mesh"}

if "bpy" in locals():
    import imp
    imp.reload(rockgen)
else:
    from add_mesh_rocks import rockgen

import bpy


# Register:
def menu_func_rocks(self, context):
    self.layout.operator(rockgen.rocks.bl_idname,
                         text="Rock Generator",
                         icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_mesh_add.append(menu_func_rocks)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_mesh_add.remove(menu_func_rocks)


if __name__ == "__main__":
    register()
