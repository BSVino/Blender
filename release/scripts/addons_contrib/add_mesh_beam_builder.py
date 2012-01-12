bl_info = {
    "name": "Beam Builder",
    "description": "Creates various types of beams.",
    "author": "revolt_randy",
    "version": (0, 1, 2),
    "blender": (2, 5, 6),
    "api": 35968,
    "location": "View3D > Add > Mesh",
    "warning": "Currently under development.", 
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}
       
# Version History
#
# v0.1 - Script only generates a multi-sided mesh object,
#           initial release for testing. 3/12/11
#
# v0.1.1 - Added 'C'-type beam, updated to work with 
#           api r35499. 3/13/11
#
# v0.1.2 - Totally changed the way beams are created, size
#           is now calculated based off width, length, & height
#           (x,y,z). Added ability to taper beams as well.
#           Add 'L' - type beam
#           Add 'T' - type beam
#           Add 'I' - type beam      

# Creates a rectangluar, or 'C', or 'L' or 'T' or 'I' - type beam.

import bpy
import math
import mathutils
#import space_info

# The following bit of code was taken from spindle.py
# a script by Campbell Barton that creates a spindle mesh.
# The script was found someplace at blender.org
# Code determines the align_matrix to align the new object to 
def align_matrix(context):
    loc = mathutils.Matrix.Translation(context.scene.cursor_location)
    obj_align = context.user_preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.rotation_part().invert().resize4x4()
    else:
        rot = mathutils.Matrix()
    align_matrix = loc * rot
    return align_matrix


def create_mesh (name, verts, faces, align_matrix):
    # Creates mesh and object
    # name - name of object to create
    # verts - a list of vertex tuples
    # faces - a list of face tuples
    # align_matrix - alignment of the mesh based on user prefs - see above code
    
    # Check if in edit mode, if so, get name of active object and enter object mode
    if bpy.context.mode == 'EDIT_MESH':
        # toggle to object mode
        bpy.ops.object.editmode_toggle()
        # get name of active object
        obj_act = bpy.context.scene.objects.active
        #print ("\n\nTRAP WORKS", "\nactive object =", obj_act)
    else:
        obj_act = False
     
    # Unselect any objects
    bpy.ops.object.select_all(action="DESELECT")
    
    # Actually create mesh and object
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    # add verts & faces to object
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)    
    
    # Move object to 3d cursor & align
    #obj.location = bpy.context.scene.cursor_location
    obj.matrix_world = align_matrix
        
    # link object to scene 
    bpy.context.scene.objects.link(obj)

    #print(obj_act, obj)
    
    # Were we in edit mode - if so need to join new mesh to active mesh object
    if obj_act:
        bpy.ops.object.select_all(action="DESELECT")
        # Select first object
        obj_act.select = True
        # Select new object
        obj.select = True  
        # Join objects     
        bpy.ops.object.join()
         
        #print("\n\n2nd TRAP Works")

    else:
        # Not in edit mode, so just make new object active object 
        bpy.context.scene.objects.active = obj
        obj.select = True
        
    # Enter edit mode
    bpy.ops.object.editmode_toggle()
    
    # Recalcuate normals
    bpy.ops.mesh.normals_make_consistent()
    
    # Return to object mode if mesh created in object mode
    if not obj_act:
        bpy.ops.object.editmode_toggle()
    
    return


def create_end_faces(verts_list, thick, debug):
    # Create End Faces
    # verts_list - list of vertices
    # thick - if true object is hollow, so construct loop of end faces
    #           instead of a solid end face
    # debug - if true prints values from this function to console
    
    # returns:
    # faces - a list of tuples defining the end faces
    
    faces = []
    
    num_of_verts = len(verts_list)
    faces_temp = []

    sides = 4 # sides - number of sides to mesh *added because of code re-write
    
    if thick:
        # has thickness, so build end faces            
        num_of_verts = int(num_of_verts / 2)
        
        # Create a list of the front faces
        for index in range(num_of_verts):
            if index == (num_of_verts - 1):
                faces_temp.append(verts_list[index])
                faces_temp.append(verts_list[index-index])
                faces_temp.append(verts_list[index+1])
                faces_temp.append(verts_list[index*2+1])
            else:
                faces_temp.append(verts_list[index])
                faces_temp.append(verts_list[index+1])
                faces_temp.append(verts_list[index+num_of_verts+1])
                faces_temp.append(verts_list[index+num_of_verts])
                        
            faces.append(tuple(faces_temp))
            faces_temp = []                
    else:
        #this code may not be needed, depends upon rewrite...
        if sides > 4:
            # more than 4 sides, so replace last list item (center vert) with first list item 
            # for looping and building faces
            center_vert = verts_list[num_of_verts - 1]
            verts_list[num_of_verts - 1] = verts_list[0]

            for index in range(int(num_of_verts - 1)):
                faces_temp.append(verts_list[index])
                faces_temp.append(verts_list[index + 1])
                faces_temp.append(center_vert)
                faces.append(tuple(faces_temp))
                faces_temp = []
        
        else:
            # create 1 end face
            for index in range(num_of_verts):
                faces_temp.append(verts_list[index])
            faces.append(tuple(faces_temp))               
    
    # print debug info to console
    if debug:
        print("\ncreate_end_faces Function Starts")
        print("\n End Face Verts list :", verts_list)
        print("\n End Faces: ", faces)
        print("\ncreate_end_faces Function Ends\n\n")
            
    return faces


