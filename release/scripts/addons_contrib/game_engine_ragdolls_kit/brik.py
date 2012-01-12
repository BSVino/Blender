#brik_0_2.py

# ***** BEGIN GPL LICENSE BLOCK *****
#
# Script copyright (C) Marcus Jenkins (Blenderartists user name FunkyWyrm)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
# --------------------------------------------------------------------------

"""
brik is the Blender Ragdoll Implementation Kit.

It aims to provide a tool kit that enables the easy implementation of ragdolls in Blender.

Acnowledgements:
    This section comes first because I am grateful to Thomas Eldredge (teldredge on
www.blenderartists.com). Without his great script to take apart, I would never have got
around to this even though it's been in my todo list for a while. The link to his thread is
http://blenderartists.org/forum/showthread.php?t=152150
    
Website:
    Blenderartists script development thread is:
    http://blenderartists.org/forum/showthread.php?t=199191

Bugs:
    
    Editing a text file after hitting the create or destroy button and then
    changing an option such as writing the hierarchy file will undo the edits
    to the text. This is a known bug due to the lack of a text editor global
    undo push. See the bug tracker:
        https://projects.blender.org/tracker/index.php?func=detail&aid=21043&group_id=9&atid=498
            
    Creating rigid body structures based on multiple armatures in the scene that have similarly
    named bones can cause some rigid body objects to be removed. This can probably be fixed by
    testing for membership of a group. However, similarly named bones should be renamed to a
    unique name since bone name and driver object name being similar is essential for correct
    operation of both the brik script and the brik_Use_doll game engine script.
    
    Running Create multiple times on the same armature will recreate the rigid body joints
    rather than editing existing ones.

Notes:
    
    The mass of each object could be calculated using their volume. The
    armature could be assigned a mass and the bones' mass could be calculated
    from this using their volume.
    
    Non-deforming bones do not have rigid body objects created for them. 
    Perhaps this would be better given as a toggle option.
"""

import bpy
from bpy.props import *
import mathutils
from mathutils import Vector
from game_engine_ragdolls_kit.brik_funcs import *

