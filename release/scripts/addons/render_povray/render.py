#  ##### BEGIN GPL LICENSE BLOCK #####
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

# <pep8 compliant>

import bpy
import subprocess
import os
import sys
import time
from math import atan, pi, degrees, sqrt
import re

##############################SF###########################
##############find image texture


def imageFormat(imgF):
    ext = {
        'JPG': "jpeg",
        'JPEG': "jpeg",
        'GIF': "gif",
        'TGA': "tga",
        'IFF': "iff",
        'PPM': "ppm",
        'PNG': "png",
        'SYS': "sys",
        'TIFF': "tiff",
        'TIF': "tiff",
        'EXR': "exr",  # POV3.7 Only!
        'HDR': "hdr",  # POV3.7 Only! --MR
    }.get(os.path.splitext(imgF)[-1].upper(), "")

    if not ext:
        print(" WARNING: texture image format not supported ")

    return ext


def imgMap(ts):
    image_map = ""
    if ts.mapping == 'FLAT':
        image_map = "map_type 0 "
    elif ts.mapping == 'SPHERE':
        image_map = "map_type 1 "  # map_type 7 in megapov
    elif ts.mapping == 'TUBE':
        image_map = "map_type 2 "

    ## map_type 3 and 4 in development (?)
    ## for POV-Ray, currently they just seem to default back to Flat (type 0)
    #elif ts.mapping=="?":
    #    image_map = " map_type 3 "
    #elif ts.mapping=="?":
    #    image_map = " map_type 4 "
    if ts.texture.use_interpolation:
        image_map += " interpolate 2 "
    if ts.texture.extension == 'CLIP':
        image_map += " once "
    #image_map += "}"
    #if ts.mapping=='CUBE':
    #    image_map+= "warp { cubic } rotate <-90,0,180>"
    # no direct cube type mapping. Though this should work in POV 3.7
    # it doesn't give that good results(best suited to environment maps?)
    #if image_map == "":
    #    print(" No texture image  found ")
    return image_map


def imgMapBG(wts):
    image_mapBG = ""
    # texture_coords refers to the mapping of world textures:
    if wts.texture_coords == 'VIEW':
        image_mapBG = " map_type 0 "
    elif wts.texture_coords == 'ANGMAP':
        image_mapBG = " map_type 1 "
    elif wts.texture_coords == 'TUBE':
        image_mapBG = " map_type 2 "

    if wts.texture.use_interpolation:
        image_mapBG += " interpolate 2 "
    if wts.texture.extension == 'CLIP':
        image_mapBG += " once "
    #image_mapBG += "}"
    #if wts.mapping == 'CUBE':
    #   image_mapBG += "warp { cubic } rotate <-90,0,180>"
    # no direct cube type mapping. Though this should work in POV 3.7
    # it doesn't give that good results(best suited to environment maps?)
    #if image_mapBG == "":
    #    print(" No background texture image  found ")
    return image_mapBG


def path_image(image):
    return bpy.path.abspath(image.filepath, library=image.library)

# end find image texture
# -----------------------------------------------------------------------------


def string_strip_hyphen(name):
    return name.replace("-", "")


def safety(name, Level):
    # safety string name material
    #
    # Level=1 is for texture with No specular nor Mirror reflection
    # Level=2 is for texture with translation of spec and mir levels
    # for when no map influences them
    # Level=3 is for texture with Maximum Spec and Mirror

    try:
        if int(name) > 0:
            prefix = "shader"
    except:
        prefix = ""
    prefix = "shader_"
    name = string_strip_hyphen(name)
    if Level == 2:
        return prefix + name
    elif Level == 1:
        return prefix + name + "0"  # used for 0 of specular map
    elif Level == 3:
        return prefix + name + "1"  # used for 1 of specular map


##############end safety string name material
##############################EndSF###########################

def is_renderable(scene, ob):
    return (ob.is_visible(scene) and not ob.hide_render)


def renderable_objects(scene):
    return [ob for ob in scene.objects if is_renderable(scene, ob)]


tabLevel = 0