def create_side_faces(front_verts, back_verts, debug):
    # Create side faces - simple bridging of front_verts & back_verts vertices,
    #                     both front_verts & back_verts must be ordered in same direction
    #                     with respect to y-axis
    # front_verts - a list of front face vertices
    # back_verts - a list of back face vertices
    # debug - if true prints values from this function to console
    
    # returns:
    # new_faces - a list of tuples defining the faces bridged between front_verts & back_verts
    
    # Number of faces to create
    num_of_faces = (len(front_verts))
    new_faces = []
    
    # add first value to end of lists for looping
    front_verts.append(front_verts[0])
    back_verts.append(back_verts[0])
    
    # Build the new_faces list with tuples defining each face    
    for index in range(num_of_faces):
        facestemp = (front_verts[index], front_verts[index+1], back_verts[index+1], back_verts[index])
        new_faces.append(facestemp)
    
    # print debug info to console
    if debug:
        print("\ncreate_side_faces Function Starts") 
        print("\n Number of faces to create: ", num_of_faces)
        print("\n New faces :", new_faces)
        print("\ncreate_side_faces Function Ends\n\n")

    return new_faces


def calc_end_verts(size, y_off, thick, debug):
    # Calculates vertex location for end of mesh
    
    # size - tuple of x,y,z dimensions of mesh to create
    # y_off - y offset, lets function know where to create verts on y-axis
    # thick - thickness, if not zero this is the thickness of a hollow mesh
    #         with the inner faces inset from size dimensions
    # debug - if true prints values from this function to console
    
    # returns:
    # verts - a list of tuples of the x,y,z location of each vertex
    
    verts = []
    
    if debug:
        print ("\ncalc_end_verts Function Starts\n")
    
    print("\nsize = ",size)
    print("y_off = ",y_off)
        
    # Create vertices by calculation 
    x_pos = 0 + size[0]/2
    z_pos = 0 + size[2]/2
    verts.append((x_pos, y_off, z_pos))

    x_pos = 0 - size[0]/2
    z_pos = 0 + size[2]/2
    verts.append((x_pos, y_off, z_pos))
    
    x_pos = 0 - size[0]/2
    z_pos = 0 - size[2]/2
    verts.append((x_pos, y_off, z_pos)) 
    
    x_pos = 0 + size[0]/2
    z_pos = 0 - size[2]/2
    verts.append((x_pos, y_off, z_pos))   
         
    if thick:
        # has thickness, so calculate inside vertices
        #### not too sure about this, but it does work the way the 
        #### solidify modifier works, so leaving as is for now
        x_pos = size[0] - (thick * 2)
        z_pos = size[2] - (thick * 2)
        size = (x_pos, y_off, z_pos)
        
        # Create vertices by calculation 
        x_pos = 0 + size[0]/2
        z_pos = 0 + size[2]/2
        verts.append((x_pos, y_off, z_pos))

        x_pos = 0 - size[0]/2
        z_pos = 0 + size[2]/2
        verts.append((x_pos, y_off, z_pos))
    
        x_pos = 0 - size[0]/2
        z_pos = 0 - size[2]/2
        verts.append((x_pos, y_off, z_pos)) 
    
        x_pos = 0 + size[0]/2
        z_pos = 0 - size[2]/2
        verts.append((x_pos, y_off, z_pos))          
            
    if debug:
        print ("verts :", verts)
        print ("\ncalc_end_verts Function Ends.\n\n")
    
    return verts


def adjust_c_beam_verts(verts, taper, debug):
    # Adjusts verts produced to correct c beam shape
    # verts - a list of tuples of vertex locations for one end of beam
    # taper - % to taper outside verts by
    # debug - if true values are printed to console for debugging
    
    # returns:
    # verts - the corrected list of tuples of the adjustec vertex locations
    
    # This function corrects vertex locations to properly shape the
    # beam, because creating a c beam uses the same code as the 
    # create_multi_side_box function does. Therefore the 5th & 6th
    # vertice's z location needs to be changed to match the 1st & 2nd
    # vertice's z location.

    vert_orig = verts[0]
    
    # get 3rd value, the z location
    vert_z = vert_orig[2] 
    # get 1st value, the x location, for vert taper calcs    
    vert_x = vert_orig[0]
  
    # vert_z has the z value to be used in the 5th & 6th verts
    # get value of 5th vert 
    vert_temp = verts[4]
    
    print ("vert_orig = ",vert_orig[0])
    print ("vert_x = ",vert_x)
    
    # calculate the amount of taper, updating vert_x
    # with the new value calculated.
    vert_x = calc_taper(vert_orig[0], vert_temp[0], taper)
    
    vert_new = (vert_x,vert_temp[1],vert_z)
    
    if debug:
        print("vert_temp =",vert_temp)
        print("vert_new =",vert_new)

    # update 5th vert with new value
    verts[4] = vert_new
    
    vert_orig = verts[1]
    
    # get 3rd value, the z location
    vert_z = vert_orig[2] 
    # get 1st value, the x location, for vert taper calcs    
    vert_x = vert_orig[0]
    # vert_z has the z value to be used in the 5th & 6th verts
    # get value of 5th vert 
    vert_temp = verts[5]
    
    print ("vert_orig = ",vert_orig[0])
    print ("vert_x = ",vert_x)
    
    # calculate the amount of taper, updating vert_x
    # with the new value calculated.
    vert_x = calc_taper(vert_orig[0], vert_temp[0], taper)
    
    vert_new = (vert_x,vert_temp[1],vert_z)
    
    if debug:
        print("vert_temp =",vert_temp)
        print("vert_new =",vert_new)
    
    # update 6th vert with new value
    verts[5] = vert_new    
    
    if debug:
        print("\n adjust_c_beam_verts function ending")
        print("verts =", verts)
        
    return verts        


