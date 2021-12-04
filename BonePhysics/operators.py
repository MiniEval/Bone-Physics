import math

from .mesh_helpers import *


def init_box(context, bone):
    mesh = bpy.data.meshes.new(bone.name + "_bonephys_box")
    if bpy.data.objects.get(bone.name + "_bonephys_col"):
        bpy.data.objects.remove(bpy.data.objects.get(bone.name + "_bonephys_col"), do_unlink=True)
    box_obj = bpy.data.objects.new(bone.name + "_bonephys_col", mesh)
    context.scene.collection.objects.link(box_obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)

    subd_edges = []
    for face in bm.faces:
        if abs(face.calc_center_bounds()[1]) > 1e-4:
            for edge in face.edges:
                subd_edges.append(edge)

    bmesh.ops.subdivide_edges(bm, edges=subd_edges, smooth=0.0, cuts=1, use_only_quads=True, use_grid_fill=True)

    bm.to_mesh(mesh)
    bm.free()

    box_obj.parent = context.active_object
    box_obj.parent_type = "BONE"
    box_obj.parent_bone = bone.name
    box_obj.scale = [bone.length / 2, bone.length / 2, bone.length / 2]
    box_obj.location[1] = -bone.length / 2
    box_obj.lock_location = (True, True, True)
    box_obj.lock_rotation = (True, False, True)

    return box_obj


class BonePhys_Initialise_Box(bpy.types.Operator):
    """Generate a default collision box for selected bones"""

    bl_idname = "armature.init_collision_box"
    bl_label = "Initialise collision boxes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for bone in context.selected_bones:
            if len(bone.name) >= 60 - len("_bonephys_col"):
                self.report({'ERROR_INVALID_CONTEXT'}, "Excessively long bone name")
                return {'CANCELLED'}
            if context.active_object.data.bonephys.find(bone.name) != -1:
                continue
            box_obj = init_box(context, bone)

            props = context.active_object.data.bonephys.add()
            props.name = bone.name
            props.obj_id = box_obj

        return {'FINISHED'}


def delete_box(context, bone_names, empty=False):
    for bone_name in bone_names:
        prop = context.active_object.data.bonephys.find(bone_name)
        if prop != -1:
            if not empty:
                bpy.data.objects.remove(context.active_object.data.bonephys[prop].obj_id, do_unlink=True)
            context.active_object.data.bonephys.remove(prop)

    context.active_object.data.bonephys_index = 0


class BonePhys_Delete_Box(bpy.types.Operator):
    """Delete collision boxes for selected bones"""

    bl_idname = "armature.delete_collision_box"
    bl_label = "Delete collision boxes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bone_names = []
        for bone in context.selected_bones:
            bone_names.append(bone.name)

        delete_box(context, bone_names)

        return {'FINISHED'}