class VIEW3D_PT_brik_panel(bpy.types.Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'objectmode'
    bl_label = 'brik'
    
    #Draws the panel header in the tools pane
    def draw_header(self, context):
        layout = self.layout
        layout.label(text='', icon='CONSTRAINT_BONE')
    
    #Draws the brik panel in the tools pane
    def draw(self, context):
        
        ob = bpy.context.object

        layout = self.layout

        col = layout.column()
        if ob:
            col.prop(ob, 'name', text = 'Selected', icon = 'OUTLINER_OB_'+str(ob.type))
    
            layout.separator()
    
            box = layout.box()
            box.label(text = 'Create or remove?')
            
            if ob.type == 'ARMATURE':
                col = box.column(align=True)
                col.operator('object.brik_create_structure', text = 'Create structure')
                
                row = col.row()
                remove_structure_active = 'brik_structure_created' in ob.keys() and ob['brik_structure_created']
                row.active = remove_structure_active
                row.operator('object.brik_destroy_structure', text = 'Remove structure')
                
                col = box.column(align = True)
                col.operator('object.brik_create_hit_boxes', text = 'Create hit boxes')
                
                row = col.row()
                remove_hit_boxes_active = 'brik_hit_boxes_created' in ob.keys() and ob['brik_hit_boxes_created']
                row.active = remove_hit_boxes_active
                row.operator('object.brik_remove_hit_boxes', text = 'Remove hit boxes')
            else:
                box.label(text='Select armature')
                
            game_options_active = 'brik_structure_created' in ob.keys() and ob['brik_structure_created'] \
                                    and 'brik_hit_boxes_created' in ob.keys() and ob['brik_hit_boxes_created']
            col = box.column(align = True)
            col.active = game_options_active
            col.label(text='Game options:')
            col.operator('object.brik_write_game_file', text = 'Write game file')
            create_logic_active = 'brik_file_written' in ob.keys() and ob['brik_file_written']
            row = col.row()
            row.active = create_logic_active
            row.operator('object.brik_create_game_logic', text = 'Create game logic')
                
        else:
            col.label(text='Select an object')

class brik_create_structure(bpy.types.Operator):
    bl_label = 'brik create structure operator'
    bl_idname = 'object.brik_create_structure'
    bl_description = 'Create a rigid body structure based on an amature.'
    bl_options = {'REGISTER', 'UNDO'}

    #Properties that can be changed by the user

    prefix = StringProperty(name='Prefix', \
                            description='Prefix to be appended to the bone name that defines the rigid body object.',\
                            default='RB_')
    
    driver_length = FloatProperty(name='Driver length',\
                              description='Length of rigid body driver objects as proportion of bone length.',\
                              min=0.05,\
                              max=1.0,\
                              step=0.05,\
                              default=0.8)
    
    driver_width = FloatProperty(name = 'Driver width',\
                                  description='Width of rigid body driver objects as proportion of bone length',\
                                  min=0.05,\
                                  max=1.0,\
                                  step=0.05,\
                                  default=0.2)
    
    add_to_group = BoolProperty(name='Add to group',\
                                description='Add all created objects to a group',\
                                default=True)
                                
    box_type = EnumProperty(name="Box type",
        description="Shape that rigid body objects are created from.",
        items=[ \
          ('BONE', "Bone",
              "Plain bone dimensions are used."),
          ('ENVELOPE', "Envelope",
              "Bone envelope dimensions are used."),
          ('BBONE', "BBone",
              "BBone dimensions are used. "\
              "(BBones can be scaled using Ctrl+Alt+S in armature edit mode.)"),
          ],
        default='BBONE')
    
    #Create the rigid body boxes
    def create_boxes(self, armature):
        bones_dict = armature.pose.bones      #Dictionary of posebones
        bones = bones_dict.values()
        armature = bpy.context.object
        
        RB_dict = {}            #Dictionary of rigid body objects
        
        armature['brik_bone_driver_dict'] = {}
        armature['brik_armature_locator_name'] = ''
        
        #All deforming bones have boxes created for them
        for bone in bones:
            if bone.bone.use_deform:
                #print(self.box_type)
                box = None
                volume = 0.0
                #Create boxes that do not exist
                if self.box_type == 'BONE':
                    box, volume = create_box(self.prefix, self.driver_length, self.driver_width, armature, bone)
                elif self.box_type == 'BBONE':
                    box, volume = create_box_bbone(self.prefix, armature, bone)
                elif self.box_type == 'ENVELOPE':
                    box, volume = create_box_envelope(self.prefix, armature, bone)
                #box = create_box(self.prefix, self.driver_length, self.driver_width, armature, bone)
                RB_dict[box.name] = box
                armature['brik_bone_driver_dict'][bone.name] = box.name
            
                #Orientate and position the box
                self.position_box(armature, bone, box)
                box['brik_bone_name'] = bone.name
                
                #### Contributed by Wraaah #########
                box.game.physics_type = 'RIGID_BODY'
                box.game.mass = volume * 1.5 #Density I used was 1.5
                ##############################
        return RB_dict
    
    def make_bone_constraints(self, armature, RB_dict):
        bones_dict = armature.pose.bones
        
        for bone in bones_dict:
            if not 'brik_copy_rot' in bone.constraints:
                constraint = bone.constraints.new(type='COPY_ROTATION')
                constraint.name = 'brik_copy_rot'
                constraint.target = RB_dict[armature['brik_bone_driver_dict'][bone.name]]
            if not 'brik_copy_loc' in bone.constraints:
                if not bone.parent:
                    #print(bone.head, bone.tail)
                    if armature['brik_armature_locator_name'] == '':
                        bpy.ops.object.add(type='EMPTY')
                        locator = bpy.context.object
                        locator.name = 'brik_'+armature.name+'_loc'
                        locator.location = (0.0,-bone.length/2,0.0)
                        locator.parent = RB_dict[armature['brik_bone_driver_dict'][bone.name]]
                        armature['brik_armature_locator_name'] = locator.name
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.ops.object.select_name(name=armature.name, extend=False)
                    else:
                        locator = bpy.data.objects['brik_armature_locator_name']
                        locator.location = (0.0,-bone.length/2,0.0)
                        locator.parent = RB_dict[armature['brik_bone_driver_dict'][bone.name]]
                    constraint = bone.constraints.new(type='COPY_LOCATION')
                    constraint.name = 'brik_copy_loc'
                    constraint.target = locator
    
    def reshape_boxes(self, armature):
        '''
        Reshape an existing box based on parameter changes.
        I introduced this as an attempt to improve responsiveness. This should
        eliminate the overhead from creating completely new meshes or objects on
        each refresh.
        '''
        objects = bpy.context.scene.objects
        
        for bone_name in armature['brik_bone_driver_dict']:
            bone = armature.bones[bone_name]
            box = objects[armature['brik_bone_driver_dict'][bone_name]]
        
            height = bone.length
            #gap = height * self.hit_box_length      #The distance between two boxes
            box_length = bone.length*self.driver_length
            width = bone.length * self.driver_width
            
            x = width/2
            y = box_length/2
            z = width/2
            
            verts = [[-x,y,-z],[-x,y,z],[x,y,z],[x,y,-z],\
                     [x,-y,-z],[-x,-y,-z],[-x,-y,z],[x,-y,z]]
            
            #This could be a problem if custom object shapes are used...
            count = 0
            for vert in box.data.vertices:
                vert.co = Vector(verts[count])
                count += 1
    
    #Orient the box to the bone and set the box object centre to the bone location
    def position_box(self, armature, bone, box):
        scene = bpy.context.scene
        
        #Set the box to the bone orientation and location
        box.matrix_world = bone.matrix
        box.location = armature.location+bone.bone.head_local+(bone.bone.tail_local-bone.bone.head_local)/2
    
    #Set up the objects for rigid body physics and create rigid body joints.
    def make_RB_constraints(self, armature, RB_dict):
        bones_dict = armature.pose.bones
        
        for box in RB_dict:
            bone = bones_dict[RB_dict[box]['brik_bone_name']]
            
            boxObj = RB_dict[box]
            
            #Make the radius half the length of the longest axis of the box
            radius_driver_length = (bone.length*self.driver_length)/2
            radius_driver_width = (bone.length*self.driver_width)/2
            radius = radius_driver_length
            if radius_driver_width > radius:
                radius = radius_driver_width
            
            
            #Set up game physics attributes
            boxObj.game.use_actor = True
            boxObj.game.use_ghost = False
            boxObj.game.physics_type = 'RIGID_BODY'
            boxObj.game.use_collision_bounds = True
            boxObj.game.collision_bounds_type = 'BOX'
            boxObj.game.radius = radius
                
            #Make the rigid body joints
            if bone.parent:
                #print(bone, bone.parent)
                boxObj['brik_joint_target'] = armature['brik_bone_driver_dict'][bone.parent.name]
                RB_joint = boxObj.constraints.new('RIGID_BODY_JOINT')
                RB_joint.pivot_y = -bone.length/2
                RB_joint.target = RB_dict[boxObj['brik_joint_target']]
                RB_joint.use_linked_collision = True
                RB_joint.pivot_type = ("GENERIC_6_DOF")
                RB_joint.limit_angle_max_x = bone.ik_max_x
                RB_joint.limit_angle_max_y = bone.ik_max_y
                RB_joint.limit_angle_max_z = bone.ik_max_z
                RB_joint.limit_angle_min_x = bone.ik_min_x
                RB_joint.limit_angle_min_y = bone.ik_min_y
                RB_joint.limit_angle_min_z = bone.ik_min_z
                RB_joint.use_limit_x = True
                RB_joint.use_limit_y = True
                RB_joint.use_limit_z = True
                RB_joint.use_angular_limit_x = True
                RB_joint.use_angular_limit_y = True
                RB_joint.use_angular_limit_z = True
            else:
                boxObj['brik_joint_target'] = 'None'
    
    def add_boxes_to_group(self, armature, RB_dict):
        #print("Adding boxes to group")
        group_name = self.prefix+armature.name+"_Group"
        if not group_name in bpy.data.groups:
            group = bpy.data.groups.new(group_name)
        else:
            group = bpy.data.groups[group_name]
        #print(group)
        #print(RB_dict)
        for box in RB_dict:
            if not box in group.objects:
                group.objects.link(bpy.context.scene.objects[box])
        
        return
    
    #Armature and mesh need to be set to either no collision or ghost. No collision
    #is much faster.
    def set_armature_physics(self, armature):
        armature.game.physics_type = 'NO_COLLISION'
        for child in armature.children:
            if hasattr(armature, "['brik_hit_boxes_created']"):
                if child.name in armature['brik_bone_hit_box_dict'].values():
                    continue
                else:
                    child.game.physics_type = 'NO_COLLISION'
            else:
                child.game.physics_type = 'NO_COLLISION'
                

    #The ui of the create operator that appears when the operator is called
    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self.properties, 'prefix')
        box.prop(self.properties, 'add_to_group')
        box.prop(self.properties, 'box_type')
        if self.box_type == 'BONE':
            box.prop(self.properties, 'driver_length')
            box.prop(self.properties, 'driver_width')
            
    #The main part of the create operator
    def execute(self, context):
        #print("\n##########\n")
        #print("EXECUTING brik_create_structure\n")
        
        armature = context.object
        
        self.set_armature_physics(armature)
        
        
        if 'brik_structure_created' in armature.keys()\
                and armature['brik_structure_created'] == True\
                and self.box_type == 'BONE':
            
            self.reshape_boxes(armature)
            
        else:
            RB_dict = self.create_boxes(armature)
            armature['brik_structure_created'] = True
            armature['brik_prefix'] = self.prefix
            
            self.make_RB_constraints(armature, RB_dict)
            self.make_bone_constraints(armature, RB_dict)
            
            if self.add_to_group:
                self.add_boxes_to_group(armature, RB_dict)
        
        return{'FINISHED'}