def calc_taper(outer_vert, inner_vert, taper):
    # Calculate tapered edges of beam - inner vert is moved towards
    #    outer vert based upon percentage value in taper
    # outer_vert - the outside vertex
    # inner_vert - the inside vertex to be moved
    # taper - percentage to move vert
    
    # returns:
    # adjusted_vert - the calculated vertex

    #print("outer_vert =",outer_vert,"inner_vert",inner_vert)
    
    # taper values range from 0 to 100 for UI, but for calculations
    # this value needs to be flipped, ranging from 100 to 0
    taper = 100 - taper
    
    # calcuate taper & adjust vertex
    vert_delta = inner_vert - outer_vert
    adjusted_vert = outer_vert + ((vert_delta/100) * taper)    
    
    #print("adjusted_vert =", adjusted_vert)    
    return adjusted_vert

    
def create_rectangular_beam(size, thick, debug):
    # Creates a rectangular beam mesh object
    # size - tuple of x,y,z dimensions of box
    # thick - thickness, if not zero this is the thickness of a hollow 
    #         box with inner faces inset from size dimensions
    # debug - if true prints values from this function to console
    
    # returns: 
    # verts_final - a list of tuples of the x, y, z, location of each vertice
    # faces_final - a list of tuples of the vertices that make up each face  
    
    # Create temporarylists to hold vertices locations
    verts_front_temp=[]
    verts_back_temp=[]
    
    #calculate y offset from center for front vertices
    y_off = size[1]/2 
      
        
    # Create front vertices by calculation
    verts_front_temp = calc_end_verts(size, y_off, thick, debug)
    
    # re-calculate y offset from center for back vertices
    y_off = 0 - y_off
    
    # Create back vertices by calculation
    verts_back_temp = calc_end_verts(size, y_off, thick, debug)
    
    # Combine all vertices into a final list of tuples
    verts_final = verts_front_temp + verts_back_temp   
           
    # Print debug info to console
    if debug:
        print("\ncreate_multi_side_box Function Start")
        print("\n Front vertices :", verts_front_temp)
        print("\n Back vertices:", verts_back_temp)
        print("\n All vertices:", verts_final)
                      
    # Create front face
    faces_front_temp = []
    verts_front_list = []
    numofverts = len(verts_front_temp)
    
    # Build vertex list
    for index in range(numofverts):
        verts_front_list.append(index)
       
    faces_front_temp = create_end_faces(verts_front_list, thick, debug) 
    
    # Create back face
    faces_back_temp = []
    verts_back_list = []
    numofverts = len(verts_back_temp)
    
    # Build vertex list
    for index in range(numofverts):
        verts_back_list.append(index + len(verts_back_temp))
        
    faces_back_temp = create_end_faces(verts_back_list, thick, debug)

    # Create side faces
    faces_side_temp = []
    
    # better code needed here???
    if thick:
        # Object has thickness, create list of outside vertices
        numofverts = len(verts_front_list)
        verts_front_temp = verts_front_list[0:int(numofverts/2)]
        verts_back_temp = verts_back_list[0:int(numofverts/2)]
        
        faces_side_temp = create_side_faces(verts_front_temp, verts_back_temp, debug)
        
        # Create list of inside vertices
        verts_front_temp = verts_front_list[int(numofverts/2):numofverts]
        verts_back_temp = verts_back_list[int(numofverts/2):numofverts]
        
        faces_side_temp += create_side_faces(verts_front_temp, verts_back_temp, debug)            
    else:
        # Create list of only outside faces
        faces_side_temp = create_side_faces(verts_front_list, verts_back_list, debug)
    
    # Combine all faces 
    faces_final = faces_front_temp + faces_back_temp + faces_side_temp
    
    # print debug info to console   
    if debug:
        print("\ncreate_multi_side_box Function")
        print("\nAll faces :",faces_final)
        print("\ncreate_multi_side_box Function Ends\n\n")
    
    return verts_final, faces_final


