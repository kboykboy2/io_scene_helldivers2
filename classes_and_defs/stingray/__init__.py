class StingrayMatrix4x4: # https://help.autodesk.com/cloudhelp/ENU/Stingray-SDK-Help/engine_c/plugin__api__types_8h.html#line_89
    def __init__(self):
        self.v = [float(0)]*16
    def Serialize(self, f):
        self.v = [f.float32(value) for value in self.v]
        return self

class StingrayMatrix3x3: # https://help.autodesk.com/cloudhelp/ENU/Stingray-SDK-Help/engine_c/plugin__api__types_8h.html#line_84
    def __init__(self):
        self.x = [0,0,0]
        self.y = [0,0,0]
        self.z = [0,0,0]
    def Serialize(self, f):
        self.x = f.vec3_float(self.x)
        self.y = f.vec3_float(self.x)
        self.z = f.vec3_float(self.x)
        return self

class StingrayLocalTransform: # https://help.autodesk.com/cloudhelp/ENU/Stingray-SDK-Help/engine_c/plugin__api__types_8h.html#line_100
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
