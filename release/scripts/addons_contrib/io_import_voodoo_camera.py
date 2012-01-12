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

bl_info = {
    "name": "Import Voodoo camera",
    "author": "Fazekas Laszlo",
    "version": (0, 7),
    "blender": (2, 5, 7),
    "api": 36339,
    "location": "File > Import > Voodoo camera",
    "description": "Imports a Blender (2.4x or 2.5x) Python script from the Voodoo camera tracker software.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Import-Export/Voodoo_camera",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22510",
    "category": "Import-Export"}

"""
This script loads a Blender Python script from the Voodoo camera
tracker program into Blender 2.5x.

It processes the script as a text file and not as a Python executable
because of the incompatible Python APIs of Blender 2.4x and 2.5x.
"""

import bpy
from bpy.props import *
import mathutils
import os
import string
import math

def voodoo_import(infile,ld_cam,ld_points):

    checktype = os.path.splitext(infile)[1]

    if checktype.upper() != '.PY':
        print ("Selected file: ",infile)
        raise IOError("The selected input file is not a *.py file")
        return

    print ("--------------------------------------------------")
    print ("Importing Voodoo file: ", infile)

    file = open(infile,'rU')
    scene = bpy.context.scene
    initfr = scene.frame_current
    b24= True

    dummy = bpy.data.objects.new('voodoo_scene', None)
    dummy.location = (0.0, 0.0, 0.0)
    dummy.rotation_euler = ( -3.141593/2, 0.0, 0.0)
    dummy.scale = (0.2, 0.2, 0.2)
    scene.objects.link(dummy)

    if ld_cam:
        data = bpy.data.cameras.new('voodoo_render_cam')
        vcam = bpy.data.objects.new('voodoo_render_cam', data)
        vcam.location = (0.0, 0.0, 0.0)
        vcam.rotation_euler = (0.0, 0.0, 0.0)
        vcam.scale = (1.0, 1.0, 1.0)
        data.lens = 35.0
        data.shift_x = 0.0
        data.shift_y = 0.0
        data.dof_distance = 0.0
        data.clip_start = 0.1
        data.clip_end = 1000.0
        data.draw_size = 0.5
        scene.objects.link(vcam)
        vcam.parent = dummy

    if ld_points:
        data = bpy.data.meshes.new('voodoo_FP3D_cloud')
        mesh = bpy.data.objects.new('voodoo_FP3D_cloud', data)
        mesh.location = (0.0, 0.0, 0.0)
        mesh.rotation_euler = (3.141593/2, 0.0, 0.0)
        mesh.scale = (5.0, 5.0, 5.0)
        scene.objects.link(mesh)
        mesh.parent = dummy

    verts = []

    def process_line(line):
        lineSplit = line.split()

        if (line[0] == '#'): return

        if b24:

            # Blender 2.4x mode
            # process camera commands

            if ld_cam:
                if (line[0] == 'c' and line[1] != 'r'):
                    pos= line.find('.lens')

                    if (pos != -1):
                        fr = int(lineSplit[0][1:pos],10)
                        scene.frame_set(fr)
                        vcam.data.lens= float(lineSplit[2])
                        vcam.data.keyframe_insert('lens')
                        return

                if (line[0] == 'o'):
                    pos= line.find('.setMatrix')

                    if (pos != -1):
                        fr = int(lineSplit[0][1:pos],10)
                        scene.frame_set(fr)
                        # for up to 2.55
                        # vcam.matrix_world = eval('mathutils.' + line.rstrip()[pos+21:-1])
                        # for 2.56, from Michael (Meikel) Oetjen 
                        # vcam.matrix_world = eval('mathutils.Matrix(' + line.rstrip()[pos+28:-2].replace('[','(',4).replace(']',')',4) + ')')
                        # for 2.57
                        vcam.matrix_world = eval('mathutils.Matrix([' + line.rstrip()[pos+28:-2] + '])')
                        vcam.keyframe_insert('location')
                        vcam.keyframe_insert('scale')
                        vcam.keyframe_insert('rotation_euler')
                        return

            # process mesh commands

            if ld_points:
                if (line[0] == 'v'):
                    pos= line.find('NMesh.Vert')

                    if (pos != -1):
                        verts.append(eval(line[pos+10:]))

            return

        # Blender 2.5x mode
        # process camera commands

        if ld_cam:
            pos= line.find('set_frame')

            if (pos == -1):
                pos= line.find('frame_set')

            if (pos != -1):
                scene.frame_set(eval(line[pos+9:]))
                return

            pos= line.find('vcam.data.lens')

            if (pos != -1):
                vcam.data.lens= float(lineSplit[2])
                vcam.data.keyframe_insert('lens')
                return

            pos= line.find('.Matrix')

            if (pos != -1):

                # for up to 2.55
                # vcam.matrix_world = eval('mathutils' + line[pos:])

                # for 2.56
                # if (line[pos+8] == '['):
                #   # from Michael (Meikel) Oetjen
                #     vcam.matrix_world = eval('mathutils.Matrix((' + line.rstrip()[pos+9:-1].replace('[','(',3).replace(']',')',4) + ')')
                # else:
                #   vcam.matrix_world = eval('mathutils' + line[pos:])

                # for 2.57
                vcam.matrix_world = eval('mathutils.Matrix([' + line.rstrip()[pos+8:-1] + '])')
                vcam.keyframe_insert('location')
                vcam.keyframe_insert('scale')
                vcam.keyframe_insert('rotation_euler')
                return

        # process mesh commands

        if ld_points:
            pos= line.find('.append')

            if (pos != -1):
                verts.append(eval(line[pos+8:-2]))

    #read lines

    for line in file.readlines():

        if (b24 and (line.find('import') != -1) and (line.find('bpy') != -1)):
            b24= False

        process_line(line)

    scene.frame_set(initfr)

    if ld_points:
        mesh.data.from_pydata(verts, [], [])

    mesh.data.update()


# Operator
class ImportVoodooCamera(bpy.types.Operator):
    ''''''
    bl_idname = "import.voodoo_camera"
    bl_label = "Import Voodoo camera"
    bl_description = "Load a Blender export script from the Voodoo motion tracker"
    bl_options = {'REGISTER', 'UNDO'}

    filepath = StringProperty(name="File Path",
        description="Filepath used for processing the script",
        maxlen= 1024,default= "")

#    filter_python = BoolProperty(name="Filter python",
#    description="",default=True,options={'HIDDEN'})

    load_camera = BoolProperty(name="Load camera",
        description="Load the camera",
        default=True)
    load_points = BoolProperty(name="Load points",
        description="Load the FP3D point cloud",
        default=True)

    def execute(self, context):
        voodoo_import(self.filepath,self.load_camera,self.load_points)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


# Registering / Unregister
def menu_func(self, context):
    self.layout.operator(ImportVoodooCamera.bl_idname, text="Voodoo camera", icon='PLUGIN')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)


if __name__ == "__main__":
    register()
