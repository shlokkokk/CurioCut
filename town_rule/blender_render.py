"""
Headless Blender 4.3 EEVEE Next 3D Renderer for Town-Rule Episodes.
Builds modular 3D R6 characters, procedural monsters/pets, 6 environments,
2D face decals, weather particles, bloom, and dynamic camera cuts from episode_timed.json.

Usage:
  blender --background --python town_rule/blender_render.py -- --episode work/episode_timed.json --out work/raw_video.mp4 [--fps 30] [--draft]
"""

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector

# Parse args after '--'
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1 :]
else:
    argv = []

parser = argparse.ArgumentParser()
parser.add_argument("--episode", required=True)
parser.add_argument("--out", required=True)
parser.add_argument("--fps", type=int, default=30)
parser.add_argument("--draft", action="store_true", help="Fast 540x960 preview render")
parser.add_argument("--max-frames", type=int, default=0, help="Optional cap on rendered frames for quick QA")
parser.add_argument("--faces-dir", default=str(Path(__file__).resolve().parent / "assets" / "faces"))
args = parser.parse_args(argv)

try:
    import gpu
    print(f"[blender_render] Active GPU: {gpu.platform.device_type_get()} | Vendor: {gpu.platform.vendor_get()} | Renderer: {gpu.platform.renderer_get()}", flush=True)
except Exception as e:
    print(f"[blender_render] GPU detection notice: {e}", flush=True)


