import bpy
from bpy.types import Panel, PropertyGroup
from bpy.props import BoolProperty, EnumProperty, StringProperty

from ..utils.hash import GetFriendlyNameFromID, GetTypeNameFromID
from .. import globals

def DrawEntryButtonsSimple(box, row, Entry, PatchOnly):
    if Entry.TypeID == globals.MeshID:
        row.operator("helldiver2.archive_mesh_save", icon="FILE_BLEND", text="").object_id = str(Entry.FileID)
        row.operator("helldiver2.archive_mesh_import", icon="IMPORT", text="").object_id = str(Entry.FileID)
    elif Entry.TypeID == globals.TexID:
        row.operator("helldiver2.texture_saveblendimage", icon="FILE_BLEND", text="").object_id = str(Entry.FileID)
        row.operator("helldiver2.texture_import", icon="IMPORT", text="").object_id = str(Entry.FileID)
    elif Entry.TypeID == globals.MaterialID:
        row.operator("helldiver2.material_save", icon="FILE_BLEND", text="").object_id = str(Entry.FileID)
        row.operator("helldiver2.material_import", icon="IMPORT", text="").object_id = str(Entry.FileID)
        DrawMaterialEditor(Entry, box, row)
    if globals.TocManager.IsInPatch(Entry):
        props = row.operator("helldiver2.archive_removefrompatch", icon="FAKE_USER_ON", text="")
        props.object_id     = str(Entry.FileID)
        props.object_typeid = str(Entry.TypeID)
    else:
        props = row.operator("helldiver2.archive_addtopatch", icon="FAKE_USER_OFF", text="")
        props.object_id     = str(Entry.FileID)
        props.object_typeid = str(Entry.TypeID)
    if Entry.IsModified:
        props = row.operator("helldiver2.archive_undo_mod", icon="TRASH", text="")
        props.object_id     = str(Entry.FileID)
        props.object_typeid = str(Entry.TypeID)
    if PatchOnly:
        props = row.operator("helldiver2.archive_removefrompatch", icon="X", text="")
        props.object_id     = str(Entry.FileID)
        props.object_typeid = str(Entry.TypeID)

def DrawMaterialEditor(Entry, layout, row):
    row.operator("helldiver2.material_showeditor", icon="MOD_LINEART", text="").object_id = str(Entry.FileID)
    if Entry.IsLoaded:
        mat = Entry.LoadedData
        if mat.DEV_ShowEditor:
            for TexIndex in range(len(mat.TexIDs)):
                row = layout.row()
                row.separator(); row.separator(); row.separator()
                if mat.DEV_DDSPaths[TexIndex] != None:
                    row.label(text=mat.DEV_DDSPaths[TexIndex], icon="FILE_IMAGE")
                else:
                    textstr = str(mat.TexIDs[TexIndex])
                    if mat.TexIDs[TexIndex] == 14423187101809176546: textstr += ": color"
                    if mat.TexIDs[TexIndex] == 12451968300768537108: textstr += ": sss color"
                    if mat.TexIDs[TexIndex] == 16331558339684530227: textstr += ": pbr"
                    if mat.TexIDs[TexIndex] == 6363549403025827661: textstr += ": normal"
                    row.label(text=textstr, icon="FILE_IMAGE")
                props = row.operator("helldiver2.material_settex", icon="FILEBROWSER", text="")
                props.object_id = str(Entry.FileID)
                props.tex_idx   = TexIndex

