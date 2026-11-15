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
parser.add_argument("--still-frame", type=int, default=0, help="Render a single still snapshot frame and exit")
parser.add_argument("--engine", default="auto", choices=["auto", "CYCLES", "EEVEE", "EEVEE_NEXT", "BLENDER_EEVEE_NEXT"], help="Render engine (CYCLES, EEVEE_NEXT, or auto)")
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


def make_mat(name: str, color=(0.8, 0.8, 0.8, 1.0), roughness=0.65, metallic=0.0, emission=None, emission_strength=0.0, alpha=1.0, transmission=0.0, ior=1.45):
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
    if transmission > 0.0:
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = transmission
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = transmission
        if "IOR" in bsdf.inputs:
            bsdf.inputs["IOR"].default_value = ior
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


def add_box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, parent=None, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
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


def add_sphere(name, radius, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), mat=None, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=12, radius=radius, location=loc, rotation=rot)
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
        glass_m = make_mat(f"{self.id}_glass", (0.82, 0.90, 0.96, 1.0), roughness=0.15)

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

        # Jigsaw Puzzle Piece in right hand (held up proudly, facing camera)
        puz_root = bpy.data.objects.new(f"{self.id}_p_puzzle", None)
        puz_root.location = (0, -0.28, -0.56)
        # Face angled flat toward camera, fully visible
        puz_root.rotation_euler = (math.radians(150), math.radians(-30), 0)
        bpy.context.scene.collection.objects.link(puz_root)
        puz_root.parent = self.arm_r
        puz_m = make_mat(f"{self.id}_puz_m", (0.10, 0.78, 0.85, 1.0), metallic=0.75, roughness=0.20, emission=(0.08, 0.65, 0.75, 1.0), emission_strength=2.2)
        puz_trim = make_mat(f"{self.id}_puz_tr", (0.95, 0.85, 0.35, 1.0), metallic=0.9, roughness=0.15)
        # Main square tile
        add_box(f"{self.id}_puz_body", (0.34, 0.34, 0.06), loc=(0, 0, 0), mat=puz_m, parent=puz_root, bevel=0.015)
        # Interlocking circular tabs (top and right)
        add_cyl(f"{self.id}_puz_tab_top", 0.085, 0.065, loc=(0, 0.18, 0), mat=puz_m, parent=puz_root, verts=16)
        add_cyl(f"{self.id}_puz_tab_rt", 0.085, 0.065, loc=(0.18, 0, 0), mat=puz_m, parent=puz_root, verts=16)
        # Gold emblem center ring
        add_cyl(f"{self.id}_puz_emb", 0.055, 0.072, loc=(0, 0, 0.005), mat=puz_trim, parent=puz_root, verts=12)
        puz_root.scale = (0, 0, 0)
        self.props["puzzle"] = puz_root
        self.props["puzzle_piece"] = puz_root

        # Perched Bird (Raven/Crow) on right forearm/wrist
        bird_root = bpy.data.objects.new(f"{self.id}_p_bird", None)
        bird_root.location = (0, -0.26, -0.68)
        bird_root.rotation_euler = (math.radians(72), 0, math.radians(-25))
        bpy.context.scene.collection.objects.link(bird_root)
        bird_root.parent = self.arm_r
        raven_m = make_mat(f"{self.id}_p_rav", (0.08, 0.08, 0.10, 1.0), roughness=0.6)
        beak_m = make_mat(f"{self.id}_p_bk", (0.85, 0.60, 0.10, 1.0), roughness=0.4)
        add_sphere(f"{self.id}_p_bbod", 0.12, loc=(0, 0, 0.10), scale=(0.7, 1.2, 0.7), mat=raven_m, parent=bird_root)
        add_sphere(f"{self.id}_p_bhd", 0.075, loc=(0, -0.10, 0.19), mat=raven_m, parent=bird_root)
        add_cone(f"{self.id}_p_bbk", 0.04, 0.005, 0.11, loc=(0, -0.19, 0.18), rot=(math.radians(90), 0, 0), mat=beak_m, parent=bird_root, verts=6)
        eye_m = make_mat(f"{self.id}_p_beye", (1.0, 1.0, 1.0, 1.0), emission=(1.0, 1.0, 1.0, 1.0), emission_strength=2.0)
        add_sphere(f"{self.id}_p_beL", 0.015, loc=(-0.05, -0.14, 0.22), mat=eye_m, parent=bird_root)
        add_sphere(f"{self.id}_p_beR", 0.015, loc=(0.05, -0.14, 0.22), mat=eye_m, parent=bird_root)
        add_box(f"{self.id}_p_bwL", (0.025, 0.24, 0.13), loc=(-0.09, 0.02, 0.10), mat=raven_m, parent=bird_root, bevel=0.005)
        add_box(f"{self.id}_p_bwR", (0.025, 0.24, 0.13), loc=(0.09, 0.02, 0.10), mat=raven_m, parent=bird_root, bevel=0.005)
        add_box(f"{self.id}_p_btail", (0.07, 0.20, 0.02), loc=(0, 0.18, 0.07), rot=(math.radians(-25), 0, 0), mat=raven_m, parent=bird_root, bevel=0.005)
        bird_root.scale = (0, 0, 0)
        self.props["bird"] = bird_root
        self.props["perched_bird"] = bird_root

        # Ornate Skeleton Key held beside shoulder/chest (unobscured face)
        key_root = bpy.data.objects.new(f"{self.id}_p_key", None)
        key_root.location = (0.10, -0.28, -0.60)
        key_root.rotation_euler = (math.radians(85), math.radians(18), math.radians(-35))
        bpy.context.scene.collection.objects.link(key_root)
        key_root.parent = self.arm_r
        add_cyl(f"{self.id}_p_kshaft", 0.03, 0.48, loc=(0, 0, 0.05), mat=gold_m, parent=key_root, verts=10)
        # Vertical ornate bow ring facing camera
        add_cyl(f"{self.id}_p_kbow", 0.12, 0.035, loc=(0, 0, 0.32), rot=(0, math.radians(90), 0), mat=gold_m, parent=key_root, verts=16)
        add_cyl(f"{self.id}_p_kbow_in", 0.065, 0.038, loc=(0, 0, 0.32), rot=(0, math.radians(90), 0), mat=make_mat(f"{self.id}_kbow_in", (0.35, 0.25, 0.05, 1.0), metallic=0.9), parent=key_root, verts=14)
        # Jagged antique bit teeth protruding outward clearly into light
        add_box(f"{self.id}_p_kbit1", (0.025, 0.11, 0.08), loc=(0, 0.06, -0.12), mat=gold_m, parent=key_root, bevel=0.005)
        add_box(f"{self.id}_p_kbit2", (0.025, 0.08, 0.05), loc=(0, 0.05, -0.02), mat=gold_m, parent=key_root, bevel=0.005)
        add_box(f"{self.id}_p_kbit3", (0.025, 0.06, 0.05), loc=(0, 0.04, -0.17), mat=gold_m, parent=key_root, bevel=0.005)
        key_root.scale = (0, 0, 0)
        self.props["key"] = key_root

        # Crystal Relic Orb with Refractive Shell & Glowing Core
        orb_root = bpy.data.objects.new(f"{self.id}_p_orb", None)
        orb_root.location = (0, -0.28, -0.54)
        # Upright claw cradle cupping the orb vertically in world space
        orb_root.rotation_euler = (math.radians(60), math.radians(-30), 0)
        bpy.context.scene.collection.objects.link(orb_root)
        orb_root.parent = self.arm_r
        # Three-claw antique bronze/silver cradle
        cradle_m = make_mat(f"{self.id}_p_crad", (0.75, 0.65, 0.40, 1.0), metallic=0.85, roughness=0.25)
        add_cyl(f"{self.id}_p_crbase", 0.08, 0.04, loc=(0, 0, -0.14), mat=cradle_m, parent=orb_root, verts=12)
        for c_ang in (0, 2.094, 4.188):
            cx = math.cos(c_ang) * 0.13
            cy = math.sin(c_ang) * 0.13
            add_cone(f"{self.id}_p_claw_{c_ang:.1f}", 0.022, 0.005, 0.18, loc=(cx, cy, -0.03), rot=(math.radians(18), 0, c_ang), mat=cradle_m, parent=orb_root, verts=4)
        # Outer transparent crystal glass sphere with high transmission & refraction
        cryst_glass = make_mat(f"{self.id}_p_cryst_g", (0.80, 0.94, 1.0, 0.15), roughness=0.03, transmission=0.96, ior=1.52)
        add_sphere(f"{self.id}_p_orbsph", 0.15, loc=(0, 0, 0), mat=cryst_glass, parent=orb_root)
        # Inner glowing arcane core
        core_m = make_mat(f"{self.id}_p_core_m", (0.15, 0.88, 1.0, 1.0), emission=(0.15, 0.88, 1.0, 1.0), emission_strength=1.8)
        add_sphere(f"{self.id}_p_core", 0.065, loc=(0, 0, 0), mat=core_m, parent=orb_root)
        orb_root.scale = (0, 0, 0)
        self.props["orb"] = orb_root
        self.props["crystal_orb"] = orb_root

        # Antique Running Hourglass with Brass Pillars and Glowing Sand
        # Positioned cleanly on top of the palm fingers (no clipping into the hand!)
        hg_root = bpy.data.objects.new(f"{self.id}_p_hourglass", None)
        hg_root.location = (0, -0.30, -0.48)
        # Upright orientation in world space
        hg_root.rotation_euler = (math.radians(60), math.radians(-30), 0)
        bpy.context.scene.collection.objects.link(hg_root)
        hg_root.parent = self.arm_r
        add_cyl(f"{self.id}_p_hg_top", 0.10, 0.035, loc=(0, 0, 0.18), mat=wood_m, parent=hg_root, verts=14)
        add_cyl(f"{self.id}_p_hg_bot", 0.10, 0.035, loc=(0, 0, -0.18), mat=wood_m, parent=hg_root, verts=14)
        # 3 slender wood/brass support pillars
        for hg_ang in (0, 2.094, 4.188):
            px = math.cos(hg_ang) * 0.085
            py = math.sin(hg_ang) * 0.085
            add_cyl(f"{self.id}_p_hg_col_{hg_ang:.1f}", 0.010, 0.35, loc=(px, py, 0), mat=wood_m, parent=hg_root, verts=8)
        # Clear transmission glass bulbs
        hg_glass = make_mat(f"{self.id}_hg_glass", (0.90, 0.95, 1.0, 0.20), roughness=0.03, transmission=0.95, ior=1.45)
        add_cone(f"{self.id}_p_hg_g1", 0.085, 0.015, 0.16, loc=(0, 0, 0.08), rot=(math.radians(180), 0, 0), mat=hg_glass, parent=hg_root, verts=14)
        add_cone(f"{self.id}_p_hg_g2", 0.085, 0.015, 0.16, loc=(0, 0, -0.08), mat=hg_glass, parent=hg_root, verts=14)
        # Glowing amber falling sand
        sand_glow = make_mat(f"{self.id}_p_sand_m", (1.0, 0.76, 0.18, 1.0), roughness=0.35, emission=(1.0, 0.72, 0.15, 1.0), emission_strength=2.8)
        add_cone(f"{self.id}_p_hg_sand_top", 0.065, 0.01, 0.09, loc=(0, 0, 0.05), rot=(math.radians(180), 0, 0), mat=sand_glow, parent=hg_root, verts=10)
        add_cyl(f"{self.id}_p_hg_sand_stream", 0.007, 0.14, loc=(0, 0, 0), mat=sand_glow, parent=hg_root, verts=6)
        add_cone(f"{self.id}_p_hg_sand_bot", 0.07, 0.01, 0.08, loc=(0, 0, -0.12), mat=sand_glow, parent=hg_root, verts=10)
        hg_root.scale = (0, 0, 0)
        self.props["hourglass"] = hg_root

        # Antique Pocket Watch with Top Winding Crown & Loop
        clock_root = bpy.data.objects.new(f"{self.id}_p_clock", None)
        clock_root.location = (0, -0.28, -0.54)
        # Face angled directly toward the camera (normal: -Y, stem: +Z)
        clock_root.rotation_euler = (math.radians(150), math.radians(-30), 0)
        bpy.context.scene.collection.objects.link(clock_root)
        clock_root.parent = self.arm_r
        add_cyl(f"{self.id}_p_ck_case", 0.145, 0.035, loc=(0, 0, 0), mat=gold_m, parent=clock_root, verts=24)
        add_cyl(f"{self.id}_p_ck_dial", 0.125, 0.038, loc=(0, 0, 0.002), mat=make_mat(f"{self.id}_p_dial", (0.97, 0.95, 0.90, 1.0), roughness=0.3), parent=clock_root, verts=24)
        hand_m = make_mat(f"{self.id}_p_hnd", (0.05, 0.05, 0.05, 1.0), metallic=0.5)
        add_box(f"{self.id}_p_ck_handH", (0.012, 0.060, 0.042), loc=(0, 0.028, 0.006), mat=hand_m, parent=clock_root)
        add_box(f"{self.id}_p_ck_handM", (0.009, 0.090, 0.042), loc=(0.038, 0.018, 0.006), rot=(0, 0, math.radians(-55)), mat=hand_m, parent=clock_root)
        add_cyl(f"{self.id}_p_ck_pin", 0.016, 0.044, loc=(0, 0, 0.007), mat=gold_m, parent=clock_root, verts=8)
        add_cyl(f"{self.id}_p_ck_stem", 0.024, 0.045, loc=(0, 0.165, 0), rot=(math.radians(90), 0, 0), mat=gold_m, parent=clock_root, verts=8)
        add_cyl(f"{self.id}_p_ck_loop", 0.048, 0.018, loc=(0, 0.210, 0), mat=gold_m, parent=clock_root, verts=16)
        clock_root.scale = (0, 0, 0)
        self.props["clock"] = clock_root

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
                if active_prop in ("none", "backpack"):
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
        elif anim in ("lie", "sleep", "bed"):
            # Hospital patient propped up comfortably in adjustable bed (~22 deg incline):
            # Head and chest elevated so facial expressions are clearly visible to camera/visitor
            set_key(self.root, "rotation_euler", f0, (math.radians(-68), 0, rot_z), "CONSTANT")
            set_key(self.root, "location", f0, (bx, by - 0.72, bz + 0.16), "CONSTANT")
            set_key(self.leg_l, "rotation_euler", f0, (0, 0, 0), "CONSTANT")
            set_key(self.leg_r, "rotation_euler", f0, (0, 0, 0), "CONSTANT")
            set_key(self.arm_l, "rotation_euler", f0, (-0.35, 0, 0.22), "CONSTANT")
            set_key(self.arm_r, "rotation_euler", f0, (-0.35, 0, -0.22), "CONSTANT")
            set_key(self.head_pivot, "rotation_euler", f0, (0.26, 0, 0), "CONSTANT")
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

        # Raise right arm naturally to showcase and inspect handheld props in front of torso
        if active_prop not in ("none", "backpack"):
            if active_prop in ("bird", "perched_bird"):
                # Forward falconer pose: forearm extended forward in front of right shoulder, fully framed in 9:16
                set_key(self.arm_r, "rotation_euler", f0, (math.radians(-65), math.radians(10), math.radians(-10)), "CONSTANT")
            elif anim in ("idle", "talk", "stand", "walk", "run"):
                # Present / examine held prop in front of chest
                set_key(self.arm_r, "rotation_euler", f0, (math.radians(-62), math.radians(15), math.radians(-28)), "CONSTANT")


