# -*- coding: utf-8 -*-
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####



# Blender Add-Ons menu registration (in User Prefs)
bl_info = {
    'name': 'Cursor Control',
    'author': 'Morgan Mörtsell (Seminumerical)',
    'version': (0, 7, 0),
    'blender': (2, 5, 9),
    'api': 39307,
    'location': 'View3D > Properties > Cursor',
    'description': 'Control the Cursor',
    'warning': '', # used for warning icon and text in addons panel
    'wiki_url': 'http://blenderpythonscripts.wordpress.com/',
    'tracker_url': '',
    'category': '3D View'}



import bpy

# To support reload properly, try to access a package var, if it's there, reload everything
if "local_var" in locals():
    import imp
    imp.reload(data)
    imp.reload(ui)
    imp.reload(operators)
    imp.reload(history)
    imp.reload(memory)
else:
    from cursor_control import data
    from cursor_control import ui
    from cursor_control import operators
    from cursor_control import history
    from cursor_control import memory

local_var = True

def register():
    bpy.utils.register_module(__name__)
    # Register Cursor Control Structure
    bpy.types.Scene.cursor_control = bpy.props.PointerProperty(type=data.CursorControlData, name="")
    bpy.types.Scene.cursor_history = bpy.props.PointerProperty(type=history.CursorHistoryData, name="")
    bpy.types.Scene.cursor_memory  = bpy.props.PointerProperty(type=memory.CursorMemoryData, name="")
    # Register menu
    bpy.types.VIEW3D_MT_snap.append(ui.menu_callback)

def unregister():
    # Register menu
    bpy.types.VIEW3D_MT_snap.remove(ui.menu_callback)
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
