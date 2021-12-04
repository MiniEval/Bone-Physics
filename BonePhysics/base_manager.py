import bpy
from bpy.props import PointerProperty, StringProperty, IntProperty, CollectionProperty, BoolProperty


class BonePhys_UL_BoxList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index = 0, flt_flag = 0):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.obj_id.name, icon="OBJECT_DATAMODE")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon="OBJECT_DATAMODE")

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)

        if context.mode == "EDIT_ARMATURE":
            filtered = [self.bitflag_filter_item] * len(items)
            bones = [bone.name for bone in context.selected_bones]
            for i, item in enumerate(items):
                if item.name not in bones:
                    filtered[i] &= ~self.bitflag_filter_item
        else:
            filtered = []

        ordered = []

        return filtered, ordered


class ManagerPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Bone_Physics"
    bl_label = "Bone Physics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Bone Physics"

    def draw(self, context):
        row = self.layout.row()
        row.label(text="Gravity Collider v1.0.2")

        if context.active_object and context.active_object.type == "ARMATURE":
            rows = 5
            row = self.layout.row()
            row.template_list("BonePhys_UL_BoxList", "", context.active_object.data, "bonephys", context.active_object.data, "bonephys_index", rows=rows)

            if context.mode == "EDIT_ARMATURE":
                row = self.layout.row()
                row.operator("armature.init_collision_box", text="Initialise Collision Boxes")
                row = self.layout.row()
                row.operator("armature.delete_collision_box", text="Delete Collision Boxes")
                row = self.layout.row()
                row.operator("armature.bake_collision_box", text="Bake Collision Boxes")
                row = self.layout.row()
                row.prop(context.active_object.data, "bake_with_pt", text="Bake with Pole Targets")

    def invoke(self, context, event):
        pass


class EditPanel(bpy.types.Panel):
    bl_parent_id = "OBJECT_PT_Bone_Physics"
    bl_label = "Edit Collision Box"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        if context.active_bone and context.mode == "EDIT_ARMATURE":
            obj = None
            for prop in context.active_object.data.bonephys:
                if prop.name == context.active_bone.name:
                    obj = prop.obj_id
                    break

            if obj:
                row = self.layout.row()
                row.label(text="Collision Box Scale")
                row = self.layout.row()
                col = row.column()
                col.prop(obj, "scale")

                row = self.layout.row()
                row.label(text="Collision Box Roll")
                row = self.layout.row()
                row.prop(obj, "rotation_euler", index=1, text="Roll")


class BonePhys_Collection(bpy.types.PropertyGroup):
    name: StringProperty(name="Bone")
    obj_id: PointerProperty(name="Object", type=bpy.types.Object)


def register():
    bpy.utils.register_class(BonePhys_UL_BoxList)
    bpy.utils.register_class(ManagerPanel)
    bpy.utils.register_class(EditPanel)
    bpy.utils.register_class(BonePhys_Collection)

    bpy.types.Armature.bonephys = CollectionProperty(type=BonePhys_Collection)
    bpy.types.Armature.bonephys_index = IntProperty()
    bpy.types.Armature.bake_with_pt = BoolProperty()


def unregister():
    bpy.utils.unregister_class(BonePhys_Collection)
    bpy.utils.unregister_class(EditPanel)
    bpy.utils.unregister_class(ManagerPanel)
    bpy.utils.unregister_class(BonePhys_UL_BoxList)

    del bpy.types.Armature.bonephys_index
    del bpy.types.Armature.bonephys
    del bpy.types.Armature.bake_with_pt