def create_U_beam(size, thick, taper, debug):
    # Creates a C or U shaped mesh beam object 
    # size - tuple of x,y,z dimensions of beam
    # thick - thickness, the amount the inner faces will be
    #           inset from size dimensions
    # taper - % to taper outside edges by
    # debug - if true prints values from this function to console
    
    # returns: 
    # verts_final - a list of tuples of the x, y, z, location of each vertice
    # faces_final - a list of tuples of the vertices that make up each face
    
    # print debug info to console
    if debug:
        print ("\ncreate_U_beam - function called")

    # Get y offset of vertices from center
    y_off = size[1] / 2
    print("\n y_off =",y_off)
    
    # Create temporarylists to hold vertices locations
    verts_front_temp=[]
    verts_back_temp=[]
    
    # Create front vertices by calculation
    verts_front_temp = calc_end_verts(size, y_off, thick, debug)
    # Additional adjustment to the verts needed - 5th & 6th verts
    # needed because the calc_end_verts creates a rectangluar beam
    # the insides are inset, for a U channel we need the inside
    # verts on the open end to match the z-loc of the outside verts 
    verts_front_temp = adjust_c_beam_verts(verts_front_temp, taper, 1)
    print("\n front verts =",verts_front_temp)       
    
    # recalculate y_off for other end vertices
    y_off = 0 - y_off
    print("\n y_off =",y_off)
    
    # Create back vertices by calculation
    verts_back_temp = calc_end_verts(size, y_off, thick, debug)
    # Additional adjustment to the verts needed - the z location
    verts_back_temp = adjust_c_beam_verts(verts_back_temp, taper, debug)
    print("\n back verts =",verts_back_temp)  
    
    # Combine all vertices into a final list of tuples
    verts_final = verts_front_temp + verts_back_temp   
  
    # Print debug info to console
    if debug:
        print("\ncreate_U_beam function start")
        print("\n Front vertices :", verts_front_temp)
        print("\n Back vertices:", verts_back_temp)
        print("\n All vertices:", verts_final)
    
    # Create front face
    faces_front_temp = []
    verts_front_list = []
    numofverts = len(verts_front_temp)
    
    # Build vertex list
    for index in range(numofverts):
        verts_front_list.append(index)
    # problem area   
    faces_front_temp = create_end_faces(verts_front_list, thick, debug) 
    # Remove 1st face - only 3 end faces needed
    faces_front_temp = faces_front_temp[1:4]
        
    # Create back face
    faces_back_temp = []
    verts_back_list = []
    numofverts = len(verts_back_temp)
    
    # Build vertex list
    for index in range(numofverts):
        verts_back_list.append(index + len(verts_back_temp))
      
    faces_back_temp = create_end_faces(verts_back_list, thick, debug)
    # Remove 1st face - only 3 end faces needed
    faces_back_temp = faces_back_temp[1:4]

    # Create list of outside vertices for the 3 outside faces
    numofverts = (len(verts_front_list))
    verts_front_temp = verts_front_list[0:int(numofverts/2)]
    verts_back_temp = verts_back_list[0:int(numofverts/2)]
        
    faces_side_temp = create_side_faces(verts_front_temp, verts_back_temp, debug)
    # create_side_faces creates 4 outside faces, we only want 3
    # so remove the 1st face
    faces_side_temp  = faces_side_temp[1:]
    
    # Create list of inside vertices for the 3 inside faces
    verts_front_temp = verts_front_list[int(numofverts/2):numofverts]
    verts_back_temp = verts_back_list[int(numofverts/2):numofverts]
        
    faces_side_temp += create_side_faces(verts_front_temp, verts_back_temp, debug)
    # create_side_faces creates 4 outside faces, we only want 3
    # so remove the 1st face
    faces_side_temp  = faces_side_temp[0:3] + faces_side_temp[4:]
    
    # fill in top two faces
    faces_side_temp.append((0, 4, 12, 8))
    faces_side_temp.append((5, 1, 9, 13))    
    
    # Combine all faces 
    faces_final = faces_front_temp + faces_back_temp + faces_side_temp

    # Print debug info to console
    if debug:
        print("\ncreate_U_beam function") 
        print("\nAll faces =", faces_final)
        print("\ncreate_c_beam function ending")
         
    return verts_final, faces_final


def create_L_beam(size, thick, taper, debug):
    # Creates a L shaped mesh beam object
    # size - tuple of x,y,z dimensions of beam
    # thick - thickness, the amount the inner faces will be
    #           inset from size dimensions
    # taper - % to taper outside edges by
    # debug - if true prints values from this function to console
    
    # returns:
    # verts_final - a list of tuples of the x, y, z, location of each vertice
    # faces_final - a list of tuples of the vertices that make up each face
    
    if debug:
        print("\ncreate_L_beam function starting")

    # Get offset of vertices from center
    x_off = size[0] / 2
    y_off = size[1] / 2
    z_off = size[2] / 2
    
    # Create temporarylists to hold vertices locations
    verts_front_temp=[]
    verts_back_temp=[]
    
    # Create front vertices by calculation
    verts_front_temp = [(0 - x_off, 0 - y_off, z_off), \
        (0 - (x_off - thick), 0 - y_off, z_off), \
        (0 - (x_off - thick), 0 - y_off, 0 - (z_off - thick)), \
        (x_off, 0 - y_off, 0 - (z_off - thick)), \
        (x_off, 0 - y_off, 0 - z_off), \
        (0 - x_off, 0 - y_off, 0 - z_off)]
    
    # Adjust taper
    vert_outside = verts_front_temp[0]
    vert_inside = verts_front_temp[1]
    verts_front_temp[1] = [(calc_taper(vert_outside[0], vert_inside[0], taper)), vert_inside[1],vert_inside[2]]
   
    vert_outside = verts_front_temp[4]
    vert_inside = verts_front_temp[3]
    verts_front_temp[3] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]
    
    # Create back vertices by calculation
    verts_back_temp = [(0 - x_off, y_off, z_off), \
        (0 - (x_off - thick), y_off, z_off), \
        (0 - (x_off - thick), y_off, 0 - (z_off - thick)), \
        (x_off, y_off, 0 - (z_off - thick)), \
        (x_off, y_off, 0 - z_off), \
        (0 - x_off, y_off, 0 - z_off)]

    # Adjust taper
    vert_outside = verts_back_temp[0]
    vert_inside = verts_back_temp[1]
    verts_back_temp[1] = [(calc_taper(vert_outside[0], vert_inside[0], taper)), vert_inside[1],vert_inside[2]]   
    
    vert_outside = verts_back_temp[4]
    vert_inside = verts_back_temp[3]
    verts_back_temp[3] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))] 
    
    verts_final = verts_front_temp + verts_back_temp
    
    if debug:
        print("\n verts_front_temp =", verts_front_temp)
        print("\n verts_back_temp =", verts_back_temp)
        print("\n verts_final =", verts_final)
    
    # define end faces, only 4 so just coded
    faces_front_temp = []
    faces_back_temp = []
    faces_side_temp = []
    
    faces_front_temp = [(0, 1, 2, 5), (2, 3, 4, 5)]
    faces_back_temp = [(6, 7, 8, 11), (8, 9, 10, 11)]
    
    verts_front_list = []
    verts_back_list = []
    num_of_verts = len(verts_front_temp)
    
    # build lists of back and front verts for create_side_faces function
    for index in range(num_of_verts):
        verts_front_list.append(index)
    for index in range(num_of_verts):
        verts_back_list.append(index  + 6)
    
    faces_side_temp = create_side_faces(verts_front_list, verts_back_list, debug)
        
    faces_final = faces_front_temp + faces_back_temp + faces_side_temp
    
    if debug:
        print("\n faces_front_temp =", faces_front_temp)
        print("\n faces_back_temp =", faces_back_temp)
        print("\n faces_side_temp =", faces_side_temp)
        print("\n faces_final =", faces_final)
        print("\ncreate_L_beam function ending")
        
    return verts_final, faces_final



