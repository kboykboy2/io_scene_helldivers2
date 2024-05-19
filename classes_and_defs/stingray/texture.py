import os, subprocess, tempfile, time

import bpy

from ..memoryStream import MemoryStream
from ... import globals

def DXGI_FORMAT(format):
    Dict = {0: "UNKNOWN", 1: "R32G32B32A32_TYPELESS", 2: "R32G32B32A32_FLOAT", 3: "R32G32B32A32_UINT", 4: "R32G32B32A32_SINT", 5: "R32G32B32_TYPELESS", 6: "R32G32B32_FLOAT", 7: "R32G32B32_UINT", 8: "R32G32B32_SINT", 9: "R16G16B16A16_TYPELESS", 10: "R16G16B16A16_FLOAT", 11: "R16G16B16A16_UNORM", 12: "R16G16B16A16_UINT", 13: "R16G16B16A16_SNORM", 14: "R16G16B16A16_SINT", 15: "R32G32_TYPELESS", 16: "R32G32_FLOAT", 17: "R32G32_UINT", 18: "R32G32_SINT", 19: "R32G8X24_TYPELESS", 20: "D32_FLOAT_S8X24_UINT", 21: "R32_FLOAT_X8X24_TYPELESS", 22: "X32_TYPELESS_G8X24_UINT", 23: "R10G10B10A2_TYPELESS", 24: "R10G10B10A2_UNORM", 25: "R10G10B10A2_UINT", 26: "R11G11B10_FLOAT", 27: "R8G8B8A8_TYPELESS", 28: "R8G8B8A8_UNORM", 29: "R8G8B8A8_UNORM_SRGB", 30: "R8G8B8A8_UINT", 31: "R8G8B8A8_SNORM", 32: "R8G8B8A8_SINT", 33: "R16G16_TYPELESS", 34: "R16G16_FLOAT", 35: "R16G16_UNORM", 36: "R16G16_UINT", 37: "R16G16_SNORM", 38: "R16G16_SINT", 39: "R32_TYPELESS", 40: "D32_FLOAT", 41: "R32_FLOAT", 42: "R32_UINT", 43: "R32_SINT", 44: "R24G8_TYPELESS", 45: "D24_UNORM_S8_UINT", 46: "R24_UNORM_X8_TYPELESS", 47: "X24_TYPELESS_G8_UINT", 48: "R8G8_TYPELESS", 49: "R8G8_UNORM", 50: "R8G8_UINT", 51: "R8G8_SNORM", 52: "R8G8_SINT", 53: "R16_TYPELESS", 54: "R16_FLOAT", 55: "D16_UNORM", 56: "R16_UNORM", 57: "R16_UINT", 58: "R16_SNORM", 59: "R16_SINT", 60: "R8_TYPELESS", 61: "R8_UNORM", 62: "R8_UINT", 63: "R8_SNORM", 64: "R8_SINT", 65: "A8_UNORM", 66: "R1_UNORM", 67: "R9G9B9E5_SHAREDEXP", 68: "R8G8_B8G8_UNORM", 69: "G8R8_G8B8_UNORM", 70: "BC1_TYPELESS", 71: "BC1_UNORM", 72: "BC1_UNORM_SRGB", 73: "BC2_TYPELESS", 74: "BC2_UNORM", 75: "BC2_UNORM_SRGB", 76: "BC3_TYPELESS", 77: "BC3_UNORM", 78: "BC3_UNORM_SRGB", 79: "BC4_TYPELESS", 80: "BC4_UNORM", 81: "BC4_SNORM", 82: "BC5_TYPELESS", 83: "BC5_UNORM", 84: "BC5_SNORM", 85: "B5G6R5_UNORM", 86: "B5G5R5A1_UNORM", 87: "B8G8R8A8_UNORM", 88: "B8G8R8X8_UNORM", 89: "R10G10B10_XR_BIAS_A2_UNORM", 90: "B8G8R8A8_TYPELESS", 91: "B8G8R8A8_UNORM_SRGB", 92: "B8G8R8X8_TYPELESS", 93: "B8G8R8X8_UNORM_SRGB", 94: "BC6H_TYPELESS", 95: "BC6H_UF16", 96: "BC6H_SF16", 97: "BC7_TYPELESS", 98: "BC7_UNORM", 99: "BC7_UNORM_SRGB", 100: "AYUV", 101: "Y410", 102: "Y416", 103: "NV12", 104: "P010", 105: "P016", 106: "420_OPAQUE", 107: "YUY2", 108: "Y210", 109: "Y216", 110: "NV11", 111: "AI44", 112: "IA44", 113: "P8", 114: "A8P8", 115: "B4G4R4A4_UNORM", 130: "P208", 131: "V208", 132: "V408"}
    return Dict[format]

def DXGI_FORMAT_SIZE(format):
    if format.find("BC1") != -1 or format.find("BC4") != -1:
        return 8
    elif format.find("BC") != -1:
        return 16
    else:
        raise Exception("Fuck this shit man")

class StingrayMipmapInfo:
    def __init__(self):
        self.Start     = self.BytesLeft = self.Height = self.Width  = 0
    def Serialize(self, Toc):
        self.Start      = Toc.uint32(self.Start)
        self.BytesLeft  = Toc.uint32(self.BytesLeft)
        self.Height     = Toc.uint16(self.Height)
        self.Width      = Toc.uint16(self.Width)
        return self

