import math

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
        raise Exception(f"Cannot get size of unknown vertex format: {self.Format}")
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
            raise Exception(f"Cannot serialize unknown vertex format: {self.Format}")

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