def GetDisplayData():
    # Set display archive
    # TODO: TocManager.LastSelected Draw Index could be wrong if we switch to patch only mode, that should be fixed
    DisplayTocEntries = []
    DisplayTocTypes   = []
    DisplayArchive = globals.TocManager.ActiveArchive
    if bpy.context.scene.Hd2ToolPanelSettings.PatchOnly:
        if globals.TocManager.ActivePatch != None:
            DisplayTocEntries = [[Entry, True] for Entry in globals.TocManager.ActivePatch.TocEntries]
            DisplayTocTypes   = globals.TocManager.ActivePatch.TocTypes
    elif globals.TocManager.ActiveArchive != None:
        DisplayTocEntries = [[Entry, False] for Entry in globals.TocManager.ActiveArchive.TocEntries]
        DisplayTocTypes   = [Type for Type in globals.TocManager.ActiveArchive.TocTypes]
        AddedTypes   = [Type.TypeID for Type in DisplayTocTypes]
        AddedEntries = [Entry[0].FileID for Entry in DisplayTocEntries]
        if globals.TocManager.ActivePatch != None:
            for Type in globals.TocManager.ActivePatch.TocTypes:
                if Type.TypeID not in AddedTypes:
                    AddedTypes.append(Type.TypeID)
                    DisplayTocTypes.append(Type)
            for Entry in globals.TocManager.ActivePatch.TocEntries:
                if Entry.FileID not in AddedEntries:
                    AddedEntries.append(Entry.FileID)
                    DisplayTocEntries.append([Entry, True])
    return [DisplayTocEntries, DisplayTocTypes]

def Patches_callback(scene, context):
    return [(Archive.Name, Archive.Name, "") for Archive in globals.TocManager.Patches]

def LoadedArchives_callback(scene, context):
    return [(Archive.Name, Archive.Name, "") for Archive in globals.TocManager.LoadedArchives]

class Hd2ToolPanelSettings(PropertyGroup):
    # Patches
    Patches       : EnumProperty(name="Patches", items=Patches_callback)
    PatchOnly     : BoolProperty(name="PatchOnly", description = "Show only patch entries", default = False)
    # Archive
    LoadedArchives : EnumProperty(name="LoadedArchives", items=LoadedArchives_callback)
    ShowMeshes     : BoolProperty(name="Mesh", description = "Show Meshes", default = True)
    ShowTextures   : BoolProperty(name="Tex", description = "Show Textures", default = True)
    ShowMaterials  : BoolProperty(name="Mat", description = "Show Materials", default = True)
    ShowAllElse    : BoolProperty(name="Other", description = "Show All Else", default = False)
    MenuExpanded   : BoolProperty(default = False)
    ContentsExpanded : BoolProperty(default = True)
    SearchField    : StringProperty(default = "")
    # Mesh Import
    MeshImportMenuExpanded : BoolProperty(default = False)
    ImportMaterials        : BoolProperty(name="ImportMaterials", description = "Import Materials", default = True)
    ImportLods             : BoolProperty(name="ImportLods", description = "Import Lods", default = False)
    ImportGroup0           : BoolProperty(name="ImportOnlyGroup0", description = "Only import the first vertex group, ignore others", default = True)
    ImportPhysics          : BoolProperty(name="ImportPhysics", description = "Import Physics Bodies", default = False)
    MakeCollections        : BoolProperty(name="MakeCollections", description = "Make New Collection When Importing Meshes", default = True)
    # Mesh Export
    MeshExportMenuExpanded : BoolProperty(default = False)
    Force2UVs              : BoolProperty(name="Force2UVs", description = "Force at least 2 uv sets (some materials require at least 2)", default = True)
    Force1Group            : BoolProperty(name="Force1Group", description = "Force mesh to only have 1 vertex group", default = True)
    AutoLods               : BoolProperty(name="AutoLods", description = "Automatically generate lods based on lod0 (duplicates lod0 for now)", default = True)