def bake_meshes(context):
    armature = context.active_object
    bones = context.selected_bones
    objs = []
    obj_bone_names = []

    if len(armature.name) >= 60 - len("_bonephys_col"):
        return None, ["Excessively long armature name"], None

    for bone in bones:
        if len(bone.name) >= 60 - len("_bonephys_col"):
            return None, ["Excessively long bone name"], None

    for bone in bones:
        prop = context.active_object.data.bonephys.find(bone.name)
        if prop != -1:
            objs.append(context.active_object.data.bonephys[prop].obj_id)
            obj_bone_names.append(bone.name)

    col_obj = bpy.data.objects.new(armature.name + "_bonephys_col", bpy.data.meshes.new(armature.name + "_bonephys_col"))
    col_obj.parent = armature
    context.scene.collection.objects.link(col_obj)

    init_vgroups(col_obj, obj_bone_names, armature)

    for obj in objs:
        assign_ik_pole_group(obj)

    bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
    bpy.ops.object.select_all(action="DESELECT")

    for obj in objs:
        obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    for i in range(len(objs)):
        assign_stiff_group(objs[i])
        bone = armature.data.bones.get(obj_bone_names[i])
        fit_bone(objs[i], bone)

    col_obj.select_set(True)
    context.view_layer.objects.active = col_obj
    bpy.ops.object.join()

    bm = bmesh.new()
    bm.from_mesh(col_obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.to_mesh(col_obj.data)

    if armature.data.bake_with_pt:
        for i in range(len(obj_bone_names)):
            if bpy.data.objects.get(obj_bone_names[i] + "_bonephys_pt"):
                bpy.data.objects.remove(bpy.data.objects.get(obj_bone_names[i] + "_bonephys_pt"), do_unlink=True)
            pole_empty = bpy.data.objects.new(obj_bone_names[i] + "_bonephys_pt", None)
            context.scene.collection.objects.link(pole_empty)

            group = col_obj.vertex_groups.get(obj_bone_names[i] + "_bonephys_pt")
            v_parent = [v for v in col_obj.data.vertices if group.index in [vg.group for vg in v.groups]]

            pole_empty.parent = col_obj
            pole_empty.parent_type = "VERTEX"
            pole_empty.parent_vertices[0] = v_parent[0].index

            pole_empty.hide_viewport = True

    print(obj_bone_names)
    for i in range(len(obj_bone_names)):
        col_obj.vertex_groups.remove(col_obj.vertex_groups.get(obj_bone_names[i] + "_bonephys_pt"))
        if col_obj.vertex_groups.get(obj_bone_names[i]):
            col_obj.vertex_groups.remove(col_obj.vertex_groups.get(obj_bone_names[i]))

    return col_obj, obj_bone_names, armature


def init_vgroups(col_obj, obj_bone_names, armature):
    col_obj.vertex_groups.new(name="stiff")
    col_obj.vertex_groups.new(name="pin")
    for name in obj_bone_names:
        parent = armature.data.bones.get(name).parent
        if parent and parent not in obj_bone_names:
            col_obj.vertex_groups.new(name=parent.name)

        col_obj.vertex_groups.new(name=name + "_bonephys_ik")
        col_obj.vertex_groups.new(name=name + "_bonephys_pt")


def setup_ik(col_obj, bone_names, armature):
    assign_ik_target_groups(col_obj, bone_names, armature)

    stiff_group = col_obj.vertex_groups.get("stiff")
    stiff = [v.index for v in col_obj.data.vertices if stiff_group.index in [vg.group for vg in v.groups]]
    stiff_group.add(stiff, 0.0, "REPLACE")
    stiff_group.add([v.index for v in col_obj.data.vertices if v.index not in stiff], 1.0, "REPLACE")

    for group in col_obj.vertex_groups:
        if group.name.endswith("_bonephys_ik"):
            bone_name = group.name[:-len("_bonephys_ik")]
            bone = armature.pose.bones.get(bone_name)
            if bone:
                con = bone.constraints.new("IK")
                con.target = col_obj
                con.subtarget = group.name
                if armature.data.bake_with_pt:
                    con.pole_target = bpy.data.objects.get(bone_name + "_bonephys_pt")
                con.chain_count = 1

    arm_mod = col_obj.modifiers.new("Armature", type="ARMATURE")
    arm_mod.object = armature


def setup_cloth(col_obj):
    cloth = col_obj.modifiers.new("Cloth", type="CLOTH")
    cloth.settings.vertex_group_mass = "pin"
    cloth.settings.use_dynamic_mesh = True

    cloth.settings.use_internal_springs = True
    cloth.settings.vertex_group_intern = "stiff"
    cloth.settings.internal_tension_stiffness = 0.0
    cloth.settings.internal_compression_stiffness = 0.0
    cloth.settings.internal_spring_max_diversion = math.pi/180


class BonePhys_Bake_Collision_Mesh(bpy.types.Operator):
    """Bake collision boxes of selected bones into a simulated cloth-based collider"""

    bl_idname = "armature.bake_collision_box"
    bl_label = "Bake collision mesh with selected bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        col_obj, bone_names, armature = bake_meshes(context)
        if col_obj is None:
            self.report({'ERROR_INVALID_CONTEXT'}, bone_names[0])
            return {'CANCELLED'}
        setup_ik(col_obj, bone_names, armature)
        setup_cloth(col_obj)

        context.view_layer.objects.active = armature
        delete_box(context, bone_names, empty=True)
        context.view_layer.objects.active = col_obj

        return {'FINISHED'}


def register():
    bpy.utils.register_class(BonePhys_Initialise_Box)
    bpy.utils.register_class(BonePhys_Delete_Box)
    bpy.utils.register_class(BonePhys_Bake_Collision_Mesh)


def unregister():
    bpy.utils.unregister_class(BonePhys_Initialise_Box)
    bpy.utils.unregister_class(BonePhys_Delete_Box)
    bpy.utils.unregister_class(BonePhys_Bake_Collision_Mesh)