# ---------------------------------------------------------------------------
# Procedural Creature / Monster Builder
# ---------------------------------------------------------------------------
class ProceduralCreature:
    def __init__(self, spec: dict, collection):
        self.id = spec["id"]
        raw_arch = str(spec.get("archetype", "")).lower()
        cid = str(spec.get("id", "")).lower()
        feats = " ".join(str(f) for f in spec.get("features", [])).lower()
        combined = f"{raw_arch} {cid} {feats}"

        # Semantic Archetype Classifier: maps ANY arbitrary name/keyword to the best procedural body
        if any(w in combined for w in ("bird", "wing", "fly", "raven", "crow", "owl", "hawk", "feather", "sky", "bat", "gargoyle", "dragon", "avian", "phoenix")):
            arch = "winged_beast"
        elif any(w in combined for w in ("shadow", "stalker", "demon", "creep", "crawler", "horror", "spooky", "phantom", "ghost", "dark", "spider", "ghoul", "wraith", "lurker", "watcher", "wendigo", "slender", "tall", "night", "nightmare")):
            arch = "shadow_stalker"
        elif any(w in combined for w in ("pet", "tiny", "small", "cute", "spirit", "fairy", "cat", "dog", "baby", "little", "mini", "axolotl")):
            arch = "tiny_pet"
        else:
            arch = "fur_giant"

        self.arch = arch
        sc = float(spec.get("scale", 2.6))
        if arch in ("tiny_pet", "pet"):
            self.focus_height = 0.45 * sc
        elif arch in ("winged_beast", "giant_bird", "bird"):
            self.focus_height = 0.65 * sc
        elif arch in ("shadow_stalker", "scary_monster"):
            self.focus_height = 1.55 * sc
        else:
            self.focus_height = 1.25 * sc

        pcol = hex_to_rgba(spec.get("primary_color", "#141418"))
        scol = hex_to_rgba(spec.get("secondary_color", "#F2EAD8"))

        self.root = bpy.data.objects.new(f"creature_{self.id}", None)
        collection.objects.link(self.root)
        self.root.scale = (sc, sc, sc)

        body_mat = make_mat(f"{self.id}_bmat", pcol, roughness=0.88)
        teeth_mat = make_mat(f"{self.id}_tmat", (0.96, 0.93, 0.86, 1.0), roughness=0.35)
        gum_mat = make_mat(f"{self.id}_gmat", (0.32, 0.12, 0.14, 1.0), roughness=0.6)
        glow_eye_mat = make_mat(f"{self.id}_emat", (1.0, 0.08, 0.08, 1.0), emission=(1.0, 0.08, 0.08, 1.0), emission_strength=9.0)

        if arch in ("tiny_pet", "pet"):
            # Cute round potato-axolotl creature
            add_sphere(f"{self.id}_body", 0.45, loc=(0, 0, 0.45), scale=(1.08, 1.0, 0.92), mat=body_mat, parent=self.root)
            add_sphere(f"{self.id}_fL", 0.13, loc=(-0.22, -0.1, 0.10), mat=body_mat, parent=self.root)
            add_sphere(f"{self.id}_fR", 0.13, loc=(0.22, -0.1, 0.10), mat=body_mat, parent=self.root)
            if "horns" in spec.get("features", []):
                add_cone(f"{self.id}_hrnL", 0.07, 0.02, 0.24, loc=(-0.18, 0, 0.88), rot=(0, -0.2, 0), mat=make_mat(f"{self.id}_hm", scol), parent=self.root)
                add_cone(f"{self.id}_hrnR", 0.07, 0.02, 0.24, loc=(0.18, 0, 0.88), rot=(0, 0.2, 0), mat=make_mat(f"{self.id}_hm2", scol), parent=self.root)
            eye_w = make_mat(f"{self.id}_ew", (0.04, 0.04, 0.05, 1.0))
            add_sphere(f"{self.id}_eL", 0.09, loc=(-0.16, -0.40, 0.52), mat=eye_w, parent=self.root)
            add_sphere(f"{self.id}_eR", 0.09, loc=(0.16, -0.40, 0.52), mat=eye_w, parent=self.root)
            add_box(f"{self.id}_bt", (0.10, 0.04, 0.10), loc=(0, -0.44, 0.33), mat=teeth_mat, parent=self.root, bevel=0.01)

        elif arch in ("winged_beast", "giant_bird", "bird"):
            # Majestic & Terrifying Giant Bird / Winged Beast
            beak_col = (0.95, 0.70, 0.15, 1.0)
            beak_mat = make_mat(f"{self.id}_beak", beak_col, roughness=0.35)
            # Forward-leaning aerodynamic predator body
            add_sphere(f"{self.id}_btorso", 0.44, loc=(0, 0, 0.65), scale=(0.70, 1.45, 0.58), rot=(math.radians(18), 0, 0), mat=body_mat, parent=self.root)
            # Extended predatory neck & skull pitched forward in raptor dive
            add_sphere(f"{self.id}_bneck", 0.18, loc=(0, -0.38, 0.68), scale=(0.8, 1.25, 0.8), rot=(math.radians(20), 0, 0), mat=body_mat, parent=self.root)
            add_sphere(f"{self.id}_bhead", 0.22, loc=(0, -0.66, 0.72), scale=(0.80, 1.15, 0.82), mat=body_mat, parent=self.root)
            # Swept-back feathered crest spikes
            for ci, (cdy, cdz, crx) in enumerate([(0.10, 0.12, -35), (0.18, 0.15, -45), (0.26, 0.17, -55)]):
                add_cone(f"{self.id}_bcrest_{ci}", 0.06, 0.01, 0.28, loc=(0, -0.66 + cdy, 0.72 + cdz), rot=(math.radians(crx), 0, 0), mat=body_mat, parent=self.root, verts=4)
            # Deep hooked raptor beak pointing forward and curved down
            add_cone(f"{self.id}_bbeak_base", 0.11, 0.04, 0.28, loc=(0, -0.88, 0.68), rot=(math.radians(88), 0, 0), mat=beak_mat, parent=self.root, verts=6)
            add_cone(f"{self.id}_bbeak_tip", 0.05, 0.008, 0.20, loc=(0, -1.02, 0.58), rot=(math.radians(115), 0, 0), mat=beak_mat, parent=self.root, verts=4)
            # Glowing predatory eyes with angled brow glare looking at camera
            eye_mat = glow_eye_mat if spec.get("eye_type") != "none" else make_mat(f"{self.id}_bew", (0.9, 0.1, 0.1, 1.0), emission=(0.9, 0.1, 0.1, 1.0), emission_strength=4.0)
            add_sphere(f"{self.id}_beL", 0.045, loc=(-0.14, -0.72, 0.76), mat=eye_mat, parent=self.root)
            add_sphere(f"{self.id}_beR", 0.045, loc=(0.14, -0.72, 0.76), mat=eye_mat, parent=self.root)
            add_box(f"{self.id}_bbrowL", (0.08, 0.18, 0.03), loc=(-0.14, -0.72, 0.81), rot=(math.radians(14), math.radians(22), 0), mat=body_mat, parent=self.root)
            add_box(f"{self.id}_bbrowR", (0.08, 0.18, 0.03), loc=(0.14, -0.72, 0.81), rot=(math.radians(14), math.radians(-22), 0), mat=body_mat, parent=self.root)
            # Tail feather fan (+Y)
            for ti in (-0.16, 0.0, 0.16):
                add_box(f"{self.id}_btail_{ti}", (0.18, 0.85, 0.04), loc=(ti, 0.80, 0.68), rot=(math.radians(-16), ti * 0.5, 0), mat=body_mat, parent=self.root, bevel=0.01)

            # Articulated Wing Pivots
            self.wing_L_pivot = bpy.data.objects.new(f"{self.id}_wL_pivot", None)
            self.wing_L_pivot.location = (-0.30, 0, 0.75)
            collection.objects.link(self.wing_L_pivot)
            self.wing_L_pivot.parent = self.root

            self.wing_R_pivot = bpy.data.objects.new(f"{self.id}_wR_pivot", None)
            self.wing_R_pivot.location = (0.30, 0, 0.75)
            collection.objects.link(self.wing_R_pivot)
            self.wing_R_pivot.parent = self.root

            # Seamless layered flight feathers with arched dihedral
            for wi in range(4):
                w_len = 0.65 + wi * 0.12
                w_w = 0.32 - wi * 0.03
                add_box(f"{self.id}_wL_{wi}", (w_w, w_len, 0.035), loc=(-0.16 - wi * 0.20, 0.05 + wi * 0.04, -0.03 * wi), rot=(math.radians(6), math.radians(-10), math.radians(10 * wi)), mat=body_mat, parent=self.wing_L_pivot, bevel=0.01)
                add_box(f"{self.id}_wR_{wi}", (w_w, w_len, 0.035), loc=(0.16 + wi * 0.20, 0.05 + wi * 0.04, -0.03 * wi), rot=(math.radians(6), math.radians(10), math.radians(-10 * wi)), mat=body_mat, parent=self.wing_R_pivot, bevel=0.01)

            # In-flight tucked predatory talons
            talon_mat = make_mat(f"{self.id}_talon", (0.15, 0.14, 0.12, 1.0), roughness=0.5)
            for tx in (-0.18, 0.18):
                add_cyl(f"{self.id}_tleg_{tx}", 0.05, 0.38, loc=(tx, 0.22, 0.42), rot=(math.radians(-55), 0, 0), mat=body_mat, parent=self.root, verts=8)
                add_cyl(f"{self.id}_tfoot_{tx}", 0.035, 0.22, loc=(tx, 0.15, 0.24), rot=(math.radians(35), 0, 0), mat=talon_mat, parent=self.root, verts=6)
                for cl_i, cl_dx in enumerate((-0.05, 0.0, 0.05)):
                    add_cone(f"{self.id}_tclaw_{tx}_{cl_i}", 0.018, 0.004, 0.14, loc=(tx + cl_dx, 0.06, 0.15), rot=(math.radians(75), 0, 0), mat=talon_mat, parent=self.root, verts=4)

        elif arch in ("shadow_stalker", "scary_monster"):
            # Disturbingly tall, gaunt, elongated shadow nightmare entity
            scol_rgba = hex_to_rgba(spec.get("secondary_color", "#8B0000"))
            tendril_mat = make_mat(f"{self.id}_tendril", scol_rgba, emission=scol_rgba, emission_strength=4.5)
            # Slender gaunt forward-hunched predatory spine/torso
            add_box(f"{self.id}_stor", (0.52, 0.38, 1.45), loc=(0, -0.15, 1.48), rot=(math.radians(24), 0, 0), mat=body_mat, parent=self.root, bevel=0.04)
            # Narrow hollow skull head angled downward at camera
            self.stalker_head = add_box(f"{self.id}_shead", (0.38, 0.44, 0.48), loc=(0, -0.42, 2.18), rot=(math.radians(35), 0, 0), mat=body_mat, parent=self.root, bevel=0.03)
            # Multiple piercing glowing needle eyes (3 pairs!)
            for ei, (ex, ez) in enumerate([(-0.11, 2.26), (0.11, 2.26), (-0.08, 2.18), (0.08, 2.18), (-0.05, 2.10), (0.05, 2.10)]):
                add_sphere(f"{self.id}_meye_{ei}", 0.034, loc=(ex, -0.65, ez), mat=glow_eye_mat, parent=self.root)
            # Gaping jaw lined with needle fangs
            add_box(f"{self.id}_jaw_bg", (0.28, 0.16, 0.35), loc=(0, -0.58, 1.95), mat=gum_mat, parent=self.root, bevel=0.01)
            for fangi in range(8):
                fx = -0.10 + (fangi % 4) * 0.065
                fz = 2.06 if fangi < 4 else 1.85
                frot = math.radians(180) if fangi < 4 else 0
                add_cone(f"{self.id}_fang_{fangi}", 0.025, 0.005, 0.14, loc=(fx, -0.66, fz), rot=(frot, 0, 0), mat=teeth_mat, parent=self.root, verts=4)
            # Long spindly double-jointed arms reaching forward and down
            for arm_side, ax in ((-1, -0.42), (1, 0.42)):
                add_box(f"{self.id}_armU_{arm_side}", (0.14, 0.14, 0.95), loc=(ax, -0.20, 1.45), rot=(math.radians(35), 0, math.radians(-12 * arm_side)), mat=body_mat, parent=self.root, bevel=0.02)
                add_box(f"{self.id}_armL_{arm_side}", (0.12, 0.12, 1.10), loc=(ax * 1.25, -0.48, 0.55), rot=(math.radians(45), 0, math.radians(8 * arm_side)), mat=body_mat, parent=self.root, bevel=0.02)
                # Needle claw fingers reaching toward camera
                for fgi in range(3):
                    add_cone(f"{self.id}_claw_{arm_side}_{fgi}", 0.022, 0.003, 0.24, loc=(ax * 1.25 + (fgi - 1) * 0.05, -0.68, 0.05), rot=(math.radians(65), 0, 0), mat=teeth_mat, parent=self.root, verts=4)
            # Spindly legs
            for leg_side, lx in ((-1, -0.20), (1, 0.20)):
                add_box(f"{self.id}_leg_{leg_side}", (0.18, 0.20, 1.20), loc=(lx, 0.10, 0.60), rot=(math.radians(-8), 0, 0), mat=body_mat, parent=self.root, bevel=0.02)
            # Jagged shadowy spine horns down curved back
            for sp_i in range(7):
                add_cone(f"{self.id}_spine_{sp_i}", 0.06, 0.01, 0.45 + sp_i * 0.04, loc=(0, 0.15 + sp_i * 0.04, 1.05 + sp_i * 0.18), rot=(math.radians(-50), 0, 0), mat=tendril_mat, parent=self.root, verts=4)

        else:
            # Giant furry monster (fur_giant)
            add_box(f"{self.id}_torso", (0.85, 0.55, 0.92), loc=(0, 0, 1.15), mat=body_mat, parent=self.root, bevel=0.08)
            add_box(f"{self.id}_head", (0.58, 0.52, 0.50), loc=(0, -0.14, 1.68), mat=body_mat, parent=self.root, bevel=0.08)
            add_box(f"{self.id}_legL", (0.30, 0.34, 0.72), loc=(-0.25, 0, 0.36), mat=body_mat, parent=self.root, bevel=0.04)
            add_box(f"{self.id}_legR", (0.30, 0.34, 0.72), loc=(0.25, 0, 0.36), mat=body_mat, parent=self.root, bevel=0.04)
            add_box(f"{self.id}_armL", (0.28, 0.30, 0.95), loc=(-0.60, -0.05, 1.05), mat=body_mat, parent=self.root, bevel=0.04)
            add_box(f"{self.id}_armR", (0.28, 0.30, 0.95), loc=(0.60, -0.05, 1.05), mat=body_mat, parent=self.root, bevel=0.04)

            # Procedural fur spikes
            if "fur_spikes" in spec.get("features", []) or arch == "fur_giant":
                rng = random.Random(hash(self.id) & 0xFFFF)
                for idx in range(52):
                    fx = rng.uniform(-0.72, 0.72)
                    fy = rng.uniform(-0.30, 0.32)
                    fz = rng.uniform(0.35, 1.90)
                    rx = rng.uniform(-0.9, 0.9)
                    ry = rng.uniform(-0.9, 0.9)
                    add_cone(f"{self.id}_fur{idx}", 0.09, 0.008, 0.36, loc=(fx, fy, fz), rot=(rx, ry, 0), mat=body_mat, parent=self.root, verts=4)

            # Mouth
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
        set_key(self.root, "location", f1, self.shot_end_pos, "LINEAR")

        # Wing flap / soar cycle for winged beasts
        if hasattr(self, "wing_L_pivot") and hasattr(self, "wing_R_pivot"):
            mid_f = int(f0 + (f1 - f0) * 0.5)
            set_key(self.wing_L_pivot, "rotation_euler", f0, (0, 0, 0), "CONSTANT")
            set_key(self.wing_R_pivot, "rotation_euler", f0, (0, 0, 0), "CONSTANT")
            set_key(self.wing_L_pivot, "rotation_euler", mid_f, (0, 0.32, 0), "LINEAR")
            set_key(self.wing_R_pivot, "rotation_euler", mid_f, (0, -0.32, 0), "LINEAR")
            set_key(self.wing_L_pivot, "rotation_euler", f1, (0, 0, 0), "LINEAR")
            set_key(self.wing_R_pivot, "rotation_euler", f1, (0, 0, 0), "LINEAR")

        # Menacing head twitch for shadow stalker
        if hasattr(self, "stalker_head"):
            mid_f = int(f0 + (f1 - f0) * 0.5)
            set_key(self.stalker_head, "rotation_euler", f0, (math.radians(18), 0, 0), "CONSTANT")
            set_key(self.stalker_head, "rotation_euler", mid_f, (math.radians(24), 0, math.radians(12)), "LINEAR")
            set_key(self.stalker_head, "rotation_euler", f1, (math.radians(18), 0, 0), "LINEAR")


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
    car_paint = make_mat("env_car_pt", (0.18, 0.38, 0.55, 1.0), metallic=0.85, roughness=0.25)
    metal_bike = make_mat("env_bike_m", (0.82, 0.18, 0.22, 1.0), metallic=0.75, roughness=0.35)
    mailbox_red = make_mat("env_mb_flag", (0.90, 0.12, 0.12, 1.0), roughness=0.4)

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

            # Curbside Mailbox on wood post with red flag
            mb_x = side * 4.9
            mb_y = hy - 1.1
            add_env_cyl(f"sub_mb_post_{side}_{hy}", 0.05, 1.05, (mb_x, mb_y, 0.52), pole_mat, c_sub, verts=8)
            add_env_box(f"sub_mb_box_{side}_{hy}", (0.28, 0.52, 0.28), (mb_x, mb_y, 1.10), trim_white, c_sub, bevel=0.03)
            add_env_box(f"sub_mb_flag_{side}_{hy}", (0.04, 0.14, 0.08), (mb_x + side * 0.16, mb_y + 0.12, 1.18), mailbox_red, c_sub, bevel=0.01)

            # Porch Rocking Chair
            ch_x = px - side * 0.25
            ch_y = hy - 1.0
            add_env_box(f"sub_ch_seat_{side}_{hy}", (0.65, 0.65, 0.06), (ch_x, ch_y, 0.52), pole_mat, c_sub, bevel=0.01)
            add_env_box(f"sub_ch_back_{side}_{hy}", (0.06, 0.62, 0.75), (ch_x - side * 0.30, ch_y, 0.88), pole_mat, c_sub, bevel=0.01)

            # Kid's Bicycle (every other house)
            if idx_h % 2 == 1:
                bx_pos = side * 5.6
                by_pos = hy + 1.8
                for w_i, wy_off in enumerate((-0.42, 0.42)):
                    add_env_cyl(f"sub_bike_w_{side}_{hy}_{w_i}", 0.24, 0.05, (bx_pos, by_pos + wy_off, 0.24), iron_mat, c_sub, rot=(0, math.radians(90), 0), verts=12)
                add_env_box(f"sub_bike_fr_{side}_{hy}", (0.06, 0.80, 0.10), (bx_pos, by_pos, 0.30), metal_bike, c_sub, bevel=0.01)
                add_env_box(f"sub_bike_hb_{side}_{hy}", (0.35, 0.06, 0.06), (bx_pos, by_pos - 0.38, 0.52), metal_bike, c_sub, bevel=0.01)

            # Parked Pickup Truck in driveway (every 3rd house)
            if idx_h % 3 == 0:
                cx = side * 8.6
                cy = hy - 4.2
                add_env_box(f"sub_car_cab_{side}_{hy}", (2.1, 1.9, 1.1), (cx, cy, 0.95), car_paint, c_sub, bevel=0.05)
                add_env_box(f"sub_car_bed_{side}_{hy}", (2.0, 1.8, 0.65), (cx, cy + 1.8, 0.72), car_paint, c_sub, bevel=0.03)
                add_env_box(f"sub_car_hood_{side}_{hy}", (1.9, 1.4, 0.62), (cx, cy - 1.6, 0.70), car_paint, c_sub, bevel=0.04)
                for wx_off in (-1.05, 1.05):
                    for wy_off in (-1.3, 1.3):
                        add_env_cyl(f"sub_car_wh_{side}_{hy}_{wx_off}_{wy_off}", 0.34, 0.22, (cx + wx_off, cy + wy_off, 0.34), iron_mat, c_sub, rot=(0, math.radians(90), 0), verts=14)

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

    # 3. HOSPITAL ROOM (Cinematic Atmospheric Ward)
    c_hosp = make_col("set_hospital_room")
    sets["hospital_room"] = c_hosp

    # Two-Tone Walls: Deep hospital teal-slate wainscot lower half, warm textured sage-grey upper half (no cheap flat white!)
    hosp_wall_top = make_textured_mat("hosp_w_top", (0.70, 0.74, 0.72, 1.0), (0.78, 0.81, 0.79, 1.0), scale=4.0, roughness=0.65, bump_strength=0.04)
    hosp_wainscot = make_textured_mat("hosp_w_bot", (0.14, 0.26, 0.30, 1.0), (0.20, 0.32, 0.36, 1.0), scale=5.0, roughness=0.40, bump_strength=0.06)
    hosp_rail_mat = make_mat("hosp_guardrail", (0.85, 0.87, 0.90, 1.0), metallic=0.92, roughness=0.18)
    hosp_baseboard = make_mat("hosp_bboard", (0.10, 0.11, 0.13, 1.0), roughness=0.6)

    # Polished hospital linoleum / terrazzo floor with sharp specular reflections
    hosp_fl = make_textured_mat("hosp_fl_spec", (0.18, 0.22, 0.24, 1.0), (0.24, 0.28, 0.30, 1.0), scale=8.0, roughness=0.10, bump_strength=0.02)

    # Lighting & Medical equipment materials
    ceil_mat = make_mat("hosp_ceil", (0.65, 0.68, 0.70, 1.0), roughness=0.85)
    hosp_light = make_mat("hosp_ceil_light", (0.92, 0.96, 1.0, 1.0), emission=(0.92, 0.96, 1.0, 1.0), emission_strength=2.2)
    ecg_mat = make_mat("hosp_ecg", (0.05, 1.0, 0.42, 1.0), emission=(0.05, 1.0, 0.42, 1.0), emission_strength=9.0)
    curtain_mat = make_textured_mat("hosp_curt", (0.22, 0.38, 0.44, 1.0), (0.30, 0.48, 0.54, 1.0), scale=6.0, roughness=0.88, bump_strength=0.12)
    chrome_mat = make_mat("hosp_chrome", (0.88, 0.89, 0.92, 1.0), metallic=0.95, roughness=0.12)
    chair_mat = make_textured_mat("hosp_chair", (0.10, 0.18, 0.26, 1.0), (0.14, 0.24, 0.34, 1.0), scale=4.0, roughness=0.60, bump_strength=0.08)
    gas_o2 = make_mat("hosp_gas_o2", (0.12, 0.78, 0.25, 1.0), roughness=0.3)
    gas_vac = make_mat("hosp_gas_vac", (0.95, 0.82, 0.12, 1.0), roughness=0.3)
    blind_mat = make_mat("hosp_blinds", (0.75, 0.78, 0.80, 1.0), roughness=0.40)
    chart_mat = make_mat("hosp_chart", (0.92, 0.88, 0.80, 1.0), roughness=0.7)

    # Hospital Bed Fabrics
    sheet_mat = make_textured_mat("hosp_sheet", (0.78, 0.86, 0.88, 1.0), (0.84, 0.90, 0.92, 1.0), scale=12.0, roughness=0.75, bump_strength=0.04)
    blanket_mat = make_textured_mat("hosp_blanket", (0.10, 0.20, 0.32, 1.0), (0.15, 0.28, 0.42, 1.0), scale=18.0, roughness=0.88, bump_strength=0.16)
    pillow_mat = make_textured_mat("hosp_pillow", (0.86, 0.86, 0.84, 1.0), (0.90, 0.90, 0.88, 1.0), scale=8.0, roughness=0.80, bump_strength=0.05)

    for nm, sz, lc, mt in [
        # Reflective Floor & Dimmed Acoustic Ceiling
        ("hp_fl", (10, 10, 0.1), (0, 0, -0.05), hosp_fl),
        ("hp_ceil", (10, 10, 0.1), (0, 0, 4.45), ceil_mat),
        # Recessed Ceiling Troffers with Soft Frosted Diffusers
        ("hp_clight1", (2.0, 1.0, 0.06), (0, 2.3, 4.40), hosp_light),
        ("hp_clight2", (2.0, 1.0, 0.06), (0, -1.5, 4.40), hosp_light),

        # Upper Walls (Warm Sage-Grey Medical Plaster)
        ("hp_wb_top", (10, 0.22, 3.1), (0, 4.5, 2.9), hosp_wall_top),
        ("hp_wl_top", (0.22, 10, 3.1), (-4.5, 0, 2.9), hosp_wall_top),
        ("hp_wr_top", (0.22, 10, 3.1), (4.5, 0, 2.9), hosp_wall_top),

        # Lower Walls (Deep Teal-Slate Wainscoting Bumper Panels)
        ("hp_wb_bot", (10, 0.26, 1.35), (0, 4.48, 0.675), hosp_wainscot),
        ("hp_wl_bot", (0.26, 10, 1.35), (-4.48, 0, 0.675), hosp_wainscot),
        ("hp_wr_bot", (0.26, 10, 1.35), (4.48, 0, 0.675), hosp_wainscot),

        # Protective Dark Rubber Baseboards
        ("hp_bb_b", (9.8, 0.28, 0.16), (0, 4.46, 0.08), hosp_baseboard),
        ("hp_bb_l", (0.28, 9.8, 0.16), (-4.46, 0, 0.08), hosp_baseboard),
        ("hp_bb_r", (0.28, 9.8, 0.16), (4.46, 0, 0.08), hosp_baseboard),

        # Stainless Steel Hospital Wall Crash Rail
        ("hp_rail_b", (9.2, 0.08, 0.12), (0, 4.38, 1.05), hosp_rail_mat),

        # Modern Tubular Hospital Bed
        ("hp_bed_frame", (1.68, 2.58, 0.38), (0, 2.4, 0.19), chrome_mat),
        ("hp_bed_hb", (1.68, 0.08, 0.52), (0, 3.65, 0.62), hosp_rail_mat),
        ("hp_bed_fb", (1.68, 0.08, 0.42), (0, 1.15, 0.44), hosp_rail_mat),
        ("hp_bed_mat", (1.52, 2.38, 0.32), (0, 2.4, 0.48), sheet_mat),
        ("hp_bed_rail_l", (0.06, 1.4, 0.32), (-0.80, 2.4, 0.68), chrome_mat),
        ("hp_bed_rail_r", (0.06, 1.4, 0.32), (0.80, 2.4, 0.68), chrome_mat),
        ("hp_blnk", (1.48, 1.55, 0.44), (0, 2.05, 0.82), blanket_mat),
        ("hp_sheet_cuff", (1.50, 0.16, 0.08), (0, 2.65, 0.90), sheet_mat),
        ("hp_pil", (1.1, 0.48, 0.20), (0, 3.05, 0.64), pillow_mat),

        # Patient Chart Clipboard Hanging on Footboard
        ("hp_chart_board", (0.28, 0.02, 0.38), (0.25, 1.08, 0.52), chrome_mat),
        ("hp_chart_paper", (0.24, 0.03, 0.32), (0.25, 1.07, 0.52), chart_mat),

        # Medical Headwall Console behind bed
        ("hp_hwall", (2.8, 0.14, 0.55), (0, 4.38, 1.85), hosp_wall_top),
        ("hp_gas1", (0.16, 0.06, 0.22), (-0.6, 4.30, 1.85), gas_o2),
        ("hp_gas2", (0.16, 0.06, 0.22), (-0.3, 4.30, 1.85), gas_vac),
        ("hp_call", (0.14, 0.05, 0.18), (0.3, 4.30, 1.85), mailbox_red),

        # Vital Signs Monitor on Adjustable Swivel Arm (Glowing ECG Green)
        ("hp_mon_pole", (0.08, 0.08, 1.15), (1.55, 3.1, 0.95), chrome_mat),
        ("hp_mon_box", (0.68, 0.26, 0.52), (1.55, 3.0, 1.55), iron_mat),
        ("hp_mon_scr", (0.58, 0.05, 0.40), (1.55, 2.86, 1.55), ecg_mat),

        # Overbed Mayo Rolling Tray Table with Water Pitcher & Straw Cup
        ("hp_tray_top", (0.95, 0.52, 0.06), (0.45, 1.7, 0.95), chrome_mat),
        ("hp_tray_leg", (0.08, 0.08, 0.88), (0.85, 1.7, 0.46), chrome_mat),
        ("hp_med_cup", (0.08, 0.08, 0.12), (0.35, 1.7, 1.02), win_mat),

        # Bedside Visitor Armchair (Padded hospital recliner)
        ("hp_ch_seat", (0.78, 0.75, 0.20), (-1.85, 2.5, 0.44), chair_mat),
        ("hp_ch_back", (0.78, 0.18, 0.80), (-1.85, 2.85, 0.85), chair_mat),
        ("hp_ch_armL", (0.14, 0.70, 0.35), (-2.25, 2.5, 0.65), chair_mat),
        ("hp_ch_armR", (0.14, 0.70, 0.35), (-1.45, 2.5, 0.65), chair_mat),
        ("hp_ch_leg1", (0.08, 0.08, 0.40), (-2.18, 2.22, 0.20), chrome_mat),
        ("hp_ch_leg2", (0.08, 0.08, 0.40), (-1.52, 2.22, 0.20), chrome_mat),

        # Privacy Curtain on Track
        ("hp_curt", (0.08, 3.4, 2.9), (-2.55, 2.5, 1.85), curtain_mat),

        # Hospital Room Window & Venetian Blinds (creates cinematic shadow streaks!)
        ("hp_win_f", (2.2, 0.12, 1.5), (-1.8, 4.38, 2.3), hosp_rail_mat),
        ("hp_win", (2.0, 0.10, 1.3), (-1.8, 4.36, 2.3), win_mat),

        # Heavy Hospital Door with Vision Window & Kickplate
        ("hp_door_f", (1.4, 0.14, 2.5), (3.2, 4.38, 1.25), hosp_rail_mat),
        ("hp_door", (1.2, 0.12, 2.38), (3.2, 4.36, 1.20), hosp_wainscot),
        ("hp_door_win", (0.35, 0.14, 0.85), (3.2, 4.35, 1.60), win_mat),
        ("hp_door_kick", (1.18, 0.14, 0.35), (3.2, 4.35, 0.18), chrome_mat),

        # Hand Sanitizer Dispenser next to door
        ("hp_sanitizer", (0.18, 0.12, 0.32), (2.2, 4.36, 1.50), hosp_rail_mat),
        # Biohazard Step Trash Can with Foot Pedal
        ("hp_trash_can", (0.35, 0.35, 0.55), (2.3, 4.15, 0.28), mailbox_red),
    ]:
        add_env_box(nm, sz, lc, mt, c_hosp, bevel=0.02)

    # Venetian Blind Slats across window for cinematic shadow streaks
    for bi in range(12):
        b_z = 1.72 + bi * 0.10
        add_env_box(f"hp_blind_{bi}", (1.95, 0.06, 0.015), (-1.8, 4.34, b_z), blind_mat, c_hosp, rot=(math.radians(35), 0, 0), bevel=0)

    # IV Pole with dual fluid bags, drip chamber & translucent IV infusion line to bed
    add_env_cyl("hp_iv_pole", 0.04, 2.2, (1.25, 3.5, 1.1), chrome_mat, c_hosp, verts=10)
    add_env_box("hp_iv_bag1", (0.18, 0.10, 0.28), (1.15, 3.5, 1.95), win_mat, c_hosp, bevel=0.04)
    add_env_box("hp_iv_bag2", (0.18, 0.10, 0.28), (1.35, 3.5, 1.95), win_mat, c_hosp, bevel=0.04)
    add_env_cyl("hp_iv_tube", 0.014, 1.25, (1.05, 3.05, 1.25), win_mat, c_hosp, rot=(math.radians(24), math.radians(18), 0), verts=8)

    # Bedside Rolling Tray Details: Ribbed Water Pitcher & Drinking Straw
    pitcher_m = make_mat("hp_pitcher_m", (0.80, 0.90, 0.96, 1.0), roughness=0.25)
    straw_m = make_mat("hp_straw_m", (0.90, 0.22, 0.22, 1.0), roughness=0.5)
    add_env_cyl("hp_pitcher", 0.07, 0.22, (0.55, 1.65, 1.06), pitcher_m, c_hosp, verts=14)
    add_env_cyl("hp_straw", 0.008, 0.18, (0.35, 1.70, 1.08), straw_m, c_hosp, rot=(math.radians(15), 0, 0), verts=6)

    # Dedicated Atmospheric Hospital Lights:
    # 1. Warm Bedside Examination / Reading Sconce pointing over patient
    hosp_spot = bpy.data.lights.new("hp_bed_sconce", type="SPOT")
    hosp_spot.energy = 110.0
    hosp_spot.color = (1.0, 0.90, 0.74)
    hosp_spot.spot_size = math.radians(52)
    hosp_spot.spot_blend = 0.45
    hosp_spot_obj = bpy.data.objects.new("hp_bed_sconce", hosp_spot)
    hosp_spot_obj.location = (0, 3.65, 2.75)
    hosp_spot_obj.rotation_euler = (math.radians(-32), 0, 0)
    c_hosp.objects.link(hosp_spot_obj)

    # 2. Window Directional Key Light streaming through Venetian blinds
    win_spot = bpy.data.lights.new("hp_win_beam", type="SPOT")
    win_spot.energy = 220.0
    win_spot.color = (0.75, 0.88, 1.0)
    win_spot.spot_size = math.radians(48)
    win_spot.spot_blend = 0.25
    win_spot_obj = bpy.data.objects.new("hp_win_beam", win_spot)
    win_spot_obj.location = (-1.8, 6.2, 3.6)
    win_spot_obj.rotation_euler = (math.radians(145), 0, 0)
    c_hosp.objects.link(win_spot_obj)

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
def configure_render(scene, fps: int, draft: bool, engine_choice: str = "auto"):
    # Hardware acceleration selector: CYCLES, EEVEE_NEXT, or auto
    use_gpu_cycles = False
    chosen = (engine_choice or "auto").strip().upper()

    if chosen not in ("EEVEE", "EEVEE_NEXT", "BLENDER_EEVEE_NEXT"):
        try:
            import addon_utils
            addon_utils.enable("cycles")
        except Exception:
            pass

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

    if not use_gpu_cycles or chosen in ("EEVEE", "EEVEE_NEXT", "BLENDER_EEVEE_NEXT"):
        # Use EEVEE Next (ultra-fast rasterization with screen-space raytracing)
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
        "wistful_pastel": ((0.62, 0.68, 0.88, 1.0), 0.95, (1.0, 0.90, 0.78), 3.0),
        "golden_hour": ((0.98, 0.58, 0.28, 1.0), 1.05, (1.0, 0.78, 0.45), 3.6),
        "blue_hour": ((0.08, 0.12, 0.26, 1.0), 0.60, (0.55, 0.70, 0.95), 1.6),
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
    configure_render(scene, fps, args.draft, getattr(args, "engine", "auto"))
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

    # Auto-register any actor ID mentioned in shots that was missing from cast/creatures
    for s in ep.get("shots", []):
        for act in s.get("actors", []):
            aid = act.get("id", "")
            if aid and aid not in rigs:
                low = aid.lower()
                if any(w in low for w in ("monster", "creature", "beast", "shadow", "stalker", "demon", "bird", "crawler", "ghost", "entity", "hound", "wendigo", "gargoyle")):
                    print(f"[blender_render] Auto-generating procedural creature for unlisted actor: {aid}")
                    rigs[aid] = ProceduralCreature({"id": aid, "archetype": aid, "scale": 2.6}, cast_col)
                else:
                    print(f"[blender_render] Auto-generating human rig for unlisted actor: {aid}")
                    rigs[aid] = R6Rig({"id": aid, "height": "adult"}, faces_dir, cast_col)

    # Camera with shallow cinematic depth of field
    cam_data = bpy.data.cameras.new("MainCam")
    cam_data.lens = 38.0
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = 2.4
    cam_obj = bpy.data.objects.new("MainCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    shots = ep.get("shots", [])
    total_dur = float(ep.get("total_duration", 60.0))
    scene.frame_start = 1
    scene.frame_end = max(2, int(math.ceil(total_dur * fps)))
    if args.max_frames > 0 and args.still_frame == 0:
        scene.frame_end = min(scene.frame_end, args.max_frames)

    for idx, shot in enumerate(shots):
        t0 = float(shot.get("start", 0.0))
        t1 = float(shot.get("end", t0 + 2.0))
        f0 = max(1, int(round(t0 * fps)) + 1)
        f1 = max(f0 + 1, int(round(t1 * fps)))
        if idx == len(shots) - 1 and args.max_frames == 0:
            f1 = scene.frame_end

        if args.max_frames > 0 and args.still_frame == 0 and f0 > scene.frame_end:
            continue

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
                    anim_state = act.get("anim", "idle")
                    if anim_state in ("lie", "sleep", "bed"):
                        target_h = 0.32  # Bedside mattress eye-level
                        # Focus on patient's face / chest near the pillow (shifted along bed towards headboard)
                        target_pos = Vector((float(p[0]), float(p[2]) + 0.65, float(p[1]) + target_h))
                        target_pos_end = Vector((float(p[0]), float(p[2]) + 0.65, float(p[1]) + target_h))
                    elif anim_state == "sit":
                        target_h = 0.82  # Seated visitor eye-level
                        target_pos = Vector((float(p[0]), float(p[2]), float(p[1]) + target_h))
                        ep_pos = getattr(rigs[aid], "shot_end_pos", (float(p[0]), float(p[2]), float(p[1])))
                        target_pos_end = Vector((ep_pos[0], ep_pos[1], ep_pos[2] + target_h))
                    else:
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
        is_hospital = (shot.get("set") == "hospital_room")

        if is_hospital:
            # Cinematic hospital room camera framing (natural distances, clear compositions, no extreme/clipping zooms)
            if cam_type == "closeup_face":
                # Medium close-up framing patient's face & chest comfortably
                off0 = Vector((0.5, -1.8, 0.45))
                off1 = Vector((0.2, -1.3, 0.35))
            elif cam_type in ("ward_crane_swing", "crane", "high_angle", "establishing_aerial", "wide"):
                # Elevated 3rd-person swinging crane shot sweeping across the ward
                # Centered between bedside visitor and hospital bed so BOTH characters and all medical equipment are framed
                scene_center_offset = Vector((-0.45, 0.0, 0.20))
                off0 = scene_center_offset + Vector((-1.1, -5.0, 2.35))
                off1 = scene_center_offset + Vector((1.2, -4.4, 1.95))
            elif cam_type == "ots_left":
                # Over-the-shoulder behind visitor looking across at patient and medical monitors
                off0 = Vector((-1.45, -2.6, 0.65))
                off1 = Vector((-1.20, -2.0, 0.50))
            elif cam_type == "ots_right":
                off0 = Vector((1.9, -2.8, 0.65))
                off1 = Vector((1.5, -2.1, 0.50))
            elif cam_type == "dutch_angle_tension":
                off0 = Vector((1.2, -3.2, 0.65))
                off1 = Vector((0.8, -2.4, 0.45))
            elif cam_type == "low_angle_monster":
                off0 = Vector((0.8, -3.4, -0.15))
                off1 = Vector((0.4, -2.6, -0.05))
            else:  # push_in / default: clean cinematic 3/4 ward shot showing bed, patient, visitor, IV pole & monitor
                off0 = Vector((0.8, -3.6, 0.65))
                off1 = Vector((0.4, -2.6, 0.45))
        elif cam_type == "establishing_aerial":
            off0 = Vector((2.5, -12.0 * dist_scale, 7.5))
            off1 = Vector((1.0, -9.0 * dist_scale, 5.5))
        elif cam_type == "closeup_face":
            off0 = Vector((0.0, -2.1 * dist_scale, 0.15))
            off1 = Vector((0.0, -1.75 * dist_scale, 0.15))
        elif cam_type in ("medium_shot", "showcase_prop"):
            off0 = Vector((0.25, -3.2 * dist_scale, -0.15))
            off1 = Vector((0.05, -2.7 * dist_scale, -0.15))
        elif cam_type in ("ensemble_master", "wide_group"):
            off0 = Vector((0.0, -5.2 * dist_scale, 0.15))
            off1 = Vector((0.0, -4.6 * dist_scale, 0.15))
        elif cam_type == "whip_zoom":
            off0 = Vector((0.6, -4.5 * dist_scale, 0.4))
            off1 = Vector((0.0, -1.9 * dist_scale, 0.15))
        elif cam_type == "low_angle_monster":
            # Menacing low-angle towering framing that captures the monster's full height, arms/wings, and menacing face
            if target_pos.z > 0.8:
                # Airborne flying beast: wide low-to-mid dramatic perspective showcasing wingspan & raptor dive
                off0 = Vector((0.0, -7.8, -0.2))
                off1 = Vector((0.0, -6.6, -0.1))
            else:
                # Towering grounded behemoth/stalker: framed from low angle with breathing room for full spine and razor claws
                off0 = Vector((0.0, -6.2, 0.75 - target_pos.z))
                off1 = Vector((0.0, -5.2, 0.85 - target_pos.z))
        elif cam_type == "ots_left":
            off0 = Vector((-1.6, -3.0 * dist_scale, 0.2))
            off1 = Vector((-1.2, -2.6 * dist_scale, 0.2))
        elif cam_type == "ots_right":
            off0 = Vector((1.6, -3.0 * dist_scale, 0.2))
            off1 = Vector((1.2, -2.6 * dist_scale, 0.2))
        elif cam_type == "rooftop_voyeur":
            off0 = Vector((-3.2, -14.0 * dist_scale, 6.2))
            off1 = Vector((-2.6, -11.5 * dist_scale, 5.4))
        elif cam_type == "porch_voyeur":
            off0 = Vector((2.4, -4.8 * dist_scale, 1.4 - target_pos.z))
            off1 = Vector((1.8, -3.8 * dist_scale, 1.3 - target_pos.z))
        elif cam_type == "dutch_angle_tension":
            off0 = Vector((1.2, -3.6 * dist_scale, 0.45))
            off1 = Vector((0.8, -2.8 * dist_scale, 0.35))
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
        if cam_type == "dutch_angle_tension":
            cam_obj.rotation_euler.y += math.radians(6.5)
        cam_obj.keyframe_insert(data_path="location", frame=f0)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=f0)

        # Cinematic Depth of Field tracking
        dist0 = (p0 - target_pos).length
        cam_data.dof.focus_distance = dist0
        cam_data.dof.keyframe_insert(data_path="focus_distance", frame=f0)

        cam_obj.location = p1
        point_camera_at(cam_obj, target_pos_end)
        if cam_type == "dutch_angle_tension":
            cam_obj.rotation_euler.y += math.radians(5.0)
        cam_obj.keyframe_insert(data_path="location", frame=f1)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=f1)

        dist1 = (p1 - target_pos_end).length
        cam_data.dof.focus_distance = dist1
        cam_data.dof.keyframe_insert(data_path="focus_distance", frame=f1)

    # Render animation or still snapshot
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def _on_render_frame(s, *a):
        cur = s.frame_current
        end = s.frame_end
        pct = int((cur / max(1, end)) * 100)
        print(f"[blender_render] Frame {cur}/{end} ({pct}%) rendered", flush=True)

    bpy.app.handlers.render_post.append(_on_render_frame)

    if out_path.suffix.lower() == ".png" or args.still_frame > 0:
        f = args.still_frame if args.still_frame > 0 else (args.max_frames if args.max_frames > 0 else 1)
        scene.frame_set(f)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(out_path)
        bpy.ops.render.render(write_still=True)
        print(f"[blender_render] Rendered snapshot still at frame {f} to {out_path}", flush=True)
        return

    scene.render.use_file_extension = False
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(animation=True)
    print(f"[blender_render] Rendered {scene.frame_end} frames to {out_path}", flush=True)


if __name__ == "__main__":
    main()