def write_pov(filename, scene=None, info_callback=None):
    import mathutils
    #file = filename
    file = open(filename, "w")

    # Only for testing
    if not scene:
        scene = bpy.data.scenes[0]

    render = scene.render
    world = scene.world
    global_matrix = mathutils.Matrix.Rotation(-pi / 2.0, 4, 'X')

    def setTab(tabtype, spaces):
        TabStr = ""
        if tabtype == '0':
            TabStr = ""
        elif tabtype == '1':
            TabStr = "\t"
        elif tabtype == '2':
            TabStr = spaces * " "
        return TabStr

    tab = setTab(scene.pov.indentation_character, scene.pov.indentation_spaces)

    def tabWrite(str_o):
        if not scene.pov.tempfiles_enable:
            global tabLevel
            brackets = str_o.count("{") - str_o.count("}") + str_o.count("[") - str_o.count("]")
            if brackets < 0:
                tabLevel = tabLevel + brackets
            if tabLevel < 0:
                print("Indentation Warning: tabLevel = %s" % tabLevel)
                tabLevel = 0
            if tabLevel >= 1:
                file.write("%s" % tab * tabLevel)
            file.write(str_o)
            if brackets > 0:
                tabLevel = tabLevel + brackets
        else:
            file.write(str_o)

    def uniqueName(name, nameSeq):

        if name not in nameSeq:
            name = string_strip_hyphen(name)
            return name

        name_orig = name
        i = 1
        while name in nameSeq:
            name = "%s_%.3d" % (name_orig, i)
            i += 1
        name = string_strip_hyphen(name)
        return name

    def writeMatrix(matrix):
        tabWrite("matrix <%.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, " \
                 "%.6f>\n" % (matrix[0][0], matrix[0][1], matrix[0][2], matrix[1][0], matrix[1][1],
                              matrix[1][2], matrix[2][0], matrix[2][1], matrix[2][2], matrix[3][0],
                              matrix[3][1], matrix[3][2]))

    def MatrixAsPovString(matrix):
        sMatrix = ("matrix <%.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, " \
                   "%.6f>\n" % (matrix[0][0], matrix[0][1], matrix[0][2], matrix[1][0], matrix[1][1],
                                matrix[1][2], matrix[2][0], matrix[2][1], matrix[2][2], matrix[3][0],
                                matrix[3][1], matrix[3][2]))
        return sMatrix

    def writeObjectMaterial(material, ob):

        # DH - modified some variables to be function local, avoiding RNA write
        # this should be checked to see if it is functionally correct

        # Commented out: always write IOR to be able to use it for SSS, Fresnel reflections...
        #if material and material.transparency_method == 'RAYTRACE':
        if material:
            # But there can be only one!
            if material.subsurface_scattering.use:  # SSS IOR get highest priority
                tabWrite("interior {\n")
                tabWrite("ior %.6f\n" % material.subsurface_scattering.ior)
            # Then the raytrace IOR taken from raytrace transparency properties and used for
            # reflections if IOR Mirror option is checked.
            elif material.pov.mirror_use_IOR:
                tabWrite("interior {\n")
                tabWrite("ior %.6f\n" % material.raytrace_transparency.ior)
            else:
                tabWrite("interior {\n")
                tabWrite("ior %.6f\n" % material.raytrace_transparency.ior)

            pov_fake_caustics = False
            pov_photons_refraction = False
            pov_photons_reflection = False

            if material.pov.photons_reflection:
                pov_photons_reflection = True
            if material.pov.refraction_type == "0":
                pov_fake_caustics = False
                pov_photons_refraction = False
            elif material.pov.refraction_type == "1":
                pov_fake_caustics = True
                pov_photons_refraction = False
            elif material.pov.refraction_type == "2":
                pov_fake_caustics = False
                pov_photons_refraction = True

            # If only Raytrace transparency is set, its IOR will be used for refraction, but user
            # can set up 'un-physical' fresnel reflections in raytrace mirror parameters.
            # Last, if none of the above is specified, user can set up 'un-physical' fresnel
            # reflections in raytrace mirror parameters. And pov IOR defaults to 1.
            if material.pov.caustics_enable:
                if pov_fake_caustics:
                    tabWrite("caustics %.3g\n" % material.pov.fake_caustics_power)
                if pov_photons_refraction:
                    # Default of 1 means no dispersion
                    tabWrite("dispersion %.6f\n" % material.pov.photons_dispersion)
                    tabWrite("dispersion_samples %.d\n" % material.pov.photons_dispersion_samples)
            #TODO
            # Other interior args
            if material.use_transparency and material.transparency_method == 'RAYTRACE':
                # fade_distance
                # In Blender this value has always been reversed compared to what tooltip says.
                # 100.001 rather than 100 so that it does not get to 0
                # which deactivates the feature in POV
                tabWrite("fade_distance %.3g\n" % \
                         (100.001 - material.raytrace_transparency.depth_max))
                # fade_power
                tabWrite("fade_power %.3g\n" % material.raytrace_transparency.falloff)
                # fade_color
                tabWrite("fade_color <%.3g, %.3g, %.3g>\n" % material.pov.interior_fade_color[:])

            # (variable) dispersion_samples (constant count for now)
            tabWrite("}\n")

            tabWrite("photons{")
            if not ob.pov.collect_photons:
                tabWrite("collect off\n")
                tabWrite("target %.3g\n" % ob.pov.spacing_multiplier)
            if pov_photons_refraction:
                tabWrite("refraction on\n")
            if pov_photons_reflection:
                tabWrite("reflection on\n")
            tabWrite("}\n")

    materialNames = {}
    DEF_MAT_NAME = "Default"

    def writeMaterial(material):
        # Assumes only called once on each material
        if material:
            name_orig = material.name
        else:
            name_orig = DEF_MAT_NAME

        name = materialNames[name_orig] = uniqueName(bpy.path.clean_name(name_orig), materialNames)
        comments = scene.pov.comments_enable

        ##################
        # Several versions of the finish: Level conditions are variations for specular/Mirror
        # texture channel map with alternative finish of 0 specular and no mirror reflection.
        # Level=1 Means No specular nor Mirror reflection
        # Level=2 Means translation of spec and mir levels for when no map influences them
        # Level=3 Means Maximum Spec and Mirror

        def povHasnoSpecularMaps(Level):
            if Level == 1:
                tabWrite("#declare %s = finish {" % safety(name, Level=1))
                if not scene.pov.tempfiles_enable and comments:
                    file.write("  //No specular nor Mirror reflection\n")
                else:
                    tabWrite("\n")
            elif Level == 2:
                tabWrite("#declare %s = finish {" % safety(name, Level=2))
                if not scene.pov.tempfiles_enable and comments:
                    file.write("  //translation of spec and mir levels for when no map " \
                               "influences them\n")
                else:
                    tabWrite("\n")
            elif Level == 3:
                tabWrite("#declare %s = finish {" % safety(name, Level=3))
                if not scene.pov.tempfiles_enable and comments:
                    file.write("  //Maximum Spec and Mirror\n")
                else:
                    tabWrite("\n")

            if material:
                # POV-Ray 3.7 now uses two diffuse values respectively for front and back shading
                # (the back diffuse is like blender translucency)
                frontDiffuse = material.diffuse_intensity
                backDiffuse = material.translucency

                if material.pov.conserve_energy:

                    #Total should not go above one
                    if (frontDiffuse + backDiffuse) <= 1.0:
                        pass
                    elif frontDiffuse == backDiffuse:
                        # Try to respect the user's 'intention' by comparing the two values but
                        # bringing the total back to one.
                        frontDiffuse = backDiffuse = 0.5
                    # Let the highest value stay the highest value.
                    elif frontDiffuse > backDiffuse:
                        # clamps the sum below 1
                        backDiffuse = min(backDiffuse, (1.0 - frontDiffuse))
                    else:
                        frontDiffuse = min(frontDiffuse, (1.0 - backDiffuse))

                # map hardness between 0.0 and 1.0
                roughness = ((1.0 - ((material.specular_hardness - 1.0) / 510.0)))
                ## scale from 0.0 to 0.1
                roughness *= 0.1
                # add a small value because 0.0 is invalid.
                roughness += (1.0 / 511.0)

                ################################Diffuse Shader######################################
                # Not used for Full spec (Level=3) of the shader.
                if material.diffuse_shader == 'OREN_NAYAR' and Level != 3:
                    # Blender roughness is what is generally called oren nayar Sigma,
                    # and brilliance in POV-Ray.
                    tabWrite("brilliance %.3g\n" % (0.9 + material.roughness))

                if material.diffuse_shader == 'TOON' and Level != 3:
                    tabWrite("brilliance %.3g\n" % (0.01 + material.diffuse_toon_smooth * 0.25))
                    # Lower diffuse and increase specular for toon effect seems to look better
                    # in POV-Ray.
                    frontDiffuse *= 0.5

                if material.diffuse_shader == 'MINNAERT' and Level != 3:
                    #tabWrite("aoi %.3g\n" % material.darkness)
                    pass  # let's keep things simple for now
                if material.diffuse_shader == 'FRESNEL' and Level != 3:
                    #tabWrite("aoi %.3g\n" % material.diffuse_fresnel_factor)
                    pass  # let's keep things simple for now
                if material.diffuse_shader == 'LAMBERT' and Level != 3:
                    # trying to best match lambert attenuation by that constant brilliance value
                    tabWrite("brilliance 1.8\n")

                if Level == 2:
                    ###########################Specular Shader######################################
                    # No difference between phong and cook torrence in blender HaHa!
                    if (material.specular_shader == 'COOKTORR' or
                        material.specular_shader == 'PHONG'):
                        tabWrite("phong %.3g\n" % (material.specular_intensity))
                        tabWrite("phong_size %.3g\n" % (material.specular_hardness / 2 + 0.25))

                    # POV-Ray 'specular' keyword corresponds to a Blinn model, without the ior.
                    elif material.specular_shader == 'BLINN':
                        # Use blender Blinn's IOR just as some factor for spec intensity
                        tabWrite("specular %.3g\n" % (material.specular_intensity *
                                                      (material.specular_ior / 4.0)))
                        tabWrite("roughness %.3g\n" % roughness)
                        #Could use brilliance 2(or varying around 2 depending on ior or factor) too.

                    elif material.specular_shader == 'TOON':
                        tabWrite("phong %.3g\n" % (material.specular_intensity * 2.0))
                        # use extreme phong_size
                        tabWrite("phong_size %.3g\n" % (0.1 + material.specular_toon_smooth / 2.0))

                    elif material.specular_shader == 'WARDISO':
                        # find best suited default constant for brilliance Use both phong and
                        # specular for some values.
                        tabWrite("specular %.3g\n" % (material.specular_intensity /
                                                      (material.specular_slope + 0.0005)))
                        # find best suited default constant for brilliance Use both phong and
                        # specular for some values.
                        tabWrite("roughness %.4g\n" % (0.0005 + material.specular_slope / 10.0))
                        # find best suited default constant for brilliance Use both phong and
                        # specular for some values.
                        tabWrite("brilliance %.4g\n" % (1.8 - material.specular_slope * 1.8))

                ####################################################################################
                elif Level == 1:
                    tabWrite("specular 0\n")
                elif Level == 3:
                    tabWrite("specular 1\n")
                tabWrite("diffuse %.3g %.3g\n" % (frontDiffuse, backDiffuse))

                tabWrite("ambient %.3g\n" % material.ambient)
                # POV-Ray blends the global value
                #tabWrite("ambient rgb <%.3g, %.3g, %.3g>\n" % \
                #         tuple([c*material.ambient for c in world.ambient_color]))
                tabWrite("emission %.3g\n" % material.emit)  # New in POV-Ray 3.7

                #POV-Ray just ignores roughness if there's no specular keyword
                #tabWrite("roughness %.3g\n" % roughness)

                if material.pov.conserve_energy:
                    # added for more realistic shading. Needs some checking to see if it
                    # really works. --Maurice.
                    tabWrite("conserve_energy\n")

                # 'phong 70.0 '
                if Level != 1:
                    if material.raytrace_mirror.use:
                        raytrace_mirror = material.raytrace_mirror
                        if raytrace_mirror.reflect_factor:
                            tabWrite("reflection {\n")
                            tabWrite("rgb <%.3g, %.3g, %.3g>" % material.mirror_color[:])
                            if material.pov.mirror_metallic:
                                tabWrite("metallic %.3g" % (raytrace_mirror.reflect_factor))
                            if material.pov.mirror_use_IOR:  # WORKING ?
                                # Removed from the line below: gives a more physically correct
                                # material but needs proper IOR. --Maurice
                                tabWrite("fresnel 1 ")
                            tabWrite("falloff %.3g exponent %.3g} " % \
                                     (raytrace_mirror.fresnel, raytrace_mirror.fresnel_factor))

                if material.subsurface_scattering.use:
                    subsurface_scattering = material.subsurface_scattering
                    tabWrite("subsurface { <%.3g, %.3g, %.3g>, <%.3g, %.3g, %.3g> }\n" % (
                             sqrt(subsurface_scattering.radius[0]) * 1.5,
                             sqrt(subsurface_scattering.radius[1]) * 1.5,
                             sqrt(subsurface_scattering.radius[2]) * 1.5,
                             1.0 - subsurface_scattering.color[0],
                             1.0 - subsurface_scattering.color[1],
                             1.0 - subsurface_scattering.color[2])
                            )

                if material.pov.irid_enable:
                    tabWrite("irid { %.4g thickness %.4g turbulence %.4g }" % \
                             (material.pov.irid_amount, material.pov.irid_thickness,
                              material.pov.irid_turbulence))

            else:
                tabWrite("diffuse 0.8\n")
                tabWrite("phong 70.0\n")

                #tabWrite("specular 0.2\n")

            # This is written into the object
            '''
            if material and material.transparency_method=='RAYTRACE':
                'interior { ior %.3g} ' % material.raytrace_transparency.ior
            '''

            #tabWrite("crand 1.0\n") # Sand granyness
            #tabWrite("metallic %.6f\n" % material.spec)
            #tabWrite("phong %.6f\n" % material.spec)
            #tabWrite("phong_size %.6f\n" % material.spec)
            #tabWrite("brilliance %.6f " % (material.specular_hardness/256.0) # Like hardness

            tabWrite("}\n\n")

        # Level=2 Means translation of spec and mir levels for when no map influences them
        povHasnoSpecularMaps(Level=2)

        if material:
            special_texture_found = False
            for t in material.texture_slots:
                if(t and t.texture.type == 'IMAGE' and t.use and t.texture.image and
                   (t.use_map_specular or t.use_map_raymir or t.use_map_normal or t.use_map_alpha)):
                    special_texture_found = True
                    continue  # Some texture found

            if special_texture_found:
                # Level=1 Means No specular nor Mirror reflection
                povHasnoSpecularMaps(Level=1)

                # Level=3 Means Maximum Spec and Mirror
                povHasnoSpecularMaps(Level=3)

    def exportCamera():
        camera = scene.camera

        # DH disabled for now, this isn't the correct context
        active_object = None  # bpy.context.active_object # does not always work  MR
        matrix = global_matrix * camera.matrix_world
        focal_point = camera.data.dof_distance

        # compute resolution
        Qsize = float(render.resolution_x) / float(render.resolution_y)
        tabWrite("#declare camLocation  = <%.6f, %.6f, %.6f>;\n" % \
                 (matrix[3][0], matrix[3][1], matrix[3][2]))
        tabWrite("#declare camLookAt = <%.6f, %.6f, %.6f>;\n" % \
                 tuple([degrees(e) for e in matrix.to_3x3().to_euler()]))

        tabWrite("camera {\n")
        if scene.pov.baking_enable and active_object and active_object.type == 'MESH':
            tabWrite("mesh_camera{ 1 3\n")  # distribution 3 is what we want here
            tabWrite("mesh{%s}\n" % active_object.name)
            tabWrite("}\n")
            tabWrite("location <0,0,.01>")
            tabWrite("direction <0,0,-1>")
        # Using standard camera otherwise
        else:
            tabWrite("location  <0, 0, 0>\n")
            tabWrite("look_at  <0, 0, -1>\n")
            tabWrite("right <%s, 0, 0>\n" % - Qsize)
            tabWrite("up <0, 1, 0>\n")
            tabWrite("angle  %f\n" % (360.0 * atan(16.0 / camera.data.lens) / pi))

            tabWrite("rotate  <%.6f, %.6f, %.6f>\n" % \
                     tuple([degrees(e) for e in matrix.to_3x3().to_euler()]))
            tabWrite("translate <%.6f, %.6f, %.6f>\n" % (matrix[3][0], matrix[3][1], matrix[3][2]))
            if camera.data.pov.dof_enable and focal_point != 0:
                tabWrite("aperture %.3g\n" % camera.data.pov.dof_aperture)
                tabWrite("blur_samples %d %d\n" % \
                         (camera.data.pov.dof_samples_min, camera.data.pov.dof_samples_max))
                tabWrite("variance 1/%d\n" % camera.data.pov.dof_variance)
                tabWrite("confidence %.3g\n" % camera.data.pov.dof_confidence)
                tabWrite("focal_point <0, 0, %f>\n" % focal_point)
        tabWrite("}\n")

    def exportLamps(lamps):
        # Incremented after each lamp export to declare its target
        # currently used for Fresnel diffuse shader as their slope vector:
        global lampCount
        lampCount = 0
        # Get all lamps
        for ob in lamps:
            lamp = ob.data

            matrix = global_matrix * ob.matrix_world

            # Colour is modified by energy #muiltiplie by 2 for a better match --Maurice
            color = tuple([c * lamp.energy * 2.0 for c in lamp.color])

            tabWrite("light_source {\n")
            tabWrite("< 0,0,0 >\n")
            tabWrite("color rgb<%.3g, %.3g, %.3g>\n" % color)

            if lamp.type == 'POINT':
                pass
            elif lamp.type == 'SPOT':
                tabWrite("spotlight\n")

                # Falloff is the main radius from the centre line
                tabWrite("falloff %.2f\n" % (degrees(lamp.spot_size) / 2.0))  # 1 TO 179 FOR BOTH
                tabWrite("radius %.6f\n" % \
                         ((degrees(lamp.spot_size) / 2.0) * (1.0 - lamp.spot_blend)))

                # Blender does not have a tightness equivilent, 0 is most like blender default.
                tabWrite("tightness 0\n")  # 0:10f

                tabWrite("point_at  <0, 0, -1>\n")
            elif lamp.type == 'SUN':
                tabWrite("parallel\n")
                tabWrite("point_at  <0, 0, -1>\n")  # *must* be after 'parallel'

            elif lamp.type == 'AREA':
                tabWrite("area_illumination\n")
                tabWrite("fade_distance %.6f\n" % (lamp.distance / 2.0))
                # Area lights have no falloff type, so always use blenders lamp quad equivalent
                # for those?
                tabWrite("fade_power %d\n" % 2)
                size_x = lamp.size
                samples_x = lamp.shadow_ray_samples_x
                if lamp.shape == 'SQUARE':
                    size_y = size_x
                    samples_y = samples_x
                else:
                    size_y = lamp.size_y
                    samples_y = lamp.shadow_ray_samples_y

                tabWrite("area_light <%.6f,0,0>,<0,%.6f,0> %d, %d\n" % \
                         (size_x, size_y, samples_x, samples_y))
                if lamp.shadow_ray_sample_method == 'CONSTANT_JITTERED':
                    if lamp.use_jitter:
                        tabWrite("jitter\n")
                else:
                    tabWrite("adaptive 1\n")
                    tabWrite("jitter\n")

            # HEMI never has any shadow_method attribute
            if(not scene.render.use_shadows or lamp.type == 'HEMI' or
               (lamp.type != 'HEMI' and lamp.shadow_method == 'NOSHADOW')):
                tabWrite("shadowless\n")

            # Sun shouldn't be attenuated. Hemi and area lights have no falloff attribute so they
            # are put to type 2 attenuation a little higher above.
            if lamp.type not in {'SUN', 'AREA', 'HEMI'}:
                tabWrite("fade_distance %.6f\n" % (lamp.distance / 2.0))
                if lamp.falloff_type == 'INVERSE_SQUARE':
                    tabWrite("fade_power %d\n" % 2)  # Use blenders lamp quad equivalent
                elif lamp.falloff_type == 'INVERSE_LINEAR':
                    tabWrite("fade_power %d\n" % 1)  # Use blenders lamp linear
                # supposing using no fade power keyword would default to constant, no attenuation.
                elif lamp.falloff_type == 'CONSTANT':
                    pass
                # Using Custom curve for fade power 3 for now.
                elif lamp.falloff_type == 'CUSTOM_CURVE':
                    tabWrite("fade_power %d\n" % 4)

            writeMatrix(matrix)

            tabWrite("}\n")

            lampCount += 1

            # v(A,B) rotates vector A about origin by vector B.
            file.write("#declare lampTarget%s= vrotate(<%.4g,%.4g,%.4g>,<%.4g,%.4g,%.4g>);\n" % \
                       (lampCount, -(ob.location.x), -(ob.location.y), -(ob.location.z),
                        ob.rotation_euler.x, ob.rotation_euler.y, ob.rotation_euler.z))