def create_T_beam(size, thick, taper, debug):
    # Creates a T shaped mesh beam object
    # size - tuple of x,y,z dimensions of beam
    # thick - thickness, the amount the inner faces will be
    #           inset from size dimensions
    # taper - % to taper outside edges by
    # debug - if true prints values from this function to console
    
    # returns:
    # verts_final - a list of tuples of the x, y, z, location of each vertice
    # faces_final - a list of tuples of the vertices that make up each face
    debug = 0
    
    if debug:
        print("\ncreate_T_beam function starting")

    # Get offset of vertices from center
    x_off = size[0] / 2
    y_off = size[1] / 2
    z_off = size[2] / 2
    thick_off = thick / 2

    # Create temporarylists to hold vertices locations
    verts_front_temp=[]
    verts_back_temp=[]
    
    # Create front vertices by calculation
    verts_front_temp = [(0 - x_off, 0 - y_off, z_off), \
        (0 - thick_off, 0 - y_off, z_off), \
        (thick_off, 0 - y_off, z_off), \
        (x_off, 0 - y_off, z_off), \
        (x_off, 0 - y_off, z_off - thick), \
        (thick_off, 0 - y_off, z_off - thick), \
        (thick_off, 0 - y_off, 0 - z_off), \
        (0 - thick_off, 0 - y_off, 0 - z_off), \
        (0 - thick_off, 0 - y_off, z_off - thick), \
        (0 - x_off, 0 - y_off, z_off - thick)]

    # Adjust taper
    vert_outside = verts_front_temp[0]
    vert_inside = verts_front_temp[9]
    verts_front_temp[9] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]

    vert_outside = verts_front_temp[3]
    vert_inside = verts_front_temp[4]
    verts_front_temp[4] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]  

    # Adjust taper of bottom of beam, so 0 the center
    # now becomes vert_outside, and vert_inside is calculated
    # 1/2 way towards center
    vert_outside = (0, 0 - y_off, 0 - z_off)
    vert_inside = verts_front_temp[6]
    verts_front_temp[6] = [(calc_taper(vert_outside[0], vert_inside[0], taper)), vert_inside[1], vert_inside[2]]  

    vert_outside = (0, 0 - y_off, 0 - z_off)
    vert_inside = verts_front_temp[7]
    verts_front_temp[7] = [(calc_taper(vert_outside[0], vert_inside[0], taper)), vert_inside[1], vert_inside[2]]

    # Create fack vertices by calculation
    verts_back_temp = [(0 - x_off, y_off, z_off), \
        (0 - thick_off, y_off, z_off), \
        (thick_off, y_off, z_off), \
        (x_off, y_off, z_off), \
        (x_off, y_off, z_off - thick), \
        (thick_off, y_off, z_off - thick), \
        (thick_off, y_off, 0 - z_off), \
        (0 - thick_off, y_off, 0 - z_off), \
        (0 - thick_off, y_off, z_off - thick), \
        (0 - x_off, y_off, z_off - thick)]

    # Adjust taper
    vert_outside = verts_back_temp[0]
    vert_inside = verts_back_temp[9]
    verts_back_temp[9] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]

    vert_outside = verts_back_temp[3]
    vert_inside = verts_back_temp[4]
    verts_back_temp[4] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]
    
    # Adjust taper of bottom of beam, so 0 the center
    # now becomes vert_outside, and vert_inside is calculated
    # 1/2 way towards center
    vert_outside = (0, 0 - y_off, 0 - z_off)
    vert_inside = verts_back_temp[6]
    verts_back_temp[6] = [(calc_taper(vert_outside[0], vert_inside[0], taper)), vert_inside[1], vert_inside[2]]  

    vert_outside = (0, 0 - y_off, 0 - z_off)
    vert_inside = verts_back_temp[7]
    verts_back_temp[7] = [(calc_taper(vert_outside[0], vert_inside[0], taper)), vert_inside[1], vert_inside[2]]
        
    verts_final = verts_front_temp + verts_back_temp
    
    
    # define end faces, only 8 so just coded
    faces_front_temp = []
    faces_back_temp = []
    faces_side_temp = []
    
    faces_front_temp = [(0, 1, 8, 9), (1, 2, 5, 8), \
        (2, 3, 4, 5), (5, 6, 7, 8)]
        
    faces_back_temp = [(10, 11, 18, 19), (11, 12, 15, 18), \
        (12, 13, 14, 15), (15, 16, 17,  18)]

    verts_front_list = []
    verts_back_list = []
    num_of_verts = len(verts_front_temp)
    
    # build lists of back and front verts for create_side_faces function
    for index in range(num_of_verts):
        verts_front_list.append(index)
    for index in range(num_of_verts):
        verts_back_list.append(index  + 10)
    
    faces_side_temp = create_side_faces(verts_front_list, verts_back_list, debug)
    
    faces_final = faces_front_temp + faces_back_temp + faces_side_temp

    if debug:
        print("\ncreate_T_beam function ending")    
        
    return verts_final, faces_final


