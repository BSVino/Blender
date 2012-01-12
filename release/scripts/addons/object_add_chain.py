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
    "name": "Add Chain",
    "author": "Brian Hinton (Nichod)",
    "version": (0,1),
    "blender": (2, 5, 9),
    "api": 39685,
    "location": "View3D > Add > Mesh",
    "description": "Adds Chain with curve guide for easy creation",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Object/Add_Chain",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22203",
    "category": "Object"}

import bpy

def Add_Chain():
  

    ##Adds Empty to scene
    bpy.ops.object.add(type='EMPTY',
                       view_align=False,
                       enter_editmode=False,
                       location=(0, 0, 0), 
                       rotation=(0, 0, 0),
                       )

    ##Changes name of Empty to rot_link adds variable emp
    emp = bpy.context.object
    emp.name = "rot_link"

    ##Rotate emp ~ 90 degrees
    emp.rotation_euler = [1.570796, 0, 0]

    ##Adds Curve Path to scene
    bpy.ops.curve.primitive_nurbs_path_add(view_align=False,
                                           enter_editmode=False,
                                           location=(0, 0, 0),
                                           rotation=(0, 0, 0),
                                           )

    ##Change Curve name to deform adds variable curv
    curv = bpy.context.object
    curv.name = "deform"

    ##Inserts Torus primitive
    bpy.ops.mesh.primitive_torus_add(major_radius=1,
                                     minor_radius=0.25,
                                     major_segments=12,
                                     minor_segments=4,
                                     use_abso=False,
                                     abso_major_rad=1,
                                     abso_minor_rad=0.5,
                                     )

    ##Positions Torus primitive to center of scene
    bpy.context.active_object.location = 0.0, 0.0, 0.0
    
    ##Reseting Torus rotation in case of 'Align to view' option enabled
    bpy.context.active_object.rotation_euler = 0.0, 0.0, 0.0
    

    ##Changes Torus name to chain adds variable tor
    tor = bpy.context.object
    tor.name = "chain"

    ##Adds Array Modifier to tor
    bpy.ops.object.modifier_add(type='ARRAY')

    ##Adds subsurf modifier tor
    bpy.ops.object.modifier_add(type='SUBSURF')

    ##Smooths tor
    bpy.ops.object.shade_smooth()

    ##Select curv 
    sce = bpy.context.scene
    sce.objects.active = curv

    ##Toggle into editmode
    bpy.ops.object.editmode_toggle()

    ## TODO, may be better to move objects directly.
    ##Translate curve object
    bpy.ops.transform.translate(value=(2, 0, 0),
                                constraint_axis=(True, False, False),
                                constraint_orientation='GLOBAL',
                                mirror=False,
                                proportional='DISABLED',
                                proportional_edit_falloff='SMOOTH',
                                proportional_size=1,
                                snap=False,
                                snap_target='CLOSEST',
                                snap_point=(0, 0, 0),
                                snap_align=False,
                                snap_normal=(0, 0, 0),
                                release_confirm=False,
                                )

    ##Toggle into objectmode
    bpy.ops.object.editmode_toggle()

    ##Select tor or chain
    sce.objects.active = tor

    ##Selects Array Modifier for editing
    array = tor.modifiers['Array']

    ##Change Array Modifier Parameters
    array.fit_type = 'FIT_CURVE'
    array.curve = curv
    array.offset_object = emp
    array.use_object_offset = True
    array.relative_offset_displace = 0.549, 0.0, 0.0

    ##Add curve modifier
    bpy.ops.object.modifier_add(type='CURVE')

    ##Selects Curve Modifier for editing
    cur = tor.modifiers['Curve']

    ##Change Curve Modifier Parameters
    cur.object = curv

#makes AddChain an operator
class AddChain(bpy.types.Operator):
    '''Add a Chain.'''
    bl_idname = "mesh.primitive_chain_add"
    bl_label = "Add Chain"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        Add_Chain()

        return {'FINISHED'}

# Register the operator
def menu_func(self, context):
    self.layout.operator(AddChain.bl_idname, text="Chain", icon='PLUGIN')


def register():
    bpy.utils.register_module(__name__)

    # Add "Chain" menu to the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Chain" menu from the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
