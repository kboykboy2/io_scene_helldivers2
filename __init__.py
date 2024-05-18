bl_info = {
    "name": "HellDivers2 Mesh Tool",
    "blender": (3, 1, 2),
    "category": "Mod Tool",
}
from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import ExportHelper
from bpy.props import (StringProperty,BoolProperty,IntProperty,FloatProperty,FloatVectorProperty,EnumProperty,PointerProperty,)
from bpy.types import (Panel,Operator,AddonPreferences,PropertyGroup,Scene,Image)
import bpy, bmesh, mathutils
from pathlib import Path
import math, struct, ctypes, os, tempfile, subprocess, time, copy, zlib, webbrowser, threading
import random as r
#Global_dllpath              = os.path.dirname(__file__)+"/HDTool_Helper.dll"
#Global_palettepath          = os.path.dirname(__file__)+"/NormalPalette.dat"
#Global_texconvpath          = os.path.dirname(__file__)+"/texconv.exe"
#Global_defaultmaterialpath  = os.path.dirname(__file__)+"/DefaultMaterial.dat"
#Global_typehashpath         = os.path.dirname(__file__)+"/typehash.txt"
#Global_filehashpath         = os.path.dirname(__file__)+"/filehash.txt"
#Global_friendlynamespath    = os.path.dirname(__file__)+"/friendlynames.txt"
#DEVBUILD = False
Global_dllpath     = "C:\\Users\\kboyk\\OneDrive\\Desktop\\New folder\\A_HD2Tool\\HDTool_Helper.dll"
Global_palettepath = "C:\\Users\\kboyk\\OneDrive\\Desktop\\New folder\\A_HD2Tool\\NormalPalette.dat"
Global_texconvpath = "C:\\Users\\kboyk\\OneDrive\\Desktop\\New folder\\A_HD2Tool\\texconv.exe"
Global_defaultmaterialpath= "C:\\Users\\kboyk\\OneDrive\\Desktop\\New folder\\A_HD2Tool\\DefaultMaterial.dat"
Global_typehashpath      = "C:\\Users\\kboyk\\OneDrive\\Desktop\\New folder\\A_HD2Tool\\typehash.txt"
Global_filehashpath      = "C:\\Users\\kboyk\\OneDrive\\Desktop\\New folder\\A_HD2Tool\\filehash.txt"
Global_friendlynamespath = "C:\\Users\\kboyk\\OneDrive\\Desktop\\New folder\\A_HD2Tool\\friendlynames.txt"
DEVBUILD = False
Global_CPPHelper = None
# Must check all 'TODO IMPORTANT' comments before release

##################################
#### ---- Math Functions ---- ####
##################################

def InsureBitLength(bits, length):
    # cut off if to big
    if len(bits) > length:
        bits = bits[:length]
    # add to start if to small
    newbits = str().ljust(length-len(bits),"0")
    return newbits + bits

def TenBitSigned(U32):
    X = (U32 & 1023)
    Y = ((U32 >> 10) & 1023)
    Z = ((U32 >> 20) & 1023)
    W = (U32 >> 30)

    v = [((X - 511) / 512), ((Y - 511) / 512), ((Z - 511) / 512), W / 3]
    return v

def TenBitUnsigned(U32):
    X = (U32 & 1023)
    Y = ((U32 >> 10) & 1023)
    Z = ((U32 >> 20) & 1023)
    W = (U32 >> 30)

    v = [(X / 1023), (Y  / 1023), (Z  / 1023), W / 3]
    return v

def MakeTenBitUnsigned(vec):
    x = vec[0];y = vec[1];z = vec[2]
    x *= 1024; y *= 1024; z *= 1024
    xbin = bin(int(x))[2:]; ybin = bin(int(y))[2:]; zbin = bin(int(z))[2:]
    xbin = InsureBitLength(xbin, 10); ybin = InsureBitLength(ybin, 10); zbin = InsureBitLength(zbin, 10);
    binary = InsureBitLength(zbin+ybin+xbin, 32)
    return int(binary, 2)

def MakeTenBitSigned(vec):
    x = vec[0];y = vec[1];z = vec[2]
    x = (abs(x)*512); y =(abs(y)*512); z =(abs(z)*512)
    # add bias
    if vec[0] < 0:
        x = abs(x-511)
    else:
        x += 511
    if vec[1] < 0:
        y = abs(y-511)
    else:
        y += 511
    if vec[2] < 0:
        z = abs(z-511)
    else:
        z += 511
    xbin = bin(int(x))[2:]; ybin = bin(int(y))[2:]; zbin = bin(int(z))[2:]
    
    
    xbin = InsureBitLength(xbin, 10); ybin = InsureBitLength(ybin, 10); zbin = InsureBitLength(zbin, 10);
    binary = InsureBitLength(zbin+ybin+xbin, 32)
    return int(binary, 2)

###############################
#### ---- Extra Utils ---- ####
###############################
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

def EntriesFromStrings(file_id_string, type_id_string):
    FileIDs = file_id_string.split(',')
    TypeIDs = type_id_string.split(',')
    Entries = []
    for n in range(len(FileIDs)):
        if FileIDs[n] != "":
            Entries.append(Global_TocManager.GetEntry(int(FileIDs[n]), int(TypeIDs[n])))
    return Entries

def EntriesFromString(file_id_string, TypeID):
    FileIDs = file_id_string.split(',')
    Entries = []
    for n in range(len(FileIDs)):
        if FileIDs[n] != "":
            Entries.append(Global_TocManager.GetEntry(int(FileIDs[n]), int(TypeID)))
    return Entries

def IDsFromString(file_id_string):
    FileIDs = file_id_string.split(',')
    Entries = []
    for n in range(len(FileIDs)):
        if FileIDs[n] != "":
            Entries.append(int(FileIDs[n]))
    return Entries

##################################################
#### ---- Blender Object/Model Functions ---- ####
##################################################

def duplicate(obj, data=True, actions=True, collection=None):
    obj_copy = obj.copy()
    if data:
        obj_copy.data = obj_copy.data.copy()
    if actions and obj_copy.animation_data:
        obj_copy.animation_data.action = obj_copy.animation_data.action.copy()
    bpy.context.collection.objects.link(obj_copy)
    return obj_copy

def PrepareMesh(og_object):
    object = duplicate(og_object)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = object
    # split UV seams
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.seams_from_islands()
    except: print("Error attempting to create seams from uv islands")
    bpy.ops.object.mode_set(mode='OBJECT')
    
    bm = bmesh.new()
    bm.from_mesh(object.data)
    
    # get all sharp edges and uv seams
    sharp_edges = [e for e in bm.edges if not e.smooth]
    boundary_seams = [e for e in bm.edges if e.seam]
    # split edges
    bmesh.ops.split_edges(bm, edges=sharp_edges)
    bmesh.ops.split_edges(bm, edges=boundary_seams)
    # update mesh
    bm.to_mesh(object.data)
    bm.clear()
    # transfer normals
    modifier = object.modifiers.new("EXPORT_NORMAL_TRANSFER", 'DATA_TRANSFER')
    bpy.context.object.modifiers[modifier.name].data_types_loops = {'CUSTOM_NORMAL'}
    bpy.context.object.modifiers[modifier.name].object = og_object
    bpy.context.object.modifiers[modifier.name].use_loop_data = True
    bpy.context.object.modifiers[modifier.name].loop_mapping = 'TOPOLOGY'
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    # triangulate
    modifier = object.modifiers.new("EXPORT_TRIANGULATE", 'TRIANGULATE')
    bpy.context.object.modifiers[modifier.name].keep_custom_normals = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    
    # adjust weights
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    try:
        bpy.ops.object.vertex_group_normalize_all(lock_active=False)
        bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
    except: pass
    
    return object

def GetMeshData(og_object):
    global Global_palettepath
    object = PrepareMesh(og_object)
    bpy.context.view_layer.objects.active = object
    mesh = object.data
    
    vertices    = [ [vert.co[0], vert.co[1], vert.co[2]] for vert in mesh.vertices]
    normals     = [ [vert.normal[0], vert.normal[1], vert.normal[2]] for vert in mesh.vertices]
    tangents    = [ [vert.normal[0], vert.normal[1], vert.normal[2]] for vert in mesh.vertices]
    bitangents  = [ [vert.normal[0], vert.normal[1], vert.normal[2]] for vert in mesh.vertices]
    colors      = [[0,0,0,0] for n in range(len(vertices))]
    uvs         = []
    weights     = [[0,0,0,0] for n in range(len(vertices))]
    boneIndices = []
    faces       = []
    materials   = [ RawMaterialClass() for idx in range(len(object.material_slots))]
    for idx in range(len(object.material_slots)): materials[idx].IDFromName(object.material_slots[idx].name)
    
    # get vertex color
    if mesh.vertex_colors:
        color_layer = mesh.vertex_colors.active
        for face in object.data.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                col = color_layer.data[loop_idx].color
                colors[vert_idx] = [col[0], col[1], col[2], col[3]]
    
    # get normals, tangents, bitangents
    #mesh.calc_tangents()
    mesh.calc_normals_split()
    for loop in mesh.loops:
        normals[loop.vertex_index]    = loop.normal.normalized()
        #tangents[loop.vertex_index]   = loop.tangent.normalized()
        #bitangents[loop.vertex_index] = loop.bitangent.normalized()
    # if fuckywuckynormalwormal do this bullshit
    LoadNormalPalette(Global_palettepath)
    normals = NormalsFromPalette(normals)
    # get uvs
    for uvlayer in object.data.uv_layers:
        if len(uvs) >= 3:
            break
        texCoord = [[0,0] for vert in mesh.vertices]
        for face in object.data.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                texCoord[vert_idx] = [uvlayer.data[loop_idx].uv[0], uvlayer.data[loop_idx].uv[1]*-1 + 1]
        uvs.append(texCoord)

    # get weights
    vert_idx = 0
    numInfluences = 4
    if len(object.vertex_groups) > 0:
        for vertex in mesh.vertices:
            group_idx = 0
            for group in vertex.groups:
                # limit influences
                if group_idx >= numInfluences:
                    break
                if group.weight > 0.001:
                    vertex_group        = object.vertex_groups[group.group]
                    vertex_group_name   = vertex_group.name
                    parts               = vertex_group_name.split("_")
                    HDGroupIndex        = int(parts[0])
                    HDBoneIndex         = int(parts[1])
                    if HDGroupIndex+1 > len(boneIndices):
                        dif = HDGroupIndex+1 - len(boneIndices)
                        boneIndices.extend([[[0,0,0,0] for n in range(len(vertices))]]*dif)
                    boneIndices[HDGroupIndex][vert_idx][group_idx] = HDBoneIndex
                    weights[vert_idx][group_idx] = group.weight
                    group_idx += 1
            vert_idx += 1
    else:
        boneIndices = []
        weights     = []

    # get faces
    temp_faces = [[] for n in range(len(object.material_slots))]
    for f in mesh.polygons:
        temp_faces[f.material_index].append([f.vertices[0], f.vertices[1], f.vertices[2]])
        materials[f.material_index].NumIndices += 3
    for tmp in temp_faces: faces.extend(tmp)
    
    NewMesh = RawMeshClass()
    NewMesh.VertexPositions     = vertices
    NewMesh.VertexNormals       = normals
    #NewMesh.VertexTangents      = tangents
    #NewMesh.VertexBiTangents    = bitangents
    NewMesh.VertexColors        = colors
    NewMesh.VertexUVs           = uvs
    NewMesh.VertexWeights       = weights
    NewMesh.VertexBoneIndices   = boneIndices
    NewMesh.Indices             = faces
    NewMesh.Materials           = materials
    NewMesh.MeshInfoIndex       = og_object["MeshInfoIndex"]
    NewMesh.DEV_BoneInfoIndex   = og_object["BoneInfoIndex"]
    NewMesh.LodIndex            = og_object["BoneInfoIndex"]
    if len(vertices) > 0xffff: NewMesh.DEV_Use32BitIndices = True
    matNum = 0
    for material in NewMesh.Materials:
        try:
            material.DEV_BoneInfoOverride = int(og_object[f"matslot{matNum}"])
        except: pass
        matNum += 1
    
    bpy.data.objects.remove(object, do_unlink=True)
    return NewMesh

def GetObjectsMeshData():
    objects = bpy.context.selected_objects
    bpy.ops.object.select_all(action='DESELECT')
    data = []
    for object in objects:
        data.append(GetMeshData(object))
    return data

def NameFromMesh(mesh, id, customization_info, bone_names, use_sufix=True):
    # generate name
    name = str(id)
    if customization_info.BodyType != "":
        BodyType    = customization_info.BodyType.replace("HelldiverCustomizationBodyType_", "")
        Slot        = customization_info.Slot.replace("HelldiverCustomizationSlot_", "")
        Weight      = customization_info.Weight.replace("HelldiverCustomizationWeight_", "")
        PieceType   = customization_info.PieceType.replace("HelldiverCustomizationPieceType_", "")
        name = Slot+"_"+PieceType+"_"+BodyType
    name_sufix = "_lod"+str(mesh.LodIndex)
    if mesh.LodIndex == -1:
        name_sufix = "_mesh"+str(mesh.MeshInfoIndex)
    if mesh.IsPhysicsBody():
        name_sufix = "_phys"+str(mesh.MeshInfoIndex)
    if use_sufix: name = name + name_sufix
    
    if use_sufix and bone_names != None:
        for bone_name in bone_names:
            if Hash32(bone_name) == mesh.MeshID:
                name = bone_name

    return name

def CreateModel(model, id, customization_info, bone_names):
    if len(model) < 1: return
    # Make collection
    old_collection = bpy.context.collection
    if bpy.context.scene.Hd2ToolPanelSettings.MakeCollections:
        new_collection = bpy.data.collections.new(NameFromMesh(model[0], id, customization_info, bone_names, False))
        old_collection.children.link(new_collection)
    else:
        new_collection = old_collection
    # Make Meshes
    for mesh in model:
        # check lod
        if not bpy.context.scene.Hd2ToolPanelSettings.ImportLods and mesh.IsLod():
            continue
        # check physics
        if not bpy.context.scene.Hd2ToolPanelSettings.ImportPhysics and mesh.IsPhysicsBody():
            continue
        # do safety check
        for face in mesh.Indices:
            for index in face:
                if index > len(mesh.VertexPositions):
                    raise Exception("Bad Mesh Parse: indices do not match vertices")
        # generate name
        name = NameFromMesh(mesh, id, customization_info, bone_names)
        
        # create mesh
        new_mesh = bpy.data.meshes.new(name)
        #new_mesh.from_pydata(mesh.VertexPositions, [], [])
        new_mesh.from_pydata(mesh.VertexPositions, [], mesh.Indices)
        new_mesh.update()
        # make object from mesh
        new_object = bpy.data.objects.new(name, new_mesh)
        # set transform
        print("scale: ", mesh.DEV_Transform.scale)
        print("location: ", mesh.DEV_Transform.pos)
        new_object.scale = (mesh.DEV_Transform.scale[0],mesh.DEV_Transform.scale[1],mesh.DEV_Transform.scale[2])
        new_object.location = (mesh.DEV_Transform.pos[0],mesh.DEV_Transform.pos[1],mesh.DEV_Transform.pos[2])
        
        # TODO: fix incorrect rotation
        rot = mesh.DEV_Transform.rot
        rotation_matrix = mathutils.Matrix([rot.x, rot.y, rot.z])
        new_object.rotation_mode = 'QUATERNION'
        new_object.rotation_quaternion = rotation_matrix.to_quaternion()
        
        # set object properties
        new_object["MeshInfoIndex"] = mesh.MeshInfoIndex
        new_object["BoneInfoIndex"] = mesh.LodIndex
        new_object["Z_ObjectID"]      = str(id)
        if customization_info.BodyType != "":
            new_object["Z_CustomizationBodyType"] = customization_info.BodyType
            new_object["Z_CustomizationSlot"]     = customization_info.Slot
            new_object["Z_CustomizationWeight"]   = customization_info.Weight
            new_object["Z_CustomizationPieceType"]= customization_info.PieceType
        if mesh.IsPhysicsBody():
            new_object.display_type = 'WIRE'
        
        # add object to scene collection
        new_collection.objects.link(new_object)
        # -- || ASSIGN NORMALS || -- #
        if len(mesh.VertexNormals) == len(mesh.VertexPositions):
            new_mesh.use_auto_smooth = True
            new_mesh.polygons.foreach_set('use_smooth',  [True] * len(new_mesh.polygons))
            if not isinstance(mesh.VertexNormals[0], int):
                new_mesh.normals_split_custom_set_from_vertices(mesh.VertexNormals)
        
        # -- || ASSIGN VERTEX COLORS || -- #
        if len(mesh.VertexColors) == len(mesh.VertexPositions):
            color_layer = new_mesh.vertex_colors.new()
            for face in new_mesh.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    color_layer.data[loop_idx].color = (mesh.VertexColors[vert_idx][0], mesh.VertexColors[vert_idx][1], mesh.VertexColors[vert_idx][2], mesh.VertexColors[vert_idx][3])
        # -- || ASSIGN UVS || -- #
        for uvs in mesh.VertexUVs:
            uvlayer = new_mesh.uv_layers.new()
            new_mesh.uv_layers.active = uvlayer
            for face in new_mesh.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    uvlayer.data[loop_idx].uv = (uvs[vert_idx][0], uvs[vert_idx][1]*-1 + 1)
        # -- || ASSIGN WEIGHTS || -- #
        created_groups = []
        for vertex_idx in range(len(mesh.VertexWeights)):
            weights      = mesh.VertexWeights[vertex_idx]
            index_groups = [Indices[vertex_idx] for Indices in mesh.VertexBoneIndices]
            group_index  = 0
            for indices in index_groups:
                if bpy.context.scene.Hd2ToolPanelSettings.ImportGroup0 and group_index != 0:
                    continue
                if type(weights) != list:
                    weights = [weights]
                for weight_idx in range(len(weights)):
                    weight_value = weights[weight_idx]
                    bone_index   = indices[weight_idx]
                    #bone_index   = mesh.DEV_BoneInfo.GetRealIndex(bone_index)
                    group_name   = str(group_index) + "_" + str(bone_index)
                    if group_name not in created_groups:
                        created_groups.append(group_name)
                        new_vertex_group = new_object.vertex_groups.new(name=str(group_name))
                    vertex_group_data = [vertex_idx]
                    new_object.vertex_groups[str(group_name)].add(vertex_group_data, weight_value, 'ADD')
                group_index += 1
        # -- || ASSIGN MATERIALS || -- #
        # convert mesh to bmesh
        bm = bmesh.new()
        bm.from_mesh(new_object.data)
        # assign materials
        matNum = 0
        for material in mesh.Materials:
            # append material to slot
            try: new_object.data.materials.append(bpy.data.materials[material.MatID])
            except: raise Exception(f"Tool was unable to find material that this mesh uses, ID: {material.MatID}")
            # assign material to faces
            numTris    = int(material.NumIndices/3)
            StartIndex = int(material.StartIndex/3)
            for f in bm.faces[StartIndex:(numTris+(StartIndex))]:
                f.material_index = matNum
            matNum += 1
        # convert bmesh to mesh
        bm.to_mesh(new_object.data)
        
        
        # Create skeleton
        if False:
            if mesh.DEV_BoneInfo != None:
                for Bone in mesh.DEV_BoneInfo.Bones:
                    current_pos = [Bone.v[12], Bone.v[13], Bone.v[14]]
                    bpy.ops.object.empty_add(type='SPHERE', radius=0.08, align='WORLD', location=(current_pos[0], current_pos[1], current_pos[2]), scale=(1, 1, 1))