class brik_destroy_structure(bpy.types.Operator):
    bl_label = 'brik destroy structure operator'
    bl_idname = 'object.brik_destroy_structure'
    bl_description = 'Destroy a rigid body structure created by this brik.'
    bl_options = {'REGISTER', 'UNDO'}
    
    '''
    For some reason the remove operators give a "cyclic" warning in the console.
    
    I have no idea what this means and have not been able to find out what this means.
    '''
    
    def execute(self, context):
        print("\n##########\n")
        print("EXECUTING brik_remove_structure")
        armature = context.object
        scene = context.scene
        
        #Clean up all created objects, their meshes and bone constraints
        for bone_name in armature['brik_bone_driver_dict']:
            driver = scene.objects[armature['brik_bone_driver_dict'][bone_name]]
            #Unlink and remove the mesh
            mesh = driver.data
            driver.data = None
            mesh.user_clear()
            bpy.data.meshes.remove(mesh)
            #Unlink and remove the object
            scene.objects.unlink(driver)
            driver.user_clear()
            bpy.data.objects.remove(driver)
            
            #Remove bone constraints
            bone = armature.pose.bones[bone_name]
            if 'brik_copy_rot' in bone.constraints:
                const = bone.constraints['brik_copy_rot']
                bone.constraints.remove(const)
            if 'brik_copy_loc' in bone.constraints:
                const = bone.constraints['brik_copy_loc']
                bone.constraints.remove(const)
        
        #Remove armature locator
        locator = bpy.data.objects[armature['brik_armature_locator_name']]
        scene.objects.unlink(locator)
        locator.user_clear()
        bpy.data.objects.remove(locator)
        
        #Remove driver group
        group_name = armature['brik_prefix']+armature.name+'_Group'
        if group_name in bpy.data.groups:
            group = bpy.data.groups[group_name]
            bpy.data.groups.remove(group)
        
        #Remove custom properties
        del armature['brik_armature_locator_name']
        del armature['brik_structure_created']
        del armature['brik_bone_driver_dict']
        del armature['brik_prefix']
    
        return{'FINISHED'}
        
