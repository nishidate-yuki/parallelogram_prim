"""
Parallelogram primitive

Copyright (c) 2020 Nishiki

Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import os
import math
import sys
import c4d

PLUGIN_ID = 1054795

def is_close_to_zero(val):
    return abs(val) < sys.float_info.epsilon

class ParallelogramHelper(object):

    @staticmethod
    def SetAxis(op, axis):
        if axis is c4d.PRIM_AXIS_ZN or axis is c4d.PRIM_AXIS_ZN:
            return False

        pList = op.GetAllPoints()
        if pList is None:
            return False

        elif axis is c4d.PRIM_AXIS_XP or axis is c4d.PRIM_AXIS_XN:
            for i, p in enumerate(pList):
                op.SetPoint(i, c4d.Vector(p.z, p.y, p.x))

        elif axis is c4d.PRIM_AXIS_YP or axis is c4d.PRIM_AXIS_YN:
            for i, p in enumerate(pList):
                op.SetPoint(i, c4d.Vector(p.x, -p.z, p.y))

        op.Message(c4d.MSG_UPDATE)
        return True


class Parallelogram(c4d.plugins.ObjectData, ParallelogramHelper):

    def __init__(self, *args):
        super(Parallelogram, self).__init__(*args)
        self.SetOptimizeCache(True)

        self.cur_edge_b = 0
        self.cur_height = 0
        self.cur_angle = 0

    def Init(self, op):
        self.InitAttr(op, float, c4d.PY_PARALLELOGRAMOBJECT_EDGE_A)
        self.InitAttr(op, float, c4d.PY_PARALLELOGRAMOBJECT_EDGE_B)
        self.InitAttr(op, int,   c4d.PY_PARALLELOGRAMOBJECT_SUB_A)
        self.InitAttr(op, int,   c4d.PY_PARALLELOGRAMOBJECT_SUB_B)
        self.InitAttr(op, float, c4d.PY_PARALLELOGRAMOBJECT_HEIGHT)
        self.InitAttr(op, float, c4d.PY_PARALLELOGRAMOBJECT_ANGLE)
        self.InitAttr(op, int,  c4d.PY_PARALLELOGRAMOBJECT_KEEP)
        self.InitAttr(op, int, c4d.PRIM_AXIS)

        op[c4d.PY_PARALLELOGRAMOBJECT_EDGE_A] = 200.0
        op[c4d.PY_PARALLELOGRAMOBJECT_EDGE_B] = 200.0
        op[c4d.PY_PARALLELOGRAMOBJECT_SUB_A] = 10
        op[c4d.PY_PARALLELOGRAMOBJECT_SUB_B] = 10

        angle_rad = c4d.utils.DegToRad(60.0)
        op[c4d.PY_PARALLELOGRAMOBJECT_ANGLE] = angle_rad
        op[c4d.PY_PARALLELOGRAMOBJECT_HEIGHT] = 200.0 * math.sin(angle_rad)
        op[c4d.PY_PARALLELOGRAMOBJECT_KEEP] = False
        op[c4d.PRIM_AXIS] = c4d.PRIM_AXIS_ZN

        self.cur_edge_b = 200.0
        self.cur_height = op[c4d.PY_PARALLELOGRAMOBJECT_HEIGHT]
        self.cur_angle = angle_rad
        return True


    def GetVirtualObjects(self, op, hierarchyhelp):
        edge_a = op[c4d.PY_PARALLELOGRAMOBJECT_EDGE_A] if op[c4d.PY_PARALLELOGRAMOBJECT_EDGE_A] is not None else 200.0
        edge_b = op[c4d.PY_PARALLELOGRAMOBJECT_EDGE_B] if op[c4d.PY_PARALLELOGRAMOBJECT_EDGE_B] is not None else 200.0
        sub_a = op[c4d.PY_PARALLELOGRAMOBJECT_SUB_A] if op[c4d.PY_PARALLELOGRAMOBJECT_SUB_A] is not None else 10
        sub_b = op[c4d.PY_PARALLELOGRAMOBJECT_SUB_B] if op[c4d.PY_PARALLELOGRAMOBJECT_SUB_B] is not None else 10
        height = op[c4d.PY_PARALLELOGRAMOBJECT_HEIGHT] if op[c4d.PY_PARALLELOGRAMOBJECT_HEIGHT] is not None else 200.0
        angle = op[c4d.PY_PARALLELOGRAMOBJECT_ANGLE] if op[c4d.PY_PARALLELOGRAMOBJECT_ANGLE] is not None else 45.0
        keep_angle = op[c4d.PY_PARALLELOGRAMOBJECT_KEEP] if op[c4d.PY_PARALLELOGRAMOBJECT_KEEP] is not None else True
        axis = op[c4d.PRIM_AXIS]
        
        # change height or edge_b
        edge_b_changed = not is_close_to_zero(self.cur_edge_b - edge_b)
        height_changed = not is_close_to_zero(self.cur_height - height)
        angle_changed = not is_close_to_zero(self.cur_angle - angle)

        if height_changed:
            if keep_angle:
                edge_b = height / math.sin(angle)
                op[c4d.PY_PARALLELOGRAMOBJECT_EDGE_B] = edge_b
            else:
                keeped_x = self.cur_edge_b * math.cos(self.cur_angle)
                vec_b = c4d.Vector(keeped_x, height, 0)
                edge_b = vec_b.GetLength()
                angle = math.asin( vec_b.GetNormalized().y )
                op[c4d.PY_PARALLELOGRAMOBJECT_EDGE_B] = edge_b
                op[c4d.PY_PARALLELOGRAMOBJECT_ANGLE] = angle
        elif edge_b_changed or angle_changed:
            height = edge_b * math.sin(angle)
            op[c4d.PY_PARALLELOGRAMOBJECT_HEIGHT] = height
        
        self.cur_edge_b = edge_b
        self.cur_height = height
        self.cur_angle = angle

        # object
        ptCount = (sub_a + 1) * (sub_b + 1)
        polyCount = sub_a * sub_b
        op = c4d.PolygonObject(ptCount, polyCount)
        
        # angle -> dir
        dir_b = c4d.Vector(math.cos(angle), math.sin(angle), 0)

        # points
        da = edge_a / sub_a
        db = edge_b / sub_b
        index = 0
        offset_x = 0.0
        for j in xrange(sub_b + 1):
            for i in xrange(sub_a + 1):
                position = c4d.Vector(i * da, 0, 0) + (j * db * dir_b)
                op.SetPoint(index, position)
                index += 1

        # polygons
        ptIndex = 0
        polyIndex = 0
        for j in xrange(sub_b):
            for i in xrange(sub_a):
                polygon = c4d.CPolygon(ptIndex, ptIndex+sub_a+1, ptIndex+sub_a+2, ptIndex+1)
                op.SetPolygon(polyIndex, polygon)
                ptIndex += 1
                polyIndex += 1
            ptIndex += 1

        # axis
        self.SetAxis(op, axis)

        op.Message(c4d.MSG_UPDATE)
        op.SetPhong(True, True, c4d.utils.Rad(80.0))

        return op

if __name__ == "__main__":
    directory, _ = os.path.split(__file__)
    fn = os.path.join(directory, "res", "oparallelogram.tif")

    bmp = c4d.bitmaps.BaseBitmap()
    if bmp is None:
        raise MemoryError("Failed to create a BaseBitmap.")

    if bmp.InitWith(fn)[0] != c4d.IMAGERESULT_OK:
        raise MemoryError("Failed to initialize the BaseBitmap.")

    c4d.plugins.RegisterObjectPlugin(id=PLUGIN_ID, str="Parallelogram",
                                     g=Parallelogram, description="parallelogram",
                                     icon=bmp, info=c4d.OBJECT_GENERATOR)
