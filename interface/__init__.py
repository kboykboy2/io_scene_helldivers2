from .. import globals
from . import operators, panels

classes_archive = (
    operators.LoadArchiveOperator,
    operators.LoadArchivesOperator,
    operators.UnloadArchivesOperator,
    operators.ArchiveEntryOperator,
    operators.SearchArchivesOperator,
    operators.PatchArchiveOperator,
    operators.CreatePatchFromActiveOperator,
    operators.AddEntryToPatchOperator,
    operators.RemoveEntryFromPatchOperator,
    operators.UndoArchiveEntryModOperator,
    operators.CopyArchiveEntryOperator,
    operators.PasteArchiveEntryOperator,
    operators.ClearClipboardOperator,
    operators.DumpArchiveObjectOperator
)

classes_mesh = (
    operators.ImportStingrayMeshOperator,
    operators.SaveStingrayMeshOperator,
    operators.BatchSaveStingrayMeshOperator
)

classes_material = (
    operators.ImportMaterialOperator,
    operators.SaveMaterialOperator,
    operators.AddMaterialOperator,
    operators.ShowMaterialEditorOperator,
    operators.SetMaterialTexture
)

classes_texture = (
    operators.ImportTextureOperator,
    operators.ExportTextureOperator,
    operators.SaveTextureFromBlendImageOperator,
    operators.SaveTextureFromDDsOperator,
    operators.BatchExportTextureOperator
)

classes_interface = (
    panels.Hd2ToolPanelSettings,
    panels.HellDivers2ToolsPanel,
    operators.HelpOperator,
    operators.ArchiveSpreadsheetOperator,
    operators.CopyTextOperator,
    operators.SelectAllOfTypeOperator,
    operators.RenamePatchEntryOperator,
    operators.DuplicateEntryOperator,
    operators.SetEntryFriendlyNameOperator
)