def create_I_beam(size, thick, taper, debug):
    # Creates a T shaped mesh beam object
    # size - tuple of x,y,z dimensions of beam
    # thick - thickness, the amount the inner faces will be
    #           inset from size dimensions
    # taper - % to taper outside edges by
    # debug - if true prints values from this function to console
    
    # returns:
    # verts_final - a list of tuples of the x, y, z, location of each vertice
    # faces_final - a list of tuples of the vertices that make up each face
    debug = 0
    
    if debug:
        print("\ncreate_I_beam function starting")

    # Get offset of vertices from center
    x_off = size[0] / 2
    y_off = size[1] / 2
    z_off = size[2] / 2
    thick_off = thick / 2

    # Create temporarylists to hold vertices locations
    verts_front_temp=[]
    verts_back_temp=[]
    
    # Create front vertices by calculation
    verts_front_temp = [(0 - x_off, 0 - y_off, z_off), \
        (0 - thick_off, 0 - y_off, z_off), \
        (thick_off, 0 - y_off, z_off), \
        (x_off, 0 - y_off, z_off), \
        (x_off, 0 - y_off, z_off - thick), \
        (thick_off, 0 - y_off, z_off - thick), \
        (thick_off, 0 - y_off, 0 - z_off + thick), \
        (x_off, 0 - y_off, 0 - z_off + thick), \
        (x_off, 0 - y_off, 0 - z_off), \
        (thick_off, 0 - y_off, 0 - z_off), \
        (0 - thick_off, 0 - y_off, 0 - z_off), \
        (0 - x_off, 0 - y_off, 0 - z_off), \
        (0 - x_off, 0 - y_off, 0 -z_off  + thick), \
        (0 - thick_off, 0 - y_off, 0 - z_off + thick), \
        (0 - thick_off, 0 - y_off, z_off - thick), \
        (0 - x_off, 0 - y_off, z_off - thick)]
    
    # Adjust taper
    vert_outside = verts_front_temp[0]
    vert_inside = verts_front_temp[15]
    verts_front_temp[15] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]
    
    vert_outside = verts_front_temp[3]
    vert_inside = verts_front_temp[4]
    verts_front_temp[4] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]
    
    vert_outside = verts_front_temp[8]
    vert_inside = verts_front_temp[7]
    verts_front_temp[7] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]
    
    vert_outside = verts_front_temp[11]
    vert_inside = verts_front_temp[12]
    verts_front_temp[12] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]

    # Create back vertices by calculation
    verts_back_temp = [(0 - x_off, y_off, z_off), \
        (0 - thick_off, y_off, z_off), \
        (thick_off, y_off, z_off), \
        (x_off, y_off, z_off), \
        (x_off, y_off, z_off - thick), \
        (thick_off, y_off, z_off - thick), \
        (thick_off, y_off, 0 - z_off + thick), \
        (x_off, y_off, 0 - z_off + thick), \
        (x_off, y_off, 0 - z_off), \
        (thick_off, y_off, 0 - z_off), \
        (0 - thick_off, y_off, 0 - z_off), \
        (0 - x_off, y_off, 0 - z_off), \
        (0 - x_off, y_off, 0 -z_off  + thick), \
        (0 - thick_off, y_off, 0 - z_off + thick), \
        (0 - thick_off, y_off, z_off - thick), \
        (0 - x_off, y_off, z_off - thick)]

    # Adjust taper
    vert_outside = verts_back_temp[0]
    vert_inside = verts_back_temp[15]
    verts_back_temp[15] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]
    
    vert_outside = verts_back_temp[3]
    vert_inside = verts_back_temp[4]
    verts_back_temp[4] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]
    
    vert_outside = verts_back_temp[8]
    vert_inside = verts_back_temp[7]
    verts_back_temp[7] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]
    
    vert_outside = verts_back_temp[11]
    vert_inside = verts_back_temp[12]
    verts_back_temp[12] = [vert_inside[0], vert_inside[1], (calc_taper(vert_outside[2], vert_inside[2], taper))]       
 
    verts_final = verts_front_temp + verts_back_temp


# define end faces, only 7 per end, so just coded
    faces_front_temp = []
    faces_back_temp = []
    faces_side_temp = []
    
    faces_front_temp = [(0, 1, 14, 15), (1, 2, 5, 14), \
        (2, 3, 4, 5), (6, 7, 8, 9), \
        (6, 9, 10, 13), (12, 13, 10, 11), \
        (5, 6, 13, 14)]
        
    faces_back_temp = [(16, 17, 30, 31), (17, 18, 21, 30), \
        (18, 19, 20, 21), (22, 23, 24, 25), \
        (22, 25, 26, 29), (28, 29, 26, 27), \
        (21, 22, 29, 30)]
        
    verts_front_list = []
    verts_back_list = []
    num_of_verts = len(verts_front_temp)
    
    # build lists of back and front verts for create_side_faces function
    for index in range(num_of_verts):
        verts_front_list.append(index)
    for index in range(num_of_verts):
        verts_back_list.append(index  + 16)
    
    faces_side_temp = create_side_faces(verts_front_list, verts_back_list, debug)
    
    faces_final = faces_front_temp + faces_back_temp + faces_side_temp   
    
    if debug:
        print("\ncreate_I_beam function ending")
    
    return verts_final, faces_final

        

