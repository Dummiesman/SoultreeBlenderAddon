import re
import struct
from .soultree_common import *


class Object:
    def __init__(self):
        self.matrix = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
        self.parent = None
        self.name = "Object"


class ObjectHierarchy:
    def __init__(self):
        self.objects = []

    def read_binary_stage1(self, file, count):
        for x in range(count):
            name = read_constsize_str(file, 128)
            matrix = []

            for y in range(4):
                for x in range(4):
                    matrix_value = struct.unpack("<f", file.read(4))[0]
                    if x != 3:
                        matrix.append(matrix_value)

            file.seek(60, 1)

            # add to list
            obj = Object()
            obj.matrix = matrix
            obj.name = name
            obj.parent = None

            self.objects.append(obj)

    def read_binary_stage2(self, file, count):
        for x in range(count):
            parent_id = struct.unpack("<l", file.read(4))[0]
            self.objects[x].parent = None if parent_id < 0 else self.objects[parent_id]

    def parse(self, line_data):
        line_type = line_data[0]
        parent_names = []

        if line_type == TYPE_OTHER:
            _, line = line_data
            splits = line.split(",")

            # parse
            name = splits[0]
            parent_name = splits[1]
            matrix = []

            for x in range(2, len(splits)):
                matrix.append(float(splits[x]))

            # get parent
            parent = None
            for ob in self.objects:
                if ob.name == parent_name:
                    parent = ob
                    break

            # add to list
            obj = Object()
            obj.matrix = matrix
            obj.name = name
            obj.parent = parent

            self.objects.append(obj)


class Vertex:
    def __init__(self):
        self.co = (0.0, 0.0, 0.0)
        self.normal = (0.0, 0.0, 0.0)
        self.color = (1.0, 1.0, 1.0, 0.0)
        self.uv = (0.0, 0.0)


class FaceList:
    def __init__(self):
        self.faces = []

    def read_binary(self, file, count):
        for x in range(count):
            i0, i1, i2 = struct.unpack("<HHH", file.read(6))
            self.faces.append((i0, i1, i2))

    def parse(self, line_data):
        line_type = line_data[0]

        if line_type == TYPE_OTHER:
            _, line = line_data
            splits = line.split(",")

            i0 = int(splits[0])
            i1 = int(splits[1])
            i2 = int(splits[2])

            self.faces.append((i0, i1, i2))


class VertexList:
    def __init__(self):
        self.vertices = []

    def read_binary(self, file, count):
        for x in range(count):
            vx, vy, vz = struct.unpack("<fff", file.read(12))
            file.seek(4, 1)
            cr, cg, cb, ca = struct.unpack("<BBBB", file.read(4))
            file.seek(4, 1)
            tu, tv = struct.unpack("<ff", file.read(8))

            vertex = Vertex()
            vertex.co = (vx, vy, vz)
            vertex.uv = (tu, tv)
            vertex.color = (float(cr) / 255.0, float(cg) / 255.0, float(cb) / 255.0, float(ca) / 255.0)

            self.vertices.append(vertex)

    def parse(self, line_data):
        line_type = line_data[0]

        if line_type == TYPE_OTHER:
            _, line = line_data
            splits = line.split(",")

            vx = float(splits[0])
            vy = float(splits[1])
            vz = float(splits[2])

            nx = float(splits[3])
            ny = float(splits[4])
            nz = float(splits[5])

            tu = float(splits[6])
            tv = float(splits[7])

            cr = float(splits[12])
            cg = float(splits[13])
            cb = float(splits[14])

            vertex = Vertex()
            vertex.co = (vx, vy, vz)
            vertex.normal = (nx, ny, nz)
            vertex.uv = (tu, tv)
            vertex.color = (cr, cg, cb, 0.0)

            self.vertices.append(vertex)


class ObjectPointerList:
    def __init__(self):
        self.vertex_ranges = {}

    def get_vertex_range(self, obnum):
        if obnum not in self.vertex_ranges:
            return (0, 0)
        return self.vertex_ranges[obnum]

    def read_binary(self, file, count):
        temp_vertex_ranges = []

        for x in range(count):
            file.seek(4, 1)  # internal game pointer
            vertex_count = struct.unpack("<L", file.read(4))[0]
            file.seek(12, 1)  # internal game pointers

            temp_vertex_ranges.append([0, 0, vertex_count])

        for x in range(count):
            object_num, vertex_start = struct.unpack("<LL", file.read(8))
            temp_vertex_ranges[x][0] = object_num
            temp_vertex_ranges[x][1] = vertex_start

        for objnum, start, count in temp_vertex_ranges:
            self.vertex_ranges[objnum] = (start, count)

    def parse(self, line_data):
        line_type = line_data[0]

        if line_type == TYPE_OTHER:
            _, line = line_data
            splits = line.split(",")

            start = int(splits[0])
            count = int(splits[1])

            self.vertex_ranges[len(self.vertex_ranges)] = (start, count)


