import os, subprocess, webbrowser
import random as r

import bpy
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import BoolProperty, IntProperty, StringProperty

from ..classes_and_defs.memoryStream import MemoryStream
from ..classes_and_defs.stingray.texture import BlendImageToStingrayTexture
from ..classes_and_defs.stingray.toc import TocEntry
from ..utils.hash import AddFriendlyName, GetTypeNameFromID, Hash64
from .. import globals

def EntriesFromStrings(file_id_string, type_id_string):
    FileIDs = file_id_string.split(",")
    TypeIDs = type_id_string.split(",")
    Entries = []
    for n in range(len(FileIDs)):
        if FileIDs[n] != "":
            Entries.append(globals.TocManager.GetEntry(int(FileIDs[n]), int(TypeIDs[n])))
    return Entries

def EntriesFromString(file_id_string, TypeID):
    FileIDs = file_id_string.split(",")
    Entries = []
    for n in range(len(FileIDs)):
        if FileIDs[n] != "":
            Entries.append(globals.TocManager.GetEntry(int(FileIDs[n]), int(TypeID)))
    return Entries

def IDsFromString(file_id_string):
    FileIDs = file_id_string.split(",")
    Entries = []
    for n in range(len(FileIDs)):
        if FileIDs[n] != "":
            Entries.append(int(FileIDs[n]))
    return Entries

# load archive button
class LoadArchiveOperator(Operator, ImportHelper):
    bl_label = "Load Archive"
    bl_idname = "helldiver2.archive_import"
    filter_glob: StringProperty(
    default="*",
    options={"HIDDEN"}
    )
    is_patch: BoolProperty(name="is_patch", default=False)
    def execute(self, context):
        globals.TocManager.LoadArchive(self.filepath, True, self.is_patch)
        return{"FINISHED"}

# load archive button
class LoadArchivesOperator(Operator):
    bl_label = "Load Archives"
    bl_idname = "helldiver2.archives_import"

    paths_str: StringProperty(name="paths_str")
    def execute(self, context):
        paths = self.paths_str.split(",")
        for path in paths:
            if path != "" and os.path.exists(path):
                globals.TocManager.LoadArchive(path)
        self.paths = []
        return{"FINISHED"}

# patch archive button
class PatchArchiveOperator(Operator):
    bl_label = "Patch Archive"
    bl_idname = "helldiver2.archive_export"

    def execute(self, context):
        globals.TocManager.PatchActiveArchive()
        return{"FINISHED"}

