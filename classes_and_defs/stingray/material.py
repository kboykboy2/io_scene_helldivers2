import copy #, zlib
import random as r

import bpy

from .texture import StingrayTexture
from ..memoryStream import MemoryStream
from ... import globals

class StingrayMaterial:
    def __init__(self):
        self.undat1 = self.undat3 = self.undat4 = self.undat5 = self.RemainingData = bytearray()
        self.EndOffset = self.undat2 = self.UnkID = self.NumTextures = self.NumUnk = 0
        self.TexUnks = []
        self.TexIDs  = []

        self.DEV_ShowEditor = False
        self.DEV_DDSPaths = []
    def Serialize(self, f):
        self.undat1      = f.bytes(self.undat1, 12)
        self.EndOffset   = f.uint32(self.EndOffset)
        self.undat2      = f.uint64(self.undat2)
        self.UnkID       = f.uint64(self.UnkID) # could be shader id?
        self.undat3      = f.bytes(self.undat3, 32)
        self.NumTextures = f.uint32(self.NumTextures)
        self.undat4      = f.bytes(self.undat4, 36)
        self.NumUnk      = f.uint32(self.NumUnk)
        self.undat5      = f.bytes(self.undat5, 28)
        if f.IsReading():
            self.TexUnks = [0 for n in range(self.NumTextures)]
            self.TexIDs = [0 for n in range(self.NumTextures)]
        self.TexUnks = [f.uint32(TexUnk) for TexUnk in self.TexUnks]
        self.TexIDs  = [f.uint64(TexID) for TexID in self.TexIDs]

        if f.IsReading():self.RemainingData = f.bytes(self.RemainingData, len(f.Data) - f.tell())
        if f.IsWriting():self.RemainingData = f.bytes(self.RemainingData)
        self.EditorUpdate()

    def EditorUpdate(self):
        self.DEV_DDSPaths = [None for n in range(len(self.TexIDs))]

class RawMaterialClass:
    DefaultMaterialName    = "StingrayDefaultMaterial"
    DefaultMaterialShortID = 155175220
    def __init__(self):
        self.MatID      = self.DefaultMaterialName
        self.ShortID    = self.DefaultMaterialShortID
        self.StartIndex = 0
        self.NumIndices = 0
        self.DEV_BoneInfoOverride = None
    def IDFromName(self, name):
        if name.find(self.DefaultMaterialName) != -1:
            self.MatID   = self.DefaultMaterialName
            self.ShortID = self.DefaultMaterialShortID
        else:
            try:
                self.MatID   = int(name)
                # self.ShortID = zlib.crc32(name.encode())
                self.ShortID = r.randint(1, 0xffffffff)
            except:
                raise Exception("Material name must be a number")

def LoadStingrayMaterial(ID, TocData, GpuData, StreamData, Reload, MakeBlendObject):
    exists = True
    force_reload = False
    try:
        mat = bpy.data.materials[str(ID)]
        if not mat.use_nodes: force_reload = True
    except: exists = False
    f = MemoryStream(TocData)
    Material = StingrayMaterial()
    Material.Serialize(f)
    if MakeBlendObject and not (exists and not Reload): AddMaterialToBlend(ID, Material)
    elif force_reload: AddMaterialToBlend(ID, Material, True)
    return Material

def SaveStingrayMaterial(ID, TocData, GpuData, StreamData, LoadedData):
    mat = LoadedData
    for TexIdx in range(len(mat.TexIDs)):
        if mat.DEV_DDSPaths[TexIdx] != None:
            # get texture data
            StingrayTex = StingrayTexture()
            with open(mat.DEV_DDSPaths[TexIdx], 'r+b') as f:
                StingrayTex.FromDDs(f.read())
            Toc = MemoryStream(IOMode="write")
            Gpu = MemoryStream(IOMode="write")
            Stream = MemoryStream(IOMode="write")
            StingrayTex.Serialize(Toc, Gpu, Stream)
            # add texture entry to archive
            from .toc import TocEntry # put this here to avoid circular dependency. should probably figure out how to do things not shit so circular dependencies don't happen in the first place
            Entry = TocEntry()
            Entry.FileID = r.randint(1, 0xffffffffffffffff)
            Entry.TypeID = globals.TexID
            Entry.IsCreated = True
            Entry.SetData(Toc.Data, Gpu.Data, Stream.Data, False)
            globals.TocManager.AddNewEntryToPatch(Entry)
            mat.TexIDs[TexIdx] = Entry.FileID
        else:
            globals.TocManager.Load(int(mat.TexIDs[TexIdx]), globals.TexID, False, True)
            Entry = globals.TocManager.GetEntry(int(mat.TexIDs[TexIdx]), globals.TexID, True)
            if Entry != None:
                Entry = copy.deepcopy(Entry)
                Entry.FileID = r.randint(1, 0xffffffffffffffff)
                Entry.IsCreated = True
                globals.TocManager.AddNewEntryToPatch(Entry)
                mat.TexIDs[TexIdx] = Entry.FileID
    f = MemoryStream(IOMode="write")
    LoadedData.Serialize(f)
    return [f.Data, b"", b""]

def AddMaterialToBlend(ID, StringrayMat, EmptyMatExists=False):
    if EmptyMatExists:
        mat = bpy.data.materials[str(ID)]
    else:
        mat = bpy.data.materials.new(str(ID)); mat.name = str(ID)

    mat.diffuse_color = (r.random(), r.random(), r.random(), 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    idx = 0
    for TextureID in StringrayMat.TexIDs:
        # Create Node
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texImage.location = (-450, 850 - 300*idx)

        # Load Texture
        try:    bpy.data.images[str(TextureID)]
        except: globals.TocManager.Load(TextureID, globals.TexID, False, True)
        # Apply Texture
        try: texImage.image = bpy.data.images[str(TextureID)]
        except:
            print("Failed to load texture: "+str(TextureID))
            pass
        idx +=1

def AddMaterialToBlend_EMPTY(ID):
    try:
        bpy.data.materials[str(ID)]
    except:
        mat = bpy.data.materials.new(str(ID)); mat.name = str(ID)
        mat.diffuse_color = (r.random(), r.random(), r.random(), 1)
