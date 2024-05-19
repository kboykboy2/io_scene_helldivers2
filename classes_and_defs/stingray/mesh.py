import copy, math

import bpy, bmesh, mathutils

from . import StingrayLocalTransform
from .bone import BoneInfo
from .material import AddMaterialToBlend_EMPTY, RawMaterialClass
from .stream import StreamComponentInfo, StreamInfo
from ..memoryStream import MemoryStream
from ...utils.hash import Hash32, Hash64
from ...utils.normals import LoadNormalPalette, NormalsFromPalette
from ... import globals

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
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = object
    # split UV seams
    try:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.seams_from_islands()
    except: print("Error attempting to create seams from uv islands")
    bpy.ops.object.mode_set(mode="OBJECT")

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
    modifier = object.modifiers.new("EXPORT_NORMAL_TRANSFER", "DATA_TRANSFER")
    bpy.context.object.modifiers[modifier.name].data_types_loops = {"CUSTOM_NORMAL"}
    bpy.context.object.modifiers[modifier.name].object = og_object
    bpy.context.object.modifiers[modifier.name].use_loop_data = True
    bpy.context.object.modifiers[modifier.name].loop_mapping = "TOPOLOGY"
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    # triangulate
    modifier = object.modifiers.new("EXPORT_TRIANGULATE", "TRIANGULATE")
    bpy.context.object.modifiers[modifier.name].keep_custom_normals = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    # adjust weights
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    try:
        bpy.ops.object.vertex_group_normalize_all(lock_active=False)
        bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    except: pass

    return object

def GetMeshData(og_object):
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
        normals[loop.vertex_index] = loop.normal.normalized()
        # tangents[loop.vertex_index] = loop.tangent.normalized()
        # bitangents[loop.vertex_index] = loop.bitangent.normalized()
    # if fuckywuckynormalwormal do this bullshit
    LoadNormalPalette()
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
    bpy.ops.object.select_all(action="DESELECT")
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
        name = f"{Slot}_{PieceType}_{BodyType}"
    name_sufix = f"_lod{mesh.LodIndex}"
    if mesh.LodIndex == -1:
        name_sufix = f"_mesh{mesh.MeshInfoIndex}"
    if mesh.IsPhysicsBody():
        name_sufix = f"_phys{mesh.MeshInfoIndex}"
    if use_sufix: name = f"{name}{name_sufix}"

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
        new_object.rotation_mode = "QUATERNION"
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
            new_object.display_type = "WIRE"

        # add object to scene collection
        new_collection.objects.link(new_object)
        # -- || ASSIGN NORMALS || -- #
        if len(mesh.VertexNormals) == len(mesh.VertexPositions):
            new_mesh.use_auto_smooth = True
            new_mesh.polygons.foreach_set("use_smooth",  [True] * len(new_mesh.polygons))
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
                    group_name   = f"{group_index}_{bone_index}"
                    if group_name not in created_groups:
                        created_groups.append(group_name)
                        new_vertex_group = new_object.vertex_groups.new(name=str(group_name))
                    vertex_group_data = [vertex_idx]
                    new_object.vertex_groups[str(group_name)].add(vertex_group_data, weight_value, "ADD")
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
                    bpy.ops.object.empty_add(type="SPHERE", radius=0.08, align="WORLD", location=(current_pos[0], current_pos[1], current_pos[2]), scale=(1, 1, 1))

class TransformInfo: # READ ONLY
    def __init__(self):
        self.NumTransforms = 0
        self.Transforms = []
    def Serialize(self, f):
        if f.IsWriting():
            raise Exception("This struct is read only (write not implemented)")
        self.NumTransforms = f.uint32(self.NumTransforms)
        f.seek(f.tell()+12)
        self.Transforms = [StingrayLocalTransform().Serialize(f) for n in range(self.NumTransforms)]

class CustomizationInfo: # READ ONLY
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
            Entry = globals.TocManager.GetEntry(self.CompositeRef, globals.CompositeMeshID)
            if Entry != None:
                globals.TocManager.Load(Entry.FileID, Entry.TypeID)
                self.StreamInfoArray = Entry.LoadedData.StreamInfoArray
                gpu = Entry.LoadedData.GpuData
            else:
                raise Exception(f"Composite mesh file {self.CompositeRef} could not be found")

        # Get bones file
        if f.IsReading() and self.BonesRef != 0:
            Entry = globals.TocManager.GetEntry(self.BonesRef, Hash64("bones"))
            if Entry != None:
                globals.TocManager.Load(Entry.FileID, Entry.TypeID)
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
                            globals.TocManager.Load(mat.MatID, globals.MaterialID, False, True)
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
            # print("Num: ", len(self.StreamInfoArray), " Index: ", Mesh_Info.StreamIndex)
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

def LoadStingrayCompositeMesh(ID, TocData, GpuData, StreamData, Reload, MakeBlendObject):
    StingrayCompositeMeshData = StingrayCompositeMesh()
    StingrayCompositeMeshData.Serialize(MemoryStream(TocData), MemoryStream(GpuData))
    return StingrayCompositeMeshData

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
