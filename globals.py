import ctypes, os

from .classes_and_defs.stingray.toc import TocManager

DEVBUILD = False

DefaultMaterialPath = f"{os.path.dirname(__file__)}\\DefaultMaterial.dat"
FileHashPath        = f"{os.path.dirname(__file__)}\\filehash.txt"
FriendlyNamesPath   = f"{os.path.dirname(__file__)}\\friendlynames.txt"
DLLPath             = f"{os.path.dirname(__file__)}\\HDTool_Helper.dll"
PalettePath         = f"{os.path.dirname(__file__)}\\NormalPalette.dat"
TexconvPath         = f"{os.path.dirname(__file__)}\\texconv.exe"
TypeHashPath        = f"{os.path.dirname(__file__)}\\typehash.txt"

CPPHelper  = ctypes.cdll.LoadLibrary(DLLPath) if os.path.isfile(DLLPath) else None
TocManager = TocManager()

NormalPalette = []
TypeHashes = []
NameHashes = []

CompositeMeshID = 14191111524867688662
MeshID = 16187218042980615487
TexID  = 14790446551990181426
MaterialID  = 16915718763308572383
