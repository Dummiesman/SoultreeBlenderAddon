bl_info = {
    "name": "Rainbow Studios SoulTree Format",
    "author": "Dummiesman",
    "version": (0, 0, 2),
    "blender": (2, 90, 0),
    "location": "File > Import-Export",
    "description": "Import-Export SLT files",
    "warning": "",
    "doc_url": "https://github.com/Dummiesman/SoultreeBlenderAddon/",
    "tracker_url": "https://github.com/Dummiesman/SoultreeBlenderAddon/",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

import bpy
import textwrap 

from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )

class ImportSLT(bpy.types.Operator, ImportHelper):
    """Import from SLT/SLB file format (.slt/.slb)"""
    bl_idname = "import_scene.slt"
    bl_label = 'Import SoulTree'
    bl_options = {'UNDO'}

    filename_ext = ".slt;*.slb"
    filter_glob: StringProperty(default="*.slt;*.slb", options={'HIDDEN'})

    def execute(self, context):
        from . import import_slt
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_slt.load(self, context, **keywords)


# Add to a menu
def menu_func_import_slt(self, context):
    self.layout.operator(ImportSLT.bl_idname, text="SoulTree Model (.slt/.slb)")

# Register factories
classes = (
    
)

def register():
    bpy.utils.register_class(ImportSLT)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_slt)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_slt)
    bpy.utils.unregister_class(ImportSLT)

if __name__ == "__main__":
    register()