#######################################
#### ---- Memory Stream Class ---- ####
#######################################
class MemoryStream:
    def __init__(self, Data=b"", IOMode = "read"):
        self.Location = 0
        self.Data = bytearray(Data)
        self.IOMode = IOMode
        self.Endian = "<"
    
    # -- Open Stream -- 
    def open(self, Data, IOMode = "read"):
        self.Data = bytearray(Data)
        self.IOMode = IOMode
       
    # -- IO Mode Functions --  
    def SetReadMode(self):
        self.IOMode = "read"
    def SetWriteMode(self):
        self.IOMode = "write"
    def IsReading(self):
        return self.IOMode == "read"
    def IsWriting(self):
        return self.IOMode == "write"
    
    # -- Go To Position In Stream -- 
    def seek(self, Location):
        self.Location = Location
        if self.Location > len(self.Data):
            missing_bytes = self.Location - len(self.Data)
            self.Data += bytearray(missing_bytes)
    
    # -- Get Position In Stream -- 
    def tell(self):
        return self.Location
    
    # -- Read Bytes From Stream -- 
    def read(self, length=-1):
        if length == -1:
            length = len(self.Data) - self.Location
        if self.Location + length > len(self.Data):
            raise Exception("reading past end of stream")
        
        newData = self.Data[self.Location:self.Location+length]
        self.Location += length
        return bytes(newData)
    
    # -- Write Bytes To Stream -- 
    def write(self, bytes):
        length = len(bytes)
        if self.Location + length > len(self.Data):
            missing_bytes = (self.Location + length) - len(self.Data)
            self.Data += bytearray(missing_bytes)
        self.Data[self.Location:self.Location+length] = bytearray(bytes)
        self.Location += length
        
    # -- Serialization Functions -- 
    def serialize(self, value, format, size):
        format = self.Endian+format
        if self.IsReading():
            return struct.unpack(format, self.read(size))[0]
        elif self.IsWriting():
            self.write(struct.pack(format, value))
            return value
    
    def int8(self, value):
        return self.serialize(value, 'b', 1)
    def uint8(self, value):
        return self.serialize(value, 'B', 1)
    def int16(self, value):
        return self.serialize(value, 'h', 2)
    def uint16(self, value):
        return self.serialize(value, 'H', 2)
    def int32(self, value):
        return self.serialize(value, 'i', 4)
    def uint32(self, value):
        return self.serialize(value, 'I', 4)
    def int64(self, value):
        return self.serialize(value, 'q', 8)
    def uint64(self, value):
        return self.serialize(value, 'Q', 8)
    def float16(self, value):
        return self.serialize(value, 'e', 2)
    def float32(self, value):
        return self.serialize(value, 'f', 4)
    def float64(self, value):
        return self.serialize(value, 'd', 8)
    def __resize_vec(self, value, length):
        value = list(value)
        if len(value) < length:
            dif = length - len(value)
            value.extend([0]*dif)
        if len(value) > length:
            value = value[:length]
        return value
    def vec2_float(self, value):
        value = self.__resize_vec(value, 2)
        return [self.float32(value[0]), self.float32(value[1])]
    def vec3_float(self, value):
        value = self.__resize_vec(value, 3)
        return [self.float32(value[0]), self.float32(value[1]), self.float32(value[2])]
    def vec2_half(self, value):
        value = self.__resize_vec(value, 2)
        return [self.float16(value[0]), self.float16(value[1])]
    def vec3_half(self, value):
        value = self.__resize_vec(value, 3)
        return [self.float16(value[0]), self.float16(value[1]), self.float16(value[2])]
    def vec4_half(self, value):
        value = self.__resize_vec(value, 4)
        return [self.float16(value[0]), self.float16(value[1]), self.float16(value[2]), self.float16(value[3])]
    def vec4_uint8(self, value):
        value = self.__resize_vec(value, 4)
        return [self.uint8(value[0]), self.uint8(value[1]), self.uint8(value[2]), self.uint8(value[3])]
    def vec4_uint16(self, value):
        value = self.__resize_vec(value, 4)
        return [self.uint16(value[0]), self.uint16(value[1]), self.uint16(value[2]), self.uint16(value[3])]
    def vec4_uint32(self, value):
        value = self.__resize_vec(value, 4)
        return [self.uint32(value[0]), self.uint32(value[1]), self.uint32(value[2]), self.uint32(value[3])]
    def array(self, type, value, size = -1):
        if size == -1:
            size = len(value)
        if len(value) != size:
            value = range(size)
            
        for n in range(size):
            value[n] = type()
        return value
    def bytes(self, value, size = -1):
        if size == -1:
            size = len(value)
        if len(value) != size:
            value = bytearray(size)
            
        if self.IsReading():
            return bytearray(self.read(size))
        elif self.IsWriting():
            self.write(value)
            return bytearray(value)
        return value


#############################################
#### ---- Load Normals Palette File ---- ####
#############################################

Global_NormalPalette = []
def LoadNormalPalette_py(path):
    global Global_NormalPalette
    if len(Global_NormalPalette) > 0:
        return
    with open(path, 'r+b') as f:
        data = f.read()
    f = MemoryStream(data, IOMode="read")
    num = f.uint32(0)
    normals = []
    normal_palettes = []
    for n in range(num):
        normals.append(f.vec3_float([]))
        normal_palettes.append(f.uint32(0))
    Global_NormalPalette = [normals, normal_palettes]

def NormalFromPalette_py(normal):
    lowest_dif = 9999999999999999999
    lowest_dif_idx = 0
    for n in range(len(Global_NormalPalette[0])):
        guide_normal = Global_NormalPalette[0][n]
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(normal, guide_normal)))
        if distance < lowest_dif:
            lowest_dif = distance
            lowest_dif_idx = n
    return [Global_NormalPalette[1][lowest_dif_idx], Global_NormalPalette[0][lowest_dif_idx]]

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
    global Global_CPPHelper
    if Global_CPPHelper != None:
        f = MemoryStream(IOMode = "write")
        normals = [f.vec3_float(normal) for normal in normals]
        output    = bytearray(len(normals)*4)
        c_normals = ctypes.c_char_p(bytes(f.Data))
        c_output  = (ctypes.c_char * len(output)).from_buffer(output)
        Global_CPPHelper.dll_NormalsFromPalette(c_output, c_normals, ctypes.c_uint32(len(normals)))
        F = MemoryStream(output, IOMode = "read")
        return [F.uint32(0) for normal in normals]
    else:
        return NormalsFromPalette_py(normals)

def LoadNormalPalette(path):
    global Global_CPPHelper
    global Global_dllpath
    if os.path.isfile(Global_dllpath):
        Global_CPPHelper = ctypes.cdll.LoadLibrary(Global_dllpath)
        Global_CPPHelper.dll_LoadPalette(path.encode())
    else:
        LoadNormalPalette_py(path)


###########################################
#### ---- Stingray Hash Functions ---- ####
###########################################

CompositeMeshID = 14191111524867688662
MeshID = 16187218042980615487
TexID  = 14790446551990181426
MaterialID  = 16915718763308572383
Global_TypeHashes = []
def LoadTypeHashes():
    with open(Global_typehashpath, 'r') as f:
        for line in f.readlines():
            parts = line.split(" ")
            Global_TypeHashes.append([int(parts[0], 16), parts[1].replace("\n", "")])
        
def GetTypeNameFromID(ID):
    for hash_info in Global_TypeHashes:
        if int(ID) == hash_info[0]:
            return hash_info[1]
    return "unknown"

def GetIDFromTypeName(Name):
    for hash_info in Global_TypeHashes:
        if hash_info[1] == Name:
            return int(hash_info[0])
    return None

Global_NameHashes = []
def LoadNameHashes():
    Loaded = []
    with open(Global_filehashpath, 'r') as f:
        for line in f.readlines():
            parts = line.split(" ")
            Global_NameHashes.append([int(parts[0]), parts[1].replace("\n", "")])
            Loaded.append(int(parts[0]))
    with open(Global_friendlynamespath, 'r') as f:
        for line in f.readlines():
            parts = line.split(" ")
            if int(parts[0]) not in Loaded:
                Global_NameHashes.append([int(parts[0]), parts[1].replace("\n", "")])
                Loaded.append(int(parts[0]))
def GetFriendlyNameFromID(ID):
    for hash_info in Global_NameHashes:
        if int(ID) == hash_info[0]:
            if hash_info[1] != "":
                return hash_info[1]
    return str(ID)

def HasFriendlyName(ID):
    for hash_info in Global_NameHashes:
        if int(ID) == hash_info[0]:
            return True
    return False

def AddFriendlyName(ID, Name):
    Global_TocManager.SavedFriendlyNames = []
    Global_TocManager.SavedFriendlyNameIDs = []
    for hash_info in Global_NameHashes:
        if int(ID) == hash_info[0]:
            hash_info[1] = str(Name)
            return
    Global_NameHashes.append([int(ID), str(Name)])
    SaveFriendlyNames()
    
def SaveFriendlyNames():
    with open(Global_filehashpath, 'w') as f:
        for hash_info in Global_NameHashes:
            if hash_info[1] != "" and int(hash_info[0]) == Hash64(hash_info[1]):
                string = str(hash_info[0]) + " " + str(hash_info[1])
                f.writelines(string+"\n")
    with open(Global_friendlynamespath, 'w') as f:
        for hash_info in Global_NameHashes:
            if hash_info[1] != "":
                string = str(hash_info[0]) + " " + str(hash_info[1])
                f.writelines(string+"\n")
      
def Hash32(string):
    output    = bytearray(4)
    c_output  = (ctypes.c_char * len(output)).from_buffer(output)
    Global_CPPHelper.dll_Hash32(c_output, string.encode())
    F = MemoryStream(output, IOMode = "read")
    return F.uint32(0)

def Hash64(string):
    output    = bytearray(8)
    c_output  = (ctypes.c_char * len(output)).from_buffer(output)
    Global_CPPHelper.dll_Hash64(c_output, string.encode())
    F = MemoryStream(output, IOMode = "read")
    return F.uint64(0)

#################################################
#### ---- Archive Classes And Functions ---- ####
#################################################

# ----------------------- #
# -- File Entry In Toc -- #

class TocEntry:
    def __init__(self):
        self.FileID = self.TypeID = self.TocDataOffset = self.Unknown1 = self.GpuResourceOffset = self.Unknown2 = self.TocDataSize = self.GpuResourceSize = self.EntryIndex = self.StreamSize = self.StreamOffset = 0
        self.Unknown3 = 16
        self.Unknown4 = 64
        
        self.TocData =  self.TocData_OLD = b""
        self.GpuData =  self.GpuData_OLD = b""
        self.StreamData =  self.StreamData_OLD = b""
        
        # Custom Dev stuff
        self.LoadedData = None
        self.IsLoaded   = False
        self.IsModified = False
        self.IsCreated  = False # custom created, can be removed from archive
        self.IsSelected = False
        self.DEV_DrawIndex = -1
    # -- Serialize TocEntry -- #
    def Serialize(self, TocFile, Index=0):
        self.FileID             = TocFile.uint64(self.FileID)
        self.TypeID             = TocFile.uint64(self.TypeID)
        self.TocDataOffset      = TocFile.uint64(self.TocDataOffset)
        self.StreamOffset       = TocFile.uint64(self.StreamOffset)
        self.GpuResourceOffset  = TocFile.uint64(self.GpuResourceOffset)
        self.Unknown1           = TocFile.uint64(self.Unknown1)
        self.Unknown2           = TocFile.uint64(self.Unknown2)
        self.TocDataSize        = TocFile.uint32(len(self.TocData))
        self.StreamSize         = TocFile.uint32(len(self.StreamData))
        self.GpuResourceSize    = TocFile.uint32(len(self.GpuData))
        self.Unknown3           = TocFile.uint32(self.Unknown3)
        self.Unknown4           = TocFile.uint32(self.Unknown4)
        self.EntryIndex         = TocFile.uint32(Index)
        return self
        
    # -- Write TocEntry Data -- #
    def SerializeData(self, TocFile, GpuFile, StreamFile):
        if TocFile.IsReading(): 
            TocFile.seek(self.TocDataOffset)
            self.TocData = bytearray(self.TocDataSize)
        elif TocFile.IsWriting(): 
            self.TocDataOffset = TocFile.tell()
        self.TocData = TocFile.bytes(self.TocData)
        
        if GpuFile.IsWriting(): self.GpuResourceOffset = math.ceil(float(GpuFile.tell())/64)*64
        if self.GpuResourceSize > 0:
            GpuFile.seek(self.GpuResourceOffset)
            if GpuFile.IsReading(): self.GpuData = bytearray(self.GpuResourceSize)
            self.GpuData = GpuFile.bytes(self.GpuData)
        
        if StreamFile.IsWriting(): self.StreamOffset = math.ceil(float(StreamFile.tell())/64)*64
        if self.StreamSize > 0:
            StreamFile.seek(self.StreamOffset)
            if StreamFile.IsReading(): self.StreamData = bytearray(self.StreamSize)
            self.StreamData = StreamFile.bytes(self.StreamData)
        if GpuFile.IsReading():
            self.TocData_OLD    = bytearray(self.TocData)
            self.GpuData_OLD    = bytearray(self.GpuData)
            self.StreamData_OLD = bytearray(self.StreamData)
    
    # -- Get Data -- #
    def GetData(self):
        return [self.TocData, self.GpuData, self.StreamData]
    # -- Set Data -- #
    def SetData(self, TocData, GpuData, StreamData, IsModified=True):
        self.TocData = TocData
        self.GpuData = GpuData
        self.StreamData = StreamData
        self.TocDataSize     = len(self.TocData)
        self.GpuResourceSize = len(self.GpuData)
        self.StreamSize      = len(self.StreamData)
        self.IsModified = IsModified
    # -- Undo Modified Data -- #
    def UndoModifiedData(self):
        self.TocData = bytearray(self.TocData_OLD)
        self.GpuData = bytearray(self.GpuData_OLD)
        self.StreamData = bytearray(self.StreamData_OLD)
        self.TocDataSize     = len(self.TocData)
        self.GpuResourceSize = len(self.GpuData)
        self.StreamSize      = len(self.StreamData)
        self.IsModified = False
        if self.IsLoaded:
            self.Load(True, False)
    # -- Load Data -- #
    def Load(self, Reload=False, MakeBlendObject=True):
        callback = None
        if self.TypeID == MeshID: callback = LoadStingrayMesh
        if self.TypeID == TexID: callback = LoadStingrayTexture
        if self.TypeID == MaterialID: callback = LoadStingrayMaterial
        if self.TypeID == CompositeMeshID: callback = LoadStingrayCompositeMesh
        if self.TypeID == Hash64("bones"): callback = LoadStingrayBones
        if callback != None:
            self.LoadedData = callback(self.FileID, self.TocData, self.GpuData, self.StreamData, Reload, MakeBlendObject)
            if self.LoadedData == None: raise Exception("Archive Entry Load Failed")
            self.IsLoaded   = True
        else: raise Exception("Load Callback could not be found")
    # -- Write Data -- #
    def Save(self):
        if not self.IsLoaded: self.Load(True, False)
        if self.TypeID == MeshID: callback = SaveStingrayMesh
        if self.TypeID == TexID: callback = SaveStingrayTexture
        if self.TypeID == MaterialID: callback = SaveStingrayMaterial
        if callback == None: raise Exception("Save Callback could not be found")
        
        if self.IsLoaded:
            data = callback(self.FileID, self.TocData, self.GpuData, self.StreamData, self.LoadedData)
            self.SetData(data[0], data[1], data[2])