####################################################################################################

    def exportMeta(metas):

        # TODO - blenders 'motherball' naming is not supported.

        if not scene.pov.tempfiles_enable and scene.pov.comments_enable and len(metas) >= 1:
            file.write("//--Blob objects--\n\n")

        for ob in metas:
            meta = ob.data

            # important because no elements will break parsing.
            elements = [elem for elem in meta.elements if elem.type in {'BALL', 'ELLIPSOID'}]

            if elements:
                tabWrite("blob {\n")
                tabWrite("threshold %.4g\n" % meta.threshold)
                importance = ob.pov.importance_value

                try:
                    material = meta.materials[0]  # lame! - blender cant do enything else.
                except:
                    material = None

                for elem in elements:
                    loc = elem.co

                    stiffness = elem.stiffness
                    if elem.use_negative:
                        stiffness = - stiffness

                    if elem.type == 'BALL':

                        tabWrite("sphere { <%.6g, %.6g, %.6g>, %.4g, %.4g }\n" % \
                                 (loc.x, loc.y, loc.z, elem.radius, stiffness))

                        # After this wecould do something simple like...
                        # 	"pigment {Blue} }"
                        # except we'll write the color

                    elif elem.type == 'ELLIPSOID':
                        # location is modified by scale
                        tabWrite("sphere { <%.6g, %.6g, %.6g>, %.4g, %.4g }\n" % \
                                 (loc.x / elem.size_x, loc.y / elem.size_y, loc.z / elem.size_z,
                                  elem.radius, stiffness))
                        tabWrite("scale <%.6g, %.6g, %.6g> \n" % \
                                 (elem.size_x, elem.size_y, elem.size_z))

                if material:
                    diffuse_color = material.diffuse_color
                    trans = 1.0 - material.alpha
                    if material.use_transparency and material.transparency_method == 'RAYTRACE':
                        povFilter = material.raytrace_transparency.filter * (1.0 - material.alpha)
                        trans = (1.0 - material.alpha) - povFilter
                    else:
                        povFilter = 0.0

                    material_finish = materialNames[material.name]

                    tabWrite("pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>} \n" % \
                             (diffuse_color[0], diffuse_color[1], diffuse_color[2],
                              povFilter, trans))
                    tabWrite("finish {%s}\n" % safety(material_finish, Level=2))

                else:
                    tabWrite("pigment {rgb<1 1 1>} \n")
                    # Write the finish last.
                    tabWrite("finish {%s}\n" % (safety(DEF_MAT_NAME, Level=2)))

                writeObjectMaterial(material, ob)

                writeMatrix(global_matrix * ob.matrix_world)
                #Importance for radiosity sampling added here:
                tabWrite("radiosity { \n")
                tabWrite("importance %3g \n" % importance)
                tabWrite("}\n")

                tabWrite("}\n")  # End of Metaball block

                if not scene.pov.tempfiles_enable and scene.pov.comments_enable and len(metas) >= 1:
                    file.write("\n")

#    objectNames = {}
    DEF_OBJ_NAME = "Default"

    def exportMeshes(scene, sel):
#        obmatslist = []
#        def hasUniqueMaterial():
#            # Grab materials attached to object instances ...
#            if hasattr(ob, 'material_slots'):
#                for ms in ob.material_slots:
#                    if ms.material != None and ms.link == 'OBJECT':
#                        if ms.material in obmatslist:
#                            return False
#                        else:
#                            obmatslist.append(ms.material)
#                            return True
#        def hasObjectMaterial(ob):
#            # Grab materials attached to object instances ...
#            if hasattr(ob, 'material_slots'):
#                for ms in ob.material_slots:
#                    if ms.material != None and ms.link == 'OBJECT':
#                        # If there is at least one material slot linked to the object
#                        # and not the data (mesh), always create a new, “private” data instance.
#                        return True
#            return False
        # For objects using local material(s) only!
        # This is a mapping between a tuple (dataname, materialnames, ...), and the POV dataname.
        # As only objects using:
        #     * The same data.
        #     * EXACTLY the same materials, in EXACTLY the same sockets.
        # ... can share a same instance in POV export.
        obmats2data = {}

        def checkObjectMaterials(ob, name, dataname):
            if hasattr(ob, 'material_slots'):
                has_local_mats = False
                key = [dataname]
                for ms in ob.material_slots:
                    if ms.material != None:
                        key.append(ms.material.name)
                        if ms.link == 'OBJECT' and not has_local_mats:
                            has_local_mats = True
                    else:
                        # Even if the slot is empty, it is important to grab it...
                        key.append("")
                if has_local_mats:
                    # If this object uses local material(s), lets find if another object
                    # using the same data and exactly the same list of materials
                    # (in the same slots) has already been processed...
                    # Note that here also, we use object name as new, unique dataname for Pov.
                    key = tuple(key)  # Lists are not hashable...
                    if key not in obmats2data:
                        obmats2data[key] = name
                    return obmats2data[key]
            return None

        data_ref = {}

        def store(scene, ob, name, dataname, matrix):
            # The Object needs to be written at least once but if its data is
            # already in data_ref this has already been done.
            # This func returns the “povray” name of the data, or None
            # if no writing is needed.
            if ob.is_modified(scene, 'RENDER'):
                # Data modified.
                # Create unique entry in data_ref by using object name
                # (always unique in Blender) as data name.
                data_ref[name] = [(name, MatrixAsPovString(matrix))]
                return name
            # Here, we replace dataname by the value returned by checkObjectMaterials, only if
            # it is not evaluated to False (i.e. only if the object uses some local material(s)).
            dataname = checkObjectMaterials(ob, name, dataname) or dataname
            if dataname in data_ref:
                # Data already known, just add the object instance.
                data_ref[dataname].append((name, MatrixAsPovString(matrix)))
                # No need to write data
                return None
            else:
                # Data not yet processed, create a new entry in data_ref.
                data_ref[dataname] = [(name, MatrixAsPovString(matrix))]
                return dataname

        ob_num = 0
        for ob in sel:
            ob_num += 1

            # XXX I moved all those checks here, as there is no need to compute names
            #     for object we won’t export here!
            if ob.type in {'LAMP', 'CAMERA', 'EMPTY', 'META', 'ARMATURE', 'LATTICE'}:
                continue

            try:
                me = ob.to_mesh(scene, True, 'RENDER')
            except:
                # happens when curves cant be made into meshes because of no-data
                continue

            importance = ob.pov.importance_value
            me_materials = me.materials
            me_faces = me.faces[:]

            if not me or not me_faces:
                continue

#############################################
            # Generating a name for object just like materials to be able to use it
            # (baking for now or anything else).
            # XXX I don’t understand that – if we are here, sel if a non-empty iterable,
            #     so this condition is always True, IMO -- mont29
            if sel:
                name_orig = "OB" + ob.name
                dataname_orig = "DATA" + ob.data.name
            else:
                name_orig = DEF_OBJ_NAME
                dataname_orig = DEF_OBJ_NAME
            name = string_strip_hyphen(bpy.path.clean_name(name_orig))
            dataname = string_strip_hyphen(bpy.path.clean_name(dataname_orig))
##            for slot in ob.material_slots:
##                if slot.material != None and slot.link == 'OBJECT':
##                    obmaterial = slot.material