class brik_create_game_logic(bpy.types.Operator):
    bl_label = 'brik create game logic operator'
    bl_idname = 'object.brik_create_game_logic'
    bl_description = 'Create the game logic for the created objects.'
    bl_options = {'REGISTER', 'UNDO'}
    
    template_path = bpy.utils.script_paths()[0]+'\\addons\\game_engine_ragdolls_kit\\templates\\'
    
    game_script_list = ['brik_load.py', \
                        'brik_init_ragdoll.py', \
                        'brik_spawn.py']
                            
    
    def set_up_armature_logic(self, armature):
        
        if not 'brik_use_ragdoll' in armature.game.properties:
            
            bpy.ops.object.game_property_new()
            prop = armature.game.properties[-1]
            prop.name = 'brik_use_ragdoll'
            prop.type = 'BOOL'
            prop.value = False
            
            bpy.ops.object.game_property_new()
            prop = armature.game.properties[-1]
            prop.name = 'brik_init_ragdoll'
            prop.type = 'BOOL'
            prop.value = True
            
            #Logic to spawn the rigid body boxes
            bpy.ops.logic.sensor_add(type='PROPERTY', name='brik_use_changed_sens', object=armature.name)
            sens = armature.game.sensors[-1]
            sens.property = 'brik_use_ragdoll'
            sens.evaluation_type = 'PROPCHANGED'
            
            bpy.ops.logic.controller_add(type='PYTHON', name='brik_init_ragdoll_cont', object=armature.name)
            cont = armature.game.controllers[-1]
            cont.mode = 'MODULE'
            cont.module = 'brik_init_ragdoll.main'
            
            bpy.ops.logic.actuator_add(type='EDIT_OBJECT', name='brik_spawn_boxes_act', object=armature.name)
            act = armature.game.actuators[-1]
            act.mode = 'ADDOBJECT'
            
            cont.link(sens, act)
            
            #Logic to change the value of brik_use_ragdoll property
            bpy.ops.logic.sensor_add(type='KEYBOARD', name='brik_set_use_ragdoll_sens', object=armature.name)
            sens = armature.game.sensors[-1]
            sens.key = 'SPACE'
            
            bpy.ops.logic.controller_add(type='LOGIC_AND', name='brik_set_use_ragdoll_cont', object=armature.name)
            cont = armature.game.controllers[-1]
            
            bpy.ops.logic.actuator_add(type='PROPERTY', name='brik_set_use_ragdoll_act', object=armature.name)
            act = armature.game.actuators[-1]
            act.mode = 'ASSIGN'
            act.property = 'brik_use_ragdoll'
            act.value = "True"
            
            cont.link(sens, act)
            
            #Logic to use the ragdoll.
            bpy.ops.logic.sensor_add(type='PROPERTY', name='brik_use_sens', object=armature.name)
            sens = armature.game.sensors[-1]
            sens.property = 'brik_use_ragdoll'
            sens.value = 'True'
            sens.use_pulse_true_level = True
            
            bpy.ops.logic.controller_add(type='LOGIC_AND', name='brik_use_cont', object=armature.name)
            cont = armature.game.controllers[-1]
            
            bpy.ops.logic.actuator_add(type='ARMATURE', name='brik_use_act', object=armature.name)
            act = armature.game.actuators[-1]
            act.mode = 'RUN'
            
            cont.link(sens, act)
    
    def set_up_spawn_logic(self, armature):
        print('SETTING UP SPAWN LOGIC')
        scene = bpy.context.scene
        
        #Need to use data to avoid naming conflicts
        if not 'brik_spawn_location' in bpy.data.objects:
            bpy.ops.object.add()
            spawn_object = bpy.context.object
            spawn_object.name = 'brik_spawn_location'
        else:
            spawn_object = bpy.data.objects['brik_spawn_location']
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_name(name=armature.name, extend=False)
        
        spawn_object.game.show_state_panel = False
        
        #Quick and dirty check to see if the spawn logic is already set up.
        if not 'brik_spawn_cont' in spawn_object.game.controllers:
            #The logic to spawn the mob
            bpy.ops.logic.sensor_add(type='KEYBOARD', name='brik_Tab_sens', object=spawn_object.name)
            sens = spawn_object.game.sensors[-1]
            sens.key = 'TAB'
            
            bpy.ops.logic.controller_add(type='PYTHON', name='brik_spawn_cont', object=spawn_object.name)
            cont = spawn_object.game.controllers[-1]
            cont.mode = 'MODULE'
            cont.module = 'brik_spawn.main'
            
            bpy.ops.logic.actuator_add(type='EDIT_OBJECT', name='brik_spawn_act', object=spawn_object.name)
            act = spawn_object.game.actuators[-1]
            
            cont.link(sens, act)
            
            #Logic to load structure information
            bpy.ops.logic.sensor_add(type='ALWAYS', name='brik_load_sens', object=spawn_object.name)
            sens = spawn_object.game.sensors[-1]
            
            bpy.ops.logic.controller_add(type='PYTHON', name='brik_load_cont', object=spawn_object.name)
            cont = spawn_object.game.controllers[-1]
            cont.text = bpy.data.texts['brik_load.py']
            
            sens.link(cont)
            
            #Logic to initialise the spawn point with object to add, added object list and added object count.
            bpy.ops.logic.controller_add(type='PYTHON', name='brik_spawn_init_cont', object=spawn_object.name)
            cont = spawn_object.game.controllers[-1]
            cont.mode = 'MODULE'
            cont.module = 'brik_spawn.initialize'
            
            sens.link(cont)
        
        #Properties and text files to define the mobs that can be spawned.
        for text in bpy.data.texts:
            
            print('CONSIDERING TEXT '+text.name)
            prefix = armature['brik_prefix']
            print(text.name[len(prefix):-4])
            
            
            #If there is an armature and text pair.
            if text.name[len(prefix):-4] == armature.name:
                #If no mobs have been accounted for yet.
                if not 'brik_mob_count' in spawn_object.game.properties:
                    print('CREATING PROPERTY brik_mob_count')
                    bpy.ops.object.select_all(action='DESELECT')
                    spawn_object.select = True
                    scene.objects.active = spawn_object
                    
                    bpy.ops.object.game_property_new()
                    count_prop = spawn_object.game.properties[-1]
                    count_prop.name = 'brik_mob_count'
                    count_prop.type = 'INT'
                    count_prop.value = -1   #Initialised to -1 meaning no data controllers yet created.
        
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.ops.object.select_name(name=armature.name, extend=False)
                else:
                    count_prop = spawn_object.game.properties['brik_mob_count']
                
                #Find a list of armature texts currently accounted for in logic.
                current_texts = []
                for cont in spawn_object.game.controllers:
                    if cont.name[:-1] == 'brik_ragdoll_data_':
                        current_texts.append(cont.text)
                
                #Create a new data controller for any text not considered.
                if not text in current_texts:
                    count_prop.value += 1
                    #Controller to store structure information.
                    print('CREATING DATA CONTROLLER')
                    bpy.ops.logic.controller_add(type='PYTHON', name='brik_ragdoll_data_'+str(int(count_prop.value)), object=spawn_object.name)
                    cont = spawn_object.game.controllers[-1]
                    cont.text = text
        
    
    def set_up_hit_box_logic(self, armature, bone_name):
        hit_box = bpy.data.objects[armature['brik_bone_hit_box_dict'][bone_name]]
        scene = bpy.context.scene
        
        #Simply create a property for the ray cast to look for.
        if not 'brik_can_hit' in hit_box.game.properties:
            hit_box.select = True
            scene.objects.active = hit_box
            bpy.ops.object.game_property_new()
            print(*hit_box.game.properties)
            prop = hit_box.game.properties[-1]
            prop.name = 'brik_can_hit'
            prop.type = 'BOOL'
            prop.value = True
            scene.objects.active = armature
            hit_box.select = False
            
        return
    
    def load_game_scripts(self):
        
        for script_name in self.game_script_list:
            if not script_name in bpy.data.texts:
                bpy.data.texts.load(self.template_path+script_name)
                
        return
            
    
    def execute(self, context):
        self.load_game_scripts()
        
        armature = context.object
        
        self.set_up_armature_logic(armature)
        
        for bone_name in armature['brik_optimal_order']:
            self.set_up_hit_box_logic(armature, bone_name)
        
        self.set_up_spawn_logic(armature)
        
        
        return{'FINISHED'}

