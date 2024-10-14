bl_info = {
    "name": "Bones Renamer",
    "author": "Hogarth-MMD,空想幻灵",
    "version": (2022, 7, 18),
    "blender": (2, 83, 0),
    "location": "View 3D > Tool Shelf > Tool",
    "description": "bones renamer for armature conversion",
    "warning": "",
    "wiki_url": "https://gitee.com/uitcis/bones_renamer",
    "category": "Armature",
}

import bpy
from bpy.types import Operator, Panel
import csv
import os

# 读取CSV文件中的骨骼名称字典
def use_csv_bones_dictionary():
    bones_dictionary = os.path.join(os.path.dirname(__file__), "bones_dictionary.csv")
    with open(bones_dictionary, newline='', encoding='utf-8') as csvfile:
        CSVreader = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
        BONES_DICTIONARY = [tuple(x) for x in CSVreader if x]
    return BONES_DICTIONARY

def use_csv_bones_fingers_dictionary():
    finger_bones_dictionary = os.path.join(os.path.dirname(__file__), "bones_fingers_dictionary.csv")
    with open(finger_bones_dictionary, newline='', encoding='utf-8') as csvfile:
        CSVreader = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
        FINGER_BONES_DICTIONARY = [tuple(x) for x in CSVreader if x]
    return FINGER_BONES_DICTIONARY

# 重命名骨骼的函数
def rename_bones(boneMap1, boneMap2, BONE_NAMES_DICTIONARY):
    if not BONE_NAMES_DICTIONARY:
        print("No bone names found in the dictionary.")
        return

    boneMaps = BONE_NAMES_DICTIONARY[0]
    boneMap1_index = boneMaps.index(boneMap1) if boneMap1 in boneMaps else -1
    boneMap2_index = boneMaps.index(boneMap2) if boneMap2 in boneMaps else -1

    if boneMap1_index == -1 or boneMap2_index == -1:
        print("Invalid Origin or Destination Armature Type.")
        return

    bpy.ops.object.mode_set(mode='OBJECT')
    for k in BONE_NAMES_DICTIONARY:
        if k[boneMap1_index] in bpy.context.active_object.data.bones.keys():
            if k[boneMap2_index] != '':
                bpy.context.active_object.data.bones[k[boneMap1_index]].name = k[boneMap2_index]

def rename_finger_bones(boneMap1, boneMap2, FINGER_BONE_NAMES_DICTIONARY):
    if not FINGER_BONE_NAMES_DICTIONARY:
        print("No finger bone names found in the dictionary.")
        return

    boneMaps = FINGER_BONE_NAMES_DICTIONARY[0]
    boneMap1_index = boneMaps.index(boneMap1) if boneMap1 in boneMaps else -1
    boneMap2_index = boneMaps.index(boneMap2) if boneMap2 in boneMaps else -1

    if boneMap1_index == -1 or boneMap2_index == -1:
        print("Invalid Origin or Destination Armature Type for fingers.")
        return

    bpy.ops.object.mode_set(mode='OBJECT')
    for k in FINGER_BONE_NAMES_DICTIONARY:
        if k[boneMap1_index] in bpy.context.active_object.data.bones.keys():
            if k[boneMap2_index] != '':
                bpy.context.active_object.data.bones[k[boneMap1_index]].name = k[boneMap2_index]

# 操作符：批量重命名骨骼
class BonesRenamerLeftToRight(Operator):
    """Rename bones from left to right"""
    bl_idname = "object.bones_renamer_left_to_right"
    bl_label = "Rename Left to Right"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        BONE_NAMES_DICTIONARY = use_csv_bones_dictionary()
        FINGER_BONE_NAMES_DICTIONARY = use_csv_bones_fingers_dictionary()

        origin_type = context.scene.Origin_Armature_Type
        destination_type = context.scene.Destination_Armature_Type

        rename_bones(origin_type, destination_type, BONE_NAMES_DICTIONARY)
        rename_finger_bones(origin_type, destination_type, FINGER_BONE_NAMES_DICTIONARY)

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        return {'FINISHED'}

class BonesRenamerRightToLeft(Operator):
    """Rename bones from right to left"""
    bl_idname = "object.bones_renamer_right_to_left"
    bl_label = "Rename Right to Left"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        BONE_NAMES_DICTIONARY = use_csv_bones_dictionary()
        FINGER_BONE_NAMES_DICTIONARY = use_csv_bones_fingers_dictionary()

        origin_type = context.scene.Destination_Armature_Type
        destination_type = context.scene.Origin_Armature_Type

        rename_bones(origin_type, destination_type, BONE_NAMES_DICTIONARY)
        rename_finger_bones(origin_type, destination_type, FINGER_BONE_NAMES_DICTIONARY)

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        return {'FINISHED'}

# 面板类
class Bones_PT_Renamer(Panel):
    """Creates the Bones Renamer Panel in a VIEW_3D TOOLS tab"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Bones Renamer Panel"
    bl_category = "Tool"
    bl_idname = "OBJECT_PT_bones_renamer"

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.5)

        col = split.column()
        col.label(text="From:")
        col.prop(context.scene, "Origin_Armature_Type")
        col.operator("object.bones_renamer_left_to_right", text="Rename Left to Right")

        col = split.column()
        col.label(text="To:")
        col.prop(context.scene, "Destination_Armature_Type")
        col.operator("object.bones_renamer_right_to_left", text="Rename Right to Left")

# 从CSV文件中动态生成EnumProperty的选项
def generate_enum_items(bone_names):
    if not bone_names:
        print("Warning: No bone names found in CSV file.")
        return [('', '', '')]
    return [(bone_name, bone_name, '') for bone_name in bone_names]

# 注册和注销
classes = (
    Bones_PT_Renamer,
    BonesRenamerLeftToRight,
    BonesRenamerRightToLeft,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # 从CSV文件中读取骨骼名称
    BONES_DICTIONARY = use_csv_bones_dictionary()
    if BONES_DICTIONARY:
        bone_names = BONES_DICTIONARY[0][1:]  # 假设第一行是预设类型
    else:
        bone_names = []

    # 生成EnumProperty的选项
    enum_items = generate_enum_items(bone_names)

    # 设置默认值
    default_value = bone_names[0] if bone_names else ''

    # 动态设置EnumProperty
    bpy.types.Scene.Origin_Armature_Type = bpy.props.EnumProperty(
        items=enum_items,
        name="Rename bones from :",
        default=default_value
    )

    bpy.types.Scene.Destination_Armature_Type = bpy.props.EnumProperty(
        items=enum_items,
        name="Rename bones to :",
        default=default_value
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.Origin_Armature_Type
    del bpy.types.Scene.Destination_Armature_Type

if __name__ == "__main__":
    register()