#UI Panel Class
class HellDivers2ToolsPanel(Panel):
    bl_label = "HellDivers2 Mesh Editing"
    bl_idname = "SF_PT_Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "HellDivers2 Tools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()

        # Draw Archive Display Settings
        row.prop(scene.Hd2ToolPanelSettings, "MenuExpanded",
            icon="DOWNARROW_HLT" if scene.Hd2ToolPanelSettings.MenuExpanded else "RIGHTARROW",
            icon_only=True, emboss=False, text="Archive Display Settings")
        if scene.Hd2ToolPanelSettings.MenuExpanded:
            row = layout.row(); row.separator(); box = row.box(); row = box.grid_flow(row_major=False, columns=4)
            row.prop(scene.Hd2ToolPanelSettings, "ShowMeshes")
            row.prop(scene.Hd2ToolPanelSettings, "ShowTextures")
            row.prop(scene.Hd2ToolPanelSettings, "ShowMaterials")
            row.prop(scene.Hd2ToolPanelSettings, "ShowAllElse")
        # Mesh Import Settings
        row = layout.row()
        row.prop(scene.Hd2ToolPanelSettings, "MeshImportMenuExpanded",
            icon="DOWNARROW_HLT" if scene.Hd2ToolPanelSettings.MeshImportMenuExpanded else "RIGHTARROW",
            icon_only=True, emboss=False, text="Mesh Import Settings")
        if scene.Hd2ToolPanelSettings.MeshImportMenuExpanded:
            row = layout.row(); row.separator(); box = row.box(); row = box.grid_flow(row_major=True, columns=3)
            row.prop(scene.Hd2ToolPanelSettings, "ImportMaterials")
            row.prop(scene.Hd2ToolPanelSettings, "ImportLods")
            row.prop(scene.Hd2ToolPanelSettings, "ImportGroup0")
            row.prop(scene.Hd2ToolPanelSettings, "MakeCollections")
            row.prop(scene.Hd2ToolPanelSettings, "ImportPhysics")
        # Mesh Export Settings
        row = layout.row()
        row.prop(scene.Hd2ToolPanelSettings, "MeshExportMenuExpanded",
            icon="DOWNARROW_HLT" if scene.Hd2ToolPanelSettings.MeshExportMenuExpanded else "RIGHTARROW",
            icon_only=True, emboss=False, text="Mesh Export Settings")
        if scene.Hd2ToolPanelSettings.MeshExportMenuExpanded:
            row = layout.row(); row.separator(); box = row.box(); row = box.grid_flow(row_major=True, columns=3)
            row.prop(scene.Hd2ToolPanelSettings, "Force2UVs")
            row.prop(scene.Hd2ToolPanelSettings, "Force1Group")
            row.prop(scene.Hd2ToolPanelSettings, "AutoLods")

        # Draw Patch Stuff
        row = layout.row(); row = layout.row(align=True)
        row.operator("helldiver2.archive_createpatch", icon= "COLLECTION_NEW", text="New Patch")
        row.operator("helldiver2.archive_export", icon= "DISC", text="Write Patch")
        row = layout.row()
        row.prop(scene.Hd2ToolPanelSettings, "Patches", text="Patches")
        if len(globals.TocManager.Patches) > 0:
            globals.TocManager.SetActivePatchByName(scene.Hd2ToolPanelSettings.Patches)
        row.operator("helldiver2.archive_import", icon= "IMPORT", text="").is_patch = True

        # Draw Archive Import/Export Buttons
        row = layout.row(); row = layout.row(align=True)
        row.operator("helldiver2.help", icon= "HELP", text="")
        row.operator("helldiver2.archive_spreadsheet", icon= "INFO", text="")
        row.operator("helldiver2.archive_import", icon= "IMPORT").is_patch = False
        row.operator("helldiver2.archive_unloadall", icon= "FILE_REFRESH", text="")
        row = layout.row()
        row.prop(scene.Hd2ToolPanelSettings, "LoadedArchives", text="Archives")
        row.operator("helldiver2.search_archives", icon= "VIEWZOOM", text="")
        row = layout.row()
        if len(globals.TocManager.LoadedArchives) > 0:
            globals.TocManager.SetActiveByName(scene.Hd2ToolPanelSettings.LoadedArchives)

        # Draw Search Bar
        row = layout.row(); row = layout.row()
        row.prop(scene.Hd2ToolPanelSettings, "SearchField", icon="VIEWZOOM", text="")
        row.prop(scene.Hd2ToolPanelSettings, "PatchOnly", text="")
        # Draw Paste Button
        row = layout.row(align=True)
        row.operator("helldiver2.archive_paste", icon="PASTEDOWN", text="Paste "+str(len(globals.TocManager.CopyBuffer)))
        row.operator("helldiver2.archive_clearclipboard", icon="TRASH", text="Clear Clipboard")
        row = layout.row()

        # Draw Archive Contents
        row.prop(scene.Hd2ToolPanelSettings, "ContentsExpanded",
            icon="DOWNARROW_HLT" if scene.Hd2ToolPanelSettings.ContentsExpanded else "RIGHTARROW",
            icon_only=True, emboss=True, text="Archive Contents")

        # Get Display Data
        DisplayData = GetDisplayData()
        DisplayTocEntries = DisplayData[0]
        DisplayTocTypes   = DisplayData[1]

        # Draw Contents
        NewFriendlyNames = []
        NewFriendlyIDs = []
        if scene.Hd2ToolPanelSettings.ContentsExpanded:
            if len(DisplayTocEntries) == 0: return
            DrawChain = []
            for Type in DisplayTocTypes:
                # check if there is any entry of this type that matches search field
                # TODO: should probably make a better way to do this
                bFound = False
                for EntryInfo in DisplayTocEntries:
                    Entry = EntryInfo[0]
                    if Entry.TypeID == Type.TypeID:
                        if str(Entry.FileID).find(scene.Hd2ToolPanelSettings.SearchField) != -1:
                            bFound = True
                if not bFound: continue

                # Get Type Icon
                type_icon = "FILE"
                if Type.TypeID == globals.MeshID:
                    type_icon = "FILE_3D"
                    if not scene.Hd2ToolPanelSettings.ShowMeshes: continue
                elif Type.TypeID == globals.TexID:
                    type_icon = "FILE_IMAGE"
                    if not scene.Hd2ToolPanelSettings.ShowTextures: continue
                elif Type.TypeID == globals.MaterialID:
                    type_icon = "MATERIAL"
                    if not scene.Hd2ToolPanelSettings.ShowMaterials: continue
                elif not scene.Hd2ToolPanelSettings.ShowAllElse: continue

                # Draw Type Header
                box = layout.box(); row = box.row()
                typeName = GetTypeNameFromID(Type.TypeID)
                row.label(text=f"{typeName}: {Type.TypeID}", icon=type_icon)
                row.operator("helldiver2.select_type", icon="RESTRICT_SELECT_OFF", text="").object_typeid = str(Type.TypeID)
                if typeName == "material": row.operator("helldiver2.material_add", icon="FILE_NEW", text="")

                # Draw Archive Entries
                col = box.column(align=True)
                for EntryInfo in DisplayTocEntries:
                    Entry = EntryInfo[0]
                    PatchOnly = EntryInfo[1]
                    # Exclude entries that should not be drawn
                    if Entry.TypeID != Type.TypeID: continue
                    if str(Entry.FileID).find(scene.Hd2ToolPanelSettings.SearchField) == -1: continue
                    # Deal with friendly names
                    if len(globals.TocManager.SavedFriendlyNameIDs) > len(DrawChain) and globals.TocManager.SavedFriendlyNameIDs[len(DrawChain)] == Entry.FileID:
                        FriendlyName = globals.TocManager.SavedFriendlyNames[len(DrawChain)]
                    else:
                        try:
                            FriendlyName = globals.TocManager.SavedFriendlyNames[globals.TocManager.SavedFriendlyNameIDs.index(Entry.FileID)]
                            NewFriendlyNames.append(FriendlyName)
                            NewFriendlyIDs.append(Entry.FileID)
                        except:
                            FriendlyName = GetFriendlyNameFromID(Entry.FileID)
                            NewFriendlyNames.append(FriendlyName)
                            NewFriendlyIDs.append(Entry.FileID)


                    # Draw Entry
                    PatchEntry = globals.TocManager.GetEntry(int(Entry.FileID), int(Entry.TypeID))
                    PatchEntry.DEV_DrawIndex = len(DrawChain)

                    row = col.row(align=True); row.separator()
                    props = row.operator("helldiver2.archive_entry", icon=type_icon, text=FriendlyName, emboss=PatchEntry.IsSelected, depress=PatchEntry.IsSelected)
                    props.object_id     = str(Entry.FileID)
                    props.object_typeid = str(Entry.TypeID)
                    # Draw Buttons
                    DrawEntryButtonsSimple(box, row, PatchEntry, PatchOnly)
                    # Update Draw Chain
                    DrawChain.append(PatchEntry)
            globals.TocManager.DrawChain = DrawChain
        globals.TocManager.SavedFriendlyNames = NewFriendlyNames
        globals.TocManager.SavedFriendlyNameIDs = NewFriendlyIDs
