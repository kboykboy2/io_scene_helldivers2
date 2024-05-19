import ctypes, math, os

from ..classes_and_defs.memoryStream import MemoryStream
from .. import globals

def NormalFromPalette_py(normal):
    lowest_dif = 9999999999999999999
    lowest_dif_idx = 0
    for n in range(len(globals.NormalPalette[0])):
        guide_normal = globals.NormalPalette[0][n]
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(normal, guide_normal)))
        if distance < lowest_dif:
            lowest_dif = distance
            lowest_dif_idx = n
    return [globals.NormalPalette[1][lowest_dif_idx], globals.NormalPalette[0][lowest_dif_idx]]

def NormalsFromPalette_py(normals, return_real_normals = False):
    new_normals = []
    new_normals_testing = []
    for normal in normals:
        norms = NormalFromPalette_py(normal)
        new_normals.append(norms[0])
        new_normals_testing.append(norms[1])
    if return_real_normals:
        return new_normals_testing
    else:
        return new_normals

def NormalsFromPalette(normals):
    if globals.CPPHelper:
        f = MemoryStream(IOMode = "write")
        normals   = [f.vec3_float(normal) for normal in normals]
        output    = bytearray(len(normals)*4)
        c_normals = ctypes.c_char_p(bytes(f.Data))
        c_output  = (ctypes.c_char * len(output)).from_buffer(output)
        globals.CPPHelper.dll_NormalsFromPalette(c_output, c_normals, ctypes.c_uint32(len(normals)))
        F = MemoryStream(output, IOMode = "read")
        return [F.uint32(0) for normal in normals]
    else:
        return NormalsFromPalette_py(normals)

def LoadNormalPalette_py():
    if len(globals.NormalPalette) > 0:
        return
    with open(globals.PalettePath, 'r+b') as f:
        data = f.read()
    f = MemoryStream(data, IOMode="read")
    num = f.uint32(0)
    normals = []
    normal_palettes = []
    for n in range(num):
        normals.append(f.vec3_float([]))
        normal_palettes.append(f.uint32(0))
    globals.NormalPalette = [normals, normal_palettes]

def LoadNormalPalette():
    if globals.CPPHelper:
        globals.CPPHelper.dll_LoadPalette(globals.PalettePath.encode())
    else:
        LoadNormalPalette_py()