# ------------------------- #
# -- Toc File Type Entry -- #

class TocFileType:
    def __init__(self, ID=0, NumFiles=0):
        self.unk1     = 0
        self.TypeID   = ID
        self.NumFiles = NumFiles
        self.unk2     = 16
        self.unk3     = 64
    def Serialize(self, TocFile):
        self.unk1     = TocFile.uint64(self.unk1)
        self.TypeID   = TocFile.uint64(self.TypeID)
        self.NumFiles = TocFile.uint64(self.NumFiles)
        self.unk2     = TocFile.uint32(self.unk2)
        self.unk3     = TocFile.uint32(self.unk3)
        return self


# --------------------------- #
# -- Stream Toc File Class -- #
 
class StreamToc:
    def __init__(self):
        self.magic      = self.numTypes = self.numFiles = self.unknown = 0
        self.unk4Data   = bytearray(56)
        self.TocTypes   = []
        self.TocEntries = []
        self.Path = ""
        self.Name = ""
        
    def Serialize(self, SerializeData=True):
        # Create Toc Types Structs
        if self.TocFile.IsWriting():
            self.UpdateTypes()    
        # Begin Serializing file
        self.magic      = self.TocFile.uint32(self.magic)
        if self.magic != 4026531857: return False
        
        self.numTypes   = self.TocFile.uint32(len(self.TocTypes))
        self.numFiles   = self.TocFile.uint32(len(self.TocEntries))
        self.unknown    = self.TocFile.uint32(self.unknown)
        self.unk4Data   = self.TocFile.bytes(self.unk4Data, 56)

        if self.TocFile.IsReading():
            self.TocTypes   = [TocFileType() for n in range(self.numTypes)]
            self.TocEntries = [TocEntry() for n in range(self.numFiles)]
        # serialize Entries in correct order 
        self.TocTypes   = [Entry.Serialize(self.TocFile) for Entry in self.TocTypes]
        TocEntryStart   = self.TocFile.tell()
        if self.TocFile.IsReading(): self.TocEntries = [Entry.Serialize(self.TocFile) for Entry in self.TocEntries]
        else:
            Index = 1
            for Type in self.TocTypes:
                for Entry in self.TocEntries:
                    if Entry.TypeID == Type.TypeID:
                        Entry.Serialize(self.TocFile, Index)
                        Index += 1
    
        # Serialize Data
        if SerializeData:
            for FileEntry in self.TocEntries:
                FileEntry.SerializeData(self.TocFile, self.GpuFile, self.StreamFile)
        
        # re-write toc entry info with updated offsets
        if self.TocFile.IsWriting():
            self.TocFile.seek(TocEntryStart)
            Index = 1
            for Type in self.TocTypes:
                for Entry in self.TocEntries:
                    if Entry.TypeID == Type.TypeID:
                        Entry.Serialize(self.TocFile, Index)
                        Index += 1
        return True
    
    def UpdateTypes(self):
        self.TocTypes = []
        for Entry in self.TocEntries:
            exists = False
            for Type in self.TocTypes:
                if Type.TypeID == Entry.TypeID:
                    Type.NumFiles += 1; exists = True
                    break
            if not exists:
                self.TocTypes.append(TocFileType(Entry.TypeID, 1))
   
    def UpdatePath(self, path):
        self.Path = path
        self.Name = Path(path).name
        
    def FromFile(self, path, SerializeData=True):
        self.UpdatePath(path)
        with open(path, 'r+b') as f:
            self.TocFile = MemoryStream(f.read())
        
        self.GpuFile    = MemoryStream()
        self.StreamFile = MemoryStream()
        if SerializeData:
            if os.path.isfile(path+".gpu_resources"):
                with open(path+".gpu_resources", 'r+b') as f:
                    self.GpuFile = MemoryStream(f.read())
            if os.path.isfile(path+".stream"):
                with open(path+".stream", 'r+b') as f:
                    self.StreamFile = MemoryStream(f.read())
        return self.Serialize(SerializeData)
    
    def ToFile(self, path=None):
        self.TocFile = MemoryStream(IOMode = "write")
        self.GpuFile = MemoryStream(IOMode = "write")
        self.StreamFile = MemoryStream(IOMode = "write")
        self.Serialize()
        if path == None: path = self.Path
        
        with open(path, 'w+b') as f:
            f.write(bytes(self.TocFile.Data))
        with open(path+".gpu_resources", 'w+b') as f:
            f.write(bytes(self.GpuFile.Data))
        with open(path+".stream", 'w+b') as f:
            f.write(bytes(self.StreamFile.Data))
            
    def GetFileData(self, FileID, TypeID):
        for FileEntry in self.TocEntries:
            if FileEntry.FileID == FileID and FileEntry.TypeID == TypeID:
                return FileEntry.GetData()
        return None
    def GetEntry(self, FileID, TypeID):
        for Entry in self.TocEntries:
            if Entry.FileID == int(FileID) and Entry.TypeID == TypeID:
                return Entry
        return None
    def AddEntry(self, NewEntry):
        if self.GetEntry(NewEntry.FileID, NewEntry.TypeID) != None:
            raise Exception("Entry with same ID already exists")
        self.TocEntries.append(NewEntry)
        self.UpdateTypes()
    def RemoveEntry(self, FileID, TypeID):
        Entry = self.GetEntry(FileID, TypeID)
        if Entry != None:
            self.TocEntries.remove(Entry)
            self.UpdateTypes()

# ------------------------------ #
# -- Stream Toc Manager Class -- #
class TocManager():
    def __init__(self):
        self.SearchArchives  = []
        self.LoadedArchives  = []
        self.ActiveArchive   = None
        self.Patches         = []
        self.ActivePatch     = None
        
        self.CopyBuffer      = []
        self.SelectedEntries = []
        self.DrawChain       = []
        self.LastSelected = None # Last Entry Manually Selected
        self.SavedFriendlyNames   = []
        self.SavedFriendlyNameIDs = []
    #________________________________#
    # ---- Entry Selection Code ---- #
    def SelectEntries(self, Entries, Append=False):
        if not Append: self.DeselectAll()
        if len(Entries) == 1:
            Global_TocManager.LastSelected = Entries[0]
        
        for Entry in Entries:
            if Entry not in self.SelectedEntries:
                Entry.IsSelected = True
                self.SelectedEntries.append(Entry)
    def DeselectEntries(self, Entries):
        for Entry in Entries:
            Entry.IsSelected = False
            if Entry in self.SelectedEntries:
                self.SelectedEntries.remove(Entry)
    def DeselectAll(self):
        for Entry in self.SelectedEntries:
            Entry.IsSelected = False
        self.SelectedEntries = []
        self.LastSelected = None
    
    #________________________#
    # ---- Archive Code ---- #
    def LoadArchive(self, path, SetActive=True, IsPatch=False):
        # TODO: Add error if IsPatch is true but the path is not to a patch
        
        for Archive in self.LoadedArchives:
            if Archive.Path == path:
                return Archive
        toc = StreamToc()
        toc.FromFile(path)
        if SetActive and not IsPatch:
            self.LoadedArchives.append(toc)
            self.ActiveArchive = toc
        elif SetActive and IsPatch:
            self.Patches.append(toc)
            self.ActivePatch = toc
        
        # Get search archives
        if len(self.SearchArchives) == 0:
            for root, dirs, files in os.walk(Path(path).parent):
                for name in files:
                    if Path(name).suffix == "":
                        search_toc = StreamToc()
                        success = search_toc.FromFile(os.path.join(root, name), False)
                        if success:
                            self.SearchArchives.append(search_toc)

        return toc
    
    def UnloadArchives(self):
        # TODO: Make sure all data gets unloaded...
        # some how memory can still be too high after calling this
        self.LoadedArchives = []
        self.ActiveArchive  = None
        self.SearchArchives = []
    
    def SetActive(self, Archive):
        if Archive != self.ActiveArchive:
            self.ActiveArchive = Archive
            self.DeselectAll()
        
    def SetActiveByName(self, Name):
        for Archive in self.LoadedArchives:
            if Archive.Name == Name:
                self.SetActive(Archive)
    
    #______________________#
    # ---- Entry Code ---- #
    def GetEntry(self, FileID, TypeID, SearchAll=False, IgnorePatch=False):
        # Check Active Patch
        if not IgnorePatch and self.ActivePatch != None:
            Entry = self.ActivePatch.GetEntry(FileID, TypeID)
            if Entry != None:
                return Entry
        # Check Active Archive
        if self.ActiveArchive != None:
            Entry = self.ActiveArchive.GetEntry(FileID, TypeID)
            if Entry != None:
                return Entry
        # Check All Loaded Archives
        for Archive in self.LoadedArchives:
            Entry = Archive.GetEntry(FileID, TypeID)
            if Entry != None:
                return Entry
        # Check All Search Archives
        if SearchAll:
            for Archive in self.SearchArchives:
                Entry = Archive.GetEntry(FileID, TypeID)
                if Entry != None:
                    return self.LoadArchive(Archive.Path, False).GetEntry(FileID, TypeID)
        return None
        
    def Load(self, FileID, TypeID, Reload=False, SearchAll=False):
        Entry = self.GetEntry(FileID, TypeID, SearchAll)
        if Entry != None: Entry.Load(Reload)
    def Save(self, FileID, TypeID):
        Entry = self.GetEntry(FileID, TypeID)
        if not Global_TocManager.IsInPatch(Entry):
            Entry = self.AddEntryToPatch(FileID, TypeID)
        
        if Entry != None: Entry.Save()
    
    def CopyPaste(self, Entry, GenID = False, NewID = None):
        if self.ActivePatch == None:
            raise Exception("No patch exists, please create one first")
        if self.ActivePatch:
            dup = copy.deepcopy(Entry)
            dup.IsCreated = True
            if self.ActivePatch.GetEntry(dup.FileID, dup.TypeID) != None and DEVBUILD and NewID == None:
                GenID = True
            if GenID and NewID == None: dup.FileID = r.randint(1, 0xffffffffffffffff)
            if NewID != None:
                dup.FileID = NewID
                
            self.ActivePatch.AddEntry(dup)
    def Copy(self, Entries):
        self.CopyBuffer = []
        for Entry in Entries:
            if Entry != None: self.CopyBuffer.append(Entry)
    def Paste(self, GenID = False, NewID = None):
        if self.ActivePatch == None:
            raise Exception("No patch exists, please create one first")
        if self.ActivePatch:
            for ToCopy in self.CopyBuffer:
                self.CopyPaste(ToCopy, GenID, NewID)
            self.CopyBuffer = []
            
    def ClearClipboard(self):
        self.CopyBuffer = []
    
    #______________________#
    # ---- Patch Code ---- #
    def PatchActiveArchive(self):
        self.ActivePatch.ToFile()
        
    def CreatePatchFromActive(self):
        if self.ActiveArchive == None:
            raise Exception("No Archive exists to create patch from, please open one first")
            
        self.ActivePatch = copy.deepcopy(self.ActiveArchive)
        self.ActivePatch.TocEntries  = []
        self.ActivePatch.TocTypes    = []
        # TODO: ask for which patch index
        path = self.ActiveArchive.Path
        if path.find(".patch_") != -1:
            num = int(path[path.find(".patch_")+len(".patch_"):]) + 1
            path = path[:path.find(".patch_")] + ".patch_" + str(num)
        else:
            path += ".patch_0"
        self.ActivePatch.UpdatePath(path)
        self.Patches.append(self.ActivePatch)
        
    def SetActivePatch(self, Patch):
        self.ActivePatch = Patch
        
    def SetActivePatchByName(self, Name):
        for Patch in self.Patches:
            if Patch.Name == Name:
                self.SetActivePatch(Patch)
              
    def AddNewEntryToPatch(self, Entry):
        if self.ActivePatch == None:
            raise Exception("No patch exists, please create one first")
        self.ActivePatch.AddEntry(Entry)
    
    def AddEntryToPatch(self, FileID, TypeID):
        if self.ActivePatch == None:
            raise Exception("No patch exists, please create one first")
        
        Entry = self.GetEntry(FileID, TypeID)
        if Entry != None:
            PatchEntry = copy.deepcopy(Entry)
            if PatchEntry.IsSelected:
                self.SelectEntries([PatchEntry], True)
            self.ActivePatch.AddEntry(PatchEntry)
            return PatchEntry
        return None
    
    def RemoveEntryFromPatch(self, FileID, TypeID):
        if self.ActivePatch != None:
            self.ActivePatch.RemoveEntry(FileID, TypeID)
        return None
    
    def GetPatchEntry(self, Entry):
        if self.ActivePatch != None:
            return self.ActivePatch.GetEntry(Entry.FileID, Entry.TypeID)
        return None
    def GetPatchEntry_B(self, FileID, TypeID):
        if self.ActivePatch != None:
            return self.ActivePatch.GetEntry(FileID, TypeID)
        return None
    
    def IsInPatch(self, Entry):
        if self.ActivePatch != None:
            PatchEntry = self.ActivePatch.GetEntry(Entry.FileID, Entry.TypeID)
            if PatchEntry != None: return True
            else: return False
        return False
    
    def DuplicateEntry(self, FileID, TypeID, NewID):
        Entry = self.GetEntry(FileID, TypeID)
        if Entry != None:
            self.CopyPaste(Entry, False, NewID)
            
                
Global_TocManager = TocManager()

# load archive button
class LoadArchiveOperator(Operator, ImportHelper):
    bl_label = "Load Archive"
    bl_idname = "helldiver2.archive_import"
    filter_glob: StringProperty(
    default='*',
    options={'HIDDEN'}
    )
    is_patch: BoolProperty(name="is_patch", default=False)
    def execute(self, context):
        global Global_TocManager
        Global_TocManager.LoadArchive(self.filepath, True, self.is_patch)
        return{'FINISHED'}
    
# load archive button
class LoadArchivesOperator(Operator):
    bl_label = "Load Archives"
    bl_idname = "helldiver2.archives_import"
    
    paths_str: StringProperty(name="paths_str")
    def execute(self, context):
        global Global_TocManager
        paths = self.paths_str.split(',')
        for path in paths:
            if path != "" and os.path.exists(path):
                Global_TocManager.LoadArchive(path)
        self.paths = []
        return{'FINISHED'}