class brik_write_game_file(bpy.types.Operator):
    bl_label = 'brik write game file operator'
    bl_idname = 'object.brik_write_game_file'
    bl_description = 'Write a file containing a description of the rigid body structure'
    bl_options = {'REGISTER', 'UNDO'} 
    
    #Find the most efficient order to calculate bone rotations in the game engine
    def calculate_structure(self, armature):
        boneDict = armature.pose.bones
        
        boneChainsDict = {}
        maxLength = 0       #This is the length of the longest chain of bones
        
        #Find the chains of bone parentage in the armature
        for poseBone in boneDict:
            bone = poseBone.bone
            boneChain = []
            while True:
                boneChain.append(bone.name)
                if bone.parent:
                    bone = bone.parent
                else:
                    boneChainsDict[boneChain[0]] = boneChain
                    if len(boneChain) > maxLength:
                        maxLength = len(boneChain)
                    break
        
        #Sort the bone chains to find which bone rotations to calculate first
        optimalBoneOrder = self.find_optimal_bone_order(boneChainsDict, maxLength)
        
        return optimalBoneOrder, boneChainsDict
        
    def find_optimal_bone_order(self, boneChainsDict, maxLength):
        tempBoneChainsOrder = []
        
        #Reorder the bone chains so that shorter bone chains are at the start of the list
        for n in range(1,maxLength+1):
            for chain in boneChainsDict:
                if len(boneChainsDict[chain]) == n:
                    tempBoneChainsOrder.append(boneChainsDict[chain])
        
        #Create a final list of bones so that the bones that need to be calculated first are
        #at the start
        finalBoneOrder = []
        for chain in tempBoneChainsOrder:
            finalBoneOrder.append(chain[0])     
        return finalBoneOrder
    
    '''
    I've found a method of reading from an internal text file in the game
    engine... Place the text file in a python script controller set to 'script'
    and it can be accessed as a string through cont.script. To avoid  throwing
    a script compilation error on startup, all text must be enclosed within
    triple quotation marks as a block comment.
    There is no need to mess with different file systems and platforms... It can
    all be done internally. =D
    '''
    
    def save_structure_data(self, armature, optimalBoneOrder, boneChainsDict):
        
        prefix = armature['brik_prefix']
        #Create or clear the text file for this armature
        texts = bpy.data.texts
        if prefix+armature.name+".txt" not in texts:
            dataFile = texts.new(prefix+armature.name+".txt")
        else:
            dataFile = texts[prefix+armature.name+".txt"]
            dataFile.clear()
        
        #Write to the text file
        dataFile.write("'''\n")
        
        dataFile.write(armature.name+"\n")
        
        #Write bone data to the file
        for bone_name in optimalBoneOrder:
            #Write bone name and rigid body box for this bone
            #If the bone is part of a chain (not the root bone)
            dataFile.write(bone_name+"\n")
            
            box_name = armature['brik_bone_driver_dict'][bone_name]
            dataFile.write(box_name+"\n")
            
            if len(boneChainsDict[bone_name])>1:
                parent_bone_name = boneChainsDict[bone_name][1]
                joint_target_name = armature['brik_bone_driver_dict'][parent_bone_name]
                dataFile.write(joint_target_name+"\n")
            else:
                dataFile.write("None\n")
            
            #Write hit box name for this bone
            if 'brik_bone_hit_box_dict' in armature.keys():
                hit_box_name = armature['brik_bone_hit_box_dict'][bone_name]
                dataFile.write(hit_box_name+"\n")
            else:
                dataFile.write('None\n')
            
            obj = bpy.data.objects[armature['brik_bone_driver_dict'][bone_name]]
            
            if not obj['brik_joint_target'] == 'None':
                #Write rigid body joint position to file
                pos_x = obj['joint_position_x']
                pos_y = obj['joint_position_y']
                pos_z = obj['joint_position_z']
                itemString = str(pos_x)+"\n"+str(pos_y)+"\n"+str(pos_z)+"\n"
                dataFile.write(itemString)
                #############################################
                #Should no longer need to do this.
				
                #Write rigid body joint limits to the file
                max_x = obj['rot_max_x']
                max_y = obj['rot_max_y']
                max_z = obj['rot_max_z']
                itemString = str(max_x)+"\n"+str(max_y)+"\n"+str(max_z)+"\n"
                dataFile.write(itemString)
                min_x = obj['rot_min_x']
                min_y = obj['rot_min_y']
                min_z = obj['rot_min_z']
                itemString = str(min_x)+"\n"+str(min_y)+"\n"+str(min_z)+"\n"
                dataFile.write(itemString)
                
            
        dataFile.write("'''")
        
        return
    
    def store_joint_data(self, armature):
        '''
        Joint data is stored on the rigid body objects themselves. This will not be
        necessary when the convertor is properly transferring these values from Blender
        to the game engine.
        '''
        for bone_name in armature['brik_optimal_order']:
            box = bpy.data.objects[armature['brik_bone_driver_dict'][bone_name]]
            if not box['brik_joint_target'] == 'None':
                RB_joint = box.constraints[0]
                bone = armature.pose.bones[box['brik_bone_name']]
                
                ###############################
                #Required for dynamic creation of joint in game
                box['joint_position_x'] = RB_joint.pivot_x
                box['joint_position_y'] = RB_joint.pivot_y
                box['joint_position_z'] = RB_joint.pivot_z
            
            
                '''
                It would be nice to use IK limits to define rigid body joint limits,
                but the limit arrays have not yet been wrapped in RNA apparently...
                properties_object_constraint.py in ui directory, line 554 says:
                Missing: Limit arrays (not wrapped in RNA yet)
                
                It is necessary to create the joint when spawning ragdolls anyway.
                Joints can still be created in the game.
                '''
            
                box['rot_max_x'] = bone.ik_max_x
                box['rot_max_y'] = bone.ik_max_y
                box['rot_max_z'] = bone.ik_max_z
                box['rot_min_x'] = bone.ik_min_x
                box['rot_min_y'] = bone.ik_min_y
                box['rot_min_z'] = bone.ik_min_z
    
    def execute(self, context):
        armature = context.object
        
        optimalBoneOrder, boneChainsDict = self.calculate_structure(armature)
        
        armature['brik_optimal_order'] = optimalBoneOrder
        
        self.store_joint_data(armature)
        
        self.save_structure_data(armature, optimalBoneOrder, boneChainsDict)
        
        armature['brik_file_written'] = True
        
        
        return{'FINISHED'}

