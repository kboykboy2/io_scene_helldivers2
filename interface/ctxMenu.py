from bpy.types import Menu

from ..utils.hash import GetFriendlyNameFromID
from .. import globals

def DrawEntryButtons(row, Entry):
    #TODO: Figure out how to redraw gui panel to update it
    if not Entry.IsSelected:
        globals.TocManager.SelectEntries([Entry])

    # Combine entry strings to be passed to operators
    FileIDStr = ""
    TypeIDStr = ""
    for SelectedEntry in globals.TocManager.SelectedEntries:
        FileIDStr += str(SelectedEntry.FileID)+","
        TypeIDStr += str(SelectedEntry.TypeID)+","
    # Get common class
    AreAllMeshes    = True
    AreAllTextures  = True
    AreAllMaterials = True
    SingleEntry = True
    NumSelected = len(globals.TocManager.SelectedEntries)
    if len(globals.TocManager.SelectedEntries) > 1:
        SingleEntry = False
    for SelectedEntry in globals.TocManager.SelectedEntries:
        if SelectedEntry.TypeID == globals.MeshID:
            AreAllTextures = False
            AreAllMaterials = False
        elif SelectedEntry.TypeID == globals.TexID:
            AreAllMeshes = False
            AreAllMaterials = False
        elif SelectedEntry.TypeID == globals.MaterialID:
            AreAllTextures = False
            AreAllMeshes = False
    if SingleEntry:
        RemoveFromPatchName = "Remove From Patch"
        AddToPatchName = "Add To Patch"
        ImportMeshName = "Import Mesh"
        ImportTextureName = "Import Texture"
        ImportMaterialName = "Import Material"
        DumpObjectName = "Dump Object"
        SaveTextureName = "Save Blender Texture"
        SaveMaterialName = "Save Material"
        UndoName = "Undo Modifications"
        CopyName = "Copy Entry"
    else:
        RemoveFromPatchName = f"Remove {NumSelected} From Patch"
        AddToPatchName = f"Add {NumSelected} To Patch"
        ImportMeshName = f"Import {NumSelected} Meshes"
        ImportTextureName = f"Import {NumSelected} Textures"
        ImportMaterialName = f"Import {NumSelected} Materials"
        DumpObjectName = f"Dump {NumSelected} Objects"
        SaveTextureName = f"Save Blender {NumSelected} Textures"
        SaveMaterialName = f"Save {NumSelected} Materials"
        UndoName = f"Undo {NumSelected} Modifications"
        CopyName = f"Copy {NumSelected} Entries"
    # Draw seperator
    row.separator()
    row.label(text="---------- HellDivers2 ----------")

    # Draw copy button
    row.separator()
    props = row.operator("helldiver2.archive_copy", icon="COPYDOWN", text=CopyName)
    props.object_id     = FileIDStr
    props.object_typeid = TypeIDStr
    if SingleEntry:
        props = row.operator("helldiver2.archive_duplicate", icon="DUPLICATE", text="Duplicate Entry")
        props.object_id     = str(Entry.FileID)
        props.object_typeid = str(Entry.TypeID)
    if globals.TocManager.IsInPatch(Entry):
        props = row.operator("helldiver2.archive_removefrompatch", icon="X", text=RemoveFromPatchName)
        props.object_id     = FileIDStr
        props.object_typeid = TypeIDStr
    else:
        props = row.operator("helldiver2.archive_addtopatch", icon="PLUS", text=AddToPatchName)
        props.object_id     = FileIDStr
        props.object_typeid = TypeIDStr

    # Draw import buttons
    # TODO: Add generic import buttons
    row.separator()
    if   AreAllMeshes   : row.operator("helldiver2.archive_mesh_import", icon="IMPORT", text=ImportMeshName).object_id = FileIDStr
    elif AreAllTextures : row.operator("helldiver2.texture_import", icon="IMPORT", text=ImportTextureName).object_id = FileIDStr
    elif AreAllMaterials: row.operator("helldiver2.material_import", icon="IMPORT", text=ImportMaterialName).object_id = FileIDStr
    # Draw export buttons
    row.separator()
    if AreAllTextures:
        if SingleEntry:
            row.operator("helldiver2.texture_export", icon="EXPORT", text="Export Texture").object_id = str(Entry.FileID)
        else:
            row.operator("helldiver2.texture_batchexport", icon="EXPORT", text=f"Export {NumSelected} Textures").object_id = FileIDStr
    props = row.operator("helldiver2.archive_object_dump", icon="PACKAGE", text=DumpObjectName)
    props.object_id     = FileIDStr
    props.object_typeid = TypeIDStr
    # Draw save buttons
    row.separator()
    if AreAllMeshes:
        if SingleEntry:
            row.operator("helldiver2.archive_mesh_save", icon="FILE_BLEND", text="Save Mesh").object_id = str(Entry.FileID)
        else:
            row.operator("helldiver2.archive_mesh_batchsave", icon="FILE_BLEND", text=f"Save {NumSelected} Meshes")
    elif AreAllTextures:
        row.operator("helldiver2.texture_saveblendimage", icon="FILE_BLEND", text=SaveTextureName).object_id = FileIDStr
        if SingleEntry:
            row.operator("helldiver2.texture_savefromdds", icon="IMAGE_REFERENCE", text="Save Texture From DDs").object_id = str(Entry.FileID)
    elif AreAllMaterials: row.operator("helldiver2.material_save", icon="FILE_BLEND", text=SaveMaterialName).object_id = FileIDStr
    # Draw copy ID buttons
    if SingleEntry:
        row.separator()
        row.operator("helldiver2.copytest", icon="COPY_ID", text="Copy Entry ID").text = str(Entry.FileID)
        row.operator("helldiver2.copytest", icon="COPY_ID", text="Copy Type ID").text  = str(Entry.TypeID)
        row.operator("helldiver2.copytest", icon="COPY_ID", text="Copy Friendly Name").text  = GetFriendlyNameFromID(Entry.FileID)
        if globals.TocManager.IsInPatch(Entry):
            props = row.operator("helldiver2.archive_entryrename", icon="TEXT", text="Rename")
            props.object_id     = str(Entry.FileID)
            props.object_typeid = str(Entry.TypeID)
    if Entry.IsModified:
        row.separator()
        props = row.operator("helldiver2.archive_undo_mod", icon="TRASH", text=UndoName)
        props.object_id     = FileIDStr
        props.object_typeid = TypeIDStr

    if SingleEntry:
        row.operator("helldiver2.archive_setfriendlyname", icon="WORDWRAP_ON", text="Set Friendly Name").object_id = str(Entry.FileID)

    return

class WM_MT_button_context(Menu):
    bl_label = "Entry Context Menu"

    def draw(self, context):
        value = getattr(context, "button_operator", None)
        if type(value).__name__ == "HELLDIVER2_OT_archive_entry":
            layout = self.layout
            FileID = getattr(value, "object_id")
            TypeID = getattr(value, "object_typeid")
            DrawEntryButtons(layout, globals.TocManager.GetEntry(int(FileID), int(TypeID)))
