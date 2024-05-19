from . import StingrayMatrix4x4
from ..memoryStream import MemoryStream

class StingrayBones:
    def __init__(self):
        self.NumNames = self.NumUnk = 0
        self.UnkArray1 = []; UnkArray2 = []; UnkArray3 = []; self.Names = []
    def Serialize(self, f):
        self.NumNames = f.uint32(self.NumNames)
        self.NumUnk   = f.uint32(self.NumUnk)
        if f.IsReading():
            self.UnkArray1 = [0 for n in range(self.NumUnk)]
            self.UnkArray2 = [0 for n in range(self.NumNames)]
            self.UnkArray3 = [0 for n in range(self.NumUnk)]
        self.UnkArray1 = [f.uint32(value) for value in self.UnkArray1]
        self.UnkArray2 = [f.uint32(value) for value in self.UnkArray2]
        self.UnkArray3 = [f.uint32(value) for value in self.UnkArray3]
        if f.IsReading():
            Data = f.read().split(b"\x00")
            self.Names = [dat.decode() for dat in Data]
        else:
            Data = b""
            for string in self.Names:
                Data += string.encode() + b"\x00"
            f.write(Data)
        return self

class BoneInfo:
    def __init__(self):
        self.NumBones = self.unk1 = self.RealIndicesOffset = self.FakeIndicesOffset = self.NumFakeIndices = self.FakeIndicesUnk = 0
        self.Bones = self.RealIndices = self.FakeIndices = []
        self.DEV_RawData = bytearray()
    def Serialize(self, f, end=None):
        if f.IsReading():
            self.DEV_RawData = bytearray(end-f.tell())
            start = f.tell()
            self.Serialize_REAL(f)
            f.seek(start)
        self.DEV_RawData = f.bytes(self.DEV_RawData)
        return self

    def Serialize_REAL(self, f): # still need to figure out whats up with the unknown bit
        RelPosition = f.tell()

        self.NumBones       = f.uint32(self.NumBones)
        self.unk1           = f.uint32(self.unk1)
        self.RealIndicesOffset = f.uint32(self.RealIndicesOffset)
        self.FakeIndicesOffset = f.uint32(self.FakeIndicesOffset)
        # get bone data
        if f.IsReading():
            self.Bones = [StingrayMatrix4x4() for n in range(self.NumBones)]
            self.RealIndices = [0 for n in range(self.NumBones)]
            self.FakeIndices = [0 for n in range(self.NumBones)]
        self.Bones = [bone.Serialize(f) for bone in self.Bones]
        # get real indices
        if f.IsReading(): f.seek(RelPosition+self.RealIndicesOffset)
        else            : self.RealIndicesOffset = f.tell()-RelPosition
        self.RealIndices = [f.uint32(index) for index in self.RealIndices]
        # get unknown
        return self

        # get fake indices
        if f.IsReading(): f.seek(RelPosition+self.FakeIndicesOffset)
        else            : self.FakeIndicesOffset = f.tell()-RelPosition
        self.NumFakeIndices = f.uint32(self.NumFakeIndices)
        self.FakeIndicesUnk = f.uint64(self.FakeIndices[0])
        self.FakeIndices = [f.uint32(index) for index in self.FakeIndices]
        return self
    def GetRealIndex(self, bone_index):
        FakeIndex = self.FakeIndices.index(bone_index)
        return self.RealIndices[FakeIndex]

def LoadStingrayBones(ID, TocData, GpuData, StreamData, Reload, MakeBlendObject):
    StingrayBonesData = StingrayBones()
    StingrayBonesData.Serialize(MemoryStream(TocData))
    return StingrayBonesData