# Define "Add_Rectangular_Beam" operator
########### Needs Work ###############        
class Add_Rectangular_Beam(bpy.types.Operator):
    
    bl_idname = "mesh.primitive_rectangle_add"
    bl_label = "Add Rectangluar Beam"
    bl_description = "Create a Rectangular Beam mesh."
    bl_options = {'REGISTER', 'UNDO'}
        
    mesh_z_size = bpy.props.FloatProperty(name = "Height(z)",
        description = "Height (along the z-axis) of mesh",
        min = 0.01,
        max = 100,
        default = 1)
        
    mesh_x_size = bpy.props.FloatProperty(name = "Width(x)",
        description = "Width (along the x-axis) of mesh",
        min = 0.01,
        max = 100,
        default = .5)
        
    mesh_y_size = bpy.props.FloatProperty(name = "Length(y)",
        description = "Length (along y-axis) of mesh",
        min = 0.01,
        max = 100,
        default = 2)
            
    thick_bool = bpy.props.BoolProperty(name = "Hollow",
        description = "Create a hollow mesh with a defined thickness",
        default = True)

    thick = bpy.props.FloatProperty(name = "Thickness",
        description = "Thickness of hollow mesh",
        min = 0.01,
        max = 1,
        default = 0.1)
        
    align_matrix = mathutils.Matrix()

    # Define tool parameter layout
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'mesh_z_size')
        layout.prop(self, 'mesh_x_size')
        layout.prop(self, 'mesh_y_size')
        layout.prop(self, 'thick_bool')
        layout.prop(self, 'thick')
                
    def execute(self, context):
        # debug flag - True prints debug info to console
        debug = 0
        
        size = (self.mesh_x_size, self.mesh_y_size, self.mesh_z_size)
        if self.thick_bool is True:
            thick = self.thick
        else:
            thick = 0
                        
        verts, faces = create_rectangular_beam(size, thick, debug)
            
        if debug:
            print("\nCreated Verts:", verts)
            print("\nCreated Faces:", faces)
                
        create_mesh("Rectangular Beam", verts, faces, self.align_matrix)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}    


# Define "Add_C_Beam" operator        
class Add_C_Beam(bpy.types.Operator):
    
    bl_idname = "mesh.primitive_c_beam_add"
    bl_label = "Add C or U Channel"
    bl_description = "Create a C or U channel mesh."
    bl_options = {'REGISTER', 'UNDO'}
    
        
    mesh_z_size = bpy.props.FloatProperty(name = "Height(z)",
        description = "Height (along the z-axis) of mesh",
        min = 0.01,
        max = 100,
        default = 1)
        
    mesh_x_size = bpy.props.FloatProperty(name = "Width(x)",
        description = "Width (along the x-axis) of mesh",
        min = 0.01,
        max = 100,
        default = .5)
        
    mesh_y_size = bpy.props.FloatProperty(name = "Length(y)",
        description = "Length (along y-axis) of mesh",
        min = 0.01,
        max = 100,
        default = 2)

    thick = bpy.props.FloatProperty(name = "Thickness",
        description = "Thickness of mesh",
        min = 0.01,
        max = 1,
        default = 0.1)

    taper = bpy.props.IntProperty(name = "Taper",
        description = "Percentage to taper outside edges, 0 = no taper, 100 = full taper",
        min = 0,
        max = 100,
        default = 0)        

    type = bpy.props.BoolProperty(name = "U-shaped",
        description = "Create the beam in a U orientation rather than the defualt C orientation", 
        default = False)
                
    align_matrix = mathutils.Matrix()

    # Define tool parameter layout
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'mesh_z_size')
        layout.prop(self, 'mesh_x_size')
        layout.prop(self, 'mesh_y_size')
        layout.prop(self, 'thick')
        layout.prop(self, 'taper')
        layout.prop(self, 'type')
                
    def execute(self, context):
        # debug flag - True prints debug info to console
        debug = 0
        
        # if type == true beam is U chanel, otherwise it's a C
        if self.type:
            size = (self.mesh_x_size, self.mesh_y_size, self.mesh_z_size)
        else:
            size = (self.mesh_z_size, self.mesh_y_size, self.mesh_x_size)
            
        verts, faces = create_U_beam(size, self.thick, self.taper, debug)      
            
        if debug:
            print("\nCreated Verts:", verts)
            print("\nCreated Faces:", faces)
                
        create_mesh("C Beam", verts, faces, self.align_matrix)
        
        if not self.type:
        # C-type beam is actually created as a u-type beam
        # so rotate 90 degrees on y-axis to make a c-type
        # and apply rotation & location to reset those values
        # and reset object origin to 3d cursor if self.type is false.
        # if self.type is true, do nothing as beam is alreay u-type.
        # rotation value is in radians
            bpy.ops.transform.rotate(value=[1.570796], constraint_axis=[False, True, False])
            bpy.ops.object.rotation_clear()
            bpy.ops.object.location_clear()
            bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        # The above code might not work right if rotation set to view 
        # Need to test further!
        
        return {'FINISHED'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}
    

# Define "Add_L_Beam" operator    
class Add_L_Beam(bpy.types.Operator):
    
    bl_idname = "mesh.primitive_l_beam_add"
    bl_label = "Add L Beam"
    bl_description = "Create a L shaped mesh."
    bl_options = {'REGISTER', 'UNDO'}

    mesh_z_size = bpy.props.FloatProperty(name = "Height(z)",
        description = "Height (along the z-axis) of mesh",
        min = 0.01,
        max = 100,
        default = 1)
        
    mesh_x_size = bpy.props.FloatProperty(name = "Width(x)",
        description = "Width (along the x-axis) of mesh",
        min = 0.01,
        max = 100,
        default = .5)
        
    mesh_y_size = bpy.props.FloatProperty(name = "Length(y)",
        description = "Length (along y-axis) of mesh",
        min = 0.01,
        max = 100,
        default = 2)

    thick = bpy.props.FloatProperty(name = "Thickness",
        description = "Thickness of mesh",
        min = 0.01,
        max = 1,
        default = 0.1)

    taper = bpy.props.IntProperty(name = "Taper",
        description = "Percentage to taper outside edges, 0 = no taper, 100 = full taper",
        min = 0,
        max = 100,
        default = 0)

    align_matrix = mathutils.Matrix()

    # Define tool parameter layout
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'mesh_z_size')
        layout.prop(self, 'mesh_x_size')
        layout.prop(self, 'mesh_y_size')
        layout.prop(self, 'thick')
        layout.prop(self, 'taper')

    def execute(self, context):
        # debug flag - True prints debug info to console
        debug = 0 
        
        size = (self.mesh_x_size, self.mesh_y_size, self.mesh_z_size)
                           
        verts, faces = create_L_beam(size, self.thick, self.taper, debug)
        
        if debug:
            print("\nCreated Verts:", verts)
            print("\nCreated Faces:", faces)
                
        create_mesh("L Beam", verts, faces, self.align_matrix) 
        
        return {'FINISHED'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}
    
    