class StingrayTexture:
    def __init__(self):
        self.UnkID = self.Unk1  = self.Unk2  = 0
        self.MipMapInfo = []

        self.ddsHeader = bytearray(148)
        self.rawTex    = b""

        self.Format     = ""
        self.Width      = 0
        self.Height     = 0
        self.NumMipMaps = 0
    def Serialize(self, Toc, Gpu, Stream):
        # clear header, so we dont have to deal with the .stream file
        if Toc.IsWriting():
            self.Unk1 = 0; self.Unk2  = 0xFFFFFFFF
            self.MipMapInfo = [StingrayMipmapInfo() for n in range(15)]

        self.UnkID = Toc.uint32(self.UnkID)
        self.Unk1  = Toc.uint32(self.Unk1)
        self.Unk2  = Toc.uint32(self.Unk2)
        if Toc.IsReading(): self.MipMapInfo = [StingrayMipmapInfo() for n in range(15)]
        self.MipMapInfo = [mipmapInfo.Serialize(Toc) for mipmapInfo in self.MipMapInfo]
        self.ddsHeader  = Toc.bytes(self.ddsHeader, 148)
        self.ParseDDsHeader()

        if Toc.IsWriting():
            Gpu.bytes(self.rawTex)
        else:# IsReading
            if len(Stream.Data) > 0:
                self.rawTex = Stream.Data
            else:
                self.rawTex = Gpu.Data

    def ToDDs(self):
        return self.ddsHeader + self.rawTex
    def FromDDs(self, dds):
        self.ddsHeader = dds[:148]
        self.rawTex    = dds[148::]
    def ParseDDsHeader(self):
        dds = MemoryStream(self.ddsHeader, IOMode="read")
        dds.seek(12)
        self.Height = dds.uint32(0)
        self.Width  = dds.uint32(0)
        dds.seek(28)
        self.NumMipMaps = dds.uint32(0)
        dds.seek(128)
        self.Format = DXGI_FORMAT(dds.uint32(0))
    def CalculateGpuMipmaps(self):
        Stride = DXGI_FORMAT_SIZE(self.Format) / 16
        start_mip = max(1, self.NumMipMaps-6)

        CurrentWidth = self.Width
        CurrentSize = int((self.Width*self.Width)*Stride)
        for mip in range(self.NumMipMaps-1):
            if mip+1 == start_mip:
                return CurrentSize

            if CurrentWidth > 4: CurrentWidth /= 2
            CurrentSize += int((CurrentWidth*CurrentWidth)*Stride)

def LoadStingrayTexture(ID, TocData, GpuData, StreamData, Reload, MakeBlendObject):
    exists = True
    try: bpy.data.images[str(ID)]
    except: exists = False
    StingrayTex = StingrayTexture()
    StingrayTex.Serialize(MemoryStream(TocData), MemoryStream(GpuData), MemoryStream(StreamData))
    dds = StingrayTex.ToDDs()

    if MakeBlendObject and not (exists and not Reload):
        tempdir = tempfile.gettempdir()
        path = f"{tempdir}\\{ID}.dds"
        tga_path = f"{tempdir}\\{ID}.tga"
        with open(path, "w+b") as f:
            f.write(dds)

        # convert to dds, as blender does not support these version of dds
        subprocess.run(f"{globals.TexconvPath} \"{path}\" -ft tga -f R8G8B8A8_UNORM -o \"{tempdir}\"")

        # wait until dds is converted, or 5 seconds have passed
        max_wait_s = 5
        start = time.time()
        while time.time() - start < max_wait_s:
            if os.path.isfile(tga_path):
                break
        if os.path.isfile(tga_path):
            image = bpy.data.images.load(tga_path)
            image.name = str(ID)
            image.pack()
            os.remove(tga_path)
            os.remove(path)
        else:
            os.remove(path)
            raise Exception(f"Failed to convert tex {ID} dds to tga, or dds failed to export")
    return StingrayTex

def BlendImageToStingrayTexture(image, StingrayTex):
    tempdir  = tempfile.gettempdir()
    dds_path = f"{tempdir}\\blender_img.dds"
    tga_path = f"{tempdir}\\blender_img.tga"
    image.file_format = "TARGA_RAW"
    image.filepath_raw = tga_path
    image.save()
    command = f"\"{globals.TexconvPath}\" \"{tga_path}\" -ft dds -dx10 -f {StingrayTex.Format} -o \"{tempdir}\""
    print(command)
    subprocess.run(command)
    max_wait_s = 5
    start = time.time()
    while time.time() - start < max_wait_s:
        if os.path.isfile(dds_path):
            break
    if os.path.isfile(dds_path):
        with open(dds_path, "r+b") as f:
            StingrayTex.FromDDs(f.read())
        os.remove(tga_path)
        os.remove(dds_path)
    else:
        os.remove(tga_path)
        raise Exception("Failed to convert tga to dds")

def SaveStingrayTexture(ID, TocData, GpuData, StreamData, LoadedData):
    exists = True
    try: bpy.data.images[str(ID)]
    except: exists = False
    Toc = MemoryStream(IOMode="write")
    Gpu = MemoryStream(IOMode="write")
    Stream = MemoryStream(IOMode="write")
    LoadedData.Serialize(Toc, Gpu, Stream)
    return [Toc.Data, Gpu.Data, Stream.Data]
