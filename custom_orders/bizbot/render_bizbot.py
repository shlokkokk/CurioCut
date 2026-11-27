"""
CurioCut Peak 3D Renderer for BizBot (Blender 4.3 EEVEE Next).
Upgraded Studio-Grade Production:
- Real 3D beveled Smartphone, Laptop, Digital Clock (02:30), Coffee Mug, Desk Lamp
- Cybernetic BizBot Mascot with animated glowing eyes, visor, antenna & levitating rings
- Floating 3D WhatsApp Dark-Mode UI Card with crisp 3D Typography & Interactive Buttons
- True keyframed visibility, animated Mix Shader states, camera DOF distance, & Fog Glow compositor
- Optimized EEVEE Next samples (16 TAA) for fast, sharp 1080x1920 RTX A2000 rendering
"""

import sys
import math
import json
import argparse
from pathlib import Path

import bpy
from mathutils import Vector, Euler

argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

parser = argparse.ArgumentParser()
parser.add_argument("--episode", required=True, help="Path to episode_timed.json")
parser.add_argument("--out", required=True, help="Output MP4 file path")
parser.add_argument("--fps", type=int, default=30)
parser.add_argument("--draft", action="store_true", help="Render at 540x960 for fast preview")
parser.add_argument("--max-frames", type=int, default=0)
parser.add_argument("--still-frame", type=int, default=0, help="Render single still PNG for visual QA")
args = parser.parse_args(argv)

with open(args.episode, "r", encoding="utf-8") as f:
    ep_data = json.load(f)

FPS = args.fps
TOTAL_FRAMES = ep_data.get("total_frames", 1234)
if args.max_frames > 0:
    TOTAL_FRAMES = min(TOTAL_FRAMES, args.max_frames)