# dump archive entry button
class DumpArchiveObjectOperator(Operator, ExportHelper):
    bl_label = "Dump Archive Object"
    bl_idname = "helldiver2.archive_object_dump"
    filename_ext = ".dump"

    directory: StringProperty(name="Outdir Path",description="dump output dir")
    filter_folder: BoolProperty(default=True,options={"HIDDEN"})

    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Entries = EntriesFromStrings(self.object_id, self.object_typeid)
        for Entry in Entries:
            if Entry != None:
                data = Entry.GetData()
                FileName = str(Entry.FileID)+"."+GetTypeNameFromID(Entry.TypeID)
                with open(self.directory + FileName, "w+b") as f:
                    f.write(data[0])
                if data[1] != b"":
                    with open(self.directory + FileName+".gpu", "w+b") as f:
                        f.write(data[1])
                if data[2] != b"":
                    with open(self.directory + FileName+".stream", "w+b") as f:
                        f.write(data[2])
        return{"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

# undo modified archive entry
class UndoArchiveEntryModOperator(Operator):
    bl_label = "Remove Modifications"
    bl_idname = "helldiver2.archive_undo_mod"

    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Entries = EntriesFromStrings(self.object_id, self.object_typeid)
        for Entry in Entries:
            if Entry != None:
                Entry.UndoModifiedData()
        return{"FINISHED"}

# copy entry
class CopyArchiveEntryOperator(Operator):
    bl_label = "Copy Entry"
    bl_idname = "helldiver2.archive_copy"

    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Entries = EntriesFromStrings(self.object_id, self.object_typeid)
        globals.TocManager.Copy(Entries)
        return{"FINISHED"}

# paste entry
class PasteArchiveEntryOperator(Operator):
    bl_label = "Paste Entry"
    bl_idname = "helldiver2.archive_paste"

    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        globals.TocManager.Paste()
        return{"FINISHED"}

# clear clipboard
class ClearClipboardOperator(Operator):
    bl_label = "Clear Clipboard"
    bl_idname = "helldiver2.archive_clearclipboard"

    def execute(self, context):
        globals.TocManager.ClearClipboard()
        return{"FINISHED"}

# unload all archives
class UnloadArchivesOperator(Operator):
    bl_label = "Unload Archives"
    bl_idname = "helldiver2.archive_unloadall"

    def execute(self, context):
        globals.TocManager.UnloadArchives()
        return{"FINISHED"}

# create patch
class CreatePatchFromActiveOperator(Operator):
    bl_label = "Create Patch"
    bl_idname = "helldiver2.archive_createpatch"

    def execute(self, context):
        globals.TocManager.CreatePatchFromActive()
        return{"FINISHED"}

# add entry to patch
class AddEntryToPatchOperator(Operator):
    bl_label = "Add Entry To Patch"
    bl_idname = "helldiver2.archive_addtopatch"

    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Entries = EntriesFromStrings(self.object_id, self.object_typeid)
        for Entry in Entries:
            globals.TocManager.AddEntryToPatch(Entry.FileID, Entry.TypeID)
        return{"FINISHED"}

# remove entry from patch
class RemoveEntryFromPatchOperator(Operator):
    bl_label = "Remove Entry From Patch"
    bl_idname = "helldiver2.archive_removefrompatch"

    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Entries = EntriesFromStrings(self.object_id, self.object_typeid)
        for Entry in Entries:
            globals.TocManager.RemoveEntryFromPatch(Entry.FileID, Entry.TypeID)
        return{"FINISHED"}

# rename entry in patch
class RenamePatchEntryOperator(Operator):
    bl_label = "Rename Entry"
    bl_idname = "helldiver2.archive_entryrename"

    NewFileID : StringProperty(name="NewFileID", default="")
    def draw(self, context):
        layout = self.layout; row = layout.row()
        row.prop(self, "NewFileID", icon="COPY_ID")

    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Entry = globals.TocManager.GetPatchEntry_B(int(self.object_id), int(self.object_typeid))
        if Entry == None:
            raise Exception("Entry does not exist in patch (cannot rename non patch entries)")
        if Entry != None and self.NewFileID != "":
            Entry.FileID = int(self.NewFileID)
        return{"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

# duplicate entry in patch
class DuplicateEntryOperator(Operator):
    bl_label = "Duplicate Entry"
    bl_idname = "helldiver2.archive_duplicate"

    NewFileID : StringProperty(name="NewFileID", default="")
    def draw(self, context):
        layout = self.layout; row = layout.row()
        row.prop(self, "NewFileID", icon="COPY_ID")

    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        globals.TocManager.DuplicateEntry(int(self.object_id), int(self.object_typeid), int(self.NewFileID))
        return{"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

# rename entry in patch
class SetEntryFriendlyNameOperator(Operator):
    bl_label = "Set Friendly Name"
    bl_idname = "helldiver2.archive_setfriendlyname"

    NewFriendlyName : StringProperty(name="NewFriendlyName", default="")
    def draw(self, context):
        layout = self.layout; row = layout.row()
        row.prop(self, "NewFriendlyName", icon="COPY_ID")
        row = layout.row()
        if Hash64(str(self.NewFriendlyName)) == int(self.object_id):
            row.label(text="Hash is correct")
        else:
            row.label(text="Hash is incorrect")
        row.label(text=str(Hash64(str(self.NewFriendlyName))))

    object_id: StringProperty()
    def execute(self, context):
        AddFriendlyName(int(self.object_id), str(self.NewFriendlyName))
        return{"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class ImportMaterialOperator(Operator):
    bl_label = "Import Material"
    bl_idname = "helldiver2.material_import"

    object_id: StringProperty()
    def execute(self, context):
        EntriesIDs = IDsFromString(self.object_id)
        for EntryID in EntriesIDs:
            globals.TocManager.Load(int(EntryID), globals.MaterialID)
        return{"FINISHED"}

class AddMaterialOperator(Operator):
    bl_label = "Add Material"
    bl_idname = "helldiver2.material_add"

    def execute(self, context):
        Entry = TocEntry()
        Entry.FileID = r.randint(1, 0xffffffffffffffff)
        Entry.TypeID = globals.MaterialID
        Entry.IsCreated = True
        with open(globals.DefaultMaterialPath, "r+b") as f:
            data = f.read()
        Entry.TocData_OLD   = data
        Entry.TocData       = data

        globals.TocManager.AddNewEntryToPatch(Entry)
        return{"FINISHED"}

class SaveMaterialOperator(Operator):
    bl_label = "Save Material"
    bl_idname = "helldiver2.material_save"

    object_id: StringProperty()
    def execute(self, context):
        EntriesIDs = IDsFromString(self.object_id)
        for EntryID in EntriesIDs:
            globals.TocManager.Save(int(EntryID), globals.MaterialID)
        return{"FINISHED"}

class ShowMaterialEditorOperator(Operator):
    bl_label = "Show Material Editor"
    bl_idname = "helldiver2.material_showeditor"

    object_id: StringProperty()
    def execute(self, context):
        Entry = globals.TocManager.GetEntry(int(self.object_id), globals.MaterialID)
        if Entry != None:
            if not Entry.IsLoaded: Entry.Load(False, False)
            mat = Entry.LoadedData
            if mat.DEV_ShowEditor:
                print("MakeFalse")
                mat.DEV_ShowEditor = False
            else:
                print("MakeTrue")
                mat.DEV_ShowEditor = True
        return{"FINISHED"}

class SetMaterialTexture(Operator, ImportHelper):
    bl_label = "Set Material Texture"
    bl_idname = "helldiver2.material_settex"

    object_id: StringProperty()
    tex_idx: IntProperty()
    def execute(self, context):
        if self.filepath[-3:] != "dds":
            raise Exception("file must be dds")

        Entry = globals.TocManager.GetEntry(int(self.object_id), globals.MaterialID)
        if Entry != None:
            if Entry.IsLoaded:
                Entry.LoadedData.DEV_DDSPaths[self.tex_idx] = self.filepath
        return{"FINISHED"}

# import texture from archive button
class ImportTextureOperator(Operator):
    bl_label = "Import Texture"
    bl_idname = "helldiver2.texture_import"

    object_id: StringProperty()
    def execute(self, context):
        EntriesIDs = IDsFromString(self.object_id)
        for EntryID in EntriesIDs:
            globals.TocManager.Load(int(EntryID), globals.TexID)
        return{"FINISHED"}

# batch export texture to file
class BatchExportTextureOperator(Operator):
    bl_label = "Export Textures"
    bl_idname = "helldiver2.texture_batchexport"
    filename_ext = ".dds"

    directory: StringProperty(name="Outdir Path",description="dds output dir")
    filter_folder: BoolProperty(default=True,options={"HIDDEN"})

    object_id: StringProperty()
    def execute(self, context):
        EntriesIDs = IDsFromString(self.object_id)
        for EntryID in EntriesIDs:
            Entry = globals.TocManager.GetEntry(EntryID, globals.TexID)
            if Entry != None:
                data = Entry.Load(False, False)
                with open(self.directory + str(Entry.FileID)+".dds", "w+b") as f:
                    f.write(Entry.LoadedData.ToDDs())
        return{"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

# export texture to file
class ExportTextureOperator(Operator, ExportHelper):
    bl_label = "Export Texture"
    bl_idname = "helldiver2.texture_export"
    filename_ext = ".dds"

    object_id: StringProperty()
    def execute(self, context):
        Entry = globals.TocManager.GetEntry(int(self.object_id), globals.TexID)
        if Entry != None:
            data = Entry.Load(False, False)
            with open(self.filepath, "w+b") as f:
                f.write(Entry.LoadedData.ToDDs())
        return{"FINISHED"}

# save texture from blender to archive button
class SaveTextureFromBlendImageOperator(Operator):
    bl_label = "Save Texture"
    bl_idname = "helldiver2.texture_saveblendimage"

    object_id: StringProperty()
    def execute(self, context):
        Entries = EntriesFromString(self.object_id, globals.TexID)
        for Entry in Entries:
            if Entry != None:
                if not Entry.IsLoaded: Entry.Load()
                # BlendImageToStingrayTexture(bpy.data.images[str(self.object_id)], Entry.LoadedData)
                try: BlendImageToStingrayTexture(bpy.data.images[str(self.object_id)], Entry.LoadedData)
                except: print("Saving Texture, but no blend texture was found, using original"); pass
                # TODO: allow the user to choose an image, instead of looking for one of the same name
            globals.TocManager.Save(Entry.FileID, globals.TexID)
        return{"FINISHED"}

# import texture from archive button
class SaveTextureFromDDsOperator(Operator, ImportHelper):
    bl_label = "Save Texture"
    bl_idname = "helldiver2.texture_savefromdds"

    object_id: StringProperty()
    def execute(self, context):
        Entry = globals.TocManager.GetEntry(int(self.object_id), globals.TexID)
        if Entry != None:
            if len(self.filepath) > 1:
                # get texture data
                Entry.Load()
                StingrayTex = Entry.LoadedData
                with open(self.filepath, "r+b") as f:
                    StingrayTex.FromDDs(f.read())
                Toc = MemoryStream(IOMode="write")
                Gpu = MemoryStream(IOMode="write")
                Stream = MemoryStream(IOMode="write")
                StingrayTex.Serialize(Toc, Gpu, Stream)
                # add texture to entry
                Entry.SetData(Toc.Data, Gpu.Data, Stream.Data, False)

                globals.TocManager.Save(int(self.object_id), globals.TexID)
        return{"FINISHED"}

# import mesh from archive button
class ImportStingrayMeshOperator(Operator):
    bl_label = "Import Archive Mesh"
    bl_idname = "helldiver2.archive_mesh_import"

    object_id: StringProperty()
    def execute(self, context):
        EntriesIDs = IDsFromString(self.object_id)
        Errors = []
        for EntryID in EntriesIDs:
            if len(EntriesIDs) == 1:
                globals.TocManager.Load(EntryID, globals.MeshID)
            else:
                try:
                    globals.TocManager.Load(EntryID, globals.MeshID)
                except Exception as error:
                    Errors.append([EntryID, error])

        if len(Errors) > 0:
            print("\nThese errors occurred while attempting to load meshes...")
            idx = 0
            for error in Errors:
                print(f"  Error {idx}: for mesh {error[0]}")
                print(f"    {error[1]}\n")
                idx += 1
            raise Exception("One or more meshes failed to load")
        return{"FINISHED"}

# save mesh to archive button
class SaveStingrayMeshOperator(Operator):
    bl_label  = "Save Mesh"
    bl_idname = "helldiver2.archive_mesh_save"

    object_id: StringProperty()
    def execute(self, context):
        globals.TocManager.Save(int(self.object_id), globals.MeshID)
        return{"FINISHED"}

# batch save mesh to archive button
class BatchSaveStingrayMeshOperator(Operator):
    bl_label  = "Save Meshes"
    bl_idname = "helldiver2.archive_mesh_batchsave"

    def execute(self, context):
        objects = bpy.context.selected_objects
        bpy.ops.object.select_all(action="DESELECT")
        IDs = []
        for object in objects:
            try:
                ID = object["Z_ObjectID"]
                if ID not in IDs:
                    IDs.append(ID)
            except:
                pass
        for ID in IDs:
            for object in objects:
                try:
                    if object["Z_ObjectID"] == ID:
                       object.select_set(True)
                except: pass

            globals.TocManager.Save(int(ID), globals.MeshID)
        return{"FINISHED"}

class SearchArchivesOperator(Operator):
    bl_label = "Search All Archives"
    bl_idname = "helldiver2.search_archives"

    SearchField : StringProperty(name="SearchField", default="")
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "SearchField", icon="VIEWZOOM")
        # Update displayed archives
        if self.PrevSearch != self.SearchField:
            self.PrevSearch = self.SearchField

            self.ArchivesToDisplay = []
            friendlysearches = []
            for hash_info in globals.NameHashes:
                Found = True
                for search in self.SearchField.split(" "):
                    if not (hash_info[1].find(search) != -1 and str(hash_info[0]) not in friendlysearches):
                        Found = False
                if Found:
                    friendlysearches.append(str(hash_info[0]))

            for Archive in globals.TocManager.SearchArchives:
                NumMatches = 0
                for Entry in Archive.TocEntries:
                    Found = True
                    for search in self.SearchField.split(" "):
                        if not (str(Entry.FileID).find(search) != -1):
                            Found = False
                    if Found:
                        NumMatches += 1

                    if not Found:
                        for friendlysearch in friendlysearches:
                            if str(Entry.FileID).find(friendlysearch) != -1:
                                NumMatches += 1
                if NumMatches > 0 and [Archive, Archive.Name+": "+str(NumMatches)] not in self.ArchivesToDisplay:
                    self.ArchivesToDisplay.append([Archive, Archive.Name+": "+str(NumMatches)])

        # Draw Open All Archives Button
        if len(self.ArchivesToDisplay) > 50:
            row = layout.row()
            row.label(text="Too many archives to load all")
        else:
            paths_str = ""
            for Archive in self.ArchivesToDisplay:
                paths_str += Archive[0].Path + ","

            row = layout.row()
            row.operator("helldiver2.archives_import", icon= "FILE_NEW").paths_str = paths_str
        # Draw Display Archives
        for Archive in self.ArchivesToDisplay:
            row = layout.row()
            row.label(text=Archive[1], icon="FILE_ARCHIVE")
            row.operator("helldiver2.archives_import", icon= "FILE_NEW", text="").paths_str = Archive[0].Path
    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        self.PrevSearch = "NONE"
        self.ArchivesToDisplay = []

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

# Copy Text
class SelectAllOfTypeOperator(Operator):
    bl_label  = "Select All Of Type"
    bl_idname = "helldiver2.select_type"

    object_typeid: StringProperty()
    def execute(self, context):
        Entries = GetDisplayData()[0]
        for EntryInfo in Entries:
            Entry = EntryInfo[0]
            if Entry.TypeID == int(self.object_typeid):
                DisplayEntry = globals.TocManager.GetEntry(Entry.FileID, Entry.TypeID)
                if DisplayEntry.IsSelected:
                    # globals.TocManager.DeselectEntries([Entry])
                    pass
                else:
                    globals.TocManager.SelectEntries([Entry], True)
        return{"FINISHED"}

# Copy Text
class CopyTextOperator(Operator):
    bl_label  = "Copy ID"
    bl_idname = "helldiver2.copytest"

    text: StringProperty()
    def execute(self, context):
        cmd="echo "+str(self.text).strip()+"|clip"
        subprocess.check_call(cmd, shell=True)
        return{"FINISHED"}

# Open documentation
class HelpOperator(Operator):
    bl_label  = "Help"
    bl_idname = "helldiver2.help"

    def execute(self, context):
        url = "https://docs.google.com/document/d/1SF7iEekmxoDdf0EsJu1ww9u2Cr8vzHyn2ycZS7JlWl0/edit#heading=h.gv4shgb4on0i"
        webbrowser.open(url, new=0, autoraise=True)
        return{"FINISHED"}

# Open Archive Spreadsheet
class ArchiveSpreadsheetOperator(Operator):
    bl_label  = "Archive Spreadsheet"
    bl_idname = "helldiver2.archive_spreadsheet"

    def execute(self, context):
        url = "https://docs.google.com/spreadsheets/d/1oQys_OI5DWou4GeRE3mW56j7BIi4M7KftBIPAl1ULFw"
        webbrowser.open(url, new=0, autoraise=True)
        return{"FINISHED"}

class ArchiveEntryOperator(Operator):
    bl_label  = "Archive Entry"
    bl_idname = "helldiver2.archive_entry"

    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        return{"FINISHED"}

    def invoke(self, context, event):
        Entry = globals.TocManager.GetEntry(int(self.object_id), int(self.object_typeid))
        if event.ctrl:
            if Entry.IsSelected:
                globals.TocManager.DeselectEntries([Entry])
            else:
                globals.TocManager.SelectEntries([Entry], True)
            return {"FINISHED"}
        if event.shift:
            if globals.TocManager.LastSelected != None:
                LastSelected = globals.TocManager.LastSelected
                StartIndex   = LastSelected.DEV_DrawIndex
                EndIndex     = Entry.DEV_DrawIndex
                globals.TocManager.DeselectAll()
                globals.TocManager.LastSelected = LastSelected
                if StartIndex > EndIndex:
                    globals.TocManager.SelectEntries(globals.TocManager.DrawChain[EndIndex:StartIndex+1], True)
                else:
                    globals.TocManager.SelectEntries(globals.TocManager.DrawChain[StartIndex:EndIndex+1], True)
            else:
                globals.TocManager.SelectEntries([Entry], True)
            return {"FINISHED"}

        globals.TocManager.SelectEntries([Entry])
        return {"FINISHED"}
