import ctypes, os

from .classes_and_defs.stingray.toc import TocManager

DEVBUILD = False

AddonPath = os.path.dirname(__file__)

DLLPath     = f"{AddonPath}\\HDTool_Helper.dll"
TexconvPath = f"{AddonPath}\\texconv.exe"

TypeHashPath      = f"{AddonPath}\\hashes\\typeHashes.txt"
FileHashPath      = f"{AddonPath}\\hashes\\fileHashes.txt"
FriendlyNamesPath = f"{AddonPath}\\hashes\\friendlyNames.txt"

PalettePath         = f"{AddonPath}\\dats\\normalPalette.dat"
DefaultMaterialPath = f"{AddonPath}\\dats\\basic.dat"

CPPHelper  = ctypes.cdll.LoadLibrary(DLLPath) if os.path.isfile(DLLPath) else None
TocManager = TocManager()

NormalPalette = []
TypeHashes = []
NameHashes = []

CompositeMeshID = 14191111524867688662
MeshID = 16187218042980615487
TexID  = 14790446551990181426
MaterialID  = 16915718763308572383