print(f"[BizBot 3D Studio] Initializing Blender 4.3 scene ({TOTAL_FRAMES} frames @ {FPS}fps)...", flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Engine setup (EEVEE Next in Blender 4.3)
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES

# Fast, sharp EEVEE Next settings
if hasattr(scene, "eevee"):
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 16 if not args.draft else 8
    if hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = True
    if hasattr(scene.eevee, "use_shadows"):
        scene.eevee.use_shadows = True

# Resolution
if args.draft:
    scene.render.resolution_x = 540
    scene.render.resolution_y = 960
else:
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
scene.render.resolution_percentage = 100

# Color Management
view_transforms = [v.name for v in scene.view_settings.bl_rna.properties['view_transform'].enum_items]
scene.view_settings.view_transform = 'AgX' if 'AgX' in view_transforms else 'Filmic'
scene.view_settings.look = 'AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [l.name for l in scene.view_settings.bl_rna.properties['look'].enum_items] else 'High Contrast'

# Compositor: Cinematic Fog Glow (Bloom) - tuned so text stays razor sharp
scene.use_nodes = True
comp = scene.node_tree
comp.nodes.clear()
rl = comp.nodes.new("CompositorNodeRLayers")
glare = comp.nodes.new("CompositorNodeGlare")
glare.glare_type = 'FOG_GLOW'
glare.quality = 'HIGH'
glare.threshold = 1.85
glare.size = 6
glare.mix = -0.35
comp_out = comp.nodes.new("CompositorNodeComposite")
comp.links.new(rl.outputs["Image"], glare.inputs["Image"])
comp.links.new(glare.outputs["Image"], comp_out.inputs["Image"])

# World Ambient (Deep midnight slate)
world = bpy.data.worlds.new("NightStudio")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.012, 0.015, 0.025, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ==============================================================================
# MATERIAL & GEOMETRY HELPERS
# ==============================================================================
def make_mat(name, color=(0.8, 0.8, 0.8, 1.0), roughness=0.3, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission is not None:
            bsdf.inputs["Emission Color"].default_value = emission
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

def make_switchable_glow_mat(name, base_col=(0.02, 0.02, 0.03, 1.0), glow_col=(0.15, 0.85, 0.40, 1.0)):
    """Material whose emission color & strength can be cleanly keyframed."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = base_col
    bsdf.inputs["Roughness"].default_value = 0.08
    bsdf.inputs["Metallic"].default_value = 0.1
    bsdf.inputs["Emission Color"].default_value = glow_col
    bsdf.inputs["Emission Strength"].default_value = 2.5
    return mat, bsdf

def add_bevel(obj, width=0.015, segments=3):
    bev = obj.modifiers.new(name="Bevel", type='BEVEL')
    bev.width = width
    bev.segments = segments
    bev.limit_method = 'NONE'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

def add_text_3d(name, body, loc, rot_deg=(0, 0, 0), size=0.1, extrude=0.008, bevel=0.002, align='CENTER', mat=None, parent=None):
    bpy.ops.object.text_add(location=loc, rotation=[math.radians(a) for a in rot_deg])
    txt = bpy.context.active_object
    txt.name = name
    txt.data.body = body
    txt.data.size = size
    txt.data.extrude = extrude
    txt.data.bevel_depth = bevel
    txt.data.align_x = align
    txt.data.align_y = 'CENTER'
    if mat:
        txt.data.materials.append(mat)
    if parent:
        txt.parent = parent
    return txt

def key_vis(obj, frame, visible: bool):
    targets = [obj] + list(obj.children_recursive)
    for t in targets:
        t.hide_render = not visible
        t.hide_viewport = not visible
        t.keyframe_insert(data_path="hide_render", frame=frame)
        t.keyframe_insert(data_path="hide_viewport", frame=frame)

# Palette
mat_desk = make_mat("Mat_Desk", color=(0.035, 0.026, 0.022, 1.0), roughness=0.22, metallic=0.05)
mat_wall = make_mat("Mat_Wall", color=(0.018, 0.020, 0.032, 1.0), roughness=0.65)
mat_slat = make_mat("Mat_Slat", color=(0.028, 0.030, 0.045, 1.0), roughness=0.45, metallic=0.2)
mat_titanium = make_mat("Mat_Titanium", color=(0.12, 0.13, 0.16, 1.0), roughness=0.18, metallic=0.92)
mat_chrome = make_mat("Mat_Chrome", color=(0.92, 0.94, 0.98, 1.0), roughness=0.06, metallic=1.0)
mat_ceramic = make_mat("Mat_Ceramic", color=(0.94, 0.96, 0.99, 1.0), roughness=0.14, metallic=0.15)
mat_dark_glass = make_mat("Mat_DarkGlass", color=(0.01, 0.015, 0.02, 1.0), roughness=0.04, metallic=0.1)
mat_green_glow = make_mat("Mat_GreenGlow", color=(0.14, 0.85, 0.42, 1.0), roughness=0.12, emission=(0.14, 0.85, 0.42, 1.0), emission_strength=2.2)
mat_cyan_glow = make_mat("Mat_CyanGlow", color=(0.1, 0.75, 0.95, 1.0), roughness=0.1, emission=(0.1, 0.75, 0.95, 1.0), emission_strength=2.5)
mat_red_glow = make_mat("Mat_RedGlow", color=(0.85, 0.10, 0.12, 1.0), roughness=0.18, emission=(0.95, 0.10, 0.12, 1.0), emission_strength=1.4)
mat_gold_glow = make_mat("Mat_GoldGlow", color=(1.0, 0.78, 0.12, 1.0), roughness=0.15, metallic=0.85, emission=(1.0, 0.78, 0.12, 1.0), emission_strength=1.5)
mat_white_text = make_mat("Mat_WhiteText", color=(0.98, 0.98, 1.0, 1.0), roughness=0.2, emission=(0.95, 0.98, 1.0, 1.0), emission_strength=0.95)
mat_dark_text = make_mat("Mat_DarkText", color=(0.015, 0.02, 0.025, 1.0), roughness=0.25, metallic=0.1)
mat_wa_card = make_mat("Mat_WACard", color=(0.04, 0.06, 0.08, 1.0), roughness=0.25, metallic=0.2)
mat_wa_header = make_mat("Mat_WAHeader", color=(0.06, 0.10, 0.13, 1.0), roughness=0.3)
mat_wa_in = make_mat("Mat_WAIn", color=(0.10, 0.14, 0.18, 1.0), roughness=0.35)
mat_wa_out = make_mat("Mat_WAOut", color=(0.02, 0.30, 0.24, 1.0), roughness=0.3, emission=(0.02, 0.28, 0.22, 1.0), emission_strength=0.6)
mat_mug = make_mat("Mat_Mug", color=(0.88, 0.86, 0.82, 1.0), roughness=0.15)
mat_coffee = make_mat("Mat_Coffee", color=(0.03, 0.015, 0.008, 1.0), roughness=0.05)

mat_screen, bsdf_screen = make_switchable_glow_mat("Mat_PhoneScreen", base_col=(0.01, 0.01, 0.02, 1.0), glow_col=(1.0, 0.12, 0.15, 1.0))
mat_btn_web, bsdf_btn_web = make_switchable_glow_mat("Mat_BtnWeb", base_col=(0.14, 0.85, 0.42, 1.0), glow_col=(0.14, 0.85, 0.42, 1.0))

# ==============================================================================
# 1. STUDIO ENVIRONMENT & DECOYS
# ==============================================================================
# Desk
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.4))
desk = bpy.context.active_object
desk.name = "Desk"
desk.scale = (10.0, 6.0, 0.8)
desk.data.materials.append(mat_desk)

# Back Wall + Architectural Slats (depth & silhouette)
bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0, 2.4, 2.5), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.data.materials.append(mat_wall)

for i in range(-8, 9):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(i * 0.42, 2.32, 2.2))
    slat = bpy.context.active_object
    slat.scale = (0.12, 0.08, 5.0)
    slat.data.materials.append(mat_slat)

# Subtle Neon Accent Strip along back of desk
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 2.25, 0.03))
led_strip = bpy.context.active_object
led_strip.scale = (6.0, 0.03, 0.03)
led_strip.data.materials.append(mat_cyan_glow)

# Decoy 1: Background Sleek Laptop (Left)
laptop_root = bpy.data.objects.new("Laptop_Decoy", None)
scene.collection.objects.link(laptop_root)
laptop_root.location = (-1.45, 0.85, 0.0)
laptop_root.rotation_euler = (0, 0, math.radians(-22))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.02))
lap_base = bpy.context.active_object
lap_base.scale = (1.15, 0.78, 0.035)
lap_base.data.materials.append(mat_titanium)
add_bevel(lap_base, 0.01, 2)
lap_base.parent = laptop_root

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.38, 0.38), rotation=(math.radians(102), 0, 0))
lap_lid = bpy.context.active_object
lap_lid.scale = (1.15, 0.74, 0.025)
lap_lid.data.materials.append(mat_titanium)
add_bevel(lap_lid, 0.008, 2)
lap_lid.parent = laptop_root

bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0.365, 0.38), rotation=(math.radians(102), 0, 0))
lap_scr = bpy.context.active_object
lap_scr.scale = (1.06, 0.66, 1.0)
lap_scr.data.materials.append(make_mat("Mat_LapScr", color=(0.03, 0.08, 0.14, 1.0), emission=(0.08, 0.25, 0.45, 1.0), emission_strength=1.2))
lap_scr.parent = laptop_root

# Decoy 2: Digital Night Clock showing "02:30" (Left-Front)
clock_root = bpy.data.objects.new("Digital_Clock", None)
scene.collection.objects.link(clock_root)
clock_root.location = (-0.75, 0.35, 0.0)
clock_root.rotation_euler = (0, 0, math.radians(-14))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.14))
clk_body = bpy.context.active_object
clk_body.scale = (0.58, 0.22, 0.26)
clk_body.data.materials.append(mat_titanium)
add_bevel(clk_body, 0.02, 2)
clk_body.parent = clock_root

add_text_3d("Clock_Time", "02:30", (0, -0.115, 0.14), rot_deg=(90, 0, 0), size=0.14, extrude=0.005, bevel=0.001, mat=mat_red_glow, parent=clock_root)

# Decoy 3: Coffee Mug (Right-Back)
mug_root = bpy.data.objects.new("Coffee_Mug", None)
scene.collection.objects.link(mug_root)
mug_root.location = (1.25, 0.75, 0.0)

bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.28, location=(0, 0, 0.14))
mug = bpy.context.active_object
mug.data.materials.append(mat_mug)
add_bevel(mug, 0.015, 3)
mug.parent = mug_root

bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.02, location=(0, 0, 0.25))
coffee = bpy.context.active_object
coffee.data.materials.append(mat_coffee)
coffee.parent = mug_root

bpy.ops.mesh.primitive_torus_add(major_radius=0.075, minor_radius=0.018, location=(0.14, 0, 0.14), rotation=(math.radians(90), 0, 0))
handle = bpy.context.active_object
handle.data.materials.append(mat_mug)
handle.parent = mug_root

# ==============================================================================
# 2. HERO SMARTPHONE & NOTIFICATION BADGES
# ==============================================================================
phone_root = bpy.data.objects.new("Phone_Rig", None)
scene.collection.objects.link(phone_root)
phone_root.location = (-0.15, -0.15, 0.05)
phone_root.rotation_euler = (0, 0, math.radians(8))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
phone_body = bpy.context.active_object
phone_body.name = "Smartphone_Chassis"
phone_body.scale = (0.72, 1.48, 0.065)
phone_body.data.materials.append(mat_titanium)
add_bevel(phone_body, 0.03, 4)
phone_body.parent = phone_root

bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0.036))
phone_scr = bpy.context.active_object
phone_scr.name = "Smartphone_Screen"
phone_scr.scale = (0.65, 1.40, 1.0)
phone_scr.data.materials.append(mat_screen)
phone_scr.parent = phone_root

# Floating Red Notification Alert Badges (Shot 1 & 2) - Angled cleanly toward camera
alerts_root = bpy.data.objects.new("Alerts_Group", None)
scene.collection.objects.link(alerts_root)
alerts_root.parent = phone_root
alerts_root.rotation_euler = (math.radians(42), 0, 0)

alert_specs = [
    ("Alert_1", (-0.06, 0.42, 0.30), "12 MISSED CHATS"),
    ("Alert_2", (0.08, 0.16, 0.36), "IS THIS IN STOCK?"),
    ("Alert_3", (0.0, -0.10, 0.42), "LOST SALE -LKR 8,500"),
]
for idx, (aname, aloc, atext) in enumerate(alert_specs):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=aloc)
    badge = bpy.context.active_object
    badge.name = aname
    badge.scale = (0.78, 0.17, 0.038)
    badge.data.materials.append(mat_red_glow)
    add_bevel(badge, 0.014, 2)
    badge.parent = alerts_root
    add_text_3d(f"{aname}_Txt", atext, (aloc[0], aloc[1], aloc[2] + 0.024), rot_deg=(0, 0, 0), size=0.052, extrude=0.004, mat=mat_white_text, parent=alerts_root)

# ==============================================================================
# 3. 3D BIZBOT CYBERNETIC MASCOT
# ==============================================================================
bot_root = bpy.data.objects.new("BizBot_Mascot", None)
scene.collection.objects.link(bot_root)
bot_root.location = (0.78, 0.05, 0.72)

# Torso Pod
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, -0.22))
bot_torso = bpy.context.active_object
bot_torso.scale = (0.95, 0.85, 1.1)
bot_torso.data.materials.append(mat_titanium)
bpy.ops.object.shade_smooth()
bot_torso.parent = bot_root

# Head (Glossy White Ceramic)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.30, location=(0, 0, 0.18))
bot_head = bpy.context.active_object
bot_head.scale = (1.12, 0.95, 0.92)
bot_head.data.materials.append(mat_ceramic)
bpy.ops.object.shade_smooth()
bot_head.parent = bot_root

# Dark Glass Visor Plate
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=(0, -0.06, 0.18))
bot_visor = bpy.context.active_object
bot_visor.scale = (0.98, 0.88, 0.65)
bot_visor.data.materials.append(mat_dark_glass)
bpy.ops.object.shade_smooth()
bot_visor.parent = bot_root

# Glowing LED Eyes (2 Capsules)
for ex in (-0.10, 0.10):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ex, -0.295, 0.20))
    eye = bpy.context.active_object
    eye.scale = (0.065, 0.03, 0.095)
    eye.data.materials.append(mat_green_glow)
    add_bevel(eye, 0.012, 2)
    eye.parent = bot_root

# Side Chrome Ear Pods & Antenna
for sx in (-0.34, 0.34):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.06, location=(sx, 0, 0.18), rotation=(0, math.radians(90), 0))
    ear = bpy.context.active_object
    ear.data.materials.append(mat_chrome)
    ear.parent = bot_root

bpy.ops.mesh.primitive_cylinder_add(radius=0.014, depth=0.22, location=(0, 0, 0.52))
ant = bpy.context.active_object
ant.data.materials.append(mat_chrome)
ant.parent = bot_root

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.042, location=(0, 0, 0.65))
ant_tip = bpy.context.active_object
ant_tip.data.materials.append(mat_green_glow)
ant_tip.parent = bot_root

# Levitating Magnetic Hover Ring
bpy.ops.mesh.primitive_torus_add(major_radius=0.34, minor_radius=0.02, location=(0, 0, -0.45))
bot_ring = bpy.context.active_object
bot_ring.data.materials.append(mat_green_glow)
bot_ring.parent = bot_root

# ==============================================================================
# 4. HOLOGRAPHIC 3D WHATSAPP UI CARD (UPRIGHT FACING CAMERA)
# ==============================================================================
ui_root = bpy.data.objects.new("Hologram_UI", None)
scene.collection.objects.link(ui_root)
ui_root.location = (-0.12, -0.05, 0.85)
ui_root.rotation_euler = (math.radians(72), 0, math.radians(6))

# Card Chassis (in local XY plane, thickness Z)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
wa_card = bpy.context.active_object
wa_card.scale = (1.15, 1.48, 0.04)
wa_card.data.materials.append(mat_wa_card)
add_bevel(wa_card, 0.025, 3)
wa_card.parent = ui_root

# Header Bar
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.58, 0.025))
wa_head = bpy.context.active_object
wa_head.scale = (1.08, 0.22, 0.02)
wa_head.data.materials.append(mat_wa_header)
add_bevel(wa_head, 0.01, 2)
wa_head.parent = ui_root

add_text_3d("UI_Header", "BIZBOT • ONLINE 24/7", (0, 0.58, 0.042), size=0.062, extrude=0.004, mat=mat_green_glow, parent=ui_root)

# Customer Bubble
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.12, 0.28, 0.03))
b_in = bpy.context.active_object
b_in.scale = (0.78, 0.22, 0.025)
b_in.data.materials.append(mat_wa_in)
add_bevel(b_in, 0.015, 2)
b_in.parent = ui_root
add_text_3d("UI_CustTxt", "Hi, I need to place an order.", (-0.12, 0.28, 0.048), size=0.046, extrude=0.003, mat=mat_white_text, parent=ui_root)

# BizBot Instant Reply Bubble
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.08, 0.0, 0.03))
b_out = bpy.context.active_object
b_out.scale = (0.86, 0.24, 0.025)
b_out.data.materials.append(mat_wa_out)
add_bevel(b_out, 0.015, 2)
b_out.parent = ui_root
add_text_3d("UI_BotTxt", "Hello Dave! Tap below to order:", (0.08, 0.0, 0.048), size=0.045, extrude=0.003, mat=mat_white_text, parent=ui_root)

# Interactive Button 1: [VISIT WEBSITE]
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.28, 0.04))
btn_web = bpy.context.active_object
btn_web.name = "Btn_VisitWebsite"
btn_web.scale = (0.94, 0.16, 0.04)
btn_web.data.materials.append(mat_btn_web)
add_bevel(btn_web, 0.015, 2)
btn_web.parent = ui_root
txt_btn_web = add_text_3d("UI_BtnWebTxt", "VISIT WEBSITE", (0, -0.28, 0.068), size=0.056, extrude=0.004, mat=mat_dark_text, parent=ui_root)

# Interactive Button 2: [CALL US]
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.49, 0.04))
btn_call = bpy.context.active_object
btn_call.name = "Btn_CallUs"
btn_call.scale = (0.94, 0.16, 0.04)
btn_call.data.materials.append(mat_green_glow)
add_bevel(btn_call, 0.015, 2)
btn_call.parent = ui_root
add_text_3d("UI_BtnCallTxt", "CALL US NOW", (0, -0.49, 0.068), size=0.056, extrude=0.004, mat=mat_dark_text, parent=ui_root)

# ==============================================================================
# 5. VOLUMETRIC 3D FINALE HERO TEXT (SHOT 5)
# ==============================================================================
finale_root = bpy.data.objects.new("Finale_Group", None)
scene.collection.objects.link(finale_root)
finale_root.location = (0, -0.2, 1.05)
finale_root.rotation_euler = (math.radians(76), 0, 0)

add_text_3d("Finale_Brand", "CHATS THAT\nWORK ALONE", (0, 0.42, 0), size=0.11, extrude=0.015, bevel=0.003, mat=mat_white_text, parent=finale_root)
add_text_3d("Finale_Price", "LKR 200 / MO", (0, 0.04, 0.04), size=0.175, extrude=0.035, bevel=0.008, mat=mat_gold_glow, parent=finale_root)
add_text_3d("Finale_URL", "bizbot.zernox.net", (0, -0.26, 0.02), size=0.125, extrude=0.02, bevel=0.004, mat=mat_green_glow, parent=finale_root)

# ==============================================================================
# 6. STUDIO 3-POINT LIGHTING
# ==============================================================================
bpy.ops.object.light_add(type='AREA', location=(-2.4, -2.0, 2.8), rotation=(math.radians(45), math.radians(-28), math.radians(38)))
key_light = bpy.context.active_object
key_light.data.energy = 320.0
key_light.data.color = (0.25, 0.95, 0.55)
key_light.data.size = 2.2

bpy.ops.object.light_add(type='AREA', location=(2.6, -1.8, 2.4), rotation=(math.radians(48), math.radians(32), math.radians(-35)))
fill_light = bpy.context.active_object
fill_light.data.energy = 260.0
fill_light.data.color = (0.25, 0.50, 1.0)
fill_light.data.size = 2.8

bpy.ops.object.light_add(type='SPOT', location=(0.0, -0.4, 3.8), rotation=(math.radians(8), 0, 0))
top_light = bpy.context.active_object
top_light.data.energy = 420.0
top_light.data.spot_size = math.radians(65)
top_light.data.spot_blend = 0.5
top_light.data.color = (0.92, 0.96, 1.0)

# ==============================================================================
# 7. CAMERA & TIMELINE CHOREOGRAPHY
# ==============================================================================
bpy.ops.object.camera_add(location=(0, -3.0, 1.4))
cam = bpy.context.active_object
scene.camera = cam
cam.data.lens = 52.0
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 3.2

def aim_cam(frame, loc, target_pt, lens=52.0, dof_dist=None):
    cam.location = Vector(loc)
    direction = Vector(target_pt) - Vector(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.dof.focus_distance = dof_dist if dof_dist else direction.length
    cam.keyframe_insert(data_path="location", frame=frame)
    cam.keyframe_insert(data_path="rotation_euler", frame=frame)
    cam.data.keyframe_insert(data_path="lens", frame=frame)
    cam.data.dof.keyframe_insert(data_path="focus_distance", frame=frame)

print("[BizBot 3D Studio] Keyframing 5-shot choreography...", flush=True)

# Shot boundaries (exact from episode_timed.json)
f1_start, f1_end = 1, 232
f2_start, f2_end = 233, 442
f3_start, f3_end = 443, 652
f4_start, f4_end = 653, 995
f5_start, f5_end = 996, TOTAL_FRAMES

# --- Visibility State Machine ---
# Shot 1 & 2: Alerts visible, Bot/UI/Finale hidden
for fr in [1, f2_end]:
    key_vis(alerts_root, fr, True)
    key_vis(bot_root, fr, False)
    key_vis(ui_root, fr, False)
    key_vis(finale_root, fr, False)

# Shot 3 & 4: Alerts hidden, Bot & UI visible, Finale hidden
for fr in [f3_start, f4_end]:
    key_vis(alerts_root, fr, False)
    key_vis(bot_root, fr, True)
    key_vis(ui_root, fr, True)
    key_vis(finale_root, fr, False)

# Shot 5: Finale hero text visible + Bot beside it, UI/Alerts hidden
key_vis(alerts_root, f5_start, False)
key_vis(ui_root, f5_start, False)
key_vis(bot_root, f5_start, True)
key_vis(finale_root, f5_start, True)

# --- Keyframed Material Color Transitions ---
# Phone Screen: Red alert (Shot 1-2) -> WhatsApp Emerald Green (Shot 3-5)
bsdf_screen.inputs["Emission Color"].default_value = (1.0, 0.12, 0.15, 1.0)
bsdf_screen.inputs["Emission Color"].keyframe_insert(data_path="default_value", frame=1)
bsdf_screen.inputs["Emission Color"].keyframe_insert(data_path="default_value", frame=f2_end)
bsdf_screen.inputs["Emission Color"].default_value = (0.14, 0.85, 0.42, 1.0)
bsdf_screen.inputs["Emission Color"].keyframe_insert(data_path="default_value", frame=f3_start)

# Button Click Color Transition (Green -> Gold on click at frame 780)
f_click = 780
bsdf_btn_web.inputs["Base Color"].default_value = (0.14, 0.85, 0.42, 1.0)
bsdf_btn_web.inputs["Emission Color"].default_value = (0.14, 0.85, 0.42, 1.0)
bsdf_btn_web.inputs["Base Color"].keyframe_insert(data_path="default_value", frame=1)
bsdf_btn_web.inputs["Emission Color"].keyframe_insert(data_path="default_value", frame=1)
bsdf_btn_web.inputs["Base Color"].keyframe_insert(data_path="default_value", frame=f_click - 2)
bsdf_btn_web.inputs["Emission Color"].keyframe_insert(data_path="default_value", frame=f_click - 2)

bsdf_btn_web.inputs["Base Color"].default_value = (1.0, 0.78, 0.12, 1.0)
bsdf_btn_web.inputs["Emission Color"].default_value = (1.0, 0.78, 0.12, 1.0)
bsdf_btn_web.inputs["Base Color"].keyframe_insert(data_path="default_value", frame=f_click + 2)
bsdf_btn_web.inputs["Emission Color"].keyframe_insert(data_path="default_value", frame=f_click + 2)

# --- Continuous Animations ---
# Bot hover & ring spin
for f in range(f3_start, TOTAL_FRAMES + 1, 2):
    t = f / FPS
    bx = 0.78 if f < f5_start else 0.0
    by = 0.05 if f < f5_start else 0.35
    bz = (0.72 if f < f5_start else 1.85) + 0.045 * math.sin(t * 3.2)
    bot_root.location = (bx, by, bz)
    bot_root.rotation_euler = (0.04 * math.cos(t * 2.0), 0, 0.12 * math.sin(t * 1.5))
    bot_root.keyframe_insert(data_path="location", frame=f)
    bot_root.keyframe_insert(data_path="rotation_euler", frame=f)
    bot_ring.rotation_euler.z = t * 2.5
    bot_ring.keyframe_insert(data_path="rotation_euler", frame=f)

# Phone vibration during Shot 1 notifications
phone_root.location = (-0.15, -0.15, 0.05)
phone_root.keyframe_insert(data_path="location", frame=1)
for f in range(35, 110, 2):
    phone_root.location = (-0.15 + 0.018 * math.sin(f * 2.5), -0.15 + 0.018 * math.cos(f * 2.9), 0.05)
    phone_root.keyframe_insert(data_path="location", frame=f)
phone_root.location = (-0.15, -0.15, 0.05)
phone_root.keyframe_insert(data_path="location", frame=112)

# Alert badges gentle float in Shot 1 & 2
for f in range(1, f2_end + 1, 4):
    t = f / FPS
    alerts_root.location.z = 0.03 * math.sin(t * 3.0)
    alerts_root.keyframe_insert(data_path="location", frame=f)

# Interactive button press bounce at f_click = 780
btn_web.location.z = 0.04
btn_web.keyframe_insert(data_path="location", frame=f_click - 5)
btn_web.location.z = 0.012
btn_web.keyframe_insert(data_path="location", frame=f_click)
btn_web.location.z = 0.04
btn_web.keyframe_insert(data_path="location", frame=f_click + 6)

txt_btn_web.location.z = 0.068
txt_btn_web.keyframe_insert(data_path="location", frame=f_click - 5)
txt_btn_web.location.z = 0.040
txt_btn_web.keyframe_insert(data_path="location", frame=f_click)
txt_btn_web.location.z = 0.068
txt_btn_web.keyframe_insert(data_path="location", frame=f_click + 6)

# Finale text impact slam at f5_start
finale_root.scale = (1.45, 1.45, 1.45)
finale_root.keyframe_insert(data_path="scale", frame=f5_start)
finale_root.scale = (1.0, 1.0, 1.0)
finale_root.keyframe_insert(data_path="scale", frame=f5_start + 10)

# --- Camera Moves per Shot ---
# Shot 1: Sweeping night desk drift over clock & vibrating phone
aim_cam(f1_start, (-1.10, -3.25, 1.48), (-0.28, 0.05, 0.22), lens=42.0)
aim_cam(f1_end, (-0.15, -2.75, 1.38), (-0.20, 0.0, 0.25), lens=45.0)

# Shot 2: Dramatic close-up on red alerts & lost sale badge
aim_cam(f2_start, (0.45, -2.35, 1.22), (-0.15, -0.10, 0.35), lens=46.0)
aim_cam(f2_end, (0.20, -2.15, 1.12), (-0.15, -0.12, 0.38), lens=50.0)

# Shot 3: Hero orbital reveal of BizBot descending next to Hologram UI
aim_cam(f3_start, (1.75, -2.85, 1.40), (0.30, 0.0, 0.72), lens=46.0)
aim_cam(f3_end, (0.45, -2.75, 1.25), (0.20, 0.0, 0.75), lens=48.0)

# Shot 4: Crisp front-3/4 tracking on WhatsApp UI & Interactive Button Click
aim_cam(f4_start, (-0.15, -2.80, 1.28), (-0.10, -0.05, 0.80), lens=48.0)
aim_cam(f4_end, (0.0, -2.55, 1.18), (-0.10, -0.05, 0.74), lens=50.0)

# Shot 5: Wide epic hero pull-out with Finale 3D Typography + BizBot above
aim_cam(f5_start, (0.0, -3.55, 1.55), (0.0, -0.1, 1.15), lens=42.0)
aim_cam(TOTAL_FRAMES, (0.0, -3.10, 1.45), (0.0, -0.1, 1.15), lens=45.0)

# ==============================================================================
# 8. RENDER EXECUTION (STILL QA OR FULL ANIMATION)
# ==============================================================================
out_path = Path(args.out).resolve()
out_path.parent.mkdir(parents=True, exist_ok=True)

if args.still_frame > 0:
    scene.frame_set(args.still_frame)
    scene.render.filepath = str(out_path)
    scene.render.image_settings.file_format = 'PNG'
    print(f"[BizBot 3D Studio] Rendering QA still frame {args.still_frame} -> {out_path}", flush=True)
    bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = str(out_path)
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'
    scene.render.ffmpeg.ffmpeg_preset = 'REALTIME' if args.draft else 'GOOD'
    print(f"[BizBot 3D Studio] Rendering full 3D animation -> {out_path}", flush=True)
    bpy.ops.render.render(animation=True)

print("[BizBot 3D Studio] Render complete!", flush=True)