# patch archive button
class PatchArchiveOperator(Operator):
    bl_label = "Patch Archive"
    bl_idname = "helldiver2.archive_export"
    
    def execute(self, context):
        global Global_TocManager
        Global_TocManager.PatchActiveArchive()
        return{'FINISHED'}
    
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
                with open(self.directory + FileName, 'w+b') as f:
                    f.write(data[0])
                if data[1] != b"":
                    with open(self.directory + FileName+".gpu", 'w+b') as f:
                        f.write(data[1])
                if data[2] != b"":
                    with open(self.directory + FileName+".stream", 'w+b') as f:
                        f.write(data[2])
        return{'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

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
        return{'FINISHED'}
    
# copy entry
class CopyArchiveEntryOperator(Operator):
    bl_label = "Copy Entry"
    bl_idname = "helldiver2.archive_copy"
    
    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Entries = EntriesFromStrings(self.object_id, self.object_typeid)
        Global_TocManager.Copy(Entries)
        return{'FINISHED'}

# paste entry
class PasteArchiveEntryOperator(Operator):
    bl_label = "Paste Entry"
    bl_idname = "helldiver2.archive_paste"
    
    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Global_TocManager.Paste()
        return{'FINISHED'}
    
# clear clipboard
class ClearClipboardOperator(Operator):
    bl_label = "Clear Clipboard"
    bl_idname = "helldiver2.archive_clearclipboard"
    
    def execute(self, context):
        Global_TocManager.ClearClipboard()
        return{'FINISHED'}
    
# unload all archives
class UnloadArchivesOperator(Operator):
    bl_label = "Unload Archives"
    bl_idname = "helldiver2.archive_unloadall"
    
    def execute(self, context):
        Global_TocManager.UnloadArchives()
        return{'FINISHED'}
  
# create patch  
class CreatePatchFromActiveOperator(Operator):
    bl_label = "Create Patch"
    bl_idname = "helldiver2.archive_createpatch"
    
    def execute(self, context):
        Global_TocManager.CreatePatchFromActive()
        return{'FINISHED'}
    
# add entry to patch  
class AddEntryToPatchOperator(Operator):
    bl_label = "Add Entry To Patch"
    bl_idname = "helldiver2.archive_addtopatch"
    
    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Entries = EntriesFromStrings(self.object_id, self.object_typeid)
        for Entry in Entries:
            Global_TocManager.AddEntryToPatch(Entry.FileID, Entry.TypeID)
        return{'FINISHED'}
    
# remove entry from patch 
class RemoveEntryFromPatchOperator(Operator):
    bl_label = "Remove Entry From Patch"
    bl_idname = "helldiver2.archive_removefrompatch"
    
    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Entries = EntriesFromStrings(self.object_id, self.object_typeid)
        for Entry in Entries:
            Global_TocManager.RemoveEntryFromPatch(Entry.FileID, Entry.TypeID)
        return{'FINISHED'}
    
# rename entry in patch 
class RenamePatchEntryOperator(Operator):
    bl_label = "Rename Entry"
    bl_idname = "helldiver2.archive_entryrename"
    
    NewFileID : StringProperty(name="NewFileID", default="")
    def draw(self, context):
        layout = self.layout; row = layout.row()
        row.prop(self, "NewFileID", icon='COPY_ID')
    
    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Entry = Global_TocManager.GetPatchEntry_B(int(self.object_id), int(self.object_typeid))
        if Entry == None:
            raise Exception("Entry does not exist in patch (cannot rename non patch entries)")
        if Entry != None and self.NewFileID != "":
            Entry.FileID = int(self.NewFileID)
        return{'FINISHED'}
    
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
        row.prop(self, "NewFileID", icon='COPY_ID')
    
    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        Global_TocManager.DuplicateEntry(int(self.object_id), int(self.object_typeid), int(self.NewFileID))
        return{'FINISHED'}
    
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
        row.prop(self, "NewFriendlyName", icon='COPY_ID')
        row = layout.row()
        if Hash64(str(self.NewFriendlyName)) == int(self.object_id):
            row.label(text="Hash is correct")
        else:
            row.label(text="Hash is incorrect")
        row.label(text=str(Hash64(str(self.NewFriendlyName))))
    
    object_id: StringProperty()
    def execute(self, context):
        AddFriendlyName(int(self.object_id), str(self.NewFriendlyName))
        return{'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
#######################################################
#### ---- Stingray Material Classes/Functions ---- ####
#######################################################

# -------------------- #
# -- Material Class -- #
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
        
# ------------------------ #
# -- Material Functions -- #
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
            Entry = TocEntry()
            Entry.FileID = r.randint(1, 0xffffffffffffffff)
            Entry.TypeID = TexID
            Entry.IsCreated = True
            Entry.SetData(Toc.Data, Gpu.Data, Stream.Data, False)
            Global_TocManager.AddNewEntryToPatch(Entry)
            mat.TexIDs[TexIdx] = Entry.FileID
        else:
            Global_TocManager.Load(int(mat.TexIDs[TexIdx]), TexID, False, True)
            Entry = Global_TocManager.GetEntry(int(mat.TexIDs[TexIdx]), TexID, True)
            if Entry != None:
                Entry = copy.deepcopy(Entry)
                Entry.FileID = r.randint(1, 0xffffffffffffffff)
                Entry.IsCreated = True
                Global_TocManager.AddNewEntryToPatch(Entry)
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
        except: Global_TocManager.Load(TextureID, TexID, False, True)
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
        
class ImportMaterialOperator(Operator):
    bl_label = "Import Material"
    bl_idname = "helldiver2.material_import"
    
    object_id: StringProperty()
    def execute(self, context):
        EntriesIDs = IDsFromString(self.object_id)
        for EntryID in EntriesIDs:
            Global_TocManager.Load(int(EntryID), MaterialID)
        return{'FINISHED'}
    
class AddMaterialOperator(Operator):
    bl_label = "Add Material"
    bl_idname = "helldiver2.material_add"
    
    def execute(self, context):
        Entry = TocEntry()
        Entry.FileID = r.randint(1, 0xffffffffffffffff)
        Entry.TypeID = MaterialID
        Entry.IsCreated = True
        with open(Global_defaultmaterialpath, 'r+b') as f:
            data = f.read()
        Entry.TocData_OLD   = data
        Entry.TocData       = data
        
        Global_TocManager.AddNewEntryToPatch(Entry)
        return{'FINISHED'}

class SaveMaterialOperator(Operator):
    bl_label = "Save Material"
    bl_idname = "helldiver2.material_save"
    
    object_id: StringProperty()
    def execute(self, context):
        EntriesIDs = IDsFromString(self.object_id)
        for EntryID in EntriesIDs:
            Global_TocManager.Save(int(EntryID), MaterialID)
        return{'FINISHED'}
    
class ShowMaterialEditorOperator(Operator):
    bl_label = "Show Material Editor"
    bl_idname = "helldiver2.material_showeditor"
    
    object_id: StringProperty()
    def execute(self, context):
        Entry = Global_TocManager.GetEntry(int(self.object_id), MaterialID)
        if Entry != None:
            if not Entry.IsLoaded: Entry.Load(False, False)
            mat = Entry.LoadedData
            if mat.DEV_ShowEditor:
                print("MakeFalse")
                mat.DEV_ShowEditor = False
            else:
                print("MakeTrue")
                mat.DEV_ShowEditor = True
        return{'FINISHED'}
    
class SetMaterialTexture(Operator, ImportHelper):
    bl_label = "Set Material Texture"
    bl_idname = "helldiver2.material_settex"
    
    object_id: StringProperty()
    tex_idx: IntProperty()
    def execute(self, context):
        if self.filepath[-3:] != "dds":
            raise Exception("file must be dds")
        
        Entry = Global_TocManager.GetEntry(int(self.object_id), MaterialID)
        if Entry != None:
            if Entry.IsLoaded:
                Entry.LoadedData.DEV_DDSPaths[self.tex_idx] = self.filepath
        return{'FINISHED'}
    
def DrawMaterialEditor(Entry, layout, row):
    row.operator("helldiver2.material_showeditor", icon='MOD_LINEART', text="").object_id = str(Entry.FileID)
    if Entry.IsLoaded:
        mat = Entry.LoadedData
        if mat.DEV_ShowEditor:
            for TexIndex in range(len(mat.TexIDs)):
                row = layout.row()
                row.separator(); row.separator(); row.separator()
                if mat.DEV_DDSPaths[TexIndex] != None:
                    row.label(text=mat.DEV_DDSPaths[TexIndex], icon='FILE_IMAGE')
                else:
                    textstr = str(mat.TexIDs[TexIndex])
                    if mat.TexIDs[TexIndex] == 14423187101809176546: textstr += ": color"
                    if mat.TexIDs[TexIndex] == 12451968300768537108: textstr += ": sss color"
                    if mat.TexIDs[TexIndex] == 16331558339684530227: textstr += ": pbr"
                    if mat.TexIDs[TexIndex] == 6363549403025827661: textstr += ": normal"
                    row.label(text=textstr, icon='FILE_IMAGE')
                props = row.operator("helldiver2.material_settex", icon='FILEBROWSER', text="")
                props.object_id = str(Entry.FileID)
                props.tex_idx   = TexIndex
    
######################################################
#### ---- Stingray Texture Classes/Functions ---- ####
######################################################
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
        path = tempdir + "\\" + str(ID) + ".dds";
        tga_path = tempdir + "\\" + str(ID) + ".tga";
        with open(path, 'w+b') as f:
            f.write(dds)
        
        # convert to dds, as blender does not support these version of dds
        subprocess.run("\""+Global_texconvpath +"\" " + path + " -ft tga -f R8G8B8A8_UNORM -o \""+tempdir+"\"")
        #subprocess.run("\""+Global_texconvpath +"\" " + path + " -ft tif -o \""+tempdir+"\"") 
        
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
            raise Exception("Failed to convert tex "+str(ID)+" dds to tga, or dds failed to export")
    return StingrayTex

def BlendImageToStingrayTexture(image, StingrayTex):
    tempdir  = tempfile.gettempdir()
    dds_path = tempdir + "\\" + "blender_img" + ".dds";
    tga_path = tempdir + "\\" + "blender_img" + ".tga";
    image.file_format = 'TARGA_RAW'
    image.filepath_raw = tga_path
    image.save()
    command = f"\"{Global_texconvpath}\" \"{tga_path}\" -ft dds -dx10 -f {StingrayTex.Format} -o \"{tempdir}\""
    print(command)
    subprocess.run(command)
    max_wait_s = 5
    start = time.time()
    while time.time() - start < max_wait_s:
        if os.path.isfile(dds_path):
            break
    if os.path.isfile(dds_path):
        with open(dds_path, 'r+b') as f:
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
    
# import texture from archive button
class ImportTextureOperator(Operator):
    bl_label = "Import Texture"
    bl_idname = "helldiver2.texture_import"
    
    object_id: StringProperty()
    def execute(self, context):
        EntriesIDs = IDsFromString(self.object_id)
        for EntryID in EntriesIDs:
            Global_TocManager.Load(int(EntryID), TexID)
        return{'FINISHED'}

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
            Entry = Global_TocManager.GetEntry(EntryID, TexID)
            if Entry != None:
                data = Entry.Load(False, False)
                with open(self.directory + str(Entry.FileID)+".dds", 'w+b') as f:
                    f.write(Entry.LoadedData.ToDDs())
        return{'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
      
# export texture to file
class ExportTextureOperator(Operator, ExportHelper):
    bl_label = "Export Texture"
    bl_idname = "helldiver2.texture_export"
    filename_ext = ".dds"
    
    object_id: StringProperty()
    def execute(self, context):
        Entry = Global_TocManager.GetEntry(int(self.object_id), TexID)
        if Entry != None:
            data = Entry.Load(False, False)
            with open(self.filepath, 'w+b') as f:
                f.write(Entry.LoadedData.ToDDs())
        return{'FINISHED'}

# save texture from blender to archive button
class SaveTextureFromBlendImageOperator(Operator):
    bl_label = "Save Texture"
    bl_idname = "helldiver2.texture_saveblendimage"
    
    object_id: StringProperty()
    def execute(self, context):
        Entries = EntriesFromString(self.object_id, TexID)
        for Entry in Entries:
            if Entry != None:
                if not Entry.IsLoaded: Entry.Load()
                #BlendImageToStingrayTexture(bpy.data.images[str(self.object_id)], Entry.LoadedData)
                try: BlendImageToStingrayTexture(bpy.data.images[str(self.object_id)], Entry.LoadedData)
                except: print("Saving Texture, but no blend texture was found, using original"); pass
                #TODO: allow the user to choose an image, instead of looking for one of the same name
            Global_TocManager.Save(Entry.FileID, TexID)
        return{'FINISHED'}
    
# import texture from archive button
class SaveTextureFromDDsOperator(Operator, ImportHelper):
    bl_label = "Save Texture"
    bl_idname = "helldiver2.texture_savefromdds"
    
    object_id: StringProperty()
    def execute(self, context):
        Entry = Global_TocManager.GetEntry(int(self.object_id), TexID)
        if Entry != None:
            if len(self.filepath) > 1:
                # get texture data
                Entry.Load()
                StingrayTex = Entry.LoadedData
                with open(self.filepath, 'r+b') as f:
                    StingrayTex.FromDDs(f.read())
                Toc = MemoryStream(IOMode="write")
                Gpu = MemoryStream(IOMode="write")
                Stream = MemoryStream(IOMode="write")
                StingrayTex.Serialize(Toc, Gpu, Stream)
                # add texture to entry
                Entry.SetData(Toc.Data, Gpu.Data, Stream.Data, False)
                
                Global_TocManager.Save(int(self.object_id), TexID)
        return{'FINISHED'}

####################################################
#### ---- Stingray Bones Classes/Functions ---- ####
####################################################
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
 
def LoadStingrayBones(ID, TocData, GpuData, StreamData, Reload, MakeBlendObject):
    StingrayBonesData = StingrayBones()
    StingrayBonesData.Serialize(MemoryStream(TocData))
    return StingrayBonesData

#############################################################
#### ---- Stingray Composite Mesh Classes/Functions ---- ####
#############################################################
class StingrayCompositeMesh:
    def __init__(self):
        self.unk1 = self.NumExternalMeshes = self.StreamInfoOffset = 0
        self.Unreversed = bytearray()
        self.NumStreams = 0
        self.StreamInfoArray = []
        self.StreamInfoOffsets = []
        self.StreamInfoUnk = []
        self.StreamInfoUnk2 = 0
        self.GpuData = None
    def Serialize(self, f, gpu):
        self.unk1               = f.uint64(self.unk1)
        self.NumExternalMeshes  = f.uint32(self.NumExternalMeshes)
        self.StreamInfoOffset   = f.uint32(self.StreamInfoOffset)
        if f.IsReading():
            self.Unreversed = bytearray(self.StreamInfoOffset-f.tell())
        self.Unreversed     = f.bytes(self.Unreversed)
        
        if f.IsReading(): f.seek(self.StreamInfoOffset)
        else: 
            f.seek(math.ceil(float(f.tell())/16)*16); self.StreamInfoOffset = f.tell()
        self.NumStreams = f.uint32(len(self.StreamInfoArray))
        if f.IsWriting():
            if not redo_offsets: self.StreamInfoOffsets = [0 for n in range(self.NumStreams)]
            self.StreamInfoUnk = [mesh_info.MeshID for mesh_info in self.MeshInfoArray[:self.NumStreams]]
        if f.IsReading():
            self.StreamInfoOffsets = [0 for n in range(self.NumStreams)]
            self.StreamInfoUnk     = [0 for n in range(self.NumStreams)]
            self.StreamInfoArray   = [StreamInfo() for n in range(self.NumStreams)]

        self.StreamInfoOffsets  = [f.uint32(Offset) for Offset in self.StreamInfoOffsets]
        self.StreamInfoUnk      = [f.uint32(Unk) for Unk in self.StreamInfoUnk]
        self.StreamInfoUnk2     = f.uint32(self.StreamInfoUnk2)
        for stream_idx in range(self.NumStreams):
            if f.IsReading(): f.seek(self.StreamInfoOffset + self.StreamInfoOffsets[stream_idx])
            else            : self.StreamInfoOffsets[stream_idx] = f.tell() - self.StreamInfoOffset
            self.StreamInfoArray[stream_idx] = self.StreamInfoArray[stream_idx].Serialize(f)
            
        self.GpuData = gpu
        return self
    
def LoadStingrayCompositeMesh(ID, TocData, GpuData, StreamData, Reload, MakeBlendObject):
    StingrayCompositeMeshData = StingrayCompositeMesh()
    StingrayCompositeMeshData.Serialize(MemoryStream(TocData), MemoryStream(GpuData))
    return StingrayCompositeMeshData

###################################################
#### ---- Stingray Mesh Classes/Functions ---- ####
###################################################

# --------------- #
# -- Matrix4x4 -- # https://help.autodesk.com/cloudhelp/ENU/Stingray-SDK-Help/engine_c/plugin__api__types_8h.html#line_89
class StingrayMatrix4x4:
    def __init__(self):
        self.v = [float(0)]*16
    def Serialize(self, f):
        self.v = [f.float32(value) for value in self.v]
        return self
    
# --------------- #
# -- Matrix3x3 -- # https://help.autodesk.com/cloudhelp/ENU/Stingray-SDK-Help/engine_c/plugin__api__types_8h.html#line_84
class StingrayMatrix3x3:
    def __init__(self):
        self.x = [0,0,0]
        self.y = [0,0,0]
        self.z = [0,0,0]
    def Serialize(self, f):
        self.x = f.vec3_float(self.x)
        self.y = f.vec3_float(self.x)
        self.z = f.vec3_float(self.x)
        return self
        
# ------------------------------ #
# -- Stingray Local Transform -- # https://help.autodesk.com/cloudhelp/ENU/Stingray-SDK-Help/engine_c/plugin__api__types_8h.html#line_100
class StingrayLocalTransform:
    def __init__(self):
        self.rot   = StingrayMatrix3x3()
        self.pos   = [0,0,0]
        self.scale = [1,1,1]
        self.dummy = 0 # Force 16 byte alignment
    def Serialize(self, f):
        self.rot    = self.rot.Serialize(f)
        self.pos    = f.vec3_float(self.pos)
        self.scale  = f.vec3_float(self.scale)
        self.dummy  = f.float32(self.dummy)
        return self
        
# -------------------- #
# -- Transform Info -- # READ ONLY
class TransformInfo:
    def __init__(self):
        self.NumTransforms = 0
        self.Transforms = []
    def Serialize(self, f):
        if f.IsWriting():
            raise Exception("This struct is read only (write not implemented)")
        self.NumTransforms = f.uint32(self.NumTransforms)
        f.seek(f.tell()+12)
        self.Transforms = [StingrayLocalTransform().Serialize(f) for n in range(self.NumTransforms)]

# ------------------------ #
# -- Customization Info -- # READ ONLY
class CustomizationInfo:
    def __init__(self):
        self.BodyType  = ""
        self.Slot      = ""
        self.Weight    = ""
        self.PieceType = ""
    def Serialize(self, f):
        if f.IsWriting():
            raise Exception("This struct is read only (write not implemented)")
        try: # TODO: fix this, this is basically completely wrong, this is generic user data, but for now this works
            f.seek(f.tell()+24)
            length = f.uint32(0)
            self.BodyType = bytes(f.bytes(b"", length)).replace(b"\x00", b"").decode()
            f.seek(f.tell()+12)
            length = f.uint32(0)
            self.Slot = bytes(f.bytes(b"", length)).replace(b"\x00", b"").decode()
            f.seek(f.tell()+12)
            length = f.uint32(0)
            self.Weight = bytes(f.bytes(b"", length)).replace(b"\x00", b"").decode()
            f.seek(f.tell()+12)
            length = f.uint32(0)
            self.PieceType = bytes(f.bytes(b"", length)).replace(b"\x00", b"").decode()
        except:
            self.BodyType  = ""
            self.Slot      = ""
            self.Weight    = ""
            self.PieceType = ""
            pass # tehee

# --------------------------------- #
# -- Stream Component Info Class -- #
class StreamComponentInfo:
    def __init__(self, type="position", format="float"):
        self.Type   = self.TypeFromName(type)
        self.Format = self.FormatFromName(format)
        self.Index   = 0
        self.Unknown = 0
    def Serialize(self, f):
        self.Type      = f.uint32(self.Type)
        self.Format    = f.uint32(self.Format)
        self.Index     = f.uint32(self.Index)
        self.Unknown   = f.uint64(self.Unknown)
        return self
    def TypeName(self):
        if   self.Type == 0: return "position"
        elif self.Type == 1: return "normal"
        elif self.Type == 2: return "tangent" # not confirmed
        elif self.Type == 3: return "bitangent" # not confirmed
        elif self.Type == 4: return "uv"
        elif self.Type == 5: return "color"
        elif self.Type == 6: return "bone_index"
        elif self.Type == 7: return "bone_weight"
        return "unknown"
    def TypeFromName(self, name):
        if   name == "position": return 0
        elif name == "normal":   return 1
        elif name == "tangent":  return 2
        elif name == "bitangent":return 3
        elif name == "uv":       return 4
        elif name == "color":    return 5
        elif name == "bone_index":  return 6
        elif name == "bone_weight": return 7
        return -1
    def FormatName(self):
        # check archive 9102938b4b2aef9d
        if   self.Format == 0:  return "float"
        elif self.Format == 1:  return "vec2_float"
        elif self.Format == 2:  return "vec3_float"
        elif self.Format == 4:  return "rgba_r8g8b8a8"
        elif self.Format == 20: return "vec4_uint32" # vec4_uint32 ??
        elif self.Format == 24: return "vec4_uint8"
        elif self.Format == 25: return "vec4_1010102"
        elif self.Format == 26: return "unk_normal"
        elif self.Format == 29: return "vec2_half"
        elif self.Format == 31: return "vec4_half" # found in archive 738130362c354ceb->8166218779455159235.mesh
        return "unknown"
    def FormatFromName(self, name):
        if   name == "float":         return 0
        elif name == "vec3_float":    return 2
        elif name == "rgba_r8g8b8a8": return 4
        elif name == "vec4_uint32": return 20 # unconfirmed
        elif name == "vec4_uint8":  return 24
        elif name == "vec4_1010102":  return 25
        elif name == "unk_normal":  return 26
        elif name == "vec2_half":   return 29
        elif name == "vec4_half":   return 31
        return -1
    def GetSize(self):
        if   self.Format == 0:  return 4
        elif self.Format == 2:  return 12
        elif self.Format == 4:  return 4
        elif self.Format == 20: return 16
        elif self.Format == 24: return 4
        elif self.Format == 25: return 4
        elif self.Format == 26: return 4
        elif self.Format == 29: return 4
        elif self.Format == 31: return 8
        raise Exception("Cannot get size of unknown vertex format: "+str(self.Format))
    def SerializeComponent(self, f, value):
        format  = self.FormatName()
        if format == "float":
            return f.float32(value)
        elif format == "vec2_float":
            return f.vec2_float(value)
        elif format == "vec3_float":
            return f.vec3_float(value)
        elif format == "rgba_r8g8b8a8":
            if f.IsReading():
                r = min(255, int(value[0]*255))
                g = min(255, int(value[1]*255))
                b = min(255, int(value[2]*255))
                a = min(255, int(value[3]*255))
                value = f.vec4_uint8([r,g,b,a])
            if f.IsWriting():
                value = f.vec4_uint8([r,g,b,a])
                value[0] = min(1, float(value[0]/255))
                value[1] = min(1, float(value[1]/255))
                value[2] = min(1, float(value[2]/255))
                value[3] = min(1, float(value[3]/255))
            return value
        elif format == "vec4_uint32": # unconfirmed
            return f.vec4_uint32(value)
        elif format == "vec4_uint8":
            return f.vec4_uint8(value)
        elif format == "vec4_1010102":
            if f.IsReading():
                value = TenBitUnsigned(f.uint32(0))
                value[3] = 0 # seems to be needed for weights
            else:
                f.uint32(MakeTenBitUnsigned(value))
            return value
        elif format == "unk_normal":
            if isinstance(value, int):
                return f.uint32(value)
            else:
                return f.uint32(0)
        elif format == "vec2_half":
            return f.vec2_half(value)
        elif format == "vec4_half":
            if isinstance(value, float):
                return f.vec4_half([value,value,value,value])
            else:
                return f.vec4_half(value)
        else:
            raise Exception("Cannot serialize unknown vertex format: "+str(self.Format))
            
# --------------------- #
# -- Bone Info Class -- #
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

# ----------------------- #
# -- Stream Info Class -- #
class StreamInfo:
    def __init__(self):
        self.Components = []
        self.ComponentInfoID = self.NumComponents = self.VertexBufferID = self.VertexBuffer_unk1 = self.NumVertices = self.VertexStride = self.VertexBuffer_unk2 = self.VertexBuffer_unk3 = 0
        self.IndexBufferID = self.IndexBuffer_unk1 = self.NumIndices = self.IndexBuffer_unk2 = self.IndexBuffer_unk3 = self.IndexBuffer_Type = self.VertexBufferOffset = self.VertexBufferSize = self.IndexBufferOffset = self.IndexBufferSize = 0
        self.VertexBufferOffset = self.VertexBufferSize = self.IndexBufferOffset = self.IndexBufferSize = 0
        self.UnkEndingBytes = bytearray(16)
        self.DEV_StreamInfoOffset    = self.DEV_ComponentInfoOffset = 0 # helper vars, not in file
    
    def Serialize(self, f):
        self.DEV_StreamInfoOffset = f.tell()
        self.ComponentInfoID = f.uint64(self.ComponentInfoID)
        self.DEV_ComponentInfoOffset = f.tell()
        f.seek(self.DEV_ComponentInfoOffset + 320)
        # vertex buffer info
        self.NumComponents      = f.uint64(len(self.Components))
        self.VertexBufferID     = f.uint64(self.VertexBufferID)
        self.VertexBuffer_unk1  = f.uint64(self.VertexBuffer_unk1)
        self.NumVertices        = f.uint32(self.NumVertices)
        self.VertexStride       = f.uint32(self.VertexStride)
        self.VertexBuffer_unk2  = f.uint64(self.VertexBuffer_unk2)
        self.VertexBuffer_unk3  = f.uint64(self.VertexBuffer_unk3)
        # index buffer info
        self.IndexBufferID      = f.uint64(self.IndexBufferID)
        self.IndexBuffer_unk1   = f.uint64(self.IndexBuffer_unk1)
        self.NumIndices         = f.uint32(self.NumIndices)
        self.IndexBuffer_Type   = f.uint32(self.IndexBuffer_Type)
        self.IndexBuffer_unk2   = f.uint64(self.IndexBuffer_unk2)
        self.IndexBuffer_unk3   = f.uint64(self.IndexBuffer_unk3)
        # offset info
        self.VertexBufferOffset = f.uint32(self.VertexBufferOffset)
        self.VertexBufferSize   = f.uint32(self.VertexBufferSize)
        self.IndexBufferOffset  = f.uint32(self.IndexBufferOffset)
        self.IndexBufferSize    = f.uint32(self.IndexBufferSize)
        # allign to 16
        self.UnkEndingBytes     = f.bytes(self.UnkEndingBytes, 16) # exact length is unknown
        EndOffset = math.ceil(float(f.tell())/16) * 16
        # component info
        f.seek(self.DEV_ComponentInfoOffset)
        if f.IsReading():
            self.Components = [StreamComponentInfo() for n in range(self.NumComponents)]
        self.Components = [Comp.Serialize(f) for Comp in self.Components]
        
        # return
        f.seek(EndOffset)
        return self

# ----------------------------- #
# -- Mesh Section Info Class -- #
class MeshSectionInfo:
    def __init__(self, ID=0):
        self.unk1 = self.VertexOffset=self.NumVertices=self.IndexOffset=self.NumIndices=self.unk2 = 0
        self.DEV_MeshInfoOffset=0 # helper var, not in file
        self.ID = ID
    def Serialize(self, f):
        self.DEV_MeshInfoOffset = f.tell()
        self.unk1           = f.uint32(self.unk1)
        self.VertexOffset   = f.uint32(self.VertexOffset)
        self.NumVertices    = f.uint32(self.NumVertices)
        self.IndexOffset    = f.uint32(self.IndexOffset)
        self.NumIndices     = f.uint32(self.NumIndices)
        self.unk2           = f.uint32(self.unk1)
        return self


# --------------------- #
# -- Mesh Info Class -- #
class MeshInfo:
    def __init__(self):
        self.unk1 = self.unk3 = self.unk4 = self.TransformIndex = self.LodIndex = self.StreamIndex = self.NumSections = self.unk7 = self.unk8 = self.unk9 = self.NumSections_unk = self.MeshID = 0
        self.unk2 = bytearray(32); self.unk6 = bytearray(40)
        self.SectionIDs = self.Sections = []
    def Serialize(self, f):
        self.unk1 = f.uint64(self.unk1)
        self.unk2 = f.bytes(self.unk2, 32)
        self.MeshID= f.uint32(self.MeshID)
        self.unk3 = f.uint32(self.unk3)
        self.TransformIndex = f.uint32(self.TransformIndex)
        self.unk4 = f.uint32(self.unk4)
        self.LodIndex       = f.int32(self.LodIndex)
        self.StreamIndex    = f.uint32(self.StreamIndex)
        self.unk6           = f.bytes(self.unk6, 40)
        self.NumSections_unk= f.uint32(len(self.Sections))
        self.unk7           = f.uint32(0x80)
        self.unk8           = f.uint64(self.unk8)
        self.NumSections    = f.uint32(len(self.Sections))
        self.unk9           = f.uint32(0x80+(len(self.Sections)*4))
        if f.IsReading(): self.SectionIDs  = [0 for n in range(self.NumSections)]
        else:             self.SectionIDs  = [section.ID for section in self.Sections]
        self.SectionIDs  = [f.uint32(ID) for ID in self.SectionIDs]
        if f.IsReading(): self.Sections    = [MeshSectionInfo(self.SectionIDs[n]) for n in range(self.NumSections)]
        self.Sections   = [Section.Serialize(f) for Section in self.Sections]
        return self
    def GetNumIndices(self):
        total = 0
        for section in self.Sections:
            total += section.NumIndices
        return total
    def GetNumVertices(self):
        return self.Sections[0].NumVertices


# ---------------- #
# -- Mesh Class -- #
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
                #self.ShortID = zlib.crc32(name.encode())
                self.ShortID = r.randint(1, 0xffffffff)
            except:
                raise Exception("Material name must be a number")

class RawMeshClass:
    def __init__(self):
        self.MeshInfoIndex = 0
        self.VertexPositions  = []
        self.VertexNormals    = []
        self.VertexTangents   = []
        self.VertexBiTangents = []
        self.VertexUVs        = []
        self.VertexColors     = []
        self.VertexBoneIndices= []
        self.VertexWeights    = []
        self.Indices          = []
        self.Materials        = []
        self.LodIndex         = -1
        self.MeshID           = 0
        self.DEV_Use32BitIndices = False
        self.DEV_BoneInfo      = None
        self.DEV_BoneInfoIndex = 0
        self.DEV_Transform     = None
    def IsPhysicsBody(self):
        IsPhysics = True
        for material in self.Materials:
            if material.MatID != material.DefaultMaterialName:
                IsPhysics = False
        return IsPhysics
    def IsLod(self):
        IsLod = True
        if self.LodIndex == 0 or self.LodIndex == -1:
            IsLod = False
        if self.IsPhysicsBody():
            IsLod = False
        return IsLod
        
    def InitBlank(self, numVertices, numIndices, numUVs, numBoneIndices):
        self.VertexPositions    = [[0,0,0] for n in range(numVertices)]
        self.VertexNormals      = [[0,0,0] for n in range(numVertices)]
        self.VertexTangents     = [[0,0,0] for n in range(numVertices)]
        self.VertexBiTangents   = [[0,0,0] for n in range(numVertices)]
        self.VertexColors       = [[0,0,0,0] for n in range(numVertices)]
        self.VertexWeights      = [[0,0,0,0] for n in range(numVertices)]
        self.Indices            = [[0,0,0] for n in range(int(numIndices/3))]
        for idx in range(numUVs):
            self.VertexUVs.append([[0,0] for n in range(numVertices)])
        for idx in range(numBoneIndices):
            self.VertexBoneIndices.append([[0,0,0,0] for n in range(numVertices)])
    def ReInitVerts(self, numVertices):
        self.VertexPositions    = [[0,0,0] for n in range(numVertices)]
        self.VertexNormals      = [[0,0,0] for n in range(numVertices)]
        self.VertexTangents     = [[0,0,0] for n in range(numVertices)]
        self.VertexBiTangents   = [[0,0,0] for n in range(numVertices)]
        self.VertexColors       = [[0,0,0,0] for n in range(numVertices)]
        self.VertexWeights      = [[0,0,0,0] for n in range(numVertices)]
        numVerts        = len(self.VertexUVs)
        numBoneIndices  = len(self.VertexBoneIndices)
        self.VertexUVs = []
        self.VertexBoneIndices = []
        for idx in range(numVerts):
            self.VertexUVs.append([[0,0] for n in range(numVertices)])
        for idx in range(numBoneIndices):
            self.VertexBoneIndices.append([[0,0,0,0] for n in range(numVertices)])
        
        
# ------------------------------ #
# -- Stingray Mesh File Class -- #
class StingrayMeshFile:
    def __init__(self):
        self.HeaderData1        = bytearray(28);  self.HeaderData2        = bytearray(20); self.UnReversedData1  = bytearray(); self.UnReversedData2    = bytearray()
        self.StreamInfoOffset   = self.EndingOffset = self.MeshInfoOffset = self.NumStreams = self.NumMeshes = self.EndingBytes = self.StreamInfoUnk2 = self.HeaderUnk = self.MaterialsOffset = self.NumMaterials = self.NumBoneInfo = self.BoneInfoOffset = 0
        self.StreamInfoOffsets  = self.StreamInfoUnk = self.StreamInfoArray = self.MeshInfoOffsets = self.MeshInfoUnk = self.MeshInfoArray = []
        self.CustomizationInfoOffset = self.UnkHeaderOffset1 = self.UnkHeaderOffset2 = self.TransformInfoOffset = self.UnkRef1 = self.BonesRef = self.CompositeRef = 0
        self.BoneInfoOffsets = self.BoneInfoArray = []
        self.RawMeshes = []
        self.SectionsIDs = []
        self.MaterialIDs = []
        self.DEV_MeshInfoMap = [] # Allows removing of meshes while mapping them to the original meshes
        self.CustomizationInfo = CustomizationInfo()
        self.TransformInfo     = TransformInfo()
        self.BoneNames = None
    # -- Serialize Mesh -- #
    def Serialize(self, f, gpu, redo_offsets = False):
        print("Serialize")
        if f.IsWriting() and not redo_offsets:
            
            # duplicate bone info sections if needed
            temp_boneinfos = [None for n in range(len(self.BoneInfoArray))]
            for Raw_Mesh in self.RawMeshes:
                idx         = Raw_Mesh.MeshInfoIndex
                Mesh_info   = self.MeshInfoArray[self.DEV_MeshInfoMap[idx]]
                if Mesh_info.LodIndex == -1:
                    continue
                RealBoneInfoIdx = Mesh_info.LodIndex
                BoneInfoIdx     = Raw_Mesh.DEV_BoneInfoIndex
                temp_boneinfos[RealBoneInfoIdx] = self.BoneInfoArray[BoneInfoIdx]
            self.BoneInfoArray = temp_boneinfos
            #_____________________________________________________________________________________________#
            # ---- Most of this code below is to allow removing meshes, which is no longer supported ---- #
            if False: # disabled for now
                # set correct number of streams
                final_streams = []
                for mesh in self.MeshInfoArray:
                    if self.StreamInfoArray[mesh.StreamIndex] not in final_streams:
                        final_streams.append(self.StreamInfoArray[mesh.StreamIndex])
                self.StreamInfoArray = final_streams
                # set correct number of bone infos
                if False: # disabled due to breaking the duplicate bone info method thing
                    final_boneinfos = []
                    for Raw_Mesh in self.RawMeshes:
                        BoneInfoIdx = Raw_Mesh.MeshInfoIndex
                        if self.BoneInfoArray[BoneInfoIdx] not in final_boneinfos:
                            final_boneinfos.append(self.BoneInfoArray[BoneInfoIdx])
                    self.BoneInfoArray = final_boneinfos
            
            #_______________________________________________#
            # ---- deal with setting up material stuff ---- #
            print("setting up materials: ")
            self.SectionsIDs = []
            self.MaterialIDs = []
            Order = 0xffffffff
            for Raw_Mesh in self.RawMeshes:
                if len(Raw_Mesh.Materials) == 0:
                    raise Exception("Mesh has no materials, but at least one is required")
                idx         = Raw_Mesh.MeshInfoIndex
                Mesh_info   = self.MeshInfoArray[self.DEV_MeshInfoMap[idx]]
                Mesh_info.Sections = []
                for Material in Raw_Mesh.Materials:
                    Section = MeshSectionInfo()
                    Section.ID          = int(Material.ShortID)
                    Section.NumIndices  = Material.NumIndices
                    Section.VertexOffset  = Order # | Used for ordering function
                    Section.IndexOffset   = Order # /
                    
                    # This doesnt do what it was intended to do
                    if Material.DEV_BoneInfoOverride != None:
                        print("Overriding Material Unknown Values")
                        Section.unk1 = Material.DEV_BoneInfoOverride
                        Section.unk2 = Material.DEV_BoneInfoOverride
                    else:
                        Section.unk1 = len(Mesh_info.Sections) # | dont know what these actually are, but this is usually correct it seems
                        Section.unk2 = len(Mesh_info.Sections) # /
                    
                    Mesh_info.Sections.append(Section)
                    Order -= 1
                    try: # if material ID uses the defualt material string it will throw an error, but thats fine as we dont want to include those ones anyway
                        #if int(Material.MatID) not in self.MaterialIDs:
                        self.MaterialIDs.append(int(Material.MatID))
                        self.SectionsIDs.append(int(Material.ShortID))
                    except:
                        pass

        # serialize file
        self.UnkRef1            = f.uint64(self.UnkRef1)
        self.BonesRef           = f.uint64(self.BonesRef)
        self.CompositeRef       = f.uint64(self.CompositeRef)
        self.HeaderData1        = f.bytes(self.HeaderData1, 28)
        self.TransformInfoOffset= f.uint32(self.TransformInfoOffset)
        self.HeaderData2        = f.bytes(self.HeaderData2, 20)
        self.CustomizationInfoOffset  = f.uint32(self.CustomizationInfoOffset)
        self.UnkHeaderOffset1   = f.uint32(self.UnkHeaderOffset1)
        self.UnkHeaderOffset2   = f.uint32(self.UnkHeaderOffset1)
        self.BoneInfoOffset     = f.uint32(self.BoneInfoOffset)
        self.StreamInfoOffset   = f.uint32(self.StreamInfoOffset)
        self.EndingOffset       = f.uint32(self.EndingOffset)
        self.MeshInfoOffset     = f.uint32(self.MeshInfoOffset)
        self.HeaderUnk          = f.uint64(self.HeaderUnk)
        self.MaterialsOffset    = f.uint32(self.MaterialsOffset)
        
        if f.IsReading() and self.MeshInfoOffset == 0:
            raise Exception("Unsuported Mesh Format (No geometry)")
            
        if f.IsReading() and (self.StreamInfoOffset == 0 and self.CompositeRef == 0):
            raise Exception("Unsuported Mesh Format (No buffer stream)")
        
        # Get composite file
        if f.IsReading() and self.CompositeRef != 0:
            Entry = Global_TocManager.GetEntry(self.CompositeRef, CompositeMeshID)
            if Entry != None:
                Global_TocManager.Load(Entry.FileID, Entry.TypeID)
                self.StreamInfoArray = Entry.LoadedData.StreamInfoArray
                gpu = Entry.LoadedData.GpuData
            else:
                raise Exception(f"Composite mesh file {self.CompositeRef} could not be found")
        
        # Get bones file
        if f.IsReading() and self.BonesRef != 0:
            Entry = Global_TocManager.GetEntry(self.BonesRef, Hash64("bones"))
            if Entry != None:
                Global_TocManager.Load(Entry.FileID, Entry.TypeID)
                self.BoneNames = Entry.LoadedData.Names
        
        # Get Customization data: READ ONLY
        if f.IsReading() and self.CustomizationInfoOffset > 0:
            loc = f.tell(); f.seek(self.CustomizationInfoOffset)
            self.CustomizationInfo.Serialize(f)
            f.seek(loc)
        # Get Transform data: READ ONLY
        if f.IsReading() and self.TransformInfoOffset > 0:
            loc = f.tell(); f.seek(self.TransformInfoOffset)
            self.TransformInfo.Serialize(f)
            f.seek(loc)
        
        # Unreversed data
        if f.IsReading():
            if self.BoneInfoOffset > 0:
                UnreversedData1Size = self.BoneInfoOffset-f.tell()
            elif self.StreamInfoOffset > 0:
                UnreversedData1Size = self.StreamInfoOffset-f.tell()
        else: UnreversedData1Size = len(self.UnReversedData1)
        self.UnReversedData1    = f.bytes(self.UnReversedData1, UnreversedData1Size)
        
        # Bone Info
        if f.IsReading(): f.seek(self.BoneInfoOffset)
        else            : self.BoneInfoOffset = f.tell()
        self.NumBoneInfo = f.uint32(len(self.BoneInfoArray))
        if f.IsWriting() and not redo_offsets:
            self.BoneInfoOffsets = [0 for n in range(self.NumBoneInfo)]
        if f.IsReading():
            self.BoneInfoOffsets = [0 for n in range(self.NumBoneInfo)]
            self.BoneInfoArray   = [BoneInfo() for n in range(self.NumBoneInfo)]
        self.BoneInfoOffsets    = [f.uint32(Offset) for Offset in self.BoneInfoOffsets]
        for boneinfo_idx in range(self.NumBoneInfo):
            end_offset = None
            if f.IsReading(): 
                f.seek(self.BoneInfoOffset + self.BoneInfoOffsets[boneinfo_idx])
                if boneinfo_idx+1 != self.NumBoneInfo:
                    end_offset = self.BoneInfoOffset + self.BoneInfoOffsets[boneinfo_idx+1]
                else:
                    end_offset = self.StreamInfoOffset
                    if self.StreamInfoOffset == 0:
                        end_offset = self.MeshInfoOffset
            else: 
                self.BoneInfoOffsets[boneinfo_idx] = f.tell() - self.BoneInfoOffset
            self.BoneInfoArray[boneinfo_idx] = self.BoneInfoArray[boneinfo_idx].Serialize(f, end_offset)
            
        # Stream Info
        if self.StreamInfoOffset != 0:
            if f.IsReading(): f.seek(self.StreamInfoOffset)
            else: 
                f.seek(math.ceil(float(f.tell())/16)*16); self.StreamInfoOffset = f.tell()
            self.NumStreams = f.uint32(len(self.StreamInfoArray))
            if f.IsWriting():
                if not redo_offsets: self.StreamInfoOffsets = [0 for n in range(self.NumStreams)]
                self.StreamInfoUnk = [mesh_info.MeshID for mesh_info in self.MeshInfoArray[:self.NumStreams]]
            if f.IsReading():
                self.StreamInfoOffsets = [0 for n in range(self.NumStreams)]
                self.StreamInfoUnk     = [0 for n in range(self.NumStreams)]
                self.StreamInfoArray   = [StreamInfo() for n in range(self.NumStreams)]

            self.StreamInfoOffsets  = [f.uint32(Offset) for Offset in self.StreamInfoOffsets]
            self.StreamInfoUnk      = [f.uint32(Unk) for Unk in self.StreamInfoUnk]
            self.StreamInfoUnk2     = f.uint32(self.StreamInfoUnk2)
            for stream_idx in range(self.NumStreams):
                if f.IsReading(): f.seek(self.StreamInfoOffset + self.StreamInfoOffsets[stream_idx])
                else            : self.StreamInfoOffsets[stream_idx] = f.tell() - self.StreamInfoOffset
                self.StreamInfoArray[stream_idx] = self.StreamInfoArray[stream_idx].Serialize(f)

        # Mesh Info
        if f.IsReading(): f.seek(self.MeshInfoOffset)
        else            : self.MeshInfoOffset = f.tell()
        self.NumMeshes = f.uint32(len(self.MeshInfoArray))

        if f.IsWriting(): 
            if not redo_offsets: self.MeshInfoOffsets = [0 for n in range(self.NumMeshes)]
            self.MeshInfoUnk = [mesh_info.MeshID for mesh_info in self.MeshInfoArray]
        if f.IsReading():
            self.MeshInfoOffsets = [0 for n in range(self.NumMeshes)]
            self.MeshInfoUnk     = [0 for n in range(self.NumMeshes)]
            self.MeshInfoArray   = [MeshInfo() for n in range(self.NumMeshes)]
            self.DEV_MeshInfoMap = [n for n in range(len(self.MeshInfoArray))]
            
        self.MeshInfoOffsets  = [f.uint32(Offset) for Offset in self.MeshInfoOffsets]
        self.MeshInfoUnk      = [f.uint32(Unk) for Unk in self.MeshInfoUnk]
        for mesh_idx in range(self.NumMeshes):
            if f.IsReading(): f.seek(self.MeshInfoOffset+self.MeshInfoOffsets[mesh_idx])
            else            : self.MeshInfoOffsets[mesh_idx] = f.tell() - self.MeshInfoOffset
            self.MeshInfoArray[mesh_idx] = self.MeshInfoArray[mesh_idx].Serialize(f)

        # Materials
        if f.IsReading(): f.seek(self.MaterialsOffset)
        else            : self.MaterialsOffset = f.tell()
        self.NumMaterials = f.uint32(len(self.MaterialIDs))
        if f.IsReading():
            self.SectionsIDs = [0 for n in range(self.NumMaterials)]
            self.MaterialIDs = [0 for n in range(self.NumMaterials)]
        self.SectionsIDs = [f.uint32(ID) for ID in self.SectionsIDs]
        self.MaterialIDs = [f.uint64(ID) for ID in self.MaterialIDs]
        
        # Unreversed Data
        if f.IsReading(): UnreversedData2Size = self.EndingOffset-f.tell()
        else: UnreversedData2Size = len(self.UnReversedData2)
        self.UnReversedData2    = f.bytes(self.UnReversedData2, UnreversedData2Size)
        if f.IsWriting(): self.EndingOffset = f.tell()
        self.EndingBytes        = f.uint64(self.NumMeshes)
        if redo_offsets:
            return self
        
        # Serialize Data
        self.SerializeGpuData(gpu);
        
        # TODO: update offsets only instead of re-writing entire file
        if f.IsWriting() and not redo_offsets:
            f.seek(0)
            self.Serialize(f, gpu, True)
        return self
    
    # -- Serialize GPU Data -- #
    def SerializeGpuData(self, gpu):
        print("SerializeGpuData")
        # Init Raw Meshes If Reading
        if gpu.IsReading():
            self.InitRawMeshes()
        # re-order the meshes to match the vertex order (this is mainly for writing)
        OrderedMeshes = self.CreateOrderedMeshList()
        # Create Vertex Components If Writing
        if gpu.IsWriting():
            self.SetupRawMeshComponents(OrderedMeshes)
        
        # Serialize Gpu Data
        for stream_idx in range(len(OrderedMeshes)):
            Stream_Info = self.StreamInfoArray[stream_idx]
            if gpu.IsReading():
                self.SerializeIndexBuffer(gpu, Stream_Info, stream_idx, OrderedMeshes)
                self.SerializeVertexBuffer(gpu, Stream_Info, stream_idx, OrderedMeshes)
            else:
                self.SerializeVertexBuffer(gpu, Stream_Info, stream_idx, OrderedMeshes)
                self.SerializeIndexBuffer(gpu, Stream_Info, stream_idx, OrderedMeshes)
            
    # -- Serialize GPU Data -- #
    def SerializeIndexBuffer(self, gpu, Stream_Info, stream_idx, OrderedMeshes):
        # get indices
        IndexOffset  = 0
        if gpu.IsWriting():Stream_Info.IndexBufferOffset = gpu.tell()
        for mesh in OrderedMeshes[stream_idx][1]:
            Mesh_Info = self.MeshInfoArray[self.DEV_MeshInfoMap[mesh.MeshInfoIndex]]
            # Lod Info
            if gpu.IsReading():
                mesh.LodIndex = Mesh_Info.LodIndex
                mesh.DEV_BoneInfoIndex = Mesh_Info.LodIndex
            # handle index formats
            IndexStride = 2
            IndexInt = gpu.uint16
            if Stream_Info.IndexBuffer_Type == 1:
                IndexStride = 4
                IndexInt = gpu.uint32
            
            TotalIndex = 0
            for Section in Mesh_Info.Sections:
                # Create mat info
                if gpu.IsReading():
                    mat = RawMaterialClass()
                    if Section.ID in self.SectionsIDs:
                        mat_idx = self.SectionsIDs.index(Section.ID)
                        mat.IDFromName(str(self.MaterialIDs[mat_idx]))
                        mat.MatID = str(self.MaterialIDs[mat_idx])
                        #mat.ShortID = self.SectionsIDs[mat_idx]
                        if bpy.context.scene.Hd2ToolPanelSettings.ImportMaterials:
                            Global_TocManager.Load(mat.MatID, MaterialID, False, True)
                        else:
                            AddMaterialToBlend_EMPTY(mat.MatID)
                    else:
                        try   : bpy.data.materials[mat.MatID]
                        except: bpy.data.materials.new(mat.MatID)
                    mat.StartIndex = TotalIndex*3
                    mat.NumIndices = Section.NumIndices
                    mesh.Materials.append(mat)
                
                if gpu.IsReading(): gpu.seek(Stream_Info.IndexBufferOffset + (Section.IndexOffset*IndexStride))
                else:
                    Section.IndexOffset = IndexOffset
                    print("Updated Section Offset: ", Section.IndexOffset)
                for fidx in range(int(Section.NumIndices/3)):
                    v1 = IndexInt(mesh.Indices[TotalIndex][0])
                    v2 = IndexInt(mesh.Indices[TotalIndex][1])
                    v3 = IndexInt(mesh.Indices[TotalIndex][2])
                    mesh.Indices[TotalIndex] = [v1, v2, v3]
                    TotalIndex += 1
                IndexOffset  += Section.NumIndices
        # update stream info
        if gpu.IsWriting():
            Stream_Info.IndexBufferSize    = gpu.tell() - Stream_Info.IndexBufferOffset
            Stream_Info.NumIndices         = IndexOffset
        
        # calculate correct vertex num (sometimes its wrong, no clue why, see 9102938b4b2aef9d->7040046837345593857)
        if gpu.IsReading():
            for mesh in OrderedMeshes[stream_idx][0]:
                RealNumVerts = 0
                for face in mesh.Indices:
                    for index in face:
                        if index > RealNumVerts:
                            RealNumVerts = index
                RealNumVerts += 1
                Mesh_Info = self.MeshInfoArray[self.DEV_MeshInfoMap[mesh.MeshInfoIndex]]
                if Mesh_Info.Sections[0].NumVertices != RealNumVerts:
                    for Section in Mesh_Info.Sections:
                        Section.NumVertices = RealNumVerts
                    self.ReInitRawMeshVerts() 

    # -- Serialize GPU Data -- #
    def SerializeVertexBuffer(self, gpu, Stream_Info, stream_idx, OrderedMeshes):
        # Vertex Buffer
        VertexOffset = 0
        if gpu.IsWriting(): Stream_Info.VertexBufferOffset = gpu.tell()
        for mesh in OrderedMeshes[stream_idx][0]:   
            Mesh_Info = self.MeshInfoArray[self.DEV_MeshInfoMap[mesh.MeshInfoIndex]]
            if gpu.IsWriting():
                for Section in Mesh_Info.Sections: 
                    Section.VertexOffset = VertexOffset
                    Section.NumVertices  = len(mesh.VertexPositions)
                    print("Updated VertexOffset Offset: ", Section.VertexOffset)
            MainSection = Mesh_Info.Sections[0]
            
            # get vertices
            if gpu.IsReading(): gpu.seek(Stream_Info.VertexBufferOffset + (MainSection.VertexOffset*Stream_Info.VertexStride)) 
            for vidx in range(len(mesh.VertexPositions)):
                vstart = gpu.tell()
                
                for Component in Stream_Info.Components:
                    type = Component.TypeName()
                    # Get Vertex Position
                    if type == "position":
                        pos = Component.SerializeComponent(gpu, mesh.VertexPositions[vidx])
                        mesh.VertexPositions[vidx] = pos[:3]
                    
                    # Get Vertex Normal
                    elif type == "normal":
                        norm = Component.SerializeComponent(gpu, mesh.VertexNormals[vidx])
                        if not isinstance(norm, int) and gpu.IsReading(): 
                            norm = list(mathutils.Vector((norm[0],norm[1],norm[2])).normalized())
                            mesh.VertexNormals[vidx] = norm[:3]
                        elif isinstance(norm, int):
                            mesh.VertexNormals[vidx] = norm
                    
                    # Tangents
                    elif type == "tangent":
                        tangent = Component.SerializeComponent(gpu, mesh.VertexTangents[vidx])
                        if tangent != None: mesh.VertexTangents[vidx] = tangent[:3]
                   
                    # BiTangents
                    elif type == "bitangent":
                        bitangent = Component.SerializeComponent(gpu, mesh.VertexBiTangents[vidx])
                        if bitangent != None: mesh.VertexBiTangents[vidx] = bitangent[:3]
                        
                    # Get Vertex UVs
                    elif type == "uv":
                        uv = Component.SerializeComponent(gpu, mesh.VertexUVs[Component.Index][vidx])
                        mesh.VertexUVs[Component.Index][vidx] = uv[:2]
                    
                    # Get Vertex Color
                    elif type == "color":
                        color = Component.SerializeComponent(gpu, mesh.VertexColors[vidx])
                        if color != None: mesh.VertexColors[vidx] = color[:4]
                    
                    # Get Bone Indices
                    elif type == "bone_index":
                        mesh.VertexBoneIndices[Component.Index][vidx] = Component.SerializeComponent(gpu, mesh.VertexBoneIndices[Component.Index][vidx])
                    
                    # Get Weights
                    elif type == "bone_weight":
                        if Component.Index > 0: # TODO: add support for this (check archive 9102938b4b2aef9d)
                            gpu.seek(gpu.tell()+Component.GetSize())
                            print("Multiple Weight Indices")
                        else:
                            mesh.VertexWeights[vidx] = Component.SerializeComponent(gpu, mesh.VertexWeights[vidx])
                    
                gpu.seek(vstart + Stream_Info.VertexStride)
            VertexOffset += len(mesh.VertexPositions)
        # update stream info
        if gpu.IsWriting():
            gpu.seek(math.ceil(float(gpu.tell())/16)*16)
            Stream_Info.VertexBufferSize    = gpu.tell() - Stream_Info.VertexBufferOffset
            Stream_Info.NumVertices         = VertexOffset
    
    # -- Helper Function -- #
    def CreateOrderedMeshList(self):
        # re-order the meshes to match the vertex order (this is mainly for writing)
        # man this code is ass, there has to be a better way to do this, but i am stupid af frfr no cap
        OrderedMeshes = [ [[], []] for n in range(len(self.StreamInfoArray))]
        VertOrderedMeshes_flat = []
        IndexOrderedMeshes_flat = []
        while len(VertOrderedMeshes_flat) != len(self.RawMeshes):
            smallest_vert_mesh = None
            smallest_index_mesh = None
            for mesh in self.RawMeshes:
                mesh_info   = self.MeshInfoArray[self.DEV_MeshInfoMap[mesh.MeshInfoIndex]]
                if mesh not in VertOrderedMeshes_flat:
                    if smallest_vert_mesh == None:
                        smallest_vert_mesh = mesh
                    else:
                        smallest_mesh_info   = self.MeshInfoArray[self.DEV_MeshInfoMap[smallest_vert_mesh.MeshInfoIndex]]
                        if mesh_info.Sections[0].VertexOffset < smallest_mesh_info.Sections[0].VertexOffset:
                            smallest_vert_mesh = mesh
                
                if mesh not in IndexOrderedMeshes_flat:
                    if smallest_index_mesh == None:
                        smallest_index_mesh = mesh
                    else:
                        smallest_mesh_info   = self.MeshInfoArray[self.DEV_MeshInfoMap[smallest_index_mesh.MeshInfoIndex]]
                        if mesh_info.Sections[0].IndexOffset < smallest_mesh_info.Sections[0].IndexOffset:
                            smallest_index_mesh = mesh
            mesh_info   = self.MeshInfoArray[self.DEV_MeshInfoMap[smallest_vert_mesh.MeshInfoIndex]]
            OrderedMeshes[mesh_info.StreamIndex][0].append(smallest_vert_mesh)
            mesh_info   = self.MeshInfoArray[self.DEV_MeshInfoMap[smallest_index_mesh.MeshInfoIndex]]
            OrderedMeshes[mesh_info.StreamIndex][1].append(smallest_index_mesh)
            VertOrderedMeshes_flat.append(smallest_vert_mesh)
            IndexOrderedMeshes_flat.append(smallest_index_mesh)
        
        # set 32 bit face indices if needed
        for stream_idx in range(len(OrderedMeshes)):
            Stream_Info = self.StreamInfoArray[stream_idx]
            for mesh in OrderedMeshes[stream_idx][0]:
                if mesh.DEV_Use32BitIndices:
                    Stream_Info.IndexBuffer_Type = 1
        return OrderedMeshes
    
    # -- Helper Function -- #
    def InitRawMeshes(self):
        for n in range(len(self.MeshInfoArray)):
            NewMesh     = RawMeshClass()
            Mesh_Info   = self.MeshInfoArray[n]
            print("Num: ", len(self.StreamInfoArray), " Index: ", Mesh_Info.StreamIndex)
            Stream_Info = self.StreamInfoArray[Mesh_Info.StreamIndex]
            NewMesh.MeshInfoIndex = n
            NewMesh.MeshID = Mesh_Info.MeshID
            NewMesh.DEV_Transform = self.TransformInfo.Transforms[Mesh_Info.TransformIndex]
            try:
                NewMesh.DEV_BoneInfo  = self.BoneInfoArray[Mesh_Info.LodIndex]
            except: pass
            numUVs          = 0
            numBoneIndices  = 0
            for component in Stream_Info.Components:
                if component.TypeName() == "uv":
                    numUVs += 1
                if component.TypeName() == "bone_index":
                    numBoneIndices += 1
            NewMesh.InitBlank(Mesh_Info.GetNumVertices(), Mesh_Info.GetNumIndices(), numUVs, numBoneIndices)
            self.RawMeshes.append(NewMesh)
    def ReInitRawMeshVerts(self):
        for mesh in self.RawMeshes:
            Mesh_Info = self.MeshInfoArray[self.DEV_MeshInfoMap[mesh.MeshInfoIndex]]
            mesh.ReInitVerts(Mesh_Info.GetNumVertices())
            
    # -- Helper Function -- #
    def SetupRawMeshComponents(self, OrderedMeshes):
        for stream_idx in range(len(OrderedMeshes)):
            Stream_Info = self.StreamInfoArray[stream_idx]
            
            HasPositions = False
            HasNormals   = False
            HasTangents  = False
            HasBiTangents= False
            IsSkinned    = False
            NumUVs       = 0
            NumBoneIndices = 0
            # get total number of components
            for mesh in OrderedMeshes[stream_idx][0]:
                if len(mesh.VertexPositions)  > 0: HasPositions  = True
                if len(mesh.VertexNormals)    > 0: HasNormals    = True
                if len(mesh.VertexTangents)   > 0: HasTangents   = True
                if len(mesh.VertexBiTangents) > 0: HasBiTangents = True
                if len(mesh.VertexBoneIndices)> 0: IsSkinned     = True
                if len(mesh.VertexUVs)   > NumUVs: NumUVs = len(mesh.VertexUVs)
                if len(mesh.VertexBoneIndices) > NumBoneIndices: NumBoneIndices = len(mesh.VertexBoneIndices)
            if NumUVs < 2 and bpy.context.scene.Hd2ToolPanelSettings.Force2UVs:
                NumUVs = 2
            if IsSkinned and NumBoneIndices > 1 and bpy.context.scene.Hd2ToolPanelSettings.Force1Group:
                NumBoneIndices = 1
            
            # fill default values for meshes which are missing some components
            for mesh in OrderedMeshes[stream_idx][0]:
                if not len(mesh.VertexPositions)  > 0:
                    raise Exception("bruh... your mesh doesn't have any vertices")
                if HasNormals and not len(mesh.VertexNormals)    > 0:
                    mesh.VertexNormals = [[0,0,0] for n in mesh.VertexPositions]
                if HasTangents and not len(mesh.VertexTangents)   > 0:
                    mesh.VertexTangents = [[0,0,0] for n in mesh.VertexPositions]
                if HasBiTangents and not len(mesh.VertexBiTangents) > 0:
                    mesh.VertexBiTangents = [[0,0,0] for n in mesh.VertexPositions]
                if IsSkinned and not len(mesh.VertexWeights) > 0:
                    mesh.VertexWeights      = [[0,0,0,0] for n in mesh.VertexPositions]
                    mesh.VertexBoneIndices  = [[[0,0,0,0] for n in mesh.VertexPositions]*NumBoneIndices]
                if IsSkinned and len(mesh.VertexBoneIndices) > NumBoneIndices:
                    mesh.VertexBoneIndices = mesh.VertexBoneIndices[::NumBoneIndices]
                if NumUVs > len(mesh.VertexUVs):
                    dif = NumUVs - len(mesh.VertexUVs)
                    for n in range(dif):
                        mesh.VertexUVs.append([[0,0] for n in mesh.VertexPositions])
            # make stream components
            Stream_Info.Components = []
            if HasPositions:  Stream_Info.Components.append(StreamComponentInfo("position", "vec3_float"))
            if HasNormals:    Stream_Info.Components.append(StreamComponentInfo("normal", "unk_normal"))
            #if HasBiTangents: Stream_Info.Components.append(StreamComponentInfo("bitangent", "vec4_half"))
            #if HasTangents:   Stream_Info.Components.append(StreamComponentInfo("tangent", "vec4_half"))
            for n in range(NumUVs):
                UVComponent = StreamComponentInfo("uv", "vec2_half")
                UVComponent.Index = n
                Stream_Info.Components.append(UVComponent)
            if IsSkinned:     Stream_Info.Components.append(StreamComponentInfo("bone_weight", "vec4_half"))
            for n in range(NumBoneIndices):
                BIComponent = StreamComponentInfo("bone_index", "vec4_uint8")
                BIComponent.Index = n
                Stream_Info.Components.append(BIComponent)
            # calculate Stride
            Stream_Info.VertexStride = 0
            for Component in Stream_Info.Components:
                Stream_Info.VertexStride += Component.GetSize()

# ------------------------- #
# -- Mesh Load Functions -- #

def LoadStingrayMesh(ID, TocData, GpuData, StreamData, Reload, MakeBlendObject):
    toc  = MemoryStream(TocData)
    gpu  = MemoryStream(GpuData)
    StingrayMesh = StingrayMeshFile().Serialize(toc, gpu)
    if MakeBlendObject: CreateModel(StingrayMesh.RawMeshes, str(ID), StingrayMesh.CustomizationInfo, StingrayMesh.BoneNames)
    return StingrayMesh

def SaveStingrayMesh(ID, TocData, GpuData, StreamData, StingrayMesh):
    model = GetObjectsMeshData()
    FinalMeshes = [mesh for mesh in StingrayMesh.RawMeshes]
    for mesh in model:
        for n in range(len(StingrayMesh.RawMeshes)):
            if StingrayMesh.RawMeshes[n].MeshInfoIndex == mesh.MeshInfoIndex:
                FinalMeshes[n] = mesh
    # Propagate lods
    if bpy.context.scene.Hd2ToolPanelSettings.AutoLods:
        lod0 = None
        for mesh in FinalMeshes:
            if mesh.LodIndex == 0:
                lod0 = mesh
        print(lod0)
        if lod0 != None:
            for n in range(len(FinalMeshes)):
                if FinalMeshes[n].IsLod():
                    newmesh = copy.deepcopy(lod0)
                    newmesh.MeshInfoIndex = FinalMeshes[n].MeshInfoIndex
                    FinalMeshes[n] = newmesh
        
    StingrayMesh.RawMeshes = FinalMeshes
    
    toc  = MemoryStream(IOMode = "write")
    gpu  = MemoryStream(IOMode = "write")
    StingrayMesh.Serialize(toc, gpu)
    return [toc.Data, gpu.Data, b""]
  
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
                Global_TocManager.Load(EntryID, MeshID)
            else:
                try:
                    Global_TocManager.Load(EntryID, MeshID)
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
        return{'FINISHED'}
                 
# save mesh to archive button
class SaveStingrayMeshOperator(Operator):
    bl_label  = "Save Mesh"
    bl_idname = "helldiver2.archive_mesh_save"
    
    object_id: StringProperty()
    def execute(self, context):
        Global_TocManager.Save(int(self.object_id), MeshID)
        return{'FINISHED'}
    
# batch save mesh to archive button
class BatchSaveStingrayMeshOperator(Operator):
    bl_label  = "Save Meshes"
    bl_idname = "helldiver2.archive_mesh_batchsave"
    
    def execute(self, context):
        objects = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
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
        
            Global_TocManager.Save(int(ID), MeshID)
        return{'FINISHED'}

######################################
#### ---- Archive Search GUI ---- ####
######################################

class SearchArchivesOperator(bpy.types.Operator):
    bl_label = "Search All Archives"
    bl_idname = "helldiver2.search_archives"

    SearchField : StringProperty(name="SearchField", default="")
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "SearchField", icon='VIEWZOOM')
        # Update displayed archives
        if self.PrevSearch != self.SearchField:
            self.PrevSearch = self.SearchField
            
            self.ArchivesToDisplay = []
            friendlysearches = []
            for hash_info in Global_NameHashes:
                Found = True
                for search in self.SearchField.split(" "):
                    if not (hash_info[1].find(search) != -1 and str(hash_info[0]) not in friendlysearches):
                        Found = False
                if Found:
                    friendlysearches.append(str(hash_info[0]))

            for Archive in Global_TocManager.SearchArchives:
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
            row.operator("helldiver2.archives_import", icon= 'FILE_NEW').paths_str = paths_str
        # Draw Display Archives
        for Archive in self.ArchivesToDisplay:
            row = layout.row()
            row.label(text=Archive[1], icon='FILE_ARCHIVE')
            row.operator("helldiver2.archives_import", icon= 'FILE_NEW', text="").paths_str = Archive[0].Path
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        self.PrevSearch = "NONE"
        self.ArchivesToDisplay = []
        
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

#######################################
#### ---- Extra GUI Functions ---- ####
#######################################

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
                DisplayEntry = Global_TocManager.GetEntry(Entry.FileID, Entry.TypeID)
                if DisplayEntry.IsSelected:
                    #Global_TocManager.DeselectEntries([Entry])
                    pass
                else:
                    Global_TocManager.SelectEntries([Entry], True)
        return{'FINISHED'}
    
# Copy Text
class CopyTextOperator(Operator):
    bl_label  = "Copy ID"
    bl_idname = "helldiver2.copytest"
    
    text: StringProperty()
    def execute(self, context):
        cmd='echo '+str(self.text).strip()+'|clip'
        subprocess.check_call(cmd, shell=True)
        return{'FINISHED'}

# Open documentation
class HelpOperator(Operator):
    bl_label  = "Help"
    bl_idname = "helldiver2.help"
    
    def execute(self, context):
        url = "https://docs.google.com/document/d/1SF7iEekmxoDdf0EsJu1ww9u2Cr8vzHyn2ycZS7JlWl0/edit#heading=h.gv4shgb4on0i"
        webbrowser.open(url, new=0, autoraise=True)
        return{'FINISHED'}

# Open Archive Spreadsheet
class ArchiveSpreadsheetOperator(Operator):
    bl_label  = "Archive Spreadsheet"
    bl_idname = "helldiver2.archive_spreadsheet"
    
    def execute(self, context):
        url = "https://docs.google.com/spreadsheets/d/1oQys_OI5DWou4GeRE3mW56j7BIi4M7KftBIPAl1ULFw"
        webbrowser.open(url, new=0, autoraise=True)
        return{'FINISHED'}

class ArchiveEntryOperator(Operator):
    bl_label  = "Archive Entry"
    bl_idname = "helldiver2.archive_entry"
    
    object_id: StringProperty()
    object_typeid: StringProperty()
    def execute(self, context):
        return{'FINISHED'}

    def invoke(self, context, event):
        Entry = Global_TocManager.GetEntry(int(self.object_id), int(self.object_typeid))
        if event.ctrl:
            if Entry.IsSelected:
                Global_TocManager.DeselectEntries([Entry])
            else:
                Global_TocManager.SelectEntries([Entry], True)
            return {'FINISHED'}
        if event.shift:
            if Global_TocManager.LastSelected != None:
                LastSelected = Global_TocManager.LastSelected
                StartIndex   = LastSelected.DEV_DrawIndex
                EndIndex     = Entry.DEV_DrawIndex
                Global_TocManager.DeselectAll()
                Global_TocManager.LastSelected = LastSelected
                if StartIndex > EndIndex:
                    Global_TocManager.SelectEntries(Global_TocManager.DrawChain[EndIndex:StartIndex+1], True)
                else:
                    Global_TocManager.SelectEntries(Global_TocManager.DrawChain[StartIndex:EndIndex+1], True)
            else:
                Global_TocManager.SelectEntries([Entry], True)
            return {'FINISHED'}
        
        Global_TocManager.SelectEntries([Entry])
        return {'FINISHED'}

class WM_MT_button_context(bpy.types.Menu):
    bl_label = "Entry Context Menu"

    def draw(self, context):
        value = getattr(context, "button_operator", None)
        if type(value).__name__ == "HELLDIVER2_OT_archive_entry":
            layout = self.layout
            FileID = getattr(value, "object_id")
            TypeID = getattr(value, "object_typeid")
            DrawEntryButtons(layout, Global_TocManager.GetEntry(int(FileID), int(TypeID)))
  
def GetDisplayData():
    # Set display archive TODO: Global_TocManager.LastSelected Draw Index could be wrong if we switch to patch only mode, that should be fixed
    DisplayTocEntries = []
    DisplayTocTypes   = []
    DisplayArchive = Global_TocManager.ActiveArchive
    if bpy.context.scene.Hd2ToolPanelSettings.PatchOnly: 
        if Global_TocManager.ActivePatch != None:
            DisplayTocEntries = [[Entry, True] for Entry in Global_TocManager.ActivePatch.TocEntries]
            DisplayTocTypes   = Global_TocManager.ActivePatch.TocTypes
    elif Global_TocManager.ActiveArchive != None:
        DisplayTocEntries = [[Entry, False] for Entry in Global_TocManager.ActiveArchive.TocEntries]
        DisplayTocTypes   = [Type for Type in Global_TocManager.ActiveArchive.TocTypes]
        AddedTypes   = [Type.TypeID for Type in DisplayTocTypes]
        AddedEntries = [Entry[0].FileID for Entry in DisplayTocEntries]
        if Global_TocManager.ActivePatch != None:
            for Type in Global_TocManager.ActivePatch.TocTypes:
                if Type.TypeID not in AddedTypes:
                    AddedTypes.append(Type.TypeID)
                    DisplayTocTypes.append(Type)
            for Entry in Global_TocManager.ActivePatch.TocEntries:
                if Entry.FileID not in AddedEntries:
                    AddedEntries.append(Entry.FileID)
                    DisplayTocEntries.append([Entry, True])
    return [DisplayTocEntries, DisplayTocTypes]

################################################
#### ---- Entry Buttons Draw Functions ---- ####
################################################

def DrawEntryButtonsSimple(box, row, Entry, PatchOnly):
    if Entry.TypeID == MeshID:
        row.operator("helldiver2.archive_mesh_save", icon='FILE_BLEND', text="").object_id = str(Entry.FileID)
        row.operator("helldiver2.archive_mesh_import", icon='IMPORT', text="").object_id = str(Entry.FileID)
    elif Entry.TypeID == TexID:
        row.operator("helldiver2.texture_saveblendimage", icon='FILE_BLEND', text="").object_id = str(Entry.FileID)
        row.operator("helldiver2.texture_import", icon='IMPORT', text="").object_id = str(Entry.FileID)
    elif Entry.TypeID == MaterialID:
        row.operator("helldiver2.material_save", icon='FILE_BLEND', text="").object_id = str(Entry.FileID)
        row.operator("helldiver2.material_import", icon='IMPORT', text="").object_id = str(Entry.FileID)
        DrawMaterialEditor(Entry, box, row)
    if Global_TocManager.IsInPatch(Entry):
        props = row.operator("helldiver2.archive_removefrompatch", icon='FAKE_USER_ON', text="")
        props.object_id     = str(Entry.FileID)
        props.object_typeid = str(Entry.TypeID)
    else:
        props = row.operator("helldiver2.archive_addtopatch", icon='FAKE_USER_OFF', text="")
        props.object_id     = str(Entry.FileID)
        props.object_typeid = str(Entry.TypeID)
    if Entry.IsModified:
        props = row.operator("helldiver2.archive_undo_mod", icon='TRASH', text="")
        props.object_id     = str(Entry.FileID)
        props.object_typeid = str(Entry.TypeID)
    if PatchOnly:
        props = row.operator("helldiver2.archive_removefrompatch", icon='X', text="")
        props.object_id     = str(Entry.FileID)
        props.object_typeid = str(Entry.TypeID)

# For context menu
def DrawEntryButtons(row, Entry):
    #TODO: Figure out how to redraw gui panel to update it
    if not Entry.IsSelected:
        Global_TocManager.SelectEntries([Entry])
    
    # Combine entry strings to be passed to operators
    FileIDStr = ""
    TypeIDStr = ""
    for SelectedEntry in Global_TocManager.SelectedEntries:
        FileIDStr += str(SelectedEntry.FileID)+","
        TypeIDStr += str(SelectedEntry.TypeID)+","
    # Get common class
    AreAllMeshes    = True
    AreAllTextures  = True
    AreAllMaterials = True
    SingleEntry = True
    NumSelected = len(Global_TocManager.SelectedEntries)
    if len(Global_TocManager.SelectedEntries) > 1:
        SingleEntry = False
    for SelectedEntry in Global_TocManager.SelectedEntries:
        if SelectedEntry.TypeID == MeshID:
            AreAllTextures = False
            AreAllMaterials = False
        elif SelectedEntry.TypeID == TexID:
            AreAllMeshes = False
            AreAllMaterials = False
        elif SelectedEntry.TypeID == MaterialID:
            AreAllTextures = False
            AreAllMeshes = False
    if SingleEntry:
        RemoveFromPatchName = "Remove From Patch"
        AddToPatchName = "Add To Patch"
        ImportMeshName = "Import Mesh"
        ImportTextureName = "Import Texture"
        ImportMaterialName = "Import Material"
        DumpObjectName = "Dump Object"
        SaveTextureName = "Save Blender Texture"
        SaveMaterialName = "Save Material"
        UndoName = "Undo Modifications"
        CopyName = "Copy Entry"
    else:
        RemoveFromPatchName = f"Remove {NumSelected} From Patch"
        AddToPatchName = f"Add {NumSelected} To Patch"
        ImportMeshName = f"Import {NumSelected} Meshes"
        ImportTextureName = f"Import {NumSelected} Textures"
        ImportMaterialName = f"Import {NumSelected} Materials"
        DumpObjectName = f"Dump {NumSelected} Objects"
        SaveTextureName = f"Save Blender {NumSelected} Textures"
        SaveMaterialName = f"Save {NumSelected} Materials"
        UndoName = f"Undo {NumSelected} Modifications"
        CopyName = f"Copy {NumSelected} Entries"
    # Draw seperator
    row.separator()
    row.label(text="---------- HellDivers2 ----------")
    
    # Draw copy button
    row.separator()
    props = row.operator("helldiver2.archive_copy", icon='COPYDOWN', text=CopyName)
    props.object_id     = FileIDStr
    props.object_typeid = TypeIDStr
    if SingleEntry:
        props = row.operator("helldiver2.archive_duplicate", icon='DUPLICATE', text="Duplicate Entry")
        props.object_id     = str(Entry.FileID)
        props.object_typeid = str(Entry.TypeID)
    if Global_TocManager.IsInPatch(Entry):
        props = row.operator("helldiver2.archive_removefrompatch", icon='X', text=RemoveFromPatchName)
        props.object_id     = FileIDStr
        props.object_typeid = TypeIDStr
    else:
        props = row.operator("helldiver2.archive_addtopatch", icon='PLUS', text=AddToPatchName)
        props.object_id     = FileIDStr
        props.object_typeid = TypeIDStr
    
    # Draw import buttons
    # TODO: Add generic import buttons
    row.separator()
    if   AreAllMeshes   : row.operator("helldiver2.archive_mesh_import", icon='IMPORT', text=ImportMeshName).object_id = FileIDStr
    elif AreAllTextures : row.operator("helldiver2.texture_import", icon='IMPORT', text=ImportTextureName).object_id = FileIDStr
    elif AreAllMaterials: row.operator("helldiver2.material_import", icon='IMPORT', text=ImportMaterialName).object_id = FileIDStr
    # Draw export buttons
    row.separator()
    if AreAllTextures: 
        if SingleEntry:
            row.operator("helldiver2.texture_export", icon='EXPORT', text="Export Texture").object_id = str(Entry.FileID)
        else:
            row.operator("helldiver2.texture_batchexport", icon='EXPORT', text=f"Export {NumSelected} Textures").object_id = FileIDStr
    props = row.operator("helldiver2.archive_object_dump", icon='PACKAGE', text=DumpObjectName)
    props.object_id     = FileIDStr
    props.object_typeid = TypeIDStr
    # Draw save buttons
    row.separator()
    if AreAllMeshes: 
        if SingleEntry:
            row.operator("helldiver2.archive_mesh_save", icon='FILE_BLEND', text="Save Mesh").object_id = str(Entry.FileID)
        else:
            row.operator("helldiver2.archive_mesh_batchsave", icon='FILE_BLEND', text=f"Save {NumSelected} Meshes")
    elif AreAllTextures: 
        row.operator("helldiver2.texture_saveblendimage", icon='FILE_BLEND', text=SaveTextureName).object_id = FileIDStr
        if SingleEntry: 
            row.operator("helldiver2.texture_savefromdds", icon='IMAGE_REFERENCE', text="Save Texture From DDs").object_id = str(Entry.FileID)
    elif AreAllMaterials: row.operator("helldiver2.material_save", icon='FILE_BLEND', text=SaveMaterialName).object_id = FileIDStr
    # Draw copy ID buttons
    if SingleEntry:
        row.separator()
        row.operator("helldiver2.copytest", icon='COPY_ID', text="Copy Entry ID").text = str(Entry.FileID)
        row.operator("helldiver2.copytest", icon='COPY_ID', text="Copy Type ID").text  = str(Entry.TypeID)
        row.operator("helldiver2.copytest", icon='COPY_ID', text="Copy Friendly Name").text  = GetFriendlyNameFromID(Entry.FileID)
        if Global_TocManager.IsInPatch(Entry):
            props = row.operator("helldiver2.archive_entryrename", icon='TEXT', text="Rename")
            props.object_id     = str(Entry.FileID)
            props.object_typeid = str(Entry.TypeID)
    if Entry.IsModified:
        row.separator()
        props = row.operator("helldiver2.archive_undo_mod", icon='TRASH', text=UndoName)
        props.object_id     = FileIDStr
        props.object_typeid = TypeIDStr
        
    if SingleEntry:
        row.operator("helldiver2.archive_setfriendlyname", icon='WORDWRAP_ON', text="Set Friendly Name").object_id = str(Entry.FileID)

    return
    

#######################
#### ---- GUI ---- ####
#######################
          
def LoadedArchives_callback(scene, context):
    return [(Archive.Name, Archive.Name, "") for Archive in Global_TocManager.LoadedArchives]
def Patches_callback(scene, context):
    return [(Archive.Name, Archive.Name, "") for Archive in Global_TocManager.Patches]
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
class HellDivers2ToolsPanel(bpy.types.Panel):
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
        row.operator("helldiver2.archive_createpatch", icon= 'COLLECTION_NEW', text="New Patch")
        row.operator("helldiver2.archive_export", icon= 'DISC', text="Write Patch")
        row = layout.row()
        row.prop(scene.Hd2ToolPanelSettings, "Patches", text="Patches")
        if len(Global_TocManager.Patches) > 0:
            Global_TocManager.SetActivePatchByName(scene.Hd2ToolPanelSettings.Patches)
        row.operator("helldiver2.archive_import", icon= 'IMPORT', text="").is_patch = True
        
        # Draw Archive Import/Export Buttons
        row = layout.row(); row = layout.row(align=True)
        row.operator("helldiver2.help", icon= 'HELP', text="")
        row.operator("helldiver2.archive_spreadsheet", icon= 'INFO', text="")
        row.operator("helldiver2.archive_import", icon= 'IMPORT').is_patch = False
        row.operator("helldiver2.archive_unloadall", icon= 'FILE_REFRESH', text="")
        row = layout.row()
        row.prop(scene.Hd2ToolPanelSettings, "LoadedArchives", text="Archives")
        row.operator("helldiver2.search_archives", icon= 'VIEWZOOM', text="")
        row = layout.row()
        if len(Global_TocManager.LoadedArchives) > 0:
            Global_TocManager.SetActiveByName(scene.Hd2ToolPanelSettings.LoadedArchives)
        
        # Draw Search Bar
        row = layout.row(); row = layout.row()
        row.prop(scene.Hd2ToolPanelSettings, "SearchField", icon='VIEWZOOM', text="")
        row.prop(scene.Hd2ToolPanelSettings, "PatchOnly", text="")
        # Draw Paste Button
        row = layout.row(align=True)
        row.operator("helldiver2.archive_paste", icon='PASTEDOWN', text="Paste "+str(len(Global_TocManager.CopyBuffer)))
        row.operator("helldiver2.archive_clearclipboard", icon='TRASH', text="Clear Clipboard")
        row = layout.row()
        
        # Draw Archive Contents
        row.prop(scene.Hd2ToolPanelSettings, "ContentsExpanded",
            icon="DOWNARROW_HLT" if scene.Hd2ToolPanelSettings.ContentsExpanded else "RIGHTARROW",
            icon_only=True, emboss=True, text="Archive Contents")
        # Draw Add Entry Buttons
        row.operator("helldiver2.material_add", icon='FILE_NEW', text="")
        
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
                type_icon = 'FILE'
                if Type.TypeID == MeshID: 
                    type_icon = 'FILE_3D'
                    if not scene.Hd2ToolPanelSettings.ShowMeshes: continue
                elif Type.TypeID == TexID: 
                    type_icon = 'FILE_IMAGE'
                    if not scene.Hd2ToolPanelSettings.ShowTextures: continue
                elif Type.TypeID == MaterialID: 
                    type_icon = 'MATERIAL'
                    if not scene.Hd2ToolPanelSettings.ShowMaterials: continue
                elif not scene.Hd2ToolPanelSettings.ShowAllElse: continue
                
                # Draw Type Header
                box = layout.box(); row = box.row()
                row.label(text=GetTypeNameFromID(Type.TypeID)+": "+str(Type.TypeID), icon=type_icon)
                row.operator("helldiver2.select_type", icon='RESTRICT_SELECT_OFF', text="").object_typeid = str(Type.TypeID)
                
                # Draw Archive Entries
                col = box.column(align=True)
                for EntryInfo in DisplayTocEntries:
                    Entry = EntryInfo[0]
                    PatchOnly = EntryInfo[1]
                    # Exclude entries that should not be drawn
                    if Entry.TypeID != Type.TypeID: continue
                    if str(Entry.FileID).find(scene.Hd2ToolPanelSettings.SearchField) == -1: continue
                    # Deal with friendly names
                    if len(Global_TocManager.SavedFriendlyNameIDs) > len(DrawChain) and Global_TocManager.SavedFriendlyNameIDs[len(DrawChain)] == Entry.FileID:
                        FriendlyName = Global_TocManager.SavedFriendlyNames[len(DrawChain)]
                    else:
                        try:
                            FriendlyName = Global_TocManager.SavedFriendlyNames[Global_TocManager.SavedFriendlyNameIDs.index(Entry.FileID)]
                            NewFriendlyNames.append(FriendlyName)
                            NewFriendlyIDs.append(Entry.FileID)
                        except:
                            FriendlyName = GetFriendlyNameFromID(Entry.FileID)
                            NewFriendlyNames.append(FriendlyName)
                            NewFriendlyIDs.append(Entry.FileID)
                        
                    
                    # Draw Entry
                    PatchEntry = Global_TocManager.GetEntry(int(Entry.FileID), int(Entry.TypeID))
                    PatchEntry.DEV_DrawIndex = len(DrawChain)
                    
                    row = col.row(align=True); row.separator()
                    props = row.operator("helldiver2.archive_entry", icon=type_icon, text=FriendlyName, emboss=PatchEntry.IsSelected, depress=PatchEntry.IsSelected)
                    props.object_id     = str(Entry.FileID)
                    props.object_typeid = str(Entry.TypeID)
                    # Draw Buttons
                    DrawEntryButtonsSimple(box, row, PatchEntry, PatchOnly)
                    # Update Draw Chain
                    DrawChain.append(PatchEntry)
            Global_TocManager.DrawChain = DrawChain
        Global_TocManager.SavedFriendlyNames = NewFriendlyNames
        Global_TocManager.SavedFriendlyNameIDs = NewFriendlyIDs
        
classes_to_register = (
    LoadArchiveOperator,
    PatchArchiveOperator,
    ImportStingrayMeshOperator,
    SaveStingrayMeshOperator,
    ImportMaterialOperator,
    ImportTextureOperator,
    ExportTextureOperator,
    DumpArchiveObjectOperator,
    Hd2ToolPanelSettings,
    HellDivers2ToolsPanel,
    UndoArchiveEntryModOperator,
    AddMaterialOperator,
    SaveMaterialOperator,
    SaveTextureFromBlendImageOperator,
    ShowMaterialEditorOperator,
    SetMaterialTexture,
    SearchArchivesOperator,
    LoadArchivesOperator,
    CopyArchiveEntryOperator,
    PasteArchiveEntryOperator,
    ClearClipboardOperator,
    SaveTextureFromDDsOperator,
    HelpOperator,
    ArchiveSpreadsheetOperator,
    UnloadArchivesOperator,
    ArchiveEntryOperator,
    CreatePatchFromActiveOperator,
    AddEntryToPatchOperator,
    RemoveEntryFromPatchOperator,
    CopyTextOperator,
    BatchExportTextureOperator,
    BatchSaveStingrayMeshOperator,
    SelectAllOfTypeOperator,
    RenamePatchEntryOperator,
    DuplicateEntryOperator,
    SetEntryFriendlyNameOperator,
)

def TestTask():
    strings = []
    IDs = []
    path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Helldivers 2\\data"
    for root, dirs, files in os.walk(path):
        for name in files:
            if Path(name).suffix == "":
                toc = StreamToc()
                success = toc.FromFile(os.path.join(root, name))
                print(path)
                for Entry in toc.TocEntries:
                    if Entry.TypeID == 2114929748090776371:
                        f = MemoryStream(Entry.TocData)
                        f.seek(80)
                        string = str(Entry.FileID)+" "+f.bytes(b"", 31).decode()+"\n"
                        if Entry.FileID in IDs:
                            strings[IDs.index(Entry.FileID)] = string
                        else:
                            strings.append(string)
                            IDs.append(Entry.FileID)
                    if Entry.TypeID == 6877563742545042104 and Entry.FileID not in IDs:
                        f = MemoryStream(Entry.TocData)
                        f.seek(32)
                        strings.append(str(Entry.FileID)+" "+f.bytes(b"", 23).decode()+"\n")
                        IDs.append(Entry.FileID)
    with open("C:\\Users\\kboyk\\OneDrive\\Desktop\\New folder\\names.txt", 'w') as f:
        f.writelines(strings)

def register():
    #TestTask()
    LoadNormalPalette(Global_palettepath)
    LoadTypeHashes()
    LoadNameHashes()
    
    for cls in classes_to_register:
        bpy.utils.register_class(cls)
    bpy.types.Scene.Hd2ToolPanelSettings = PointerProperty(type=Hd2ToolPanelSettings)
    
    bpy.utils.register_class(WM_MT_button_context)

def unregister(): 
    del bpy.types.Scene.Hd2ToolPanelSettings
    for cls in classes_to_register:
        bpy.utils.unregister_class(cls)
    
    bpy.utils.unregister_class(WM_MT_button_context)


# run script
if __name__=="__main__":
    register()