class Surface:
    def __init__(self):
        self.vertex_list = VertexList()  # vertices list of class Vertex
        self.face_list = FaceList()  # faces tuples of (i0, i1, i2)
        self.object_pointer_list = ObjectPointerList()  # vertex_ranges tuples of (start, count)
        self.material_indices = []

    def read_binary(self, file):
        object_pointer_count, vertex_count = struct.unpack('<LL', file.read(8))
        face_count, material_count = struct.unpack('<LL', file.read(8))

        dummy_vertex_list = VertexList()

        # read verts
        dummy_vertex_list.read_binary(file, vertex_count)  # pretransformed set
        self.vertex_list.read_binary(file, vertex_count)  # untransformed set

        # normals?
        for x in range(vertex_count):
            nx, ny, nz = struct.unpack("<fff", file.read(12))
            self.vertex_list.vertices[x].normal = (nx, ny, nz)

        self.face_list.read_binary(file, face_count)
        file.seek(8 * vertex_count, 1)  # uvs again?
        self.material_indices = struct.unpack("<{}L".format(material_count), file.read(material_count * 4))

        # read object pointers
        self.object_pointer_list.read_binary(file, object_pointer_count)

    def parse(self, line_data):
        line_type = line_data[0]

        if line_type == TYPE_VALUE:
            _, key, value = line_data
            if key == "NumberOfMaterials":
                number_of_materials = int(value)
                self.material_indices = [-1 for i in range(number_of_materials)]
            if "Material#" in key:
                material_number = int(key[9:])
                material_index = int(value)
                self.material_indices[material_number] = material_index


class LOD:
    def __init__(self):
        self.surfaces = []

    def read_binary(self, file):
        surface_count = struct.unpack("<L", file.read(4))[0]
        self.surfaces = [Surface() for x in range(surface_count)]

        for x in range(surface_count):
            self.surfaces[x].read_binary(file)

    def parse(self, line_data):
        line_type = line_data[0]

        if line_type == TYPE_VALUE:
            _, key, value = line_data
            if key == "NumberOfSurfaces":
                number_of_surfaces = int(value)
                self.surfaces = [Surface() for i in range(number_of_surfaces)]


class Material:
    def __init__(self):
        self.texture = None

    def read_binary(self, file):
        self.texture = read_constsize_str(file, 64)
        file.seek(66, 1)

    def parse(self, line_data):
        line_type = line_data[0]

        if line_type == TYPE_VALUE:
            _, key, value = line_data
            if key == "TextureMap":
                self.texture = value


class SoulTreeModel:
    def __init__(self):
        self.lods = []
        self.materials = []
        self.object_hierarchy = ObjectHierarchy()

    def get_lod(self, lodid):
        return self.lods[lodid]

    def get_surface(self, lodid, surfid):
        return self.get_lod(lodid).surfaces[surfid]

    def get_material(self, matid):
        return self.materials[matid]

    def read_binary(self, file):
        object_count = struct.unpack("<L", file.read(4))[0]
        self.object_hierarchy.read_binary_stage1(file, object_count)
        self.object_hierarchy.read_binary_stage2(file, object_count)

        material_count = struct.unpack("<L", file.read(4))[0]
        self.materials = [Material() for x in range(material_count)]
        for x in range(material_count):
            self.materials[x].read_binary(file)

        lod_count = struct.unpack("<L", file.read(4))[0]
        auto_lod = struct.unpack("<L", file.read(4))[0] != 0
        if auto_lod:
            file.seek(4 * (lod_count - 1), 1)

        self.lods = [LOD() for x in range(lod_count)]
        for x in range(lod_count):
            self.lods[x].read_binary(file)

    def parse(self, line_data):
        line_type = line_data[0]

        if line_type == TYPE_VALUE:
            _, key, value = line_data
            if key == "NumberOfLOD":
                number_of_lods = int(value)
                self.lods = [LOD() for i in range(number_of_lods)]
            elif key == "NumberOfMaterials":
                number_of_materials = int(value)
                self.materials = [LOD() for i in range(number_of_materials)]