class brik_create_hit_boxes(bpy.types.Operator):
    bl_label = 'brik create hit boxes operator'
    bl_idname = 'object.brik_create_hit_boxes'
    bl_description = 'Create hit boxes for each bone in an armature and parent them to the bones.'
    bl_options = {'REGISTER', 'UNDO'}
    
    hit_box_prefix = StringProperty(name='Hit box prefix',\
                            description='Prefix to be appended to the bone name that defines the hit box',\
                            default='HIT')
    
    hit_box_length = FloatProperty(name='Hit box length',\
                              description='Length of a hit box as a proportion of bone length.',\
                              min=0.05,\
                              max=1.0,\
                              step=0.05,\
                              default=0.8)
    
    hit_box_width = FloatProperty(name = 'Hit box width',\
                                  description='Width of a hit box as a proportion of bone length.',\
                                  min=0.05,\
                                  max=1.0,\
                                  step=0.05,\
                                  default=0.2)
    
    add_to_group = BoolProperty(name='Add to group',\
                                description='Add hit boxes to a group',\
                                default=True)
    
    #Create the hit boxes
    def create_hit_boxes(self, hit_box_prefix):
        bones_dict = bpy.context.object.pose.bones      #Dictionary of posebones
        bones = bones_dict.values()
        armature = bpy.context.object
        scene = bpy.context.scene
        
        hit_box_dict = {}
        
        #I hate this next line. Eugh. :S
        if 'brik_hit_boxes_created' in armature.keys() and armature['brik_hit_boxes_created'] == True:
            #Modify boxes that exist
            for bone_name in armature['brik_bone_hit_box_dict']:
                bone = bones_dict[bone_name]
                hit_box = self.reshape_hit_box(armature, bone)
                
                #Orientate and position the box
                #self.position_hit_box(armature, bone, hit_box)
                hit_box['brik_bone_name'] = bone.name
                
                self.parent_to_bone(armature, hit_box, bone_name)
                
                hit_box.game.physics_type = 'STATIC'
                hit_box.game.use_ghost = True
                    
                hit_box_dict[hit_box.name] = hit_box
        
        else:
        
            armature['brik_bone_hit_box_dict'] = {}
                
            #All bones have hit boxes created for them
            for bone in bones:
                if bone.bone.use_deform:
                    #Create boxes that do not exist
                    hit_box,volume = create_box_envelope(self.hit_box_prefix, armature, bone)
                    #hit_box = create_box(self.hit_box_prefix, self.hit_box_length, self.hit_box_width, armature, bone)
                    armature['brik_bone_hit_box_dict'][bone.name] = hit_box.name
                
                    #Orientate and position the box
                    #self.position_hit_box(armature, bone, hit_box)
                    hit_box['brik_bone_name'] = bone.name
                    
                    self.parent_to_bone(armature, hit_box, bone.name)
                
                    hit_box.game.physics_type = 'STATIC'
                    hit_box.game.use_ghost = True
                    
                    hit_box_dict[hit_box.name] = hit_box
        
        return hit_box_dict
        
    #Reshape an existing box based on parameter changes.
    #I introduced this as an attempt to improve responsiveness. This should
    #eliminate the overhead from creating completely new meshes or objects on
    #each refresh.
    def reshape_hit_box(self, armature, bone):
        #print('RESHAPING BOX')
        armature_object = bpy.context.object
        scene = bpy.context.scene
        hit_box = scene.objects[armature['brik_bone_hit_box_dict'][bone.name]]
        
        height = bone.length
        box_length = bone.length*self.hit_box_length
        width = bone.length * self.hit_box_width
        
        x = width/2
        y = box_length/2
        z = width/2
        
        verts = [[-x,y,-z],[-x,y,z],[x,y,z],[x,y,-z],\
                 [x,-y,-z],[-x,-y,-z],[-x,-y,z],[x,-y,z]]
        
        #This could be a problem if custom object shapes are used...
        count = 0
        for vert in hit_box.data.vertices:
            vert.co = Vector(verts[count])
            count += 1
        
        return(hit_box)

    def add_hit_boxes_to_group(self, armature):
        #print("Adding hit boxes to group")
        group_name = self.hit_box_prefix+armature.name+"_Group"
        if not group_name in bpy.data.groups:
            group = bpy.data.groups.new(group_name)
        else:
            group = bpy.data.groups[group_name]
        for bone_name in armature['brik_bone_hit_box_dict']:
            hit_box_name = armature['brik_bone_hit_box_dict'][bone_name]
            if not hit_box_name in group.objects:
                group.objects.link(bpy.data.objects[hit_box_name])
        
        return
        
    def parent_to_bone(self, armature, hit_box, bone_name):
        #Thanks Uncle Entity. :)
        hit_box.parent = armature
        hit_box.parent_bone = bone_name
        hit_box.parent_type = 'BONE'
        
        return
    
    #The ui of the create operator that appears when the operator is called
    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self.properties, 'hit_box_prefix')
        box.prop(self.properties, 'hit_box_length')
        box.prop(self.properties, 'hit_box_width')
        box.prop(self.properties, 'add_to_group')
    
    #The main part of the create operator
    def execute(self, context):
        #print("\n##########\n")
        #print("EXECUTING brik_create_structure\n")
        
        armature = context.object
        
        hit_box_dict = self.create_hit_boxes(self.hit_box_prefix)
        
        if self.add_to_group:
            self.add_hit_boxes_to_group(armature)
        
        armature['brik_hit_box_prefix'] = self.hit_box_prefix
        armature['brik_hit_boxes_created'] = True
        
        return{'FINISHED'}

