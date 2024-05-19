bl_info = {
    "name": "Helldivers 2 Archives",
    "blender": (3, 1, 2), # NOTE: Much progress was made on 4.0 so should this reflect that in case of API incompatibilities?
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    importlib.reload(HD2_Globals)
    importlib.reload(HD2_MemoryStream)
    importlib.reload(HD2_Stingray_Bone)
    importlib.reload(HD2_Stingray_Material)
    importlib.reload(HD2_Stingray_Mesh)
    importlib.reload(HD2_Stingray_Stream)
    importlib.reload(HD2_Stingray_Texture)
    importlib.reload(HD2_Stingray_Toc)
    importlib.reload(HD2_Interface)
    importlib.reload(HD2_Interface_ContextMenu)
    importlib.reload(HD2_Interface_Operators)
    importlib.reload(HD2_Interface_Panels)
    importlib.reload(HD2_Utils_Hash)
    importlib.reload(HD2_Utils_Math)
    importlib.reload(HD2_Utils_Normals)
else:
    from . import globals as HD2_Globals
    from . import interface as HD2_Interface
    from .classes_and_defs import memoryStream as HD2_MemoryStream
    from .classes_and_defs.stingray import bone as HD2_Stingray_Bone
    from .classes_and_defs.stingray import material as HD2_Stingray_Material
    from .classes_and_defs.stingray import mesh as HD2_Stingray_Mesh
    from .classes_and_defs.stingray import stream as HD2_Stingray_Stream
    from .classes_and_defs.stingray import texture as HD2_Stingray_Texture
    from .classes_and_defs.stingray import toc as HD2_Stingray_Toc
    from .interface import ctxMenu as HD2_Interface_ContextMenu
    from .interface import operators as HD2_Interface_Operators
    from .interface import panels as HD2_Interface_Panels
    from .utils import hash as HD2_Utils_Hash
    from .utils import math as HD2_Utils_Math
    from .utils import normals as HD2_Utils_Normals

import bpy
from bpy.props import PointerProperty

classes = HD2_Interface.classes_archive + \
          HD2_Interface.classes_mesh + \
          HD2_Interface.classes_material + \
          HD2_Interface.classes_texture + \
          HD2_Interface.classes_interface

def register():
    HD2_Utils_Normals.LoadNormalPalette()
    HD2_Utils_Hash.LoadTypeHashes()
    HD2_Utils_Hash.LoadNameHashes()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.Hd2ToolPanelSettings = PointerProperty(type=HD2_Interface_Panels.Hd2ToolPanelSettings)
    bpy.utils.register_class(HD2_Interface_ContextMenu.WM_MT_button_context)

def unregister():
    bpy.utils.unregister_class(HD2_Interface_ContextMenu.WM_MT_button_context)
    del bpy.types.Scene.Hd2ToolPanelSettings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
