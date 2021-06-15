import bpy
import bmesh
import mathutils


def kdtree_bm(bm):
    bm.verts.ensure_lookup_table()
    kd = mathutils.kdtree.KDTree(len(bm.verts))
    for idx, v in enumerate(bm.verts):
        kd.insert(v.co, idx)
    kd.balance()

    return kd


def assign_stiff_group(box):
    group = box.vertex_groups.get("stiff")
    if not group:
        group = box.vertex_groups.new(name="stiff")

    bm = bmesh.new()
    bm.from_mesh(box.data)
    deforms = bm.verts.layers.deform.verify()

    kd = kdtree_bm(bm)

    HEAD_CO = (0.0, -1.0, 0.0)
    TAIL_CO = (0.0, 1.0, 0.0)

    _, head_index, _ = kd.find(HEAD_CO)
    _, tail_index, _ = kd.find(TAIL_CO)

    bm.verts[head_index][deforms][group.index] = 1.0
    bm.verts[tail_index][deforms][group.index] = 1.0

    bm.to_mesh(box.data)
    bm.free()


def get_connected_verts(bm, vert_idx):
    visited = set()
    fringe = set()
    fringe.add(vert_idx)

    while fringe:
        new_fringe = set()
        for v in fringe:
            for e in bm.verts[v].link_edges:
                other = e.other_vert(bm.verts[v])
                if other.index not in visited:
                    new_fringe.add(other.index)
            visited.add(v)

        fringe = new_fringe

    return visited


def assign_ik_target_groups(col_obj, bone_names, armature):
    vert_group = col_obj.vertex_groups.get("stiff")

    bm = bmesh.new()
    bm.from_mesh(col_obj.data)
    deforms = bm.verts.layers.deform.verify()
    bm.verts.ensure_lookup_table()

    verts = []
    for v in bm.verts:
        if vert_group.index in v[deforms].keys() and (v[deforms][vert_group.index] - 1.0) < 1e-4:
            verts.append(v)

    tail_kd = mathutils.kdtree.KDTree(len(bone_names))
    for idx, name in enumerate(bone_names):
        bone = armature.data.bones.get(name)
        tail_kd.insert(bone.tail_local, idx)
    tail_kd.balance()

    head_kd = mathutils.kdtree.KDTree(len(bone_names))
    for idx, name in enumerate(bone_names):
        bone = armature.data.bones.get(name)
        head_kd.insert(bone.head_local, idx)
    head_kd.balance()

    for v in verts:
        pin_group = col_obj.vertex_groups.get("pin")

        _, idx, dist = tail_kd.find(v.co)
        if dist < 1e-4:
            group = col_obj.vertex_groups.get(bone_names[idx] + "_bonephys_ik")
            v[deforms][group.index] = 1.0
        else:
            v[deforms][pin_group.index] = 1.0
            _, idx, dist = head_kd.find(v.co)
            bone_parent = armature.data.bones.get(bone_names[idx]).parent

            if bone_parent:
                group = col_obj.vertex_groups.get(bone_parent.name)

                if group:
                    connected_verts = get_connected_verts(bm, v.index)
                    deforms = bm.verts.layers.deform.verify()

                    for idx in connected_verts:
                        bm.verts[idx][deforms][group.index] = 1.0

    bm.to_mesh(col_obj.data)
    bm.free()


def assign_ik_pole_group(box):
    POLE_CO = (1.0, 1.0, 0.0)

    group = box.vertex_groups.new(name=box.name[:-len("_col")] + "_pt")

    bm = bmesh.new()
    bm.from_mesh(box.data)
    deforms = bm.verts.layers.deform.verify()

    kd = kdtree_bm(bm)

    _, idx, _ = kd.find(POLE_CO)
    bm.verts[idx][deforms][group.index] = 1.0

    bm.to_mesh(box.data)
    bm.free()


def fit_bone(box, bone):
    HEAD_CO = (0.0, -1.0, 0.0)
    TAIL_CO = (0.0, 1.0, 0.0)

    bm = bmesh.new()
    bm.from_mesh(box.data)
    kd = kdtree_bm(bm)

    _, head_index, _ = kd.find(HEAD_CO)
    _, tail_index, _ = kd.find(TAIL_CO)

    bm.verts[head_index].co = mathutils.Vector([0, -bone.length / 2, 0])
    bm.verts[tail_index].co = mathutils.Vector([0, bone.length / 2, 0])

    bm.to_mesh(box.data)
    bm.free()


def register():
    pass


def unregister():
    pass
