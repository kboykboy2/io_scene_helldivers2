import ctypes

from ..classes_and_defs.memoryStream import MemoryStream
from .. import globals

def Hash32(string):
    output    = bytearray(4)
    c_output  = (ctypes.c_char * len(output)).from_buffer(output)
    globals.CPPHelper.dll_Hash32(c_output, string.encode())
    F = MemoryStream(output, IOMode = "read")
    return F.uint32(0)

def Hash64(string):
    output    = bytearray(8)
    c_output  = (ctypes.c_char * len(output)).from_buffer(output)
    globals.CPPHelper.dll_Hash64(c_output, string.encode())
    F = MemoryStream(output, IOMode = "read")
    return F.uint64(0)

def LoadTypeHashes():
    with open(globals.TypeHashPath, 'r') as f:
        for line in f.readlines():
            parts = line.split(" ")
            globals.TypeHashes.append([int(parts[0], 16), parts[1].replace("\n", "")])

def GetTypeNameFromID(ID):
    for hash_info in globals.TypeHashes:
        if int(ID) == hash_info[0]:
            return hash_info[1]
    return "unknown"

def GetIDFromTypeName(Name):
    for hash_info in globals.TypeHashes:
        if hash_info[1] == Name:
            return int(hash_info[0])
    return None

def LoadNameHashes():
    Loaded = []
    with open(globals.FileHashPath, 'r') as f:
        for line in f.readlines():
            parts = line.split(" ")
            globals.NameHashes.append([int(parts[0]), parts[1].replace("\n", "")])
            Loaded.append(int(parts[0]))
    with open(globals.FriendlyNamesPath, 'r') as f:
        for line in f.readlines():
            parts = line.split(" ")
            if int(parts[0]) not in Loaded:
                globals.NameHashes.append([int(parts[0]), parts[1].replace("\n", "")])
                Loaded.append(int(parts[0]))

def GetFriendlyNameFromID(ID):
    for hash_info in globals.NameHashes:
        if int(ID) == hash_info[0]:
            if hash_info[1] != "":
                return hash_info[1]
    return str(ID)

def HasFriendlyName(ID):
    for hash_info in globals.NameHashes:
        if int(ID) == hash_info[0]:
            return True
    return False

def SaveFriendlyNames():
    with open(globals.FileHashPath, 'w') as f:
        for hash_info in globals.NameHashes:
            if hash_info[1] != "" and int(hash_info[0]) == Hash64(hash_info[1]):
                string = str(hash_info[0]) + " " + str(hash_info[1])
                f.writelines(string+"\n")
    with open(globals.FriendlyNamesPath, 'w') as f:
        for hash_info in globals.NameHashes:
            if hash_info[1] != "":
                string = str(hash_info[0]) + " " + str(hash_info[1])
                f.writelines(string+"\n")

def AddFriendlyName(ID, Name):
    globals.TocManager.SavedFriendlyNames = []
    globals.TocManager.SavedFriendlyNameIDs = []
    for hash_info in globals.NameHashes:
        if int(ID) == hash_info[0]:
            hash_info[1] = str(Name)
            return
    globals.NameHashes.append([int(ID), str(Name)])
    SaveFriendlyNames()
