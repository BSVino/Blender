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

# <pep8-80 compliant>

bl_info = {
    "name": "STL format",
    "author": "Guillaume Bouchard (Guillaum)",
    "version": (1, 0),
    "blender": (2, 5, 7),
    "api": 35622,
    "location": "File > Import-Export > Stl",
    "description": "Import-Export STL files",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
                "Scripts/Import-Export/STL",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"
                   "func=detail&aid=22837",
    "support": 'OFFICIAL',
    "category": "Import-Export"}

# @todo write the wiki page

"""
Import-Export STL files (binary or ascii)

- Import automatically remove the doubles.
- Export can export with/without modifiers applied

Issues:

Import:
    - Does not handle the normal of the triangles
    - Does not handle endien
"""

if "bpy" in locals():
    import imp
    if "stl_utils" in locals():
        imp.reload(stl_utils)
    if "blender_utils" in locals():
        imp.reload(blender_utils)

import os

import bpy
from bpy.props import StringProperty, BoolProperty, CollectionProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper


class ImportSTL(bpy.types.Operator, ImportHelper):
    '''Load STL triangle mesh data'''
    bl_idname = "import_mesh.stl"
    bl_label = "Import STL"
    bl_options = {'UNDO'}

    filename_ext = ".stl"

    filter_glob = StringProperty(
            default="*.stl",
            options={'HIDDEN'},
            )
    files = CollectionProperty(
            name="File Path",
            type=bpy.types.OperatorFileListElement,
            )
    directory = StringProperty(
            subtype='DIR_PATH',
            )

    def execute(self, context):
        from . import stl_utils
        from . import blender_utils

        paths = [os.path.join(self.directory, name.name)
                 for name in self.files]

        if not paths:
            paths.append(self.filepath)

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action='DESELECT')

        for path in paths:
            objName = bpy.path.display_name(os.path.basename(path))
            tris, pts = stl_utils.read_stl(path)
            blender_utils.create_and_link_mesh(objName, tris, pts)

        return {'FINISHED'}


class ExportSTL(bpy.types.Operator, ExportHelper):
    '''Save STL triangle mesh data from the active object'''
    bl_idname = "export_mesh.stl"
    bl_label = "Export STL"

    filename_ext = ".stl"

    ascii = BoolProperty(name="Ascii",
                         description="Save the file in ASCII file format",
                         default=False)
    apply_modifiers = BoolProperty(name="Apply Modifiers",
                                   description="Apply the modifiers "
                                               "before saving",
                                   default=True)

    def execute(self, context):
        from . import stl_utils
        from . import blender_utils
        import itertools

        faces = itertools.chain.from_iterable(
            blender_utils.faces_from_mesh(ob, self.apply_modifiers)
            for ob in context.selected_objects)

        stl_utils.write_stl(self.filepath, faces, self.ascii)

        return {'FINISHED'}


def menu_import(self, context):
    self.layout.operator(ImportSTL.bl_idname,
                         text="Stl (.stl)").filepath = "*.stl"


def menu_export(self, context):
    default_path = os.path.splitext(bpy.data.filepath)[0] + ".stl"
    self.layout.operator(ExportSTL.bl_idname,
                         text="Stl (.stl)").filepath = default_path


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_import)
    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_import)
    bpy.types.INFO_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()
