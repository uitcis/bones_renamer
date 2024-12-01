bl_info = {
    "name": "Bones Renamer",
    "author": "Hogarth-MMD,空想幻灵",
    "version": (2024, 10, 14),
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
def read_bones_dictionary(filename):
    try:
        with open(filename, newline='', encoding='utf-8-sig') as csvfile:  # 使用'utf-8-sig'以去除BOM字符
            reader = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
            preset_names = []
            bone_names = []

            for row in reader:
                if not row:  # 跳过空行
                    continue
                preset_names.append(row[0])
                bone_names.append(tuple(row[1:]))

            return (preset_names, bone_names)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return ([], [])

# 重命名骨骼的函数
def rename_bones(context, boneMap1, boneMap2, BONE_NAMES_DICTIONARY):
    preset_names, bone_names = BONE_NAMES_DICTIONARY

    # 查找对应的索引
    boneMap1_index = -1
    boneMap2_index = -1
    for index, name in enumerate(preset_names):
        if name == boneMap1:
            boneMap1_index = index
        elif name == boneMap2:
            boneMap2_index = index
        if boneMap1_index != -1 and boneMap2_index != -1:
            break

    if boneMap1_index == -1 or boneMap2_index == -1:
        print("Invalid Origin or Destination Armature Type.")
        return

    bpy.ops.object.mode_set(mode='OBJECT')
    armature = context.active_object
    if not armature or armature.type != 'ARMATURE':
        print("Active object is not an armature.")
        return

    # 创建一个字典来存储从源预设到目标预设的骨骼名称映射
    bone_name_map = {}
    for i, bone in enumerate(bone_names[boneMap1_index]):
        if i < len(bone_names[boneMap2_index]):
            bone_name_map[bone] = bone_names[boneMap2_index][i]

    # 重命名骨骼
    for bone in armature.data.bones:
        if bone.name in bone_name_map:
            new_name = bone_name_map[bone.name]
            if new_name:  # Only rename if there's a non-empty target name
                bone.name = new_name
                print(f"Renamed '{bone.name}' to '{new_name}'")
            else:
                print(f"No new name provided for bone: {bone.name}")
        else:
            print(f"Bone not found in mapping: {bone.name}")

class BonesRenamer(Operator):
    """Rename bones between two armature types"""
    bl_idname = "object.bones_renamer"
    bl_label = "Rename Bones"

    direction: bpy.props.BoolProperty(name="Direction", default=True)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        BONE_NAMES_DICTIONARY = read_bones_dictionary(os.path.join(os.path.dirname(__file__), "bones_dictionary.csv"))
        FINGER_BONE_NAMES_DICTIONARY = read_bones_dictionary(os.path.join(os.path.dirname(__file__), "bones_fingers_dictionary.csv"))

        origin_type = context.scene.Origin_Armature_Type
        destination_type = context.scene.Destination_Armature_Type

        if self.direction:
            rename_bones(context, origin_type, destination_type, BONE_NAMES_DICTIONARY)
            rename_bones(context, origin_type, destination_type, FINGER_BONE_NAMES_DICTIONARY)
        else:
            rename_bones(context, destination_type, origin_type, BONE_NAMES_DICTIONARY)
            rename_bones(context, destination_type, origin_type, FINGER_BONE_NAMES_DICTIONARY)

        # 切换到Pose模式并显示骨骼名称
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')

        # 显示骨骼名称
        context.active_object.data.show_names = True

        return {'FINISHED'}

# 检测当前骨架匹配哪套骨骼
def detect_matching_skeleton(context, BONE_NAMES_DICTIONARY):
    preset_names, bone_names = BONE_NAMES_DICTIONARY

    armature = context.active_object
    if not armature or armature.type != 'ARMATURE':
        return "No armature selected."

    current_bones = set(armature.data.bones.keys())

    best_match = None
    max_match_count = 0

    for idx, bones in enumerate(bone_names):
        match_count = sum(bone in current_bones for bone in bones)
        if match_count > max_match_count:
            max_match_count = match_count
            best_match = idx

    if best_match is not None:
        return f"The skeleton matches the '{preset_names[best_match]}' preset with {max_match_count} matching bones."
    else:
        return "No matching skeleton preset found."

# 检测操作
class BONES_OT_DetectMatchingSkeleton(Operator):
    bl_idname = "bones.detect_matching_skeleton"
    bl_label = "Detect Matching Skeleton"
    
    def execute(self, context):
        filename = os.path.join(os.path.dirname(__file__), "bones_dictionary.csv")
        BONE_NAMES_DICTIONARY = read_bones_dictionary(filename)
        if BONE_NAMES_DICTIONARY:
            result = detect_matching_skeleton(context, BONE_NAMES_DICTIONARY)
            preset_names, _ = BONE_NAMES_DICTIONARY
            best_match_preset_name = None

            # 从结果中提取最佳匹配的预设名称
            for preset_name in preset_names:
                if preset_name in result:
                    best_match_preset_name = preset_name
                    break

            if best_match_preset_name:
                # 更新 Origin_Armature_Type
                context.scene.Origin_Armature_Type = best_match_preset_name
                self.report({'INFO'}, f"Detected and set to '{best_match_preset_name}' preset: {result}")
            else:
                self.report({'WARNING'}, f"No matching skeleton preset found. {result}")
        else:
            self.report({'ERROR'}, "Failed to read any preset names from CSV file.")
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
        col.operator("object.bones_renamer", text="Rename Left to Right").direction = True

        col = split.column()
        col.label(text="To:")
        col.prop(context.scene, "Destination_Armature_Type")
        col.operator("object.bones_renamer", text="Rename Right to Left").direction = False

        # 检测按钮
        layout.operator("bones.detect_matching_skeleton", text="Detect Matching Skeleton")

# 从CSV文件中动态生成EnumProperty的选项
def generate_enum_items(preset_names):
    if not preset_names:
        print("Warning: No preset names found in CSV file.")
        return [('', '', '')]
    return [(preset_name, preset_name, '') for preset_name in preset_names]

# 注册和注销
classes = (
    Bones_PT_Renamer,
    BonesRenamer,
    BONES_OT_DetectMatchingSkeleton,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # 从CSV文件中读取骨骼名称
    BONES_DICTIONARY = read_bones_dictionary(os.path.join(os.path.dirname(__file__), "bones_dictionary.csv"))
    if BONES_DICTIONARY:
        preset_names, _ = BONES_DICTIONARY
        print(f"Read {len(preset_names)} preset names from CSV file.")
    else:
        preset_names = []
        print("Failed to read any preset names from CSV file.")

    # 生成EnumProperty的选项
    enum_items = generate_enum_items(preset_names)

    # 设置默认值
    default_value = preset_names[0] if preset_names else ''

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