#############################################

            if info_callback:
                info_callback("Object %2.d of %2.d (%s)" % (ob_num, len(sel), ob.name))

            #if ob.type != 'MESH':
            #	continue
            # me = ob.data

            matrix = global_matrix * ob.matrix_world
            povdataname = store(scene, ob, name, dataname, matrix)
            if povdataname is None:
                print("This is an instance")
                continue

            print("Writing Down First Occurence")

            try:
                uv_layer = me.uv_textures.active.data
            except AttributeError:
                uv_layer = None

            try:
                vcol_layer = me.vertex_colors.active.data
            except AttributeError:
                vcol_layer = None

            faces_verts = [f.vertices[:] for f in me_faces]
            faces_normals = [f.normal[:] for f in me_faces]
            verts_normals = [v.normal[:] for v in me.vertices]

            # quads incur an extra face
            quadCount = sum(1 for f in faces_verts if len(f) == 4)

            # Use named declaration to allow reference e.g. for baking. MR
            file.write("\n")
            tabWrite("#declare %s =\n" % povdataname)
            tabWrite("mesh2 {\n")
            tabWrite("vertex_vectors {\n")
            tabWrite("%d" % len(me.vertices))  # vert count

            tabStr = tab * tabLevel
            for v in me.vertices:
                if not scene.pov.tempfiles_enable and scene.pov.list_lf_enable:
                    file.write(",\n")
                    file.write(tabStr + "<%.6f, %.6f, %.6f>" % v.co[:])  # vert count
                else:
                    file.write(", ")
                    file.write("<%.6f, %.6f, %.6f>" % v.co[:])  # vert count
                #tabWrite("<%.6f, %.6f, %.6f>" % v.co[:])  # vert count
            file.write("\n")
            tabWrite("}\n")

            # Build unique Normal list
            uniqueNormals = {}
            for fi, f in enumerate(me_faces):
                fv = faces_verts[fi]
                # [-1] is a dummy index, use a list so we can modify in place
                if f.use_smooth:  # Use vertex normals
                    for v in fv:
                        key = verts_normals[v]
                        uniqueNormals[key] = [-1]
                else:  # Use face normal
                    key = faces_normals[fi]
                    uniqueNormals[key] = [-1]

            tabWrite("normal_vectors {\n")
            tabWrite("%d" % len(uniqueNormals))  # vert count
            idx = 0
            tabStr = tab * tabLevel
            for no, index in uniqueNormals.items():
                if not scene.pov.tempfiles_enable and scene.pov.list_lf_enable:
                    file.write(",\n")
                    file.write(tabStr + "<%.6f, %.6f, %.6f>" % no)  # vert count
                else:
                    file.write(", ")
                    file.write("<%.6f, %.6f, %.6f>" % no)  # vert count
                index[0] = idx
                idx += 1
            file.write("\n")
            tabWrite("}\n")

            # Vertex colours
            vertCols = {}  # Use for material colours also.

            if uv_layer:
                # Generate unique UV's
                uniqueUVs = {}

                for fi, uv in enumerate(uv_layer):

                    if len(faces_verts[fi]) == 4:
                        uvs = uv.uv1, uv.uv2, uv.uv3, uv.uv4
                    else:
                        uvs = uv.uv1, uv.uv2, uv.uv3

                    for uv in uvs:
                        uniqueUVs[uv[:]] = [-1]

                tabWrite("uv_vectors {\n")
                #print unique_uvs
                tabWrite("%d" % len(uniqueUVs))  # vert count
                idx = 0
                tabStr = tab * tabLevel
                for uv, index in uniqueUVs.items():
                    if not scene.pov.tempfiles_enable and scene.pov.list_lf_enable:
                        file.write(",\n")
                        file.write(tabStr + "<%.6f, %.6f>" % uv)
                    else:
                        file.write(", ")
                        file.write("<%.6f, %.6f>" % uv)
                    index[0] = idx
                    idx += 1
                '''
                else:
                    # Just add 1 dummy vector, no real UV's
                    tabWrite('1') # vert count
                    file.write(',\n\t\t<0.0, 0.0>')
                '''
                file.write("\n")
                tabWrite("}\n")

            if me.vertex_colors:

                for fi, f in enumerate(me_faces):
                    # annoying, index may be invalid
                    material_index = f.material_index
                    try:
                        material = me_materials[material_index]
                    except:
                        material = None

                    if material and material.use_vertex_color_paint:

                        col = vcol_layer[fi]

                        if len(faces_verts[fi]) == 4:
                            cols = col.color1, col.color2, col.color3, col.color4
                        else:
                            cols = col.color1, col.color2, col.color3

                        for col in cols:
                            key = col[0], col[1], col[2], material_index  # Material index!
                            vertCols[key] = [-1]

                    else:
                        if material:
                            diffuse_color = material.diffuse_color[:]
                            key = diffuse_color[0], diffuse_color[1], diffuse_color[2], \
                                  material_index
                            vertCols[key] = [-1]

            else:
                # No vertex colours, so write material colours as vertex colours
                for i, material in enumerate(me_materials):

                    if material:
                        diffuse_color = material.diffuse_color[:]
                        key = diffuse_color[0], diffuse_color[1], diffuse_color[2], i  # i == f.mat
                        vertCols[key] = [-1]

            # Vert Colours
            tabWrite("texture_list {\n")
            file.write(tabStr + "%s" % (len(vertCols)))  # vert count
            idx = 0

            for col, index in vertCols.items():
                if me_materials:
                    material = me_materials[col[3]]
                    material_finish = materialNames[material.name]

                    if material.use_transparency:
                        trans = 1.0 - material.alpha
                    else:
                        trans = 0.0

                    if material.use_transparency and material.transparency_method == 'RAYTRACE':
                        povFilter = material.raytrace_transparency.filter * (1.0 - material.alpha)
                        trans = (1.0 - material.alpha) - povFilter
                    else:
                        povFilter = 0.0
                else:
                    material_finish = DEF_MAT_NAME  # not working properly,
                    trans = 0.0

                ##############SF
                texturesDif = ""
                texturesSpec = ""
                texturesNorm = ""
                texturesAlpha = ""
                for t in material.texture_slots:
                    if t and t.texture.type == 'IMAGE' and t.use and t.texture.image:
                        image_filename = path_image(t.texture.image)
                        imgGamma = ""
                        if image_filename:
                            if t.use_map_color_diffuse:
                                texturesDif = image_filename
                                # colvalue = t.default_value  # UNUSED
                                t_dif = t
                                if t_dif.texture.pov.tex_gamma_enable:
                                    imgGamma = (" gamma %.3g " % t_dif.texture.pov.tex_gamma_value)
                            if t.use_map_specular or t.use_map_raymir:
                                texturesSpec = image_filename
                                # colvalue = t.default_value  # UNUSED
                                t_spec = t
                            if t.use_map_normal:
                                texturesNorm = image_filename
                                # colvalue = t.normal_factor * 10.0  # UNUSED
                                #textNormName=t.texture.image.name + ".normal"
                                #was the above used? --MR
                                t_nor = t
                            if t.use_map_alpha:
                                texturesAlpha = image_filename
                                # colvalue = t.alpha_factor * 10.0  # UNUSED
                                #textDispName=t.texture.image.name + ".displ"
                                #was the above used? --MR
                                t_alpha = t

                ####################################################################################

                if material.pov.replacement_text != "":
                    file.write("\n")
                    file.write(" texture{%s}\n" % material.pov.replacement_text)

                else:
                    file.write("\n")
                    # THIS AREA NEEDS TO LEAVE THE TEXTURE OPEN UNTIL ALL MAPS ARE WRITTEN DOWN.
                    # --MR
                    tabWrite("texture {\n")

                    ################################################################################
                    if material.diffuse_shader == 'MINNAERT':
                        tabWrite("\n")
                        tabWrite("aoi\n")
                        tabWrite("texture_map {\n")
                        tabWrite("[%.3g finish {diffuse %.3g}]\n" % \
                                 (material.darkness / 2.0, 2.0 - material.darkness))
                        tabWrite("[%.3g\n" % (1.0 - (material.darkness / 2.0)))

                    if material.diffuse_shader == 'FRESNEL':
                        # For FRESNEL diffuse in POV, we'll layer slope patterned textures
                        # with lamp vector as the slope vector and nest one slope per lamp
                        # into each texture map's entry.

                        c = 1
                        while (c <= lampCount):
                            tabWrite("slope { lampTarget%s }\n" % (c))
                            tabWrite("texture_map {\n")
                            # Diffuse Fresnel value and factor go up to five,
                            # other kind of values needed: used the number 5 below to remap
                            tabWrite("[%.3g finish {diffuse %.3g}]\n" % \
                                     ((5.0 - material.diffuse_fresnel) / 5,
                                      (material.diffuse_intensity *
                                       ((5.0 - material.diffuse_fresnel_factor) / 5))))
                            tabWrite("[%.3g\n" % ((material.diffuse_fresnel_factor / 5) *
                                                  (material.diffuse_fresnel / 5.0)))
                            c += 1

                    # if shader is a 'FRESNEL' or 'MINNAERT': slope pigment pattern or aoi
                    # and texture map above, the rest below as one of its entry

                    if texturesSpec != "" or texturesAlpha != "":
                        if texturesSpec != "":
                            # tabWrite("\n")
                            tabWrite("pigment_pattern {\n")
                            # POV-Ray "scale" is not a number of repetitions factor, but its
                            # inverse, a standard scale factor.
                            # Offset seems needed relatively to scale so probably center of the
                            # scale is not the same in blender and POV
                            mappingSpec = "translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>\n" % \
                                          (-t_spec.offset.x, t_spec.offset.y, t_spec.offset.z,
                                           1.0 / t_spec.scale.x, 1.0 / t_spec.scale.y,
                                           1.0 / t_spec.scale.z)
                            tabWrite("uv_mapping image_map{%s \"%s\" %s}\n" % \
                                     (imageFormat(texturesSpec), texturesSpec, imgMap(t_spec)))
                            tabWrite("%s\n" % mappingSpec)
                            tabWrite("}\n")
                            tabWrite("texture_map {\n")
                            tabWrite("[0 \n")

                        if texturesDif == "":
                            if texturesAlpha != "":
                                tabWrite("\n")
                                # POV-Ray "scale" is not a number of repetitions factor, but its
                                # inverse, a standard scale factor.
                                # Offset seems needed relatively to scale so probably center of the
                                # scale is not the same in blender and POV
                                mappingAlpha = " translate <%.4g, %.4g, %.4g> " \
                                               "scale <%.4g, %.4g, %.4g>\n" % \
                                               (-t_alpha.offset.x, -t_alpha.offset.y,
                                                t_alpha.offset.z, 1.0 / t_alpha.scale.x,
                                                1.0 / t_alpha.scale.y, 1.0 / t_alpha.scale.z)
                                tabWrite("pigment {pigment_pattern {uv_mapping image_map" \
                                         "{%s \"%s\" %s}%s" % \
                                         (imageFormat(texturesAlpha), texturesAlpha,
                                          imgMap(t_alpha), mappingAlpha))
                                tabWrite("}\n")
                                tabWrite("pigment_map {\n")
                                tabWrite("[0 color rgbft<0,0,0,1,1>]\n")
                                tabWrite("[1 color rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>]\n" % \
                                         (col[0], col[1], col[2], povFilter, trans))
                                tabWrite("}\n")
                                tabWrite("}\n")

                            else:

                                tabWrite("pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>}\n" % \
                                         (col[0], col[1], col[2], povFilter, trans))

                            if texturesSpec != "":
                                # Level 1 is no specular
                                tabWrite("finish {%s}\n" % (safety(material_finish, Level=1)))

                            else:
                                # Level 2 is translated spec
                                tabWrite("finish {%s}\n" % (safety(material_finish, Level=2)))

                        else:
                            # POV-Ray "scale" is not a number of repetitions factor, but its
                            # inverse, a standard scale factor.
                            # Offset seems needed relatively to scale so probably center of the
                            # scale is not the same in blender and POV
                            mappingDif = ("translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % \
                                          (-t_dif.offset.x, -t_dif.offset.y, t_dif.offset.z,
                                           1.0 / t_dif.scale.x, 1.0 / t_dif.scale.y,
                                           1.0 / t_dif.scale.z))
                            if texturesAlpha != "":
                                # POV-Ray "scale" is not a number of repetitions factor, but its
                                # inverse, a standard scale factor.
                                # Offset seems needed relatively to scale so probably center of the
                                # scale is not the same in blender and POV
                                mappingAlpha = " translate <%.4g,%.4g,%.4g> " \
                                               "scale <%.4g,%.4g,%.4g>" % \
                                               (-t_alpha.offset.x, -t_alpha.offset.y,
                                                t_alpha.offset.z, 1.0 / t_alpha.scale.x,
                                                1.0 / t_alpha.scale.y, 1.0 / t_alpha.scale.z)
                                tabWrite("pigment {\n")
                                tabWrite("pigment_pattern {\n")
                                tabWrite("uv_mapping image_map{%s \"%s\" %s}%s}\n" % \
                                         (imageFormat(texturesAlpha), texturesAlpha,
                                          imgMap(t_alpha), mappingAlpha))
                                tabWrite("pigment_map {\n")
                                tabWrite("[0 color rgbft<0,0,0,1,1>]\n")
                                tabWrite("[1 uv_mapping image_map {%s \"%s\" %s} %s]\n" % \
                                         (imageFormat(texturesDif), texturesDif,
                                          (imgGamma + imgMap(t_dif)), mappingDif))
                                tabWrite("}\n")
                                tabWrite("}\n")

                            else:
                                tabWrite("pigment {uv_mapping image_map {%s \"%s\" %s}%s}\n" % \
                                         (imageFormat(texturesDif), texturesDif,
                                          (imgGamma + imgMap(t_dif)), mappingDif))

                            if texturesSpec != "":
                                # Level 1 is no specular
                                tabWrite("finish {%s}\n" % (safety(material_finish, Level=1)))

                            else:
                                # Level 2 is translated specular
                                tabWrite("finish {%s}\n" % (safety(material_finish, Level=2)))

                            ## scale 1 rotate y*0
                            #imageMap = ("{image_map {%s \"%s\" %s }\n" % \
                            #            (imageFormat(textures),textures,imgMap(t_dif)))
                            #tabWrite("uv_mapping pigment %s} %s finish {%s}\n" % \
                            #         (imageMap,mapping,safety(material_finish)))
                            #tabWrite("pigment {uv_mapping image_map {%s \"%s\" %s}%s} " \
                            #         "finish {%s}\n" % \
                            #         (imageFormat(texturesDif), texturesDif, imgMap(t_dif),
                            #          mappingDif, safety(material_finish)))
                        if texturesNorm != "":
                            ## scale 1 rotate y*0
                            # POV-Ray "scale" is not a number of repetitions factor, but its
                            # inverse, a standard scale factor.
                            # Offset seems needed relatively to scale so probably center of the
                            # scale is not the same in blender and POV
                            mappingNor = " translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % \
                                         (-t_nor.offset.x, -t_nor.offset.y, t_nor.offset.z,
                                          1.0 / t_nor.scale.x, 1.0 / t_nor.scale.y,
                                          1.0 / t_nor.scale.z)
                            #imageMapNor = ("{bump_map {%s \"%s\" %s mapping}" % \
                            #               (imageFormat(texturesNorm),texturesNorm,imgMap(t_nor)))
                            #We were not using the above maybe we should?
                            tabWrite("normal {uv_mapping bump_map " \
                                     "{%s \"%s\" %s  bump_size %.4g }%s}\n" % \
                                     (imageFormat(texturesNorm), texturesNorm, imgMap(t_nor),
                                      t_nor.normal_factor * 10, mappingNor))
                        if texturesSpec != "":
                            tabWrite("]\n")
                        ##################Second index for mapping specular max value###############
                            tabWrite("[1 \n")

                if texturesDif == "" and material.pov.replacement_text == "":
                    if texturesAlpha != "":
                        # POV-Ray "scale" is not a number of repetitions factor, but its inverse,
                        # a standard scale factor.
                        # Offset seems needed relatively to scale so probably center of the scale
                        # is not the same in blender and POV
                        # Strange that the translation factor for scale is not the same as for
                        # translate.
                        # TODO: verify both matches with blender internal.
                        mappingAlpha = " translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>\n" % \
                                       (-t_alpha.offset.x, -t_alpha.offset.y, t_alpha.offset.z,
                                        1.0 / t_alpha.scale.x, 1.0 / t_alpha.scale.y,
                                        1.0 / t_alpha.scale.z)
                        tabWrite("pigment {pigment_pattern {uv_mapping image_map" \
                                 "{%s \"%s\" %s}%s}\n" % \
                                 (imageFormat(texturesAlpha), texturesAlpha, imgMap(t_alpha),
                                  mappingAlpha))
                        tabWrite("pigment_map {\n")
                        tabWrite("[0 color rgbft<0,0,0,1,1>]\n")
                        tabWrite("[1 color rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>]\n" % \
                                 (col[0], col[1], col[2], povFilter, trans))
                        tabWrite("}\n")
                        tabWrite("}\n")

                    else:
                        tabWrite("pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>}\n" % \
                                 (col[0], col[1], col[2], povFilter, trans))

                    if texturesSpec != "":
                        # Level 3 is full specular
                        tabWrite("finish {%s}\n" % (safety(material_finish, Level=3)))

                    else:
                        # Level 2 is translated specular
                        tabWrite("finish {%s}\n" % (safety(material_finish, Level=2)))

                elif material.pov.replacement_text == "":
                    # POV-Ray "scale" is not a number of repetitions factor, but its inverse,
                    # a standard scale factor.
                    # Offset seems needed relatively to scale so probably center of the scale is
                    # not the same in blender and POV
                    # Strange that the translation factor for scale is not the same as for
                    # translate.
                    # TODO: verify both matches with blender internal.
                    mappingDif = ("translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % \
                                  (-t_dif.offset.x, -t_dif.offset.y, t_dif.offset.z,
                                   1.0 / t_dif.scale.x, 1.0 / t_dif.scale.y, 1.0 / t_dif.scale.z))
                    if texturesAlpha != "":
                        # Strange that the translation factor for scale is not the same as for
                        # translate.
                        # TODO: verify both matches with blender internal.
                        mappingAlpha = "translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % \
                                       (-t_alpha.offset.x, -t_alpha.offset.y, t_alpha.offset.z,
                                        1.0 / t_alpha.scale.x, 1.0 / t_alpha.scale.y,
                                        1.0 / t_alpha.scale.z)
                        tabWrite("pigment {pigment_pattern {uv_mapping image_map" \
                                 "{%s \"%s\" %s}%s}\n" % \
                                 (imageFormat(texturesAlpha), texturesAlpha, imgMap(t_alpha),
                                  mappingAlpha))
                        tabWrite("pigment_map {\n")
                        tabWrite("[0 color rgbft<0,0,0,1,1>]\n")
                        tabWrite("[1 uv_mapping image_map {%s \"%s\" %s} %s]\n" % \
                                 (imageFormat(texturesDif), texturesDif,
                                  (imgMap(t_dif) + imgGamma), mappingDif))
                        tabWrite("}\n")
                        tabWrite("}\n")

                    else:
                        tabWrite("pigment {\n")
                        tabWrite("uv_mapping image_map {\n")
                        #tabWrite("%s \"%s\" %s}%s\n" % \
                        #         (imageFormat(texturesDif), texturesDif,
                        #         (imgGamma + imgMap(t_dif)),mappingDif))
                        tabWrite("%s \"%s\" \n" % (imageFormat(texturesDif), texturesDif))
                        tabWrite("%s\n" % (imgGamma + imgMap(t_dif)))
                        tabWrite("}\n")
                        tabWrite("%s\n" % mappingDif)
                        tabWrite("}\n")
                    if texturesSpec != "":
                        # Level 3 is full specular
                        tabWrite("finish {%s}\n" % (safety(material_finish, Level=3)))
                    else:
                        # Level 2 is translated specular
                        tabWrite("finish {%s}\n" % (safety(material_finish, Level=2)))

                    ## scale 1 rotate y*0
                    #imageMap = ("{image_map {%s \"%s\" %s }" % \
                    #            (imageFormat(textures), textures,imgMap(t_dif)))
                    #file.write("\n\t\t\tuv_mapping pigment %s} %s finish {%s}" % \
                    #           (imageMap, mapping, safety(material_finish)))
                    #file.write("\n\t\t\tpigment {uv_mapping image_map " \
                    #           "{%s \"%s\" %s}%s} finish {%s}" % \
                    #           (imageFormat(texturesDif), texturesDif,imgMap(t_dif),
                    #            mappingDif, safety(material_finish)))
                if texturesNorm != "" and material.pov.replacement_text == "":
                    ## scale 1 rotate y*0
                    # POV-Ray "scale" is not a number of repetitions factor, but its inverse,
                    # a standard scale factor.
                    # Offset seems needed relatively to scale so probably center of the scale is
                    # not the same in blender and POV
                    mappingNor = (" translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % \
                                  (-t_nor.offset.x, -t_nor.offset.y, t_nor.offset.z,
                                   1.0 / t_nor.scale.x, 1.0 / t_nor.scale.y, 1.0 / t_nor.scale.z))
                    #imageMapNor = ("{bump_map {%s \"%s\" %s mapping}" % \
                    #               (imageFormat(texturesNorm),texturesNorm,imgMap(t_nor)))
                    #We were not using the above maybe we should?
                    tabWrite("normal {uv_mapping bump_map {%s \"%s\" %s  bump_size %.4g }%s}\n" % \
                             (imageFormat(texturesNorm), texturesNorm, imgMap(t_nor),
                              t_nor.normal_factor * 10.0, mappingNor))
                if texturesSpec != "" and material.pov.replacement_text == "":
                    tabWrite("]\n")

                    tabWrite("}\n")

                #End of slope/ior texture_map
                if material.diffuse_shader == 'MINNAERT' and material.pov.replacement_text == "":
                    tabWrite("]\n")
                    tabWrite("}\n")
                if material.diffuse_shader == 'FRESNEL' and material.pov.replacement_text == "":
                    c = 1
                    while (c <= lampCount):
                        tabWrite("]\n")
                        tabWrite("}\n")
                        c += 1

                if material.pov.replacement_text == "":
                    tabWrite("}\n")  # THEN IT CAN CLOSE IT   --MR

                ####################################################################################
                index[0] = idx
                idx += 1

            tabWrite("}\n")

            # Face indices
            tabWrite("face_indices {\n")
            tabWrite("%d" % (len(me_faces) + quadCount))  # faces count
            tabStr = tab * tabLevel

            for fi, f in enumerate(me_faces):
                fv = faces_verts[fi]
                material_index = f.material_index
                if len(fv) == 4:
                    indices = (0, 1, 2), (0, 2, 3)
                else:
                    indices = ((0, 1, 2),)

                if vcol_layer:
                    col = vcol_layer[fi]

                    if len(fv) == 4:
                        cols = col.color1, col.color2, col.color3, col.color4
                    else:
                        cols = col.color1, col.color2, col.color3

                if not me_materials or me_materials[material_index] is None:  # No materials
                    for i1, i2, i3 in indices:
                        if not scene.pov.tempfiles_enable and scene.pov.list_lf_enable:
                            file.write(",\n")
                            # vert count
                            file.write(tabStr + "<%d,%d,%d>" % (fv[i1], fv[i2], fv[i3]))
                        else:
                            file.write(", ")
                            file.write("<%d,%d,%d>" % (fv[i1], fv[i2], fv[i3]))  # vert count
                else:
                    material = me_materials[material_index]
                    for i1, i2, i3 in indices:
                        if me.vertex_colors and material.use_vertex_color_paint:
                            # Colour per vertex - vertex colour

                            col1 = cols[i1]
                            col2 = cols[i2]
                            col3 = cols[i3]

                            ci1 = vertCols[col1[0], col1[1], col1[2], material_index][0]
                            ci2 = vertCols[col2[0], col2[1], col2[2], material_index][0]
                            ci3 = vertCols[col3[0], col3[1], col3[2], material_index][0]
                        else:
                            # Colour per material - flat material colour
                            diffuse_color = material.diffuse_color
                            ci1 = ci2 = ci3 = vertCols[diffuse_color[0], diffuse_color[1], \
                                              diffuse_color[2], f.material_index][0]

                        if not scene.pov.tempfiles_enable and scene.pov.list_lf_enable:
                            file.write(",\n")
                            file.write(tabStr + "<%d,%d,%d>, %d,%d,%d" % \
                                       (fv[i1], fv[i2], fv[i3], ci1, ci2, ci3))  # vert count
                        else:
                            file.write(", ")
                            file.write("<%d,%d,%d>, %d,%d,%d" % \
                                       (fv[i1], fv[i2], fv[i3], ci1, ci2, ci3))  # vert count

            file.write("\n")
            tabWrite("}\n")

            # normal_indices indices
            tabWrite("normal_indices {\n")
            tabWrite("%d" % (len(me_faces) + quadCount))  # faces count
            tabStr = tab * tabLevel
            for fi, fv in enumerate(faces_verts):

                if len(fv) == 4:
                    indices = (0, 1, 2), (0, 2, 3)
                else:
                    indices = ((0, 1, 2),)

                for i1, i2, i3 in indices:
                    if me_faces[fi].use_smooth:
                        if not scene.pov.tempfiles_enable and scene.pov.list_lf_enable:
                            file.write(",\n")
                            file.write(tabStr + "<%d,%d,%d>" %\
                            (uniqueNormals[verts_normals[fv[i1]]][0],\
                             uniqueNormals[verts_normals[fv[i2]]][0],\
                             uniqueNormals[verts_normals[fv[i3]]][0]))  # vert count
                        else:
                            file.write(", ")
                            file.write("<%d,%d,%d>" %\
                            (uniqueNormals[verts_normals[fv[i1]]][0],\
                             uniqueNormals[verts_normals[fv[i2]]][0],\
                             uniqueNormals[verts_normals[fv[i3]]][0]))  # vert count
                    else:
                        idx = uniqueNormals[faces_normals[fi]][0]
                        if not scene.pov.tempfiles_enable and scene.pov.list_lf_enable:
                            file.write(",\n")
                            file.write(tabStr + "<%d,%d,%d>" % (idx, idx, idx))  # vert count
                        else:
                            file.write(", ")
                            file.write("<%d,%d,%d>" % (idx, idx, idx))  # vert count

            file.write("\n")
            tabWrite("}\n")

            if uv_layer:
                tabWrite("uv_indices {\n")
                tabWrite("%d" % (len(me_faces) + quadCount))  # faces count
                tabStr = tab * tabLevel
                for fi, fv in enumerate(faces_verts):

                    if len(fv) == 4:
                        indices = (0, 1, 2), (0, 2, 3)
                    else:
                        indices = ((0, 1, 2),)

                    uv = uv_layer[fi]
                    if len(faces_verts[fi]) == 4:
                        uvs = uv.uv1[:], uv.uv2[:], uv.uv3[:], uv.uv4[:]
                    else:
                        uvs = uv.uv1[:], uv.uv2[:], uv.uv3[:]

                    for i1, i2, i3 in indices:
                        if not scene.pov.tempfiles_enable and scene.pov.list_lf_enable:
                            file.write(",\n")
                            file.write(tabStr + "<%d,%d,%d>" % (
                                     uniqueUVs[uvs[i1]][0],\
                                     uniqueUVs[uvs[i2]][0],\
                                     uniqueUVs[uvs[i3]][0]))
                        else:
                            file.write(", ")
                            file.write("<%d,%d,%d>" % (
                                     uniqueUVs[uvs[i1]][0],\
                                     uniqueUVs[uvs[i2]][0],\
                                     uniqueUVs[uvs[i3]][0]))

                file.write("\n")
                tabWrite("}\n")

            if me.materials:
                try:
                    material = me.materials[0]  # dodgy
                    writeObjectMaterial(material, ob)
                except IndexError:
                    print(me)

            #Importance for radiosity sampling added here:
            tabWrite("radiosity { \n")
            tabWrite("importance %3g \n" % importance)
            tabWrite("}\n")

            tabWrite("}\n")  # End of mesh block

            bpy.data.meshes.remove(me)

        for data_name, inst in data_ref.items():
            for ob_name, matrix_str in inst:
                tabWrite("//----Blender Object Name:%s----\n" % ob_name)
                tabWrite("object { \n")
                tabWrite("%s\n" % data_name)
                tabWrite("%s\n" % matrix_str)
                tabWrite("}\n")

    def exportWorld(world):
        render = scene.render
        camera = scene.camera
        matrix = global_matrix * camera.matrix_world
        if not world:
            return
        #############Maurice####################################
        #These lines added to get sky gradient (visible with PNG output)
        if world:
            #For simple flat background:
            if not world.use_sky_blend:
                # Non fully transparent background could premultiply alpha and avoid anti-aliasing
                # display issue:
                if render.alpha_mode == 'PREMUL':
                    tabWrite("background {rgbt<%.3g, %.3g, %.3g, 0.75>}\n" % \
                             (world.horizon_color[:]))
                #Currently using no alpha with Sky option:
                elif render.alpha_mode == 'SKY':
                    tabWrite("background {rgbt<%.3g, %.3g, %.3g, 0>}\n" % (world.horizon_color[:]))
                #StraightAlpha:
                else:
                    tabWrite("background {rgbt<%.3g, %.3g, %.3g, 1>}\n" % (world.horizon_color[:]))

            worldTexCount = 0
            #For Background image textures
            for t in world.texture_slots:  # risk to write several sky_spheres but maybe ok.
                if t and t.texture.type is not None:
                    worldTexCount += 1
                # XXX No enable checkbox for world textures yet (report it?)
                #if t and t.texture.type == 'IMAGE' and t.use:
                if t and t.texture.type == 'IMAGE':
                    image_filename = path_image(t.texture.image)
                    if t.texture.image.filepath != image_filename:
                        t.texture.image.filepath = image_filename
                    if image_filename != "" and t.use_map_blend:
                        texturesBlend = image_filename
                        #colvalue = t.default_value
                        t_blend = t

                    # Commented below was an idea to make the Background image oriented as camera
                    # taken here:
#http://news.povray.org/povray.newusers/thread/%3Cweb.4a5cddf4e9c9822ba2f93e20@news.povray.org%3E/
                    # Replace 4/3 by the ratio of each image found by some custom or existing
                    # function
                    #mappingBlend = (" translate <%.4g,%.4g,%.4g> rotate z*degrees" \
                    #                "(atan((camLocation - camLookAt).x/(camLocation - " \
                    #                "camLookAt).y)) rotate x*degrees(atan((camLocation - " \
                    #                "camLookAt).y/(camLocation - camLookAt).z)) rotate y*" \
                    #                "degrees(atan((camLocation - camLookAt).z/(camLocation - " \
                    #                "camLookAt).x)) scale <%.4g,%.4g,%.4g>b" % \
                    #                (t_blend.offset.x / 10 , t_blend.offset.y / 10 ,
                    #                 t_blend.offset.z / 10, t_blend.scale.x ,
                    #                 t_blend.scale.y , t_blend.scale.z))
                    #using camera rotation valuesdirectly from blender seems much easier
                    if t_blend.texture_coords == 'ANGMAP':
                        mappingBlend = ""
                    else:
                        mappingBlend = " translate <%.4g-0.5,%.4g-0.5,%.4g-0.5> rotate<0,0,0>  " \
                                       "scale <%.4g,%.4g,%.4g>" % \
                                       (t_blend.offset.x / 10.0, t_blend.offset.y / 10.0,
                                        t_blend.offset.z / 10.0, t_blend.scale.x * 0.85,
                                        t_blend.scale.y * 0.85, t_blend.scale.z * 0.85)

                        # The initial position and rotation of the pov camera is probably creating
                        # the rotation offset should look into it someday but at least background
                        # won't rotate with the camera now.
                    # Putting the map on a plane would not introduce the skysphere distortion and
                    # allow for better image scale matching but also some waay to chose depth and
                    # size of the plane relative to camera.
                    tabWrite("sky_sphere {\n")
                    tabWrite("pigment {\n")
                    tabWrite("image_map{%s \"%s\" %s}\n" % \
                             (imageFormat(texturesBlend), texturesBlend, imgMapBG(t_blend)))
                    tabWrite("}\n")
                    tabWrite("%s\n" % (mappingBlend))
                    # The following layered pigment opacifies to black over the texture for
                    # transmit below 1 or otherwise adds to itself
                    tabWrite("pigment {rgb 0 transmit %s}\n" % (t.texture.intensity))
                    tabWrite("}\n")
                    #tabWrite("scale 2\n")
                    #tabWrite("translate -1\n")

            #For only Background gradient

            if worldTexCount == 0:
                if world.use_sky_blend:
                    tabWrite("sky_sphere {\n")
                    tabWrite("pigment {\n")
                    # maybe Should follow the advice of POV doc about replacing gradient
                    # for skysphere..5.5
                    tabWrite("gradient y\n")
                    tabWrite("color_map {\n")
                    if render.alpha_mode == 'STRAIGHT':
                        tabWrite("[0.0 rgbt<%.3g, %.3g, %.3g, 1>]\n" % (world.horizon_color[:]))
                        tabWrite("[1.0 rgbt<%.3g, %.3g, %.3g, 1>]\n" % (world.zenith_color[:]))
                    elif render.alpha_mode == 'PREMUL':
                        tabWrite("[0.0 rgbt<%.3g, %.3g, %.3g, 0.99>]\n" % (world.horizon_color[:]))
                        # aa premult not solved with transmit 1
                        tabWrite("[1.0 rgbt<%.3g, %.3g, %.3g, 0.99>]\n" % (world.zenith_color[:]))
                    else:
                        tabWrite("[0.0 rgbt<%.3g, %.3g, %.3g, 0>]\n" % (world.horizon_color[:]))
                        tabWrite("[1.0 rgbt<%.3g, %.3g, %.3g, 0>]\n" % (world.zenith_color[:]))
                    tabWrite("}\n")
                    tabWrite("}\n")
                    tabWrite("}\n")
                    # Sky_sphere alpha (transmit) is not translating into image alpha the same
                    # way as 'background'

            #if world.light_settings.use_indirect_light:
            #    scene.pov.radio_enable=1

            # Maybe change the above to a funtion copyInternalRenderer settings when
            # user pushes a button, then:
            #scene.pov.radio_enable = world.light_settings.use_indirect_light
            # and other such translations but maybe this would not be allowed either?

        ###############################################################

        mist = world.mist_settings

        if mist.use_mist:
            tabWrite("fog {\n")
            tabWrite("distance %.6f\n" % mist.depth)
            tabWrite("color rgbt<%.3g, %.3g, %.3g, %.3g>\n" % \
                     (world.horizon_color[:] + (1.0 - mist.intensity,)))
            #tabWrite("fog_offset %.6f\n" % mist.start)
            #tabWrite("fog_alt 5\n")
            #tabWrite("turbulence 0.2\n")
            #tabWrite("turb_depth 0.3\n")
            tabWrite("fog_type 1\n")
            tabWrite("}\n")
        if scene.pov.media_enable:
            tabWrite("media {\n")
            tabWrite("scattering { 1, rgb <%.4g, %.4g, %.4g>}\n" % scene.pov.media_color[:])
            tabWrite("samples %.d\n" % scene.pov.media_samples)
            tabWrite("}\n")

    def exportGlobalSettings(scene):

        tabWrite("global_settings {\n")
        tabWrite("assumed_gamma 1.0\n")
        tabWrite("max_trace_level %d\n" % scene.pov.max_trace_level)

        if scene.pov.radio_enable:
            tabWrite("radiosity {\n")
            tabWrite("adc_bailout %.4g\n" % scene.pov.radio_adc_bailout)
            tabWrite("always_sample %d\n" % scene.pov.radio_always_sample)
            tabWrite("brightness %.4g\n" % scene.pov.radio_brightness)
            tabWrite("count %d\n" % scene.pov.radio_count)
            tabWrite("error_bound %.4g\n" % scene.pov.radio_error_bound)
            tabWrite("gray_threshold %.4g\n" % scene.pov.radio_gray_threshold)
            tabWrite("low_error_factor %.4g\n" % scene.pov.radio_low_error_factor)
            tabWrite("media %d\n" % scene.pov.radio_media)
            tabWrite("minimum_reuse %.4g\n" % scene.pov.radio_minimum_reuse)
            tabWrite("nearest_count %d\n" % scene.pov.radio_nearest_count)
            tabWrite("normal %d\n" % scene.pov.radio_normal)
            tabWrite("pretrace_start %.3g\n" % scene.pov.radio_pretrace_start)
            tabWrite("pretrace_end %.3g\n" % scene.pov.radio_pretrace_end)
            tabWrite("recursion_limit %d\n" % scene.pov.radio_recursion_limit)
            tabWrite("}\n")
        onceSss = 1
        onceAmbient = 1
        oncePhotons = 1
        for material in bpy.data.materials:
            if material.subsurface_scattering.use and onceSss:
                # In pov, the scale has reversed influence compared to blender. these number
                # should correct that
                tabWrite("mm_per_unit %.6f\n" % \
                         (material.subsurface_scattering.scale * (-100.0) + 15.0))
                # In POV-Ray, the scale factor for all subsurface shaders needs to be the same
                onceSss = 0

            if world and onceAmbient:
                tabWrite("ambient_light rgb<%.3g, %.3g, %.3g>\n" % world.ambient_color[:])
                onceAmbient = 0

            if (material.pov.photons_refraction or material.pov.photons_reflection)and oncePhotons:
                tabWrite("photons {\n")
                tabWrite("spacing %.6f\n" % scene.pov.photon_spacing)
                tabWrite("max_trace_level %d\n" % scene.pov.photon_max_trace_level)
                tabWrite("adc_bailout %.3g\n" % scene.pov.photon_adc_bailout)
                tabWrite("gather %d, %d\n" % (scene.pov.photon_gather_min, scene.pov.photon_gather_max))
                tabWrite("}\n")
                oncePhotons = 0

        tabWrite("}\n")

    def exportCustomCode():

        for txt in bpy.data.texts:
            if txt.pov.custom_code:
                # Why are the newlines needed?
                file.write("\n")
                file.write(txt.as_string())
                file.write("\n")

    sel = renderable_objects(scene)
    comments = scene.pov.comments_enable
    if not scene.pov.tempfiles_enable and comments:
        file.write("//----------------------------------------------\n" \
                   "//--Exported with POV-Ray exporter for Blender--\n" \
                   "//----------------------------------------------\n\n")
    file.write("#version 3.7;\n")

    if not scene.pov.tempfiles_enable and comments:
        file.write("\n//--CUSTOM CODE--\n\n")
    exportCustomCode()

    if not scene.pov.tempfiles_enable and comments:
        file.write("\n//--Global settings and background--\n\n")

    exportGlobalSettings(scene)

    if not scene.pov.tempfiles_enable and comments:
        file.write("\n")

    exportWorld(scene.world)

    if not scene.pov.tempfiles_enable and comments:
        file.write("\n//--Cameras--\n\n")

    exportCamera()

    if not scene.pov.tempfiles_enable and comments:
        file.write("\n//--Lamps--\n\n")

    exportLamps([l for l in sel if l.type == 'LAMP'])

    if not scene.pov.tempfiles_enable and comments:
        file.write("\n//--Material Definitions--\n\n")

    # Convert all materials to strings we can access directly per vertex.
    #exportMaterials()
    writeMaterial(None)  # default material
    for material in bpy.data.materials:
        if material.users > 0:
            writeMaterial(material)
    if not scene.pov.tempfiles_enable and comments:
        file.write("\n")

    exportMeta([l for l in sel if l.type == 'META'])

    if not scene.pov.tempfiles_enable and comments:
        file.write("//--Mesh objects--\n")

    exportMeshes(scene, sel)
    #What follow used to happen here:
    #exportCamera()
    #exportWorld(scene.world)
    #exportGlobalSettings(scene)
    # MR:..and the order was important for an attempt to implement pov 3.7 baking
    #      (mesh camera) comment for the record
    # CR: Baking should be a special case than. If "baking", than we could change the order.

    #print("pov file closed %s" % file.closed)
    file.close()
    #print("pov file closed %s" % file.closed)


