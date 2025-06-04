import bpy, bmesh, mathutils
from bpy_extras.io_utils import axis_conversion
import time
import math
import re

from . import soultree_parser
from . import soultree_classes as soultree

######################################################
# IMPORT MAIN FILES
######################################################
def new_material(name):
    # setup material
    mtl = bpy.data.materials.new(name=name)
    mtl.specular_intensity = 0

    mtl.use_nodes = True
    mtl.use_backface_culling = True

    return mtl


def new_object(name, parent):
    scn = bpy.context.scene
    # add a mesh and link it to the scene
    me = bpy.data.meshes.new(name + "Mesh")
    ob = bpy.data.objects.new(name, me)

    if parent is not None:
        ob.parent = parent

    bm = bmesh.new()
    bm.from_mesh(me)

    scn.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob

    return (ob, bm)


def get_conversion_matrix():
    mtx_convert = axis_conversion(from_forward='Z', from_up='Y',
                                  to_forward='-Y', to_up='-Z').to_4x4()

    return mtx_convert

def slt_vertex_to_blender(vtx):
    return (vtx[0], -vtx[2], vtx[1])

def slt_matrix_to_blender(mtx):
    for x in range(3):
        row = mtx[x]
        mtx[x] = (row[0], -row[2], row[1], row[3])

    x, y, z = mtx[0][3], mtx[1][3], mtx[2][3]
    mtx[0][3], mtx[1][3], mtx[2][3] = x, -z, y

    return mtx

def make_vertex_to_face_map(surface):
    """ Makes a map of [vertex_index]=[(face),(face),etc]"""
    faces = surface.face_list.faces
    vertex_map = {}

    for face in faces:
        for index in face:
            if index not in vertex_map:
                vertex_map[index] = []
            vertex_map[index].append(face)

    return vertex_map


def read_slt_file(file):
    # parse and get parsed file
    parser = soultree_parser.SoulTreeParser(file)
    model = parser.read_and_get_model()

    # import first lod
    lod = model.get_lod(0)

    # to import soultree
    # - for each object
    # -- get all surfaces
    # --- get faces and  verts in surface for the object
    object_count = len(model.object_hierarchy.objects)
    material_count = len(model.materials)

    blender_objects = [None]*object_count
    blender_materials = [None]*material_count

    for mat_num in range(material_count):
        blender_materials[mat_num] = new_material("Material#" + str(mat_num))

    for ob_num in range(object_count):
        ob_data = model.object_hierarchy.objects[ob_num]

        # get parent index
        parent_idx = -1
        if ob_data.parent is not None:
            parent_idx = model.object_hierarchy.objects.index(ob_data.parent)

        # create object
        ob, bm = new_object(ob_data.name, None if parent_idx < 0 else blender_objects[parent_idx])
        blender_objects[ob_num] = ob

        mtx = mathutils.Matrix()
        for x in range(4):
            for y in range(3):
                idx = (x * 3) + y
                mtx[y][x] = ob_data.matrix[idx]

        # ob.matrix_local = slt_matrix_to_blender(mtx)
        # ob.matrix_local = mtx @ get_conversion_matrix()
        ob.location = slt_vertex_to_blender((ob_data.matrix[9], ob_data.matrix[10], ob_data.matrix[11]))

        # create layers for this object
        uv_layer = bm.loops.layers.uv.new()
        vc_layer = bm.loops.layers.color.new()

        # add materials
        material_index_map = {}
        for surface in lod.surfaces:
            vertex_range_start, vertex_range_count = surface.object_pointer_list.get_vertex_range(ob_num)
            if vertex_range_count > 0:
                for index in surface.material_indices:
                    if index not in material_index_map:
                        material_index_map[index] = len(ob.data.materials)
                        ob.data.materials.append(blender_materials[index])

        # fill it with data
        vertex_base = 0
        surf_material_number = 0

        for surface in lod.surfaces:
            vertex_range_start, vertex_range_count = surface.object_pointer_list.get_vertex_range(ob_num)
            vertex_range_end = vertex_range_start + vertex_range_count

            # create verts and gather faces
            faces = set()
            vertex_map = {}  # index to BM
            v2f_map = make_vertex_to_face_map(surface)

            for vertnum in range(vertex_range_start, vertex_range_end):
                adjusted_vertnum = vertnum + vertex_base
                if adjusted_vertnum not in vertex_map:
                    vert = surface.vertex_list.vertices[vertnum].co
                    faces.update(v2f_map[vertnum])

                    vert = slt_vertex_to_blender(vert)
                    bmvert = bm.verts.new(vert)
                    vertex_map[vertnum] = bmvert

            # create faces
            for face_indices in faces:
                # create face
                try:
                    bmverts = [vertex_map[x] for x in face_indices]
                    verts = [surface.vertex_list.vertices[x] for x in face_indices]

                    face = bm.faces.new(bmverts)
                    face.material_index = material_index_map[surf_material_number]
                    face.smooth = True

                    for x in range(3):
                        face.loops[x][uv_layer].uv = (verts[x].uv[0], 1 - verts[x].uv[1])
                        face.loops[x][vc_layer] = verts[x].color

                except Exception as e:
                    print(str(e))

            # --
            vertex_base += vertex_range_count
            surf_material_number += 1

        # calculate normals
        bm.normal_update()

        # free resources
        bm.to_mesh(ob.data)
        bm.free()


######################################################
# IMPORT
######################################################
def load_slt(filepath,
             context):

    print("importing SoulTree: %r..." % (filepath))

    time1 = time.perf_counter()

    mode = 'rb' if filepath.lower().endswith(".slb") else 'r'
    file = open(filepath, mode)

    # start reading our slt file
    read_slt_file(file)

    print(" done in %.4f sec." % (time.perf_counter() - time1))
    file.close()


def load(operator,
         context,
         filepath="",
         ):

    load_slt(filepath,
             context,
             )

    return {'FINISHED'}
