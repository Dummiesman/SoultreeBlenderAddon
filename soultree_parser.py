import re
from . import soultree_classes as soultree
from .soultree_common import *


class SoulTreeParser:
    def __init__(self, file):
        self.file = file
        self.model = soultree.SoulTreeModel()
        pass

    def parse_line(self, file):
        raw_line = file.readline()
        if len(raw_line) == 0:
            return None

        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            return (TYPE_SECTION, line[1:-1])
        elif "=" in line:
            idx = line.index("=")
            key = line[0:idx]
            value = line[idx+1:]
            return (TYPE_VALUE, key, value)
        else:
            return (TYPE_OTHER, line)

    def ascii_get_class(self, section_name):
        if section_name == "Materials" or section_name == "LOD Information":
            return self.model
        elif section_name == "Object Hierarchy":
            return self.model.object_hierarchy
        elif m := re.match("^Material - (\d+)$", section_name):
            matnum = int(m.group(1))
            return self.model.get_material(matnum)
        elif m := re.match("^LOD (\d+)$", section_name):
            lodnum = int(m.group(1))
            return self.model.get_lod(lodnum)
        elif m := re.match("^LOD (\d+) - Surface (\d+)$", section_name):
            lodnum = int(m.group(1))
            surfnum = int(m.group(2))
            return self.model.get_surface(lodnum, surfnum)
        elif m := re.match("^LOD (\d+) - Surface (\d+) - Vertices$", section_name):
            lodnum = int(m.group(1))
            surfnum = int(m.group(2))
            return self.model.get_surface(lodnum, surfnum).vertex_list
        elif m := re.match("^LOD (\d+) - Surface (\d+) - Faces$", section_name):
            lodnum = int(m.group(1))
            surfnum = int(m.group(2))
            return self.model.get_surface(lodnum, surfnum).face_list
        elif m := re.match("^LOD (\d+) - Surface (\d+) - Object Pointer List$", section_name):
            lodnum = int(m.group(1))
            surfnum = int(m.group(2))
            return self.model.get_surface(lodnum, surfnum).object_pointer_list

    def read_ascii(self):
        # read in slt file!
        current_parser = None
        while line_data := self.parse_line(self.file):
            line_type = line_data[0]

            if line_type == TYPE_SECTION:
                section_name = line_data[1]
                current_parser = self.ascii_get_class(section_name)
            elif current_parser is not None:
                current_parser.parse(line_data)

    def read(self):
        fmode = self.file.mode
        if "b" in fmode:
            self.model.read_binary(self.file)
        else:
            self.read_ascii()

    def read_and_get_model(self):
        self.read()
        return self.model