def hex_to_rgba(h: str, a: float = 1.0):
    h = (h or "#CCCCCC").lstrip("#")
    if len(h) != 6:
        return (0.8, 0.8, 0.8, a)
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    # sRGB to linear approx for Blender color sockets
    return (r ** 2.2, g ** 2.2, b ** 2.2, a)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_mat(name: str, color=(0.8, 0.8, 0.8, 1.0), roughness=0.65, metallic=0.0, emission=None, emission_strength=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
    return mat


def make_textured_mat(name: str, col1, col2, scale=4.0, roughness=0.8, bump_strength=0.14):
    """Procedural noise-textured material with subtle bump for rich non-blocky surfaces."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness

    tc = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.65

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = col1
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = col2

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.05

    links.new(tc.outputs["Object"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def make_striped_mat(name: str, col1, col2, scale=14.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.7

    tex_coord = nodes.new("ShaderNodeTexCoord")
    wave = nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.wave_profile = "SAW"
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 0.0

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.48
    ramp.color_ramp.elements[0].color = col1
    ramp.color_ramp.elements[1].position = 0.52
    ramp.color_ramp.elements[1].color = col2
    ramp.color_ramp.interpolation = "CONSTANT"

    links.new(tex_coord.outputs["Object"], wave.inputs["Vector"])
    links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def make_face_mat(name: str, img_path: Path):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.42
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.05
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 0.22

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(img_path), check_existing=True)
    tex.extension = "CLIP"

    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    return mat


def add_box(name, size, loc=(0, 0, 0), mat=None, parent=None, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    if bevel > 0:
        bev = obj.modifiers.new(name="Bevel", type="BEVEL")
        bev.width = bevel
        bev.segments = 2
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def add_cyl(name, radius, depth, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, parent=None, verts=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def add_cone(name, r1, r2, depth, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, parent=None, verts=8):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def add_sphere(name, radius, loc=(0, 0, 0), scale=(1, 1, 1), mat=None, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=12, radius=radius, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def set_key(obj, prop, frame, val, interp="LINEAR"):
    setattr(obj, prop, val)
    obj.keyframe_insert(data_path=prop, frame=frame)
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            if fc.data_path == prop:
                for kp in fc.keyframe_points:
                    if abs(kp.co[0] - frame) < 0.01:
                        kp.interpolation = interp


# ---------------------------------------------------------------------------
# R6 Character Rig
# ---------------------------------------------------------------------------
class R6Rig:
    def __init__(self, spec: dict, faces_dir: Path, collection):
        self.id = spec["id"]
        h_map = {"kid": 0.78, "adult": 1.0, "elder": 0.96}
        self.scale_factor = h_map.get(spec.get("height", "adult"), 1.0)
        self.focus_height = 1.38 * self.scale_factor
        self.pants_col_rgba = hex_to_rgba(spec.get("pants_color", "#1E293B"))

        self.root = bpy.data.objects.new(f"char_{self.id}", None)
        collection.objects.link(self.root)
        self.root.scale = (self.scale_factor, self.scale_factor, self.scale_factor)

        skin_col = hex_to_rgba(spec.get("skin_color", "#F2C9A0"))
        shirt_col = hex_to_rgba(spec.get("shirt_color", "#3B82F6"))
        pants_col = hex_to_rgba(spec.get("pants_color", "#1E293B"))
        hair_col = hex_to_rgba(spec.get("hair_color", "#2B1D14"))

        self.skin_mat = make_mat(f"{self.id}_skin", skin_col, roughness=0.55)
        self.pants_mat = make_mat(f"{self.id}_pants", pants_col, roughness=0.75)
        self.stone_mat = make_mat(f"{self.id}_stone", (0.35, 0.36, 0.38, 1.0), roughness=0.9)
        self.hair_mat = make_mat(f"{self.id}_hair", hair_col, roughness=0.65)

        pat = spec.get("shirt_pattern", "solid")
        if pat == "stripes":
            self.shirt_mat = make_striped_mat(f"{self.id}_shirt", shirt_col, (0.06, 0.06, 0.07, 1.0), scale=1.4)
        elif pat == "suit":
            self.shirt_mat = make_mat(f"{self.id}_shirt", (0.07, 0.07, 0.09, 1.0), roughness=0.5)
        else:
            self.shirt_mat = make_mat(f"{self.id}_shirt", shirt_col, roughness=0.68)

        # Body pivot at hip (z=0.78)
        self.body_pivot = bpy.data.objects.new(f"{self.id}_body", None)
        collection.objects.link(self.body_pivot)
        self.body_pivot.parent = self.root
        self.body_pivot.location = (0, 0, 0.78)

        # Torso
        self.torso = add_box(f"{self.id}_torso", (0.76, 0.38, 0.76), loc=(0, 0, 0.38), mat=self.shirt_mat, parent=self.body_pivot, bevel=0.025)
        if pat == "suit":
            tie_mat = make_mat(f"{self.id}_tie", (0.75, 0.1, 0.1, 1.0))
            add_box(f"{self.id}_tie", (0.12, 0.04, 0.45), loc=(0, -0.195, 0.42), mat=tie_mat, parent=self.body_pivot, bevel=0.005)

        # Head pivot
        self.head_pivot = bpy.data.objects.new(f"{self.id}_head_piv", None)
        collection.objects.link(self.head_pivot)
        self.head_pivot.parent = self.body_pivot
        self.head_pivot.location = (0, 0, 0.78)

        # Classic Roblox rounded-top cylinder head
        self.head = add_cyl(f"{self.id}_head", 0.25, 0.46, loc=(0, 0, 0.23), mat=self.skin_mat, parent=self.head_pivot, verts=24)
        bev = self.head.modifiers.new("Bevel", "BEVEL")
        bev.width = 0.055
        bev.segments = 3

        # 2D Face Decal Planes (front is -Y)
        self.face_planes = {}
        for png in sorted(faces_dir.glob("*.png")):
            expr = png.stem
            bpy.ops.mesh.primitive_plane_add(size=0.42, location=(0, -0.264, 0.23), rotation=(math.radians(90), 0, 0))
            pl = bpy.context.active_object
            pl.name = f"{self.id}_face_{expr}"
            pl.parent = self.head_pivot
            pl.data.materials.append(make_face_mat(f"{self.id}_fmat_{expr}", png))
            pl.scale = (1, 1, 1) if expr == "neutral" else (0, 0, 0)
            self.face_planes[expr] = pl

        # Hair / Hat
        self._build_hair(spec.get("hair_style", "messy"), spec.get("beard", False))

        # Arms (pivot at shoulder z=0.72 relative to body_pivot)
        self.arm_l = bpy.data.objects.new(f"{self.id}_armL_piv", None)
        self.arm_r = bpy.data.objects.new(f"{self.id}_armR_piv", None)
        collection.objects.link(self.arm_l)
        collection.objects.link(self.arm_r)
        self.arm_l.parent = self.body_pivot
        self.arm_r.parent = self.body_pivot
        self.arm_l.location = (-0.55, 0, 0.72)
        self.arm_r.location = (0.55, 0, 0.72)

        add_box(f"{self.id}_armL", (0.30, 0.34, 0.72), loc=(0, 0, -0.34), mat=self.shirt_mat, parent=self.arm_l, bevel=0.02)
        add_box(f"{self.id}_handL", (0.28, 0.30, 0.16), loc=(0, 0, -0.68), mat=self.skin_mat, parent=self.arm_l, bevel=0.02)
        add_box(f"{self.id}_armR", (0.30, 0.34, 0.72), loc=(0, 0, -0.34), mat=self.shirt_mat, parent=self.arm_r, bevel=0.02)
        add_box(f"{self.id}_handR", (0.28, 0.30, 0.16), loc=(0, 0, -0.68), mat=self.skin_mat, parent=self.arm_r, bevel=0.02)

        # Legs (pivot at hip z=0.78 relative to root)
        self.leg_l = bpy.data.objects.new(f"{self.id}_legL_piv", None)
        self.leg_r = bpy.data.objects.new(f"{self.id}_legR_piv", None)
        collection.objects.link(self.leg_l)
        collection.objects.link(self.leg_r)
        self.leg_l.parent = self.root
        self.leg_r.parent = self.root
        self.leg_l.location = (-0.19, 0, 0.78)
        self.leg_r.location = (0.19, 0, 0.78)

        self.leg_l_mesh = add_box(f"{self.id}_legL", (0.34, 0.36, 0.64), loc=(0, 0, -0.32), mat=self.pants_mat, parent=self.leg_l, bevel=0.02)
        self.leg_r_mesh = add_box(f"{self.id}_legR", (0.34, 0.36, 0.64), loc=(0, 0, -0.32), mat=self.pants_mat, parent=self.leg_r, bevel=0.02)
        shoe_mat = make_mat(f"{self.id}_shoe", (0.06, 0.06, 0.07, 1.0), roughness=0.55)
        add_box(f"{self.id}_shoeL", (0.36, 0.42, 0.14), loc=(0, -0.03, -0.69), mat=shoe_mat, parent=self.leg_l, bevel=0.02)
        add_box(f"{self.id}_shoeR", (0.36, 0.42, 0.14), loc=(0, -0.03, -0.69), mat=shoe_mat, parent=self.leg_r, bevel=0.02)

        # Held / worn props
        self.props = {}
        self._build_props()

    def _build_hair(self, style: str, beard: bool):
        hp = self.head_pivot
        m = self.hair_mat
        if style == "messy":
            add_box(f"{self.id}_h1", (0.56, 0.56, 0.16), loc=(0, 0.03, 0.47), mat=m, parent=hp, bevel=0.05)
            add_box(f"{self.id}_hback", (0.56, 0.16, 0.34), loc=(0, 0.23, 0.28), mat=m, parent=hp, bevel=0.04)
            for i, (dx, dy, dz, rx, ry) in enumerate([
                (-0.16, -0.22, 0.46, 0.35, 0.25),
                (0.0, -0.24, 0.47, 0.40, 0.0),
                (0.16, -0.22, 0.46, 0.35, -0.25),
                (-0.24, -0.05, 0.42, 0.1, 0.45),
                (0.24, -0.05, 0.42, 0.1, -0.45),
            ]):
                add_cone(f"{self.id}_hsp{i}", 0.10, 0.015, 0.22, loc=(dx, dy, dz), rot=(rx, ry, 0), mat=m, parent=hp, verts=6)
        elif style == "parted":
            add_box(f"{self.id}_h1", (0.54, 0.54, 0.16), loc=(0, 0.02, 0.46), mat=m, parent=hp, bevel=0.04)
            add_box(f"{self.id}_h2", (0.10, 0.46, 0.26), loc=(-0.24, 0.05, 0.30), mat=m, parent=hp, bevel=0.02)
            add_box(f"{self.id}_h3", (0.10, 0.46, 0.26), loc=(0.24, 0.05, 0.30), mat=m, parent=hp, bevel=0.02)
        elif style == "bob":
            add_box(f"{self.id}_h1", (0.58, 0.58, 0.18), loc=(0, 0.02, 0.46), mat=m, parent=hp, bevel=0.04)
            add_box(f"{self.id}_h2", (0.58, 0.18, 0.44), loc=(0, 0.22, 0.24), mat=m, parent=hp, bevel=0.03)
            add_box(f"{self.id}_h3", (0.12, 0.44, 0.42), loc=(-0.25, 0.04, 0.24), mat=m, parent=hp, bevel=0.02)
            add_box(f"{self.id}_h4", (0.12, 0.44, 0.42), loc=(0.25, 0.04, 0.24), mat=m, parent=hp, bevel=0.02)
        elif style == "pigtails":
            add_box(f"{self.id}_h1", (0.54, 0.54, 0.16), loc=(0, 0.02, 0.46), mat=m, parent=hp, bevel=0.04)
            add_cyl(f"{self.id}_pt1", 0.09, 0.36, loc=(-0.32, 0.06, 0.28), rot=(0, 0.3, 0), mat=m, parent=hp)
            add_cyl(f"{self.id}_pt2", 0.09, 0.36, loc=(0.32, 0.06, 0.28), rot=(0, -0.3, 0), mat=m, parent=hp)
        elif style == "tophat":
            hat_m = make_mat(f"{self.id}_hatm", (0.08, 0.08, 0.1, 1.0))
            add_cyl(f"{self.id}_th1", 0.36, 0.04, loc=(0, 0, 0.46), mat=hat_m, parent=hp)
            add_cyl(f"{self.id}_th2", 0.24, 0.38, loc=(0, 0, 0.65), mat=hat_m, parent=hp)
        elif style == "cap":
            cap_m = make_mat(f"{self.id}_capm", (0.75, 0.15, 0.15, 1.0))
            add_cyl(f"{self.id}_cp1", 0.27, 0.18, loc=(0, 0, 0.47), mat=cap_m, parent=hp)
            add_box(f"{self.id}_cp2", (0.42, 0.24, 0.04), loc=(0, -0.22, 0.41), mat=cap_m, parent=hp, bevel=0.01)

        if beard:
            add_box(f"{self.id}_beard", (0.48, 0.14, 0.14), loc=(0, -0.20, 0.05), mat=m, parent=hp, bevel=0.02)

    def _build_props(self):
        gold_m = make_mat(f"{self.id}_gold", (1.0, 0.78, 0.12, 1.0), metallic=0.85, roughness=0.25)
        pack_m = make_mat(f"{self.id}_pack", (0.88, 0.42, 0.10, 1.0), roughness=0.6)
        glow_m = make_mat(f"{self.id}_glow", (1.0, 0.85, 0.4, 1.0), emission=(1.0, 0.75, 0.25, 1.0), emission_strength=6.0)
        wood_m = make_mat(f"{self.id}_wood", (0.45, 0.28, 0.14, 1.0), roughness=0.8)

        # Backpack on torso back (+Y)
        bp = add_box(f"{self.id}_p_backpack", (0.58, 0.28, 0.62), loc=(0, 0.32, 0.40), mat=pack_m, parent=self.body_pivot, bevel=0.03)
        bp.scale = (0, 0, 0)
        self.props["backpack"] = bp

        # Coin in right hand
        cn = add_cyl(f"{self.id}_p_coin", 0.12, 0.04, loc=(0, -0.18, -0.68), rot=(math.radians(90), 0, 0), mat=gold_m, parent=self.arm_r)
        cn.scale = (0, 0, 0)
        self.props["coin"] = cn

        # Lantern in right hand
        lt = add_box(f"{self.id}_p_lantern", (0.20, 0.20, 0.28), loc=(0, -0.18, -0.82), mat=glow_m, parent=self.arm_r, bevel=0.02)
        lt.scale = (0, 0, 0)
        self.props["lantern"] = lt

        # Broom / Cane in right hand
        br = add_cyl(f"{self.id}_p_broom", 0.04, 1.4, loc=(0, -0.16, -0.75), rot=(math.radians(25), 0, 0), mat=wood_m, parent=self.arm_r)
        br.scale = (0, 0, 0)
        self.props["broom"] = br
        self.props["cane"] = br

        # Letter / note
        nt = add_box(f"{self.id}_p_letter", (0.26, 0.03, 0.32), loc=(0, -0.22, -0.64), mat=make_mat(f"{self.id}_pap", (0.96, 0.94, 0.88, 1.0)), parent=self.arm_r, bevel=0.005)
        nt.scale = (0, 0, 0)
        self.props["letter"] = nt

    def set_shot(self, actor_state: dict, f0: int, f1: int, fps: int):
        pos = actor_state.get("pos", [0, 0, 0])
        # Convert Three.js-style [x, y_up, z_depth] -> Blender [x, z_depth, y_up]
        bx, by, bz = float(pos[0]), float(pos[2]), float(pos[1])
        rot_z = math.radians(float(actor_state.get("rot_y", 0)))

        set_key(self.root, "location", f0, (bx, by, bz), "CONSTANT")
        set_key(self.root, "rotation_euler", f0, (0, 0, rot_z), "CONSTANT")

        # Face decal swap (CONSTANT)
        face = actor_state.get("face", "neutral")
        if face not in self.face_planes:
            face = "neutral"
        for expr, pl in self.face_planes.items():
            set_key(pl, "scale", f0, (1, 1, 1) if expr == face else (0, 0, 0), "CONSTANT")

        # Stone legs (keyframed material Base Color so it only changes on stone_legs shots!)
        stone = bool(actor_state.get("stone_legs", False))
        leg_col = (0.35, 0.36, 0.38, 1.0) if stone else self.pants_col_rgba
        _set_socket_const(self.pants_mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"], f0, leg_col)

        # Translucent / ghost mode
        alpha = 0.38 if bool(actor_state.get("translucent", False)) else 1.0
        for mat in (self.skin_mat, self.shirt_mat, self.pants_mat, self.hair_mat):
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf and "Alpha" in bsdf.inputs:
                _set_socket_const(bsdf.inputs["Alpha"], f0, alpha)

        # Props
        active_prop = actor_state.get("prop", "none")
        for pname, pobj in self.props.items():
            on = (pname == active_prop)
            # Note: scale stored in base obj
            if pname == "backpack":
                s = (0.58, 0.28, 0.62) if on else (0, 0, 0)
            elif pname == "lantern":
                s = (0.20, 0.20, 0.28) if on else (0, 0, 0)
            elif pname == "letter":
                s = (0.26, 0.03, 0.32) if on else (0, 0, 0)
            else:
                s = (1, 1, 1) if on else (0, 0, 0)
            set_key(pobj, "scale", f0, s, "CONSTANT")

        # Animation cycles across [f0, f1]
        anim = actor_state.get("anim", "idle")
        self.shot_end_pos = (bx, by, bz)
        # Reset body/head/limbs at f0
        set_key(self.body_pivot, "location", f0, (0, 0, 0.78), "LINEAR")
        set_key(self.body_pivot, "rotation_euler", f0, (0, 0, 0), "LINEAR")
        set_key(self.head_pivot, "rotation_euler", f0, (0, 0, 0), "LINEAR")

        if anim in ("walk", "run"):
            amp = 0.78 if anim == "run" else 0.48
            step_frames = 5 if anim == "run" else 9
            speed = 5.2 if anim == "run" else 2.0
            lean = -0.22 if anim == "run" else -0.05
            # Move forward along local -Y over the shot so background scrolls past!
            dx = math.sin(rot_z) * speed * ((f1 - f0) / fps)
            dy = -math.cos(rot_z) * speed * ((f1 - f0) / fps)
            self.shot_end_pos = (bx + dx, by + dy, bz)
            set_key(self.root, "location", f1, self.shot_end_pos, "LINEAR")
            set_key(self.body_pivot, "rotation_euler", f0, (lean, 0, 0), "LINEAR")

            for f in range(f0, f1 + 1, max(2, step_frames // 2)):
                phase = ((f - f0) / step_frames) * math.pi * 2.0
                s = math.sin(phase) * amp
                set_key(self.leg_l, "rotation_euler", f, (s, 0, 0), "LINEAR")
                set_key(self.leg_r, "rotation_euler", f, (-s, 0, 0), "LINEAR")
                set_key(self.arm_l, "rotation_euler", f, (-s * 0.9, 0, 0), "LINEAR")
                set_key(self.arm_r, "rotation_euler", f, (s * 0.9, 0, 0), "LINEAR")
                set_key(self.body_pivot, "location", f, (0, 0, 0.78 + abs(math.cos(phase)) * (0.09 if anim == "run" else 0.05)), "LINEAR")
        elif anim == "wave":
            set_key(self.leg_l, "rotation_euler", f0, (0, 0, 0), "LINEAR")
            set_key(self.leg_r, "rotation_euler", f0, (0, 0, 0), "LINEAR")
            set_key(self.arm_l, "rotation_euler", f0, (0, 0, 0), "LINEAR")
            for f in range(f0, f1 + 1, 5):
                w = math.sin((f - f0) * 0.6) * 0.35
                set_key(self.arm_r, "rotation_euler", f, (0, 2.5 + w, 0), "LINEAR")
        elif anim == "cry":
            set_key(self.leg_l, "rotation_euler", f0, (0, 0, 0), "LINEAR")
            set_key(self.leg_r, "rotation_euler", f0, (0, 0, 0), "LINEAR")
            set_key(self.arm_l, "rotation_euler", f0, (-1.8, 0, 0.35), "LINEAR")
            set_key(self.arm_r, "rotation_euler", f0, (-1.8, 0, -0.35), "LINEAR")
            set_key(self.head_pivot, "rotation_euler", f0, (0.25, 0, 0), "LINEAR")
        elif anim == "fall":
            set_key(self.root, "rotation_euler", f0, (math.radians(82), 0, rot_z), "CONSTANT")
            set_key(self.root, "location", f0, (bx, by, bz + 0.25), "CONSTANT")
            set_key(self.leg_l, "rotation_euler", f0, (0, 0, 0), "CONSTANT")
            set_key(self.leg_r, "rotation_euler", f0, (0, 0, 0), "CONSTANT")
            set_key(self.arm_l, "rotation_euler", f0, (-0.8, 0, 0.5), "CONSTANT")
            set_key(self.arm_r, "rotation_euler", f0, (-0.8, 0, -0.5), "CONSTANT")
        elif anim == "sit":
            set_key(self.root, "location", f0, (bx, by, bz - 0.35), "CONSTANT")
            set_key(self.leg_l, "rotation_euler", f0, (-1.45, 0, 0), "CONSTANT")
            set_key(self.leg_r, "rotation_euler", f0, (-1.45, 0, 0), "CONSTANT")
            set_key(self.arm_l, "rotation_euler", f0, (-0.4, 0, 0), "CONSTANT")
            set_key(self.arm_r, "rotation_euler", f0, (-0.4, 0, 0), "CONSTANT")
        elif anim == "handstand":
            set_key(self.root, "rotation_euler", f0, (math.radians(180), 0, rot_z), "CONSTANT")
            set_key(self.root, "location", f0, (bx, by, bz + 2.2 * self.scale_factor), "CONSTANT")
            set_key(self.arm_l, "rotation_euler", f0, (-3.0, 0, 0), "CONSTANT")
            set_key(self.arm_r, "rotation_euler", f0, (-3.0, 0, 0), "CONSTANT")
        elif anim == "point":
            set_key(self.leg_l, "rotation_euler", f0, (0, 0, 0), "LINEAR")
            set_key(self.leg_r, "rotation_euler", f0, (0, 0, 0), "LINEAR")
            set_key(self.arm_l, "rotation_euler", f0, (0, 0, 0), "LINEAR")
            set_key(self.arm_r, "rotation_euler", f0, (-1.45, 0, 0), "LINEAR")
        else:  # idle / peek / hold_hands / hunch
            set_key(self.leg_l, "rotation_euler", f0, (0, 0, 0), "LINEAR")
            set_key(self.leg_r, "rotation_euler", f0, (0, 0, 0), "LINEAR")
            arm_x = -0.35 if anim == "hold_hands" else 0.0
            set_key(self.arm_l, "rotation_euler", f0, (arm_x, 0, 0), "LINEAR")
            set_key(self.arm_r, "rotation_euler", f0, (arm_x, 0, 0), "LINEAR")
            if anim == "hunch":
                set_key(self.body_pivot, "rotation_euler", f0, (0.35, 0, 0), "LINEAR")
            # Gentle breathing bob
            set_key(self.body_pivot, "location", f1, (0, 0, 0.80), "LINEAR")


# ---------------------------------------------------------------------------
# Procedural Creature / Monster Builder
# ---------------------------------------------------------------------------
class ProceduralCreature:
    def __init__(self, spec: dict, collection):
        self.id = spec["id"]
        arch = spec.get("archetype", "fur_giant")
        sc = float(spec.get("scale", 2.6))
        self.focus_height = (0.50 * sc) if arch == "tiny_pet" else (1.42 * sc)
        pcol = hex_to_rgba(spec.get("primary_color", "#141418"))
        scol = hex_to_rgba(spec.get("secondary_color", "#F2EAD8"))

        self.root = bpy.data.objects.new(f"creature_{self.id}", None)
        collection.objects.link(self.root)
        self.root.scale = (sc, sc, sc)

        body_mat = make_mat(f"{self.id}_bmat", pcol, roughness=0.88)
        teeth_mat = make_mat(f"{self.id}_tmat", (0.96, 0.93, 0.86, 1.0), roughness=0.35)
        gum_mat = make_mat(f"{self.id}_gmat", (0.32, 0.12, 0.14, 1.0), roughness=0.6)
        glow_eye_mat = make_mat(f"{self.id}_emat", (1.0, 0.08, 0.08, 1.0), emission=(1.0, 0.08, 0.08, 1.0), emission_strength=9.0)

        if arch == "tiny_pet":
            # Cute round potato-axolotl creature
            add_sphere(f"{self.id}_body", 0.45, loc=(0, 0, 0.45), scale=(1.08, 1.0, 0.92), mat=body_mat, parent=self.root)
            add_sphere(f"{self.id}_fL", 0.13, loc=(-0.22, -0.1, 0.10), mat=body_mat, parent=self.root)
            add_sphere(f"{self.id}_fR", 0.13, loc=(0.22, -0.1, 0.10), mat=body_mat, parent=self.root)
            if "horns" in spec.get("features", []):
                add_cone(f"{self.id}_hrnL", 0.07, 0.02, 0.24, loc=(-0.18, 0, 0.88), rot=(0, -0.2, 0), mat=make_mat(f"{self.id}_hm", scol), parent=self.root)
                add_cone(f"{self.id}_hrnR", 0.07, 0.02, 0.24, loc=(0.18, 0, 0.88), rot=(0, 0.2, 0), mat=make_mat(f"{self.id}_hm2", scol), parent=self.root)
            # Big cute eyes + buckteeth
            eye_w = make_mat(f"{self.id}_ew", (0.04, 0.04, 0.05, 1.0))
            add_sphere(f"{self.id}_eL", 0.09, loc=(-0.16, -0.40, 0.52), mat=eye_w, parent=self.root)
            add_sphere(f"{self.id}_eR", 0.09, loc=(0.16, -0.40, 0.52), mat=eye_w, parent=self.root)
            add_box(f"{self.id}_bt", (0.10, 0.04, 0.10), loc=(0, -0.44, 0.33), mat=teeth_mat, parent=self.root, bevel=0.01)
        else:
            # Giant furry / shadow monster
            add_box(f"{self.id}_torso", (0.85, 0.55, 0.92), loc=(0, 0, 1.15), mat=body_mat, parent=self.root, bevel=0.08)
            add_box(f"{self.id}_head", (0.58, 0.52, 0.50), loc=(0, -0.14, 1.68), mat=body_mat, parent=self.root, bevel=0.08)
            add_box(f"{self.id}_legL", (0.30, 0.34, 0.72), loc=(-0.25, 0, 0.36), mat=body_mat, parent=self.root, bevel=0.04)
            add_box(f"{self.id}_legR", (0.30, 0.34, 0.72), loc=(0.25, 0, 0.36), mat=body_mat, parent=self.root, bevel=0.04)
            add_box(f"{self.id}_armL", (0.28, 0.30, 0.95), loc=(-0.60, -0.05, 1.05), mat=body_mat, parent=self.root, bevel=0.04)
            add_box(f"{self.id}_armR", (0.28, 0.30, 0.95), loc=(0.60, -0.05, 1.05), mat=body_mat, parent=self.root, bevel=0.04)

            # Procedural fur spikes (dense outward-angled tufts)
            if "fur_spikes" in spec.get("features", []) or arch == "fur_giant":
                rng = random.Random(hash(self.id) & 0xFFFF)
                for idx in range(52):
                    fx = rng.uniform(-0.72, 0.72)
                    fy = rng.uniform(-0.30, 0.32)
                    fz = rng.uniform(0.35, 1.90)
                    rx = rng.uniform(-0.9, 0.9)
                    ry = rng.uniform(-0.9, 0.9)
                    add_cone(f"{self.id}_fur{idx}", 0.09, 0.008, 0.36, loc=(fx, fy, fz), rot=(rx, ry, 0), mat=body_mat, parent=self.root, verts=4)

            # Mouth: giant curved row of flat human teeth
            mouth_t = spec.get("mouth_type", "human_teeth")
            if mouth_t != "none":
                add_box(f"{self.id}_gums", (0.50, 0.12, 0.20), loc=(0, -0.40, 1.56), mat=gum_mat, parent=self.root, bevel=0.02)
                n_teeth = 7
                for ti in range(n_teeth):
                    tx = -0.18 + ti * (0.36 / (n_teeth - 1))
                    tz_off = (tx * tx) * 0.25
                    add_box(f"{self.id}_tu{ti}", (0.045, 0.05, 0.07), loc=(tx, -0.44, 1.60 + tz_off), mat=teeth_mat, parent=self.root, bevel=0.004)
                    add_box(f"{self.id}_tl{ti}", (0.045, 0.05, 0.07), loc=(tx, -0.44, 1.52 - tz_off), mat=teeth_mat, parent=self.root, bevel=0.004)

            # Eyes
            if spec.get("eye_type", "none") == "glow_red":
                add_sphere(f"{self.id}_geL", 0.06, loc=(-0.14, -0.41, 1.76), mat=glow_eye_mat, parent=self.root)
                add_sphere(f"{self.id}_geR", 0.06, loc=(0.14, -0.41, 1.76), mat=glow_eye_mat, parent=self.root)

    def set_shot(self, actor_state: dict, f0: int, f1: int):
        pos = actor_state.get("pos", [0, 0, 0])
        bx, by, bz = float(pos[0]), float(pos[2]), float(pos[1])
        self.shot_end_pos = (bx, by, bz + 0.05)
        rot_z = math.radians(float(actor_state.get("rot_y", 0)))
        set_key(self.root, "location", f0, (bx, by, bz), "CONSTANT")
        set_key(self.root, "rotation_euler", f0, (0, 0, rot_z), "CONSTANT")
        # Menacing subtle loom/bob
        set_key(self.root, "location", f1, self.shot_end_pos, "LINEAR")


# ---------------------------------------------------------------------------
# Modular 3D Environments
# ---------------------------------------------------------------------------
def build_environments(scene):
    sets = {}

    def make_col(name):
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
        return col

    def link_to(obj, col):
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        col.objects.link(obj)

    def add_env_box(name, size, loc, mat, col, rot=(0, 0, 0), bevel=0.02):
        o = add_box(name, size, loc=loc, mat=mat, bevel=bevel)
        if rot != (0, 0, 0):
            o.rotation_euler = rot
        link_to(o, col)
        return o

    def add_env_cyl(name, r, d, loc, mat, col, rot=(0, 0, 0), verts=16):
        o = add_cyl(name, r, d, loc=loc, rot=rot, mat=mat, verts=verts)
        link_to(o, col)
        return o

    def add_env_cone(name, r1, r2, d, loc, mat, col, rot=(0, 0, 0), verts=6):
        o = add_cone(name, r1, r2, d, loc=loc, rot=rot, mat=mat, verts=verts)
        link_to(o, col)
        return o

    def add_tree(prefix, x, y, col, trunk_m, leaf_m, leaf_m2, scale=1.0):
        add_env_cyl(f"{prefix}_tr", 0.22 * scale, 2.2 * scale, (x, y, 1.1 * scale), trunk_m, col, verts=10)
        add_env_cone(f"{prefix}_c1", 1.35 * scale, 0.2 * scale, 1.9 * scale, (x, y, 2.6 * scale), leaf_m, col, verts=7)
        add_env_cone(f"{prefix}_c2", 1.05 * scale, 0.15 * scale, 1.6 * scale, (x, y, 3.6 * scale), leaf_m2, col, verts=7)
        add_env_cone(f"{prefix}_c3", 0.72 * scale, 0.08 * scale, 1.2 * scale, (x, y, 4.4 * scale), leaf_m, col, verts=7)

    # Rich procedural textured materials
    road_mat = make_textured_mat("env_road", (0.12, 0.13, 0.15, 1.0), (0.20, 0.21, 0.23, 1.0), scale=6.0, roughness=0.9, bump_strength=0.18)
    stripe_mat = make_mat("env_stripe", (0.90, 0.75, 0.16, 1.0), roughness=0.55)
    grass_mat = make_textured_mat("env_grass", (0.11, 0.27, 0.09, 1.0), (0.20, 0.40, 0.15, 1.0), scale=3.5, roughness=0.92, bump_strength=0.22)
    leaf_mat1 = make_textured_mat("env_leaf1", (0.09, 0.28, 0.10, 1.0), (0.16, 0.42, 0.14, 1.0), scale=4.0, roughness=0.85, bump_strength=0.20)
    leaf_mat2 = make_textured_mat("env_leaf2", (0.14, 0.34, 0.11, 1.0), (0.22, 0.48, 0.16, 1.0), scale=4.0, roughness=0.85, bump_strength=0.20)
    sidewalk_mat = make_textured_mat("env_sw", (0.52, 0.52, 0.50, 1.0), (0.64, 0.63, 0.60, 1.0), scale=5.0, roughness=0.85, bump_strength=0.10)
    trim_white = make_mat("env_trim_w", (0.92, 0.91, 0.88, 1.0), roughness=0.6)
    shutter_mat = make_mat("env_shut", (0.14, 0.22, 0.32, 1.0), roughness=0.65)
    brick_mat = make_textured_mat("env_brick", (0.42, 0.16, 0.12, 1.0), (0.55, 0.24, 0.18, 1.0), scale=7.0, roughness=0.85, bump_strength=0.25)
    house_mats = [
        make_textured_mat("env_hw_cream", (0.76, 0.70, 0.58, 1.0), (0.84, 0.78, 0.66, 1.0), scale=4.5, roughness=0.8, bump_strength=0.10),
        make_textured_mat("env_hw_blue", (0.42, 0.56, 0.70, 1.0), (0.50, 0.64, 0.78, 1.0), scale=4.5, roughness=0.8, bump_strength=0.10),
        make_textured_mat("env_hw_sage", (0.46, 0.58, 0.48, 1.0), (0.54, 0.66, 0.56, 1.0), scale=4.5, roughness=0.8, bump_strength=0.10),
        make_textured_mat("env_hw_butter", (0.82, 0.74, 0.48, 1.0), (0.88, 0.80, 0.56, 1.0), scale=4.5, roughness=0.8, bump_strength=0.10),
    ]
    roof_mats = [
        make_textured_mat("env_rf1", (0.28, 0.16, 0.12, 1.0), (0.38, 0.23, 0.17, 1.0), scale=6.0, roughness=0.78, bump_strength=0.2),
        make_textured_mat("env_rf2", (0.18, 0.20, 0.24, 1.0), (0.25, 0.28, 0.33, 1.0), scale=6.0, roughness=0.78, bump_strength=0.2),
    ]
    door_mat = make_textured_mat("env_door", (0.22, 0.12, 0.08, 1.0), (0.30, 0.17, 0.11, 1.0), scale=6.0, roughness=0.6, bump_strength=0.12)
    brass_mat = make_mat("env_brass", (0.88, 0.70, 0.22, 1.0), metallic=0.85, roughness=0.28)
    iron_mat = make_mat("env_iron", (0.10, 0.11, 0.13, 1.0), metallic=0.65, roughness=0.45)
    win_mat = make_mat("env_win", (0.72, 0.85, 0.96, 1.0), roughness=0.15, emission=(1.0, 0.80, 0.42, 1.0), emission_strength=1.1)
    lamp_glow = make_mat("env_lamp_gl", (1.0, 0.88, 0.55, 1.0), emission=(1.0, 0.82, 0.40, 1.0), emission_strength=6.5)
    pole_mat = make_textured_mat("env_pole", (0.24, 0.16, 0.10, 1.0), (0.34, 0.23, 0.14, 1.0), scale=5.0, roughness=0.88, bump_strength=0.22)

    # 1. SUBURBAN STREET
    c_sub = make_col("set_suburban_street")
    sets["suburban_street"] = c_sub
    add_env_box("sub_grass", (110, 180, 0.2), (0, 0, -0.1), grass_mat, c_sub, bevel=0)
    add_env_box("sub_road", (6.4, 180, 0.05), (0, 0, 0.015), road_mat, c_sub, bevel=0)
    for dy in range(-75, 78, 5):
        add_env_box(f"sub_line_{dy}", (0.18, 2.3, 0.06), (0, dy, 0.025), stripe_mat, c_sub, bevel=0)

    for side in (-1, 1):
        # Curbs + sidewalks
        add_env_box(f"sub_curb_{side}", (0.22, 180, 0.14), (side * 3.25, 0, 0.07), sidewalk_mat, c_sub, bevel=0.01)
        add_env_box(f"sub_sw_{side}", (1.65, 180, 0.10), (side * 4.15, 0, 0.05), sidewalk_mat, c_sub, bevel=0)

        for idx_h, hy in enumerate(range(-60, 65, 13)):
            hx = side * 9.0
            hmat = house_mats[(idx_h + (0 if side == -1 else 2)) % len(house_mats)]
            rmat = roof_mats[idx_h % len(roof_mats)]
            face_x = hx - side * 2.8  # Front wall X facing road

            # Stone foundation + Main house body
            add_env_box(f"sub_fnd_{side}_{hy}", (5.8, 7.6, 0.35), (hx, hy, 0.175), sidewalk_mat, c_sub, bevel=0.02)
            add_env_box(f"sub_h_{side}_{hy}", (5.6, 7.4, 3.4), (hx, hy, 2.05), hmat, c_sub, bevel=0.03)
            # Overhanging roof + fascia trim + chimney
            add_env_cone(f"sub_r_{side}_{hy}", 5.3, 0.15, 2.4, (hx, hy, 4.95), rmat, c_sub, rot=(0, 0, math.radians(45)), verts=4)
            add_env_box(f"sub_fas_{side}_{hy}", (6.1, 7.9, 0.18), (hx, hy, 3.78), trim_white, c_sub, bevel=0.01)
            add_env_box(f"sub_chm_{side}_{hy}", (0.75, 0.75, 1.8), (hx + side * 1.4, hy + 2.0, 5.1), brick_mat, c_sub, bevel=0.02)

            # Covered Front Porch (deck, steps, 2 pillars, porch roof)
            px = face_x - side * 0.85
            add_env_box(f"sub_pd_{side}_{hy}", (1.7, 3.8, 0.28), (px, hy, 0.14), sidewalk_mat, c_sub, bevel=0.02)
            add_env_box(f"sub_pr_{side}_{hy}", (1.9, 4.0, 0.18), (px, hy, 2.75), rmat, c_sub, bevel=0.02)
            for py_off in (-1.65, 1.65):
                add_env_box(f"sub_pp_{side}_{hy}_{py_off}", (0.18, 0.18, 2.4), (px - side * 0.65, hy + py_off, 1.48), trim_white, c_sub, bevel=0.01)

            # Framed Front Door + Brass handle + Mail slot
            add_env_box(f"sub_df_{side}_{hy}", (0.12, 1.32, 2.28), (face_x, hy, 1.42), trim_white, c_sub, bevel=0.01)
            add_env_box(f"sub_d_{side}_{hy}", (0.14, 1.10, 2.14), (face_x, hy, 1.36), door_mat, c_sub, bevel=0.01)
            add_env_box(f"sub_ms_{side}_{hy}", (0.16, 0.34, 0.10), (face_x, hy, 1.15), brass_mat, c_sub, bevel=0.005)
            add_env_box(f"sub_dk_{side}_{hy}", (0.18, 0.08, 0.08), (face_x, hy + 0.38, 1.25), brass_mat, c_sub, bevel=0.005)

            # Framed Windows + Shutters
            for wy in (hy - 2.3, hy + 2.3):
                add_env_box(f"sub_wf_{side}_{hy}_{wy}", (0.12, 1.45, 1.38), (face_x, wy, 2.0), trim_white, c_sub, bevel=0.01)
                add_env_box(f"sub_w_{side}_{hy}_{wy}", (0.14, 1.22, 1.14), (face_x, wy, 2.0), win_mat, c_sub, bevel=0.01)
                for sy in (-0.82, 0.82):
                    add_env_box(f"sub_sh_{side}_{hy}_{wy}_{sy}", (0.10, 0.28, 1.24), (face_x, wy + sy, 2.0), shutter_mat, c_sub, bevel=0.01)

            # Walk path + White Picket Fence between yards
            add_env_box(f"sub_wp_{side}_{hy}", (1.8, 1.2, 0.08), (side * 5.2, hy, 0.04), sidewalk_mat, c_sub, bevel=0)
            fy = hy + 6.5
            add_env_box(f"sub_frail_{side}_{hy}", (0.08, 0.08, 0.10), (side * 5.3, fy, 0.65), trim_white, c_sub, bevel=0)
            for fx_i in range(4):
                add_env_box(f"sub_fp_{side}_{hy}_{fx_i}", (0.12, 0.12, 0.95), (side * (5.3 + fx_i * 1.1), fy, 0.48), trim_white, c_sub, bevel=0.01)

            # Stylized Tree + Bushes in yard
            add_tree(f"sub_tr_{side}_{hy}", side * 6.0, hy - 4.3, c_sub, pole_mat, leaf_mat1, leaf_mat2, scale=0.95 + (idx_h % 2) * 0.2)
            add_env_box(f"sub_bsh_{side}_{hy}", (0.95, 1.3, 0.65), (face_x - side * 0.4, hy + 2.4, 0.35), leaf_mat2, c_sub, bevel=0.14)

            # Tall Iron Streetlamp along curb
            lx = side * 3.45
            ly = hy + 4.8
            add_env_cyl(f"sub_lp_{side}_{hy}", 0.07, 4.4, (lx, ly, 2.2), iron_mat, c_sub, verts=10)
            add_env_box(f"sub_la_{side}_{hy}", (0.75, 0.08, 0.08), (lx - side * 0.35, ly, 4.35), iron_mat, c_sub, bevel=0.01)
            add_env_box(f"sub_lh_{side}_{hy}", (0.34, 0.34, 0.42), (lx - side * 0.68, ly, 4.15), lamp_glow, c_sub, bevel=0.02)

            # Utility pole + overhead wire
            add_env_cyl(f"sub_pl_{side}_{hy}", 0.11, 6.2, (side * 5.0, hy + 6.2, 3.1), pole_mat, c_sub, verts=10)
            add_env_box(f"sub_wr_{side}_{hy}", (0.03, 13.0, 0.03), (side * 5.0, hy + 12.7, 5.9), iron_mat, c_sub, bevel=0)

    # Park benches along sidewalk (including near y=-3 where characters sit!)
    for by in (-3.0, 10.0, 23.0):
        add_env_box(f"sub_bn_seat_{by}", (0.65, 1.8, 0.10), (-3.5, by, 0.48), pole_mat, c_sub, bevel=0.02)
        add_env_box(f"sub_bn_back_{by}", (0.10, 1.8, 0.55), (-3.8, by, 0.78), pole_mat, c_sub, bevel=0.02)
        for bleg in (-0.75, 0.75):
            add_env_box(f"sub_bn_leg_{by}_{bleg}", (0.60, 0.08, 0.48), (-3.5, by + bleg, 0.24), iron_mat, c_sub, bevel=0.01)

    # 2. HOUSE INTERIOR
    c_int = make_col("set_house_interior")
    sets["house_interior"] = c_int
    wood_wall = make_textured_mat("int_wall", (0.40, 0.24, 0.13, 1.0), (0.48, 0.30, 0.17, 1.0), scale=4.0, roughness=0.80, bump_strength=0.14)
    wood_floor = make_textured_mat("int_floor", (0.24, 0.14, 0.08, 1.0), (0.33, 0.20, 0.11, 1.0), scale=6.0, roughness=0.72, bump_strength=0.15)
    bed_mat = make_textured_mat("int_bed", (0.18, 0.28, 0.45, 1.0), (0.24, 0.35, 0.54, 1.0), scale=5.0, roughness=0.85, bump_strength=0.10)
    rug_mat = make_textured_mat("int_rug", (0.52, 0.15, 0.15, 1.0), (0.64, 0.22, 0.20, 1.0), scale=8.0, roughness=0.92, bump_strength=0.18)
    note_mat = make_mat("int_note", (0.94, 0.90, 0.78, 1.0), roughness=0.7)
    for nm, sz, lc, mt in [
        ("int_fl", (10, 10, 0.1), (0, 0, -0.05), wood_floor),
        ("int_rug_b", (4.0, 3.1, 0.02), (0, 1.2, 0.01), trim_white),
        ("int_rug", (3.6, 2.7, 0.03), (0, 1.2, 0.02), rug_mat),
        ("int_wb", (10, 0.22, 4.4), (0, 4.5, 2.2), wood_wall),
        ("int_wl", (0.22, 10, 4.4), (-4.5, 0, 2.2), wood_wall),
        ("int_wr", (0.22, 10, 4.4), (4.5, 0, 2.2), wood_wall),
        ("int_base_b", (9.2, 0.28, 0.22), (0, 4.44, 0.11), trim_white),
        ("int_tbl_top", (2.0, 1.15, 0.10), (0, 1.5, 0.80), wood_floor),
        ("int_tbl_l1", (0.12, 0.12, 0.78), (-0.85, 1.05, 0.39), wood_floor),
        ("int_tbl_l2", (0.12, 0.12, 0.78), (0.85, 1.05, 0.39), wood_floor),
        ("int_tbl_l3", (0.12, 0.12, 0.78), (-0.85, 1.95, 0.39), wood_floor),
        ("int_tbl_l4", (0.12, 0.12, 0.78), (0.85, 1.95, 0.39), wood_floor),
        ("int_note_p", (0.35, 0.45, 0.02), (0.1, 1.4, 0.86), note_mat),
        ("int_bed_hb", (1.7, 0.16, 1.35), (-2.9, 3.8, 0.68), wood_floor),
        ("int_bed", (1.6, 2.4, 0.62), (-2.9, 2.6, 0.31), bed_mat),
        ("int_pil", (1.2, 0.5, 0.18), (-2.9, 3.4, 0.70), note_mat),
        ("int_door_f", (1.42, 0.18, 2.42), (2.4, 4.35, 1.21), trim_white),
        ("int_door", (1.2, 0.16, 2.3), (2.4, 4.33, 1.15), door_mat),
        ("int_win_f", (2.05, 0.14, 1.42), (-1.4, 4.38, 2.2), trim_white),
        ("int_win", (1.8, 0.12, 1.2), (-1.4, 4.36, 2.2), win_mat),
        ("int_pic_f", (1.06, 0.08, 0.86), (0.4, 4.38, 2.15), wood_floor),
        ("int_pic", (0.88, 0.09, 0.68), (0.4, 4.36, 2.15), note_mat),
        # Bookshelf
        ("int_sh_bk", (1.5, 0.45, 2.3), (3.8, 3.8, 1.15), wood_floor),
    ]:
        add_env_box(nm, sz, lc, mt, c_int, bevel=0.02)
    # Table lamp + wall sconce
    add_env_cyl("int_tl_base", 0.12, 0.30, (-0.65, 1.7, 1.0), brass_mat, c_int)
    add_env_cone("int_tl_shade", 0.24, 0.14, 0.28, (-0.65, 1.7, 1.24), lamp_glow, c_int, verts=12)
    add_env_box("int_lamp", (0.32, 0.32, 0.36), (0, 4.2, 3.2), lamp_glow, c_int, bevel=0.02)

    # 3. HOSPITAL ROOM
    c_hosp = make_col("set_hospital_room")
    sets["hospital_room"] = c_hosp
    hosp_wall = make_textured_mat("hosp_w", (0.78, 0.83, 0.88, 1.0), (0.85, 0.89, 0.93, 1.0), scale=4.0, roughness=0.45, bump_strength=0.06)
    hosp_fl = make_textured_mat("hosp_f", (0.62, 0.68, 0.74, 1.0), (0.72, 0.78, 0.82, 1.0), scale=8.0, roughness=0.35, bump_strength=0.08)
    ecg_mat = make_mat("hosp_ecg", (0.1, 0.95, 0.35, 1.0), emission=(0.1, 0.95, 0.35, 1.0), emission_strength=5.5)
    curtain_mat = make_mat("hosp_curt", (0.65, 0.80, 0.88, 1.0), roughness=0.85)
    for nm, sz, lc, mt in [
        ("hp_fl", (10, 10, 0.1), (0, 0, -0.05), hosp_fl),
        ("hp_wb", (10, 0.22, 4.4), (0, 4.5, 2.2), hosp_wall),
        ("hp_wl", (0.22, 10, 4.4), (-4.5, 0, 2.2), hosp_wall),
        ("hp_wr", (0.22, 10, 4.4), (4.5, 0, 2.2), hosp_wall),
        ("hp_bed_hb", (1.7, 0.14, 1.25), (0, 3.65, 0.62), trim_white),
        ("hp_bed", (1.6, 2.5, 0.68), (0, 2.4, 0.34), trim_white),
        ("hp_blnk", (1.64, 1.6, 0.22), (0, 1.95, 0.62), shutter_mat),
        ("hp_pil", (1.1, 0.45, 0.18), (0, 3.25, 0.75), note_mat),
        ("hp_cab", (0.75, 0.65, 0.95), (1.45, 3.2, 0.48), trim_white),
        ("hp_mon", (0.65, 0.25, 0.50), (1.45, 3.2, 1.22), iron_mat),
        ("hp_scr", (0.55, 0.05, 0.38), (1.45, 3.06, 1.22), ecg_mat),
        ("hp_curt", (0.08, 3.2, 2.8), (-1.9, 2.4, 1.8), curtain_mat),
        ("hp_win_f", (2.2, 0.12, 1.5), (-1.8, 4.38, 2.3), trim_white),
        ("hp_win", (2.0, 0.10, 1.3), (-1.8, 4.36, 2.3), win_mat),
    ]:
        add_env_box(nm, sz, lc, mt, c_hosp, bevel=0.02)
    add_env_cyl("hp_iv_pole", 0.04, 2.2, (-1.15, 3.1, 1.1), iron_mat, c_hosp, verts=10)
    add_env_box("hp_iv_bag", (0.22, 0.12, 0.34), (-1.05, 3.1, 1.95), win_mat, c_hosp, bevel=0.04)

    # 4. MEDIEVAL VILLAGE
    c_med = make_col("set_medieval_village")
    sets["medieval_village"] = c_med
    cobble = make_textured_mat("med_cob", (0.26, 0.25, 0.27, 1.0), (0.42, 0.41, 0.42, 1.0), scale=9.0, roughness=0.90, bump_strength=0.30)
    tudor_w = make_textured_mat("med_tw", (0.76, 0.72, 0.62, 1.0), (0.86, 0.82, 0.72, 1.0), scale=5.0, roughness=0.85, bump_strength=0.14)
    med_roof = make_textured_mat("med_rf", (0.20, 0.18, 0.42, 1.0), (0.28, 0.25, 0.54, 1.0), scale=6.0, roughness=0.72, bump_strength=0.18)
    add_env_box("med_fl", (90, 90, 0.1), (0, 0, -0.05), cobble, c_med, bevel=0)
    for side in (-1, 1):
        for hy in range(-36, 40, 13):
            hx = side * 7.8
            face_x = hx - side * 2.55
            # Stone ground floor + overhanging Tudor upper floor + steep roof
            add_env_box(f"med_st_{side}_{hy}", (5.0, 6.4, 1.8), (hx, hy, 0.9), cobble, c_med, bevel=0.03)
            add_env_box(f"med_h_{side}_{hy}", (5.4, 6.8, 2.3), (hx - side * 0.15, hy, 2.95), tudor_w, c_med, bevel=0.03)
            add_env_cone(f"med_r_{side}_{hy}", 4.9, 0.15, 2.8, (hx - side * 0.15, hy, 5.5), med_roof, c_med, rot=(0, 0, math.radians(45)), verts=4)
            add_env_box(f"med_chm_{side}_{hy}", (0.7, 0.7, 1.6), (hx + side * 1.2, hy + 1.5, 5.6), cobble, c_med, bevel=0.02)
            # Tudor timber beams
            for bz in (1.85, 3.0, 4.05):
                add_env_box(f"med_bh_{side}_{hy}_{bz}", (0.14, 6.85, 0.20), (face_x - side * 0.30, hy, bz), pole_mat, c_med, bevel=0.01)
            for by_off in (-3.2, 0.0, 3.2):
                add_env_box(f"med_bv_{side}_{hy}_{by_off}", (0.14, 0.20, 2.3), (face_x - side * 0.30, hy + by_off, 2.95), pole_mat, c_med, bevel=0.01)
            # Door + Glowing Windows + Barrel
            add_env_box(f"med_d_{side}_{hy}", (0.14, 1.15, 2.1), (face_x, hy, 1.05), door_mat, c_med, bevel=0.02)
            add_env_box(f"med_w_{side}_{hy}", (0.14, 1.4, 1.1), (face_x - side * 0.30, hy + 1.6, 2.95), win_mat, c_med, bevel=0.01)
            add_env_cyl(f"med_brl_{side}_{hy}", 0.38, 0.95, (face_x - side * 0.5, hy - 1.8, 0.48), pole_mat, c_med, verts=12)
            add_env_box(f"med_sc_{side}_{hy}", (0.28, 0.28, 0.38), (face_x - side * 0.45, hy - 1.2, 2.2), lamp_glow, c_med, bevel=0.02)
    # Central Stone Town Well
    add_env_cyl("med_well_b", 1.5, 0.85, (0, 8, 0.42), cobble, c_med, verts=16)
    add_env_cyl("med_well_p1", 0.10, 2.2, (-1.1, 8, 1.5), pole_mat, c_med, verts=8)
    add_env_cyl("med_well_p2", 0.10, 2.2, (1.1, 8, 1.5), pole_mat, c_med, verts=8)
    add_env_cone("med_well_rf", 1.8, 0.1, 1.2, (0, 8, 3.1), med_roof, c_med, rot=(0, 0, math.radians(45)), verts=4)

    # 5. EMPTY WASTELAND
    c_wast = make_col("set_empty_wasteland")
    sets["empty_wasteland"] = c_wast
    dirt_mat = make_textured_mat("wst_dirt", (0.26, 0.20, 0.14, 1.0), (0.38, 0.29, 0.20, 1.0), scale=4.0, roughness=0.95, bump_strength=0.25)
    add_env_box("wst_fl", (140, 180, 0.1), (0, 0, -0.05), dirt_mat, c_wast, bevel=0)
    add_env_box("wst_rd", (5.5, 180, 0.04), (0, 0, 0.01), road_mat, c_wast, bevel=0)
    for rx, ry, rs in [(-5, 4, 0.9), (6, 12, 1.3), (-7, 22, 1.1), (5, -8, 0.8)]:
        add_env_cone(f"wst_rk_{rx}_{ry}", rs, rs * 0.4, rs * 1.1, (rx, ry, rs * 0.4), cobble, c_wast, verts=6)
        add_env_cyl(f"wst_pf_{rx}_{ry}", 0.09, 1.4, (rx * 0.7, ry + 3, 0.65), pole_mat, c_wast, rot=(0.15, 0.1, 0), verts=8)

    # 6. GRAVEYARD
    c_grav = make_col("set_graveyard")
    sets["graveyard"] = c_grav
    stone_m = make_textured_mat("grv_st", (0.38, 0.39, 0.42, 1.0), (0.50, 0.51, 0.54, 1.0), scale=6.0, roughness=0.88, bump_strength=0.22)
    add_env_box("grv_fl", (70, 70, 0.1), (0, 0, -0.05), grass_mat, c_grav, bevel=0)
    for gx in range(-10, 12, 4):
        for gy in (4, 9, 14, 19):
            tilt = 0.08 if (gx + gy) % 3 == 0 else -0.05
            add_env_box(f"grv_tb_{gx}_{gy}", (1.15, 0.45, 0.22), (gx, gy, 0.11), stone_m, c_grav, bevel=0.02)
            add_env_box(f"grv_t_{gx}_{gy}", (0.85, 0.22, 1.35), (gx, gy, 0.75), stone_m, c_grav, rot=(0, tilt, 0), bevel=0.04)
    # Iron perimeter fence + dead trees
    for fx in range(-14, 16, 4):
        add_env_box(f"grv_fp_{fx}", (0.45, 0.45, 1.8), (fx, 22, 0.9), stone_m, c_grav, bevel=0.02)
    add_env_box("grv_fb", (28, 0.10, 1.2), (0, 22, 0.8), iron_mat, c_grav, bevel=0)
    add_env_cyl("grv_dt1", 0.25, 3.8, (-8, 12, 1.9), pole_mat, c_grav, rot=(0.1, 0.15, 0), verts=8)
    add_env_cyl("grv_dt2", 0.22, 3.4, (8, 15, 1.7), pole_mat, c_grav, rot=(-0.1, -0.18, 0), verts=8)

    # Batch static environment meshes and create a single Root Empty per set.
    # Parenting to an Empty means Blender keyframes only 5 Root Empties instead of 1,296 individual
    # objects per shot, preserving static geometry BVH in Cycles and cutting frame times from 22s to <1s!
    roots = {}
    for s_name, s_col in sets.items():
        mesh_objs = [o for o in list(s_col.objects) if o.type == "MESH"]
        if len(mesh_objs) > 1:
            try:
                for o in scene.objects:
                    o.select_set(False)
                for o in mesh_objs:
                    o.select_set(True)
                scene.view_layers[0].objects.active = mesh_objs[0]
                try:
                    with bpy.context.temp_override(active_object=mesh_objs[0], selected_editable_objects=mesh_objs):
                        bpy.ops.object.join()
                except Exception:
                    bpy.ops.object.join()
                mesh_objs[0].name = f"StaticMesh_{s_name}"
            except Exception as e:
                print(f"[blender_render] Batching {s_name} notice: {e}", flush=True)

        root = bpy.data.objects.new(f"Root_{s_name}", None)
        root.empty_display_type = "PLAIN_AXES"
        scene.collection.objects.link(root)
        roots[s_name] = root
        for obj in list(s_col.objects):
            if obj.parent is None and obj != root:
                obj.parent = root
                obj.matrix_parent_inverse = root.matrix_world.inverted()

    return sets, roots


# ---------------------------------------------------------------------------
# Lighting, Weather & Camera Director
# ---------------------------------------------------------------------------
def configure_render(scene, fps: int, draft: bool):
    # Auto-detect hardware GPU acceleration: on Linux headless cloud servers (like Kaggle with Tesla T4),
    # Cycles OptiX / CUDA communicates directly with NVIDIA hardware compute kernels, completely bypassing
    # missing X11/EGL display drivers that force EEVEE onto slow CPU llvmpipe.
    use_gpu_cycles = False
    try:
        prefs = bpy.context.preferences
        cycles_addon = prefs.addons.get("cycles")
        if cycles_addon:
            cprefs = cycles_addon.preferences
            for backend in ["OPTIX", "CUDA"]:
                try:
                    cprefs.compute_device_type = backend
                    cprefs.get_devices()
                    matched = [d for d in cprefs.devices if d.type == backend]
                    if matched:
                        for d in cprefs.devices:
                            d.use = (d.type == backend)
                        scene.render.engine = "CYCLES"
                        scene.cycles.device = "GPU"
                        scene.cycles.samples = 8 if draft else 16
                        scene.cycles.preview_samples = 8
                        # Peak-quality AI neural denoising accelerated on GPU (Blender 4.1+)
                        scene.cycles.use_denoising = True
                        if hasattr(scene.cycles, "denoiser"):
                            scene.cycles.denoiser = "OPENIMAGEDENOISE"
                        if hasattr(scene.cycles, "denoising_use_gpu"):
                            scene.cycles.denoising_use_gpu = True
                        if hasattr(scene.cycles, "denoising_prefilter"):
                            scene.cycles.denoising_prefilter = "FAST"
                        if hasattr(scene.cycles, "denoising_input_passes"):
                            scene.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
                        scene.cycles.max_bounces = 4
                        scene.cycles.diffuse_bounces = 2
                        scene.cycles.glossy_bounces = 2
                        scene.cycles.transmission_bounces = 2
                        scene.cycles.volume_bounces = 0
                        scene.cycles.transparent_max_bounces = 4
                        use_gpu_cycles = True
                        print(f"[blender_render] Activated hardware GPU: {backend} ({matched[0].name}) via CYCLES path-tracer!", flush=True)
                        break
                except Exception as ex:
                    print(f"[blender_render] Backend {backend} check: {ex}", flush=True)
    except Exception as e:
        print(f"[blender_render] GPU check error: {e}", flush=True)

    if not use_gpu_cycles:
        # Fall back to EEVEE Next (for environments with an active OpenGL/windowing display)
        engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
        scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
        if hasattr(scene, "eevee"):
            scene.eevee.taa_render_samples = 4 if draft else 8
            if hasattr(scene.eevee, "shadow_resolution_scale"):
                scene.eevee.shadow_resolution_scale = 0.5 if draft else 1.0
            if hasattr(scene.eevee, "use_gtao"):
                scene.eevee.use_gtao = True
        print(f"[blender_render] Using {scene.render.engine} display engine", flush=True)

    scene.render.resolution_x = 540 if draft else 1080
    scene.render.resolution_y = 960 if draft else 1920
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM" if draft else "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "REALTIME" if draft else "GOOD"

    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 4 if draft else 8
        if hasattr(scene.eevee, "shadow_resolution_scale"):
            scene.eevee.shadow_resolution_scale = 0.5 if draft else 1.0
        if hasattr(scene.eevee, "use_gtao"):
            scene.eevee.use_gtao = True

    # Richer AgX cinematic contrast
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass

    # Lightweight Bloom only when needed (kept fast)
    scene.use_nodes = False


def setup_world_and_lights(scene):
    world = bpy.data.worlds.new("TownWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.35, 0.62, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 1.0

    # Key Sun Light
    sun_data = bpy.data.lights.new("SunKey", type="SUN")
    sun_data.energy = 3.2
    sun_data.angle = math.radians(2.5)
    sun_obj = bpy.data.objects.new("SunKey", sun_data)
    scene.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(48), math.radians(15), math.radians(32))

    # Fill Light
    fill_data = bpy.data.lights.new("FillLight", type="AREA")
    fill_data.energy = 90.0
    fill_data.size = 14.0
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    scene.collection.objects.link(fill_obj)
    fill_obj.location = (0, -8, 6)

    # Cool Rim Light for character/building separation
    rim_data = bpy.data.lights.new("RimLight", type="AREA")
    rim_data.energy = 65.0
    rim_data.size = 10.0
    rim_data.color = (0.75, 0.88, 1.0)
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    scene.collection.objects.link(rim_obj)
    rim_obj.location = (0, 10, 7)
    return bg, sun_data, sun_obj


def _set_socket_const(sock, frame: int, val):
    sock.default_value = val
    sock.keyframe_insert(data_path="default_value", frame=frame)
    nt = sock.id_data
    if nt.animation_data and nt.animation_data.action:
        for fc in nt.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.01:
                    kp.interpolation = "CONSTANT"


def apply_lighting_key(bg, sun_data, lighting: str, f0: int):
    presets = {
        "day": ((0.35, 0.65, 0.95, 1.0), 1.0, (1.0, 0.98, 0.92), 3.4),
        "sunset": ((0.92, 0.42, 0.16, 1.0), 0.9, (1.0, 0.65, 0.35), 2.5),
        "fog_orange": ((0.75, 0.36, 0.12, 1.0), 0.75, (0.95, 0.55, 0.25), 1.8),
        "night": ((0.03, 0.05, 0.12, 1.0), 0.45, (0.45, 0.58, 0.85), 1.1),
        "red_horror": ((0.18, 0.01, 0.01, 1.0), 0.5, (1.0, 0.15, 0.15), 1.8),
    }
    wcol, wstr, scol, s_en = presets.get(lighting, presets["day"])
    _set_socket_const(bg.inputs["Color"], f0, wcol)
    _set_socket_const(bg.inputs["Strength"], f0, wstr)
    set_key(sun_data, "color", f0, scol, "CONSTANT")
    set_key(sun_data, "energy", f0, s_en, "CONSTANT")


def build_weather_systems(scene):
    """Build lightweight procedural weather particle rigs (snow, rain, gold_particles)."""
    w_col = bpy.data.collections.new("Weather")
    scene.collection.children.link(w_col)
    rng = random.Random(77)

    specs = {
        "snow": {"count": 40, "size": (0.055, 0.055, 0.055), "mat": make_mat("w_snow", (0.95, 0.97, 1.0, 1.0), roughness=0.4, emission=(0.95, 0.97, 1.0, 1.0), emission_strength=0.6), "speed": -1.4},
        "rain": {"count": 45, "size": (0.016, 0.016, 0.42), "mat": make_mat("w_rain", (0.72, 0.85, 1.0, 1.0), roughness=0.2, emission=(0.72, 0.85, 1.0, 1.0), emission_strength=0.5), "speed": -5.5},
        "gold_particles": {"count": 34, "size": (0.05, 0.05, 0.05), "mat": make_mat("w_gold", (1.0, 0.84, 0.2, 1.0), roughness=0.2, emission=(1.0, 0.84, 0.2, 1.0), emission_strength=3.2), "speed": 0.9},
    }

    groups = {}
    for w_name, cfg in specs.items():
        root = bpy.data.objects.new(f"weather_{w_name}", None)
        w_col.objects.link(root)
        root.location = (0, 0, -400.0)
        for i in range(cfg["count"]):
            x = rng.uniform(-7.0, 7.0)
            y = rng.uniform(-7.0, 7.0)
            z = rng.uniform(0.4, 7.5)
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z))
            p = bpy.context.active_object
            p.name = f"{w_name}_{i}"
            p.scale = cfg["size"]
            p.data.materials.append(cfg["mat"])
            p.parent = root
        groups[w_name] = (root, cfg["speed"])
    return groups


def apply_weather_key(weather_groups, weather_name: str, f0: int, f1: int, fps: int):
    dur = max(0.1, (f1 - f0) / fps)
    for w_name, (root, speed) in weather_groups.items():
        if w_name == weather_name:
            start_z = 0.0 if speed < 0 else -1.5
            end_z = max(-3.0, min(3.0, start_z + speed * dur * 0.35))
            set_key(root, "location", f0, (0.0, 0.0, start_z), "CONSTANT")
            set_key(root, "location", f0 + 1, (0.0, 0.0, start_z), "LINEAR")
            set_key(root, "location", f1, (0.25 if speed < 0 else 0.0, 0.0, end_z), "LINEAR")
        else:
            set_key(root, "location", f0, (0.0, 0.0, -400.0), "CONSTANT")


def point_camera_at(cam_obj, target_pos: Vector):
    direction = target_pos - cam_obj.location
    if direction.length < 1e-4:
        return
    rot_quat = direction.to_track_quat("-Z", "Y")
    cam_obj.rotation_euler = rot_quat.to_euler()


def main():
    ep = json.loads(Path(args.episode).read_text(encoding="utf-8"))
    faces_dir = Path(args.faces_dir)
    if not faces_dir.exists():
        raise FileNotFoundError(f"Faces directory missing: {faces_dir}")

    clear_scene()
    scene = bpy.context.scene
    fps = args.fps
    configure_render(scene, fps, args.draft)
    bg, sun_data, _ = setup_world_and_lights(scene)

    # Build sets & weather
    sets, set_roots = build_environments(scene)
    weather_groups = build_weather_systems(scene)

    # Build cast & creatures
    cast_col = bpy.data.collections.new("Cast")
    scene.collection.children.link(cast_col)
    rigs = {}
    for c_spec in ep.get("cast", []):
        rigs[c_spec["id"]] = R6Rig(c_spec, faces_dir, cast_col)
    for m_spec in ep.get("creatures", []):
        rigs[m_spec["id"]] = ProceduralCreature(m_spec, cast_col)

    # Camera
    cam_data = bpy.data.cameras.new("MainCam")
    cam_data.lens = 34.0
    cam_obj = bpy.data.objects.new("MainCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    shots = ep.get("shots", [])
    total_dur = float(ep.get("total_duration", 60.0))
    scene.frame_start = 1
    scene.frame_end = max(2, int(math.ceil(total_dur * fps)))
    if args.max_frames > 0:
        scene.frame_end = min(scene.frame_end, args.max_frames)

    for idx, shot in enumerate(shots):
        t0 = float(shot.get("start", 0.0))
        t1 = float(shot.get("end", t0 + 2.0))
        f0 = max(1, int(round(t0 * fps)) + 1)
        f1 = max(f0 + 1, int(round(t1 * fps)))
        if idx == len(shots) - 1:
            f1 = scene.frame_end

        # Fast set switching: keyframe only the Root Empty of each environment set.
        # This eliminates 1,296 individual fcurves, keeping environment meshes flagged as static BVH!
        active_set = shot.get("set", "suburban_street")
        for s_name, s_root in set_roots.items():
            z_off = 0.0 if s_name == active_set else -400.0
            set_key(s_root, "location", f0, (0.0, 0.0, z_off), "CONSTANT")

        # Lighting & Weather
        apply_lighting_key(bg, sun_data, shot.get("lighting", "day"), f0)
        apply_weather_key(weather_groups, shot.get("weather", "none"), f0, f1, fps)

        # Actors
        active_ids = set()
        target_pos = Vector((0, 0, 1.3))
        target_pos_end = Vector((0, 0, 1.3))
        target_h = 1.35
        target_rot_z = 0.0
        cam_target = shot.get("cam_target", "")

        for act in shot.get("actors", []):
            aid = act.get("id")
            if aid in rigs:
                active_ids.add(aid)
                rigs[aid].set_shot(act, f0, f1, fps) if isinstance(rigs[aid], R6Rig) else rigs[aid].set_shot(act, f0, f1)
                if aid == cam_target:
                    p = act.get("pos", [0, 0, 0])
                    target_h = rigs[aid].focus_height
                    target_pos = Vector((float(p[0]), float(p[2]), float(p[1]) + target_h))
                    ep_pos = getattr(rigs[aid], "shot_end_pos", (float(p[0]), float(p[2]), float(p[1])))
                    target_pos_end = Vector((ep_pos[0], ep_pos[1], ep_pos[2] + target_h))
                    target_rot_z = math.radians(float(act.get("rot_y", 0)))

        # Hide unused actors off-stage
        for aid, rig in rigs.items():
            if aid not in active_ids:
                set_key(rig.root, "location", f0, (0, 0, -250), "CONSTANT")

        # Camera framing (automatically scales distance to character/monster height, orbits to front, AND tracks moving actors!)
        dist_scale = max(1.0, target_h / 1.35)
        cam_type = shot.get("cam", "push_in")
        if cam_type == "establishing_aerial":
            off0 = Vector((2.5, -12.0 * dist_scale, 7.5))
            off1 = Vector((1.0, -9.0 * dist_scale, 5.5))
        elif cam_type == "closeup_face":
            off0 = Vector((0.0, -2.1 * dist_scale, 0.15))
            off1 = Vector((0.0, -1.75 * dist_scale, 0.15))
        elif cam_type == "whip_zoom":
            off0 = Vector((0.6, -4.5 * dist_scale, 0.4))
            off1 = Vector((0.0, -1.9 * dist_scale, 0.15))
        elif cam_type == "low_angle_monster":
            off0 = Vector((1.4, -5.4 * dist_scale, 0.75 - target_pos.z))
            off1 = Vector((0.6, -4.4 * dist_scale, 0.90 - target_pos.z))
        elif cam_type == "ots_left":
            off0 = Vector((-1.6, -3.0 * dist_scale, 0.2))
            off1 = Vector((-1.2, -2.6 * dist_scale, 0.2))
        elif cam_type == "ots_right":
            off0 = Vector((1.6, -3.0 * dist_scale, 0.2))
            off1 = Vector((1.2, -2.6 * dist_scale, 0.2))
        elif cam_type == "crowd_march":
            off0 = Vector((3.5, -8.5 * dist_scale, 4.2 - target_pos.z))
            off1 = Vector((2.5, -6.5 * dist_scale, 3.6 - target_pos.z))
        else:  # push_in / pov_window / default
            off0 = Vector((0.4, -4.2 * dist_scale, 0.25))
            off1 = Vector((0.1, -3.1 * dist_scale, 0.20))

        # Rotate camera offset around Z so it always faces the target's front (-Y local)
        rot_m = Euler((0.0, 0.0, target_rot_z), "XYZ").to_matrix()
        p0 = target_pos + (rot_m @ off0)
        p1 = target_pos_end + (rot_m @ off1)

        cam_obj.location = p0
        point_camera_at(cam_obj, target_pos)
        cam_obj.keyframe_insert(data_path="location", frame=f0)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=f0)

        cam_obj.location = p1
        point_camera_at(cam_obj, target_pos_end)
        cam_obj.keyframe_insert(data_path="location", frame=f1)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=f1)

    # Render animation
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.use_file_extension = False
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(animation=True)
    print(f"[blender_render] Rendered {scene.frame_end} frames to {out_path}")


if __name__ == "__main__":
    main()