class brik_remove_hit_boxes(bpy.types.Operator):
    bl_label = 'brik remove hit boxes operator'
    bl_idname = 'object.brik_remove_hit_boxes'
    bl_description = 'Remove hit boxes crested by this addon.'
    bl_options = {'REGISTER', 'UNDO'}
    
    '''
    For some reason the remove operators give a "cyclic" warning in the console.
    
    I have no idea what this means and have not been able to find out what this means.
    '''
    
    def remove_hit_box(self, scene, bone_name, armature):
        hit_box = scene.objects[armature['brik_bone_hit_box_dict'][bone_name]]
        #Unlink and remove the mesh
        mesh = hit_box.data
        hit_box.data = None
        mesh.user_clear()
        bpy.data.meshes.remove(mesh)
        #Unlink and remove the object
        scene.objects.unlink(hit_box)
        hit_box.user_clear()
        bpy.data.objects.remove(hit_box)
    
    def draw(self, context):
        pass
    
    def execute(self, context):
        armature = context.object
        scene = context.scene
        for bone_name in armature['brik_bone_hit_box_dict']:
            self.remove_hit_box(scene, bone_name, armature)
        
        group_name = armature['brik_hit_box_prefix']+armature.name+"_Group"
        if group_name in bpy.data.groups:
            group = bpy.data.groups[group_name]
            bpy.data.groups.remove(group)
        
        del armature['brik_bone_hit_box_dict']
        del armature['brik_hit_boxes_created']
        del armature['brik_hit_box_prefix']
        return{'FINISHED'}
    
  