def write_pov_ini(scene, filename_ini, filename_pov, filename_image):
    #scene = bpy.data.scenes[0]
    render = scene.render

    x = int(render.resolution_x * render.resolution_percentage * 0.01)
    y = int(render.resolution_y * render.resolution_percentage * 0.01)

    file = open(filename_ini, "w")
    file.write("Version=3.7\n")
    file.write("Input_File_Name='%s'\n" % filename_pov)
    file.write("Output_File_Name='%s'\n" % filename_image)

    file.write("Width=%d\n" % x)
    file.write("Height=%d\n" % y)

    # Border render.
    if render.use_border:
        file.write("Start_Column=%4g\n" % render.border_min_x)
        file.write("End_Column=%4g\n" % (render.border_max_x))

        file.write("Start_Row=%4g\n" % (1.0 - render.border_max_y))
        file.write("End_Row=%4g\n" % (1.0 - render.border_min_y))

    file.write("Bounding_Method=2\n")  # The new automatic BSP is faster in most scenes

    # Activated (turn this back off when better live exchange is done between the two programs
    # (see next comment)
    file.write("Display=1\n")
    file.write("Pause_When_Done=0\n")
    # PNG, with POV-Ray 3.7, can show background color with alpha. In the long run using the
    # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
    file.write("Output_File_Type=N\n")
    #file.write("Output_File_Type=T\n") # TGA, best progressive loading
    file.write("Output_Alpha=1\n")

    if scene.pov.antialias_enable:
        # method 2 (recursive) with higher max subdiv forced because no mipmapping in POV-Ray
        # needs higher sampling.
        # aa_mapping = {"5": 2, "8": 3, "11": 4, "16": 5}
        method = {"0": 1, "1": 2}
        file.write("Antialias=on\n")
        file.write("Sampling_Method=%s\n" % method[scene.pov.antialias_method])
        file.write("Antialias_Depth=%d\n" % scene.pov.antialias_depth)
        file.write("Antialias_Threshold=%.3g\n" % scene.pov.antialias_threshold)
        file.write("Antialias_Gamma=%.3g\n" % scene.pov.antialias_gamma)
        if scene.pov.jitter_enable:
            file.write("Jitter=on\n")
            file.write("Jitter_Amount=%3g\n" % scene.pov.jitter_amount)
        else:
            file.write("Jitter=off\n")  # prevent animation flicker

    else:
        file.write("Antialias=off\n")
    #print("ini file closed %s" % file.closed)
    file.close()
    #print("ini file closed %s" % file.closed)