# Define "Add_T_Beam" operator    
class Add_T_Beam(bpy.types.Operator):
    
    bl_idname = "mesh.primitive_t_beam_add"
    bl_label = "Add T Beam"
    bl_description = "Create a T shaped mesh."
    bl_options = {'REGISTER', 'UNDO'}    

    mesh_z_size = bpy.props.FloatProperty(name = "Height(z)",
        description = "Height (along the z-axis) of mesh",
        min = 0.01,
        max = 100,
        default = 1)
        
    mesh_x_size = bpy.props.FloatProperty(name = "Width(x)",
        description = "Width (along the x-axis) of mesh",
        min = 0.01,
        max = 100,
        default = .5)
        
    mesh_y_size = bpy.props.FloatProperty(name = "Length(y)",
        description = "Length (along y-axis) of mesh",
        min = 0.01,
        max = 100,
        default = 2)

    thick = bpy.props.FloatProperty(name = "Thickness",
        description = "Thickness of mesh",
        min = 0.01,
        max = 1,
        default = 0.1)

    taper = bpy.props.IntProperty(name = "Taper",
        description = "Percentage to taper outside edges, 0 = no taper, 100 = full taper",
        min = 0,
        max = 100,
        default = 0)

    align_matrix = mathutils.Matrix()

    # Define tool parameter layout
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'mesh_z_size')
        layout.prop(self, 'mesh_x_size')
        layout.prop(self, 'mesh_y_size')
        layout.prop(self, 'thick')
        layout.prop(self, 'taper')

    def execute(self, context):
        # debug flag - True prints debug info to console
        debug = 0
        
        size = (self.mesh_x_size, self.mesh_y_size, self.mesh_z_size)
                           
        verts, faces = create_T_beam(size, self.thick, self.taper, debug)
        
        if debug:
            print("\nCreated Verts:", verts)
            print("\nCreated Faces:", faces)
                
        create_mesh("T Beam", verts, faces, self.align_matrix) 
        
        return {'FINISHED'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}
    
    
# Define "Add_I_Beam" operator    
class Add_I_Beam(bpy.types.Operator):
    
    bl_idname = "mesh.primitive_i_beam_add"
    bl_label = "Add I Beam"
    bl_description = "Create a I shaped mesh."
    bl_options = {'REGISTER', 'UNDO'}    

    mesh_z_size = bpy.props.FloatProperty(name = "Height(z)",
        description = "Height (along the z-axis) of mesh",
        min = 0.01,
        max = 100,
        default = 1)
        
    mesh_x_size = bpy.props.FloatProperty(name = "Width(x)",
        description = "Width (along the x-axis) of mesh",
        min = 0.01,
        max = 100,
        default = .5)
        
    mesh_y_size = bpy.props.FloatProperty(name = "Length(y)",
        description = "Length (along y-axis) of mesh",
        min = 0.01,
        max = 100,
        default = 2)

    thick = bpy.props.FloatProperty(name = "Thickness",
        description = "Thickness of mesh",
        min = 0.01,
        max = 1,
        default = 0.1)

    taper = bpy.props.IntProperty(name = "Taper",
        description = "Percentage to taper outside edges, 0 = no taper, 100 = full taper",
        min = 0,
        max = 100,
        default = 0)

    align_matrix = mathutils.Matrix()
    
    # Define tool parameter layout
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'mesh_z_size')
        layout.prop(self, 'mesh_x_size')
        layout.prop(self, 'mesh_y_size')
        layout.prop(self, 'thick')
        layout.prop(self, 'taper')

    def execute(self, context):
        # debug flag - True prints debug info to console
        debug = 0
        
        size = (self.mesh_x_size, self.mesh_y_size, self.mesh_z_size)
                           
        verts, faces = create_I_beam(size, self.thick, self.taper, debug)
        
        if debug:
            print("\nCreated Verts:", verts)
            print("\nCreated Faces:", faces)
                
        create_mesh("I Beam", verts, faces, self.align_matrix) 
        
        return {'FINISHED'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}    


# Register all operators and define menus

class INFO_MT_mesh_beambuilder_add(bpy.types.Menu):
    # Define the "Beam Builder" menu
    bl_idname = "INFO_MT_mesh_beambuilder_add"
    bl_label = "Beam Builder"
    
    def draw(self, context):
        layout = self.layout  
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_rectangle_add", text = "Rectangluar Beam")  
        layout.operator("mesh.primitive_c_beam_add", text = "C or U Channel")
        layout.operator("mesh.primitive_l_beam_add", text = "L Shaped Beam")
        layout.operator("mesh.primitive_t_beam_add", text = "T Shaped Beam")
        layout.operator("mesh.primitive_i_beam_add", text = "I Shaped Beam")
        
        
    
# Define menu    
def menu_func(self, context):
    self.layout.menu("INFO_MT_mesh_beambuilder_add", icon='PLUGIN')


# Add     
def register():
    bpy.utils.register_module(__name__)
    
    # Add BeamBuilder menu to the 'Add Mesh' menu
    bpy.types.INFO_MT_mesh_add.append(menu_func)

 
# Remove 
def unregister():
    bpy.utils.unregister_module(__name__)
    
    # Remove BeamBuilder menu from 'Add Mesh' menu
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

 
if __name__ == "__main__":
    register() 
     