class PovrayRender(bpy.types.RenderEngine):
    bl_idname = 'POVRAY_RENDER'
    bl_label = "POV-Ray 3.7"
    DELAY = 0.5

    def _export(self, scene, povPath, renderImagePath):
        import tempfile

        if scene.pov.tempfiles_enable:
            self._temp_file_in = tempfile.NamedTemporaryFile(suffix=".pov", delete=False).name
            # PNG with POV 3.7, can show the background color with alpha. In the long run using the
            # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
            #self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".tga", delete=False).name
            self._temp_file_ini = tempfile.NamedTemporaryFile(suffix=".ini", delete=False).name
        else:
            self._temp_file_in = povPath + ".pov"
            # PNG with POV 3.7, can show the background color with alpha. In the long run using the
            # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            self._temp_file_out = renderImagePath + ".png"
            #self._temp_file_out = renderImagePath + ".tga"
            self._temp_file_ini = povPath + ".ini"
            '''
            self._temp_file_in = "/test.pov"
            # PNG with POV 3.7, can show the background color with alpha. In the long run using the
            # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            self._temp_file_out = "/test.png"
            #self._temp_file_out = "/test.tga"
            self._temp_file_ini = "/test.ini"
            '''

        def info_callback(txt):
            self.update_stats("", "POV-Ray 3.7: " + txt)

        write_pov(self._temp_file_in, scene, info_callback)

    def _render(self, scene):

        try:
            os.remove(self._temp_file_out)  # so as not to load the old file
        except OSError:
            pass

        write_pov_ini(scene, self._temp_file_ini, self._temp_file_in, self._temp_file_out)

        print ("***-STARTING-***")

        pov_binary = "povray"

        extra_args = []

        if scene.pov.command_line_switches != "":
            for newArg in scene.pov.command_line_switches.split(" "):
                extra_args.append(newArg)

        self._is_windows = False
        if sys.platform[:3] == "win":
            self._is_windows = True
            #extra_args.append("/EXIT")

            import winreg
            import platform as pltfrm
            if pltfrm.architecture()[0] == "64bit":
                bitness = 64
            else:
                bitness = 32

            regKey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\POV-Ray\\v3.7\\Windows")

            # TODO, report api

            # 64 bits blender
            if bitness == 64:
                try:
                    pov_binary = winreg.QueryValueEx(regKey, "Home")[0] + "\\bin\\pvengine64"
                    self._process = subprocess.Popen(
                            [pov_binary, self._temp_file_ini] + extra_args,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    # This would work too but means we have to wait until its done:
                    # os.system("%s %s" % (pov_binary, self._temp_file_ini))

                except OSError:
                    # someone might run povray 32 bits on a 64 bits blender machine
                    try:
                        pov_binary = winreg.QueryValueEx(regKey, "Home")[0] + "\\bin\\pvengine"
                        self._process = subprocess.Popen(
                                [pov_binary, self._temp_file_ini] + extra_args,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                    except OSError:
                        # TODO, report api
                        print("POV-Ray 3.7: could not execute '%s', possibly POV-Ray isn't " \
                              "installed" % pov_binary)
                        import traceback
                        traceback.print_exc()
                        print ("***-DONE-***")
                        return False

                    else:
                        print("POV-Ray 3.7 64 bits could not execute, running 32 bits instead")
                        print("Command line arguments passed: " + str(extra_args))
                        return True

                else:
                    print("POV-Ray 3.7 64 bits found")
                    print("Command line arguments passed: " + str(extra_args))
                    return True

            #32 bits blender
            else:
                try:
                    pov_binary = winreg.QueryValueEx(regKey, "Home")[0] + "\\bin\\pvengine"
                    self._process = subprocess.Popen(
                            [pov_binary, self._temp_file_ini] + extra_args,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                # someone might also run povray 64 bits with a 32 bits build of blender.
                except OSError:
                    try:
                        pov_binary = winreg.QueryValueEx(regKey, "Home")[0] + "\\bin\\pvengine64"
                        self._process = subprocess.Popen(
                                [pov_binary, self._temp_file_ini] + extra_args,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                    except OSError:
                        # TODO, report api
                        print("POV-Ray 3.7: could not execute '%s', possibly POV-Ray isn't " \
                              "installed" % pov_binary)
                        import traceback
                        traceback.print_exc()
                        print ("***-DONE-***")
                        return False

                    else:
                        print("Running POV-Ray 3.7 64 bits build with 32 bits Blender,\n" \
                              "You might want to run Blender 64 bits as well.")
                        print("Command line arguments passed: " + str(extra_args))
                        return True

                else:
                    print("POV-Ray 3.7 32 bits found")
                    print("Command line arguments passed: " + str(extra_args))
                    return True

        else:
            # DH - added -d option to prevent render window popup which leads to segfault on linux
            extra_args.append("-d")

            isExists = False
            sysPathList = os.getenv("PATH").split(':')
            sysPathList.append("")

            for dirName in sysPathList:
                if (os.path.exists(os.path.join(dirName, pov_binary))):
                    isExists = True
                    break

            if not isExists:
                print("POV-Ray 3.7: could not found execute '%s' - not if PATH" % pov_binary)
                import traceback
                traceback.print_exc()
                print ("***-DONE-***")
                return False

            try:
                self._process = subprocess.Popen([pov_binary, self._temp_file_ini] + extra_args,
                                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            except OSError:
                # TODO, report api
                print("POV-Ray 3.7: could not execute '%s'" % pov_binary)
                import traceback
                traceback.print_exc()
                print ("***-DONE-***")
                return False

            else:
                print("POV-Ray 3.7 found")
                print("Command line arguments passed: " + str(extra_args))
                return True

        # Now that we have a valid process

    def _cleanup(self):
        for f in (self._temp_file_in, self._temp_file_ini, self._temp_file_out):
            for i in range(5):
                try:
                    os.unlink(f)
                    break
                except OSError:
                    # Wait a bit before retrying file might be still in use by Blender,
                    # and Windows does not know how to delete a file in use!
                    time.sleep(self.DELAY)

    def render(self, scene):
        import tempfile

        print("***INITIALIZING***")

##WIP output format
##        if r.image_settings.file_format == 'OPENEXR':
##            fformat = 'EXR'
##            render.image_settings.color_mode = 'RGBA'
##        else:
##            fformat = 'TGA'
##            r.image_settings.file_format = 'TARGA'
##            r.image_settings.color_mode = 'RGBA'

        blendSceneName = bpy.data.filepath.split(os.path.sep)[-1].split(".")[0]
        povSceneName = ""
        povPath = ""
        renderImagePath = ""

        # has to be called to update the frame on exporting animations
        scene.frame_set(scene.frame_current)

        if not scene.pov.tempfiles_enable:

            # check paths
            povPath = bpy.path.abspath(scene.pov.scene_path).replace('\\', '/')
            if povPath == "":
                if bpy.data.is_saved:
                    povPath = bpy.path.abspath("//")
                else:
                    povPath = tempfile.gettempdir()
            elif povPath.endswith("/"):
                if povPath == "/":
                    povPath = bpy.path.abspath("//")
                else:
                    povPath = bpy.path.abspath(scene.pov.scene_path)

            if not os.path.exists(povPath):
                try:
                    os.makedirs(povPath)
                except:
                    import traceback
                    traceback.print_exc()

                    print("POV-Ray 3.7: Cannot create scenes directory: %r" % povPath)
                    self.update_stats("", "POV-Ray 3.7: Cannot create scenes directory %r" % \
                                      povPath)
                    time.sleep(2.0)
                    return

            '''
            # Bug in POV-Ray RC3
            renderImagePath = bpy.path.abspath(scene.pov.renderimage_path).replace('\\','/')
            if renderImagePath == "":
                if bpy.data.is_saved:
                    renderImagePath = bpy.path.abspath("//")
                else:
                    renderImagePath = tempfile.gettempdir()
                #print("Path: " + renderImagePath)
            elif path.endswith("/"):
                if renderImagePath == "/":
                    renderImagePath = bpy.path.abspath("//")
                else:
                    renderImagePath = bpy.path.abspath(scene.pov.renderimage_path)
            if not os.path.exists(path):
                print("POV-Ray 3.7: Cannot find render image directory")
                self.update_stats("", "POV-Ray 3.7: Cannot find render image directory")
                time.sleep(2.0)
                return
            '''

            # check name
            if scene.pov.scene_name == "":
                if blendSceneName != "":
                    povSceneName = blendSceneName
                else:
                    povSceneName = "untitled"
            else:
                povSceneName = scene.pov.scene_name
                if os.path.isfile(povSceneName):
                    povSceneName = os.path.basename(povSceneName)
                povSceneName = povSceneName.split('/')[-1].split('\\')[-1]
                if not povSceneName:
                    print("POV-Ray 3.7: Invalid scene name")
                    self.update_stats("", "POV-Ray 3.7: Invalid scene name")
                    time.sleep(2.0)
                    return
                povSceneName = os.path.splitext(povSceneName)[0]

            print("Scene name: " + povSceneName)
            print("Export path: " + povPath)
            povPath = os.path.join(povPath, povSceneName)
            povPath = os.path.realpath(povPath)

            # for now this has to be the same like the pov output. Bug in POV-Ray RC3.
            # renderImagePath = renderImagePath + "\\" + povSceneName
            renderImagePath = povPath  # Bugfix for POV-Ray RC3 bug
            # renderImagePath = os.path.realpath(renderImagePath)  # Bugfix for POV-Ray RC3 bug

            #print("Export path: %s" % povPath)
            #print("Render Image path: %s" % renderImagePath)

        # start export
        self.update_stats("", "POV-Ray 3.7: Exporting data from Blender")
        self._export(scene, povPath, renderImagePath)
        self.update_stats("", "POV-Ray 3.7: Parsing File")

        if not self._render(scene):
            self.update_stats("", "POV-Ray 3.7: Not found")
            return

        r = scene.render
        # compute resolution
        x = int(r.resolution_x * r.resolution_percentage * 0.01)
        y = int(r.resolution_y * r.resolution_percentage * 0.01)

        # This makes some tests on the render, returning True if all goes good, and False if
        # it was finished one way or the other.
        # It also pauses the script (time.sleep())
        def _test_wait():
            time.sleep(self.DELAY)

            # User interrupts the rendering
            if self.test_break():
                try:
                    self._process.terminate()
                    print("***POV INTERRUPTED***")
                except OSError:
                    pass
                return False

            poll_result = self._process.poll()
            # POV process is finisehd, one way or the other
            if poll_result is not None:
                if poll_result < 0:
                    print("***POV PROCESS FAILED : %s ***" % poll_result)
                    self.update_stats("", "POV-Ray 3.7: Failed")
                return False

            return True

        # Wait for the file to be created
        # XXX This is no more valid, as 3.7 always creates output file once render is finished!
        parsing = re.compile(br"= \[Parsing\.\.\.\] =")
        rendering = re.compile(br"= \[Rendering\.\.\.\] =")
        percent = re.compile(r"\(([0-9]{1,3})%\)")
        # print("***POV WAITING FOR FILE***")

        data = b""
        last_line = ""
        while _test_wait():
            # POV in Windows does not output its stdout/stderr, it displays them in its GUI
            if self._is_windows:
                self.update_stats("", "POV-Ray 3.7: Rendering File")
            else:
                t_data = self._process.stdout.read(10000)
                if not t_data:
                    continue

                data += t_data
                # XXX This is working for UNIX, not sure whether it might need adjustments for
                #     other OSs
                # First replace is for windows
                t_data = str(t_data).replace('\\r\\n', '\\n').replace('\\r', '\r')
                lines = t_data.split('\\n')
                last_line += lines[0]
                lines[0] = last_line
                print('\n'.join(lines), end="")
                last_line = lines[-1]

                if rendering.search(data):
                    _pov_rendering = True
                    match = percent.findall(str(data))
                    if match:
                        self.update_stats("", "POV-Ray 3.7: Rendering File (%s%%)" % match[-1])
                    else:
                        self.update_stats("", "POV-Ray 3.7: Rendering File")

                elif parsing.search(data):
                    self.update_stats("", "POV-Ray 3.7: Parsing File")

        if os.path.exists(self._temp_file_out):
            # print("***POV FILE OK***")
            #self.update_stats("", "POV-Ray 3.7: Rendering")

            # prev_size = -1

            xmin = int(r.border_min_x * x)
            ymin = int(r.border_min_y * y)
            xmax = int(r.border_max_x * x)
            ymax = int(r.border_max_y * y)

            # print("***POV UPDATING IMAGE***")
            result = self.begin_result(0, 0, x, y)
            # XXX, tests for border render.
            #result = self.begin_result(xmin, ymin, xmax - xmin, ymax - ymin)
            #result = self.begin_result(0, 0, xmax - xmin, ymax - ymin)
            lay = result.layers[0]

            # This assumes the file has been fully written We wait a bit, just in case!
            time.sleep(self.DELAY)
            try:
                lay.load_from_file(self._temp_file_out)
                # XXX, tests for border render.
                #lay.load_from_file(self._temp_file_out, xmin, ymin)
            except RuntimeError:
                print("***POV ERROR WHILE READING OUTPUT FILE***")

            # Not needed right now, might only be useful if we find a way to use temp raw output of
            # pov 3.7 (in which case it might go under _test_wait()).
#            def update_image():
#                # possible the image wont load early on.
#                try:
#                    lay.load_from_file(self._temp_file_out)
#                    # XXX, tests for border render.
#                    #lay.load_from_file(self._temp_file_out, xmin, ymin)
#                    #lay.load_from_file(self._temp_file_out, xmin, ymin)
#                except RuntimeError:
#                    pass

#            # Update while POV-Ray renders
#            while True:
#                # print("***POV RENDER LOOP***")

#                # test if POV-Ray exists
#                if self._process.poll() is not None:
#                    print("***POV PROCESS FINISHED***")
#                    update_image()
#                    break

#                # user exit
#                if self.test_break():
#                    try:
#                        self._process.terminate()
#                        print("***POV PROCESS INTERRUPTED***")
#                    except OSError:
#                        pass

#                    break

#                # Would be nice to redirect the output
#                # stdout_value, stderr_value = self._process.communicate() # locks

#                # check if the file updated
#                new_size = os.path.getsize(self._temp_file_out)

#                if new_size != prev_size:
#                    update_image()
#                    prev_size = new_size

#                time.sleep(self.DELAY)

            self.end_result(result)

        else:
            print("***POV FILE NOT FOUND***")

        print("***POV FINISHED***")

        self.update_stats("", "")

        if scene.pov.tempfiles_enable or scene.pov.deletefiles_enable:
            self._cleanup()
