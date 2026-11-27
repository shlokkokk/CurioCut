"""
CurioCut Peak 3D Renderer for BizBot (Blender 4.3 EEVEE Next).
Procedural 3D Smartphone, Floating Holographic WhatsApp Chat, Interactive Buttons,
Cybernetic BizBot Mascot, Volumetric Lighting, and Dynamic Camera Choreography.

Usage:
  & "C:\\Users\\shlok\\.faceless-shorts\\blender\\blender-4.3.2-windows-x64\\blender.exe" --background --python custom_orders/bizbot/render_bizbot.py -- --episode custom_orders/bizbot/work/episode_timed.json --out custom_orders/bizbot/work/raw_video.mp4
"""

import sys
import os
import math
import json
import argparse
from pathlib import Path

import bpy
from mathutils import Vector, Euler

# Parse CLI args after '--'
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
parser.add_argument("--max-frames", type=int, default=0, help="Optional frame limit for testing")
args = parser.parse_args(argv)

with open(args.episode, "r", encoding="utf-8") as f:
    ep_data = json.load(f)

FPS = args.fps
TOTAL_FRAMES = ep_data.get("total_frames", 1234)
if args.max_frames > 0:
    TOTAL_FRAMES = min(TOTAL_FRAMES, args.max_frames)

print(f"[BizBot 3D Renderer] Initializing Blender 4.3 scene: {TOTAL_FRAMES} frames @ {FPS} fps...", flush=True)

# 1. Factory Reset Scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Configure Render Settings (EEVEE Next / Cycles)
scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'RenderSettings') and 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES

# Resolution: Vertical 9:16 (1080x1920) or 540x960 draft
if args.draft:
    scene.render.resolution_x = 540
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
else:
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100

# Color Management
scene.view_settings.view_transform = 'AgX' if 'AgX' in [v.name for v in bpy.data.scenes[0].view_settings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
scene.view_settings.look = 'High Contrast'

# 2. Material Helpers
def make_mat(name, color=(0.8, 0.8, 0.8, 1.0), roughness=0.3, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission:
            bsdf.inputs["Emission Color"].default_value = emission
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

# Materials Palette
mat_desk = make_mat("Mat_Desk", color=(0.04, 0.03, 0.025, 1.0), roughness=0.25, metallic=0.1) # Dark luxury wood
mat_phone_body = make_mat("Mat_PhoneBody", color=(0.08, 0.08, 0.09, 1.0), roughness=0.15, metallic=0.9) # Dark Titanium
mat_phone_screen = make_mat("Mat_Screen", color=(0.01, 0.01, 0.015, 1.0), roughness=0.05, metallic=0.0)
mat_bot_body = make_mat("Mat_BotBody", color=(0.95, 0.95, 0.98, 1.0), roughness=0.12, metallic=0.7) # Glossy Ceramic
mat_bot_chrome = make_mat("Mat_BotChrome", color=(0.9, 0.92, 0.95, 1.0), roughness=0.04, metallic=1.0) # Mirror Chrome
mat_green_glow = make_mat("Mat_GreenGlow", color=(0.14, 0.83, 0.40, 1.0), roughness=0.1, emission=(0.15, 0.85, 0.40, 1.0), emission_strength=4.5) # WhatsApp Emerald
mat_wa_dark = make_mat("Mat_WADark", color=(0.07, 0.11, 0.13, 1.0), roughness=0.4, metallic=0.1) # WhatsApp Card Dark
mat_wa_bubble = make_mat("Mat_WABubble", color=(0.0, 0.36, 0.28, 1.0), roughness=0.3, metallic=0.0, emission=(0.0, 0.4, 0.3, 1.0), emission_strength=0.8)
mat_gold = make_mat("Mat_Gold", color=(1.0, 0.78, 0.15, 1.0), roughness=0.15, metallic=0.95, emission=(1.0, 0.8, 0.2, 1.0), emission_strength=2.0)
mat_red_alert = make_mat("Mat_RedAlert", color=(0.9, 0.15, 0.15, 1.0), roughness=0.2, emission=(1.0, 0.1, 0.1, 1.0), emission_strength=3.0)

# 3. Environment & Lighting
# Wooden Desk surface
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.6))
desk = bpy.context.active_object
desk.name = "Luxury_Desk"
desk.scale = (8.0, 8.0, 0.8)
desk.data.materials.append(mat_desk)

# Background Accent Wall
bpy.ops.mesh.primitive_plane_add(size=10.0, location=(0, 3.5, 2.0), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.name = "Back_Wall"
mat_wall = make_mat("Mat_Wall", color=(0.02, 0.02, 0.03, 1.0), roughness=0.7)
wall.data.materials.append(mat_wall)

# Studio Lights
# Key Emerald Rim Light
bpy.ops.object.light_add(type='AREA', location=(-2.5, -1.8, 3.5), rotation=(math.radians(35), math.radians(-30), math.radians(45)))
key_light = bpy.context.active_object
key_light.data.energy = 380.0
key_light.data.color = (0.2, 0.9, 0.5)
key_light.data.size = 2.5

# Fill Deep Indigo Light
bpy.ops.object.light_add(type='AREA', location=(2.8, -1.5, 2.8), rotation=(math.radians(40), math.radians(35), math.radians(-30)))
fill_light = bpy.context.active_object
fill_light.data.energy = 220.0
fill_light.data.color = (0.2, 0.4, 0.95)
fill_light.data.size = 3.0

# Top Rim / Overhead Hair Light
bpy.ops.object.light_add(type='SPOT', location=(0, 0.5, 4.0), rotation=(math.radians(10), 0, 0))
top_light = bpy.context.active_object
top_light.data.energy = 450.0
top_light.data.spot_size = math.radians(65)
top_light.data.spot_blend = 0.4
top_light.data.color = (0.85, 0.95, 1.0)

# 4. 3D Smartphone Model
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.05))
phone = bpy.context.active_object
phone.name = "Smartphone_Chassis"
phone.scale = (0.75, 1.5, 0.07) # Modern 9:18 aspect smartphone
phone.data.materials.append(mat_phone_body)

# Screen surface
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0.09))
screen = bpy.context.active_object
screen.name = "Smartphone_Screen"
screen.scale = (0.70, 1.44, 1.0)
screen.data.materials.append(mat_phone_screen)
screen.parent = phone

# Camera bump on back
bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.03, location=(0.22, 0.55, 0.02))
cam_lens = bpy.context.active_object
cam_lens.data.materials.append(mat_bot_chrome)
cam_lens.parent = phone

# 5. 3D BizBot Mascot Character
bot_root = bpy.data.objects.new("BizBot_Mascot", None)
scene.collection.objects.link(bot_root)
bot_root.location = (0.95, 0.2, 0.65)

# Head / Body Capsule
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.32, location=(0, 0, 0.2))
bot_head = bpy.context.active_object
bot_head.name = "Bot_Head"
bot_head.scale = (1.0, 0.92, 1.08)
bot_head.data.materials.append(mat_bot_body)
bot_head.parent = bot_root

# Visor (Curved Glowing Face Display)
bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=0.18, location=(0, -0.15, 0.22), rotation=(math.radians(90), 0, 0))
bot_visor = bpy.context.active_object
bot_visor.name = "Bot_Visor"
bot_visor.scale = (0.85, 0.65, 0.8)
bot_visor.data.materials.append(mat_green_glow)
bot_visor.parent = bot_root

# Chrome Antenna
bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=0.25, location=(0, 0, 0.58))
bot_ant = bpy.context.active_object
bot_ant.data.materials.append(mat_bot_chrome)
bot_ant.parent = bot_root

# Antenna Glowing Tip
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(0, 0, 0.72))
bot_tip = bpy.context.active_object
bot_tip.data.materials.append(mat_green_glow)
bot_tip.parent = bot_root

# Magnetic Levitating Hover Rings
bpy.ops.mesh.primitive_torus_add(major_radius=0.38, minor_radius=0.022, location=(0, 0, -0.12))
bot_ring = bpy.context.active_object
bot_ring.name = "Bot_HoverRing"
bot_ring.data.materials.append(mat_bot_chrome)
bot_ring.parent = bot_root

# 6. Floating Holographic WhatsApp UI Elements
ui_root = bpy.data.objects.new("Hologram_UI", None)
scene.collection.objects.link(ui_root)
ui_root.location = (0, 0, 0.55)

# WhatsApp Card Frame
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.1, 0.2))
wa_card = bpy.context.active_object
wa_card.name = "WA_Card"
wa_card.scale = (1.05, 1.35, 0.04)
wa_card.data.materials.append(mat_wa_dark)
wa_card.parent = ui_root

# Customer Chat Bubble (Incoming)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.15, 0.35, 0.24))
bubble_in = bpy.context.active_object
bubble_in.name = "Bubble_Customer"
bubble_in.scale = (0.65, 0.22, 0.03)
mat_bubble_in = make_mat("Mat_BubbleIn", color=(0.12, 0.18, 0.22, 1.0), roughness=0.3)
bubble_in.data.materials.append(mat_bubble_in)
bubble_in.parent = ui_root

# BizBot Chat Bubble (Outgoing)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.15, 0.05, 0.24))
bubble_out = bpy.context.active_object
bubble_out.name = "Bubble_BizBot"
bubble_out.scale = (0.65, 0.22, 0.03)
bubble_out.data.materials.append(mat_wa_bubble)
bubble_out.parent = ui_root

# Interactive Button 1: [VISIT WEBSITE]
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.22, 0.25))
btn_web = bpy.context.active_object
btn_web.name = "Btn_VisitWebsite"
btn_web.scale = (0.85, 0.14, 0.035)
btn_web.data.materials.append(mat_green_glow)
btn_web.parent = ui_root

# Interactive Button 2: [CALL US]
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.40, 0.25))
btn_call = bpy.context.active_object
btn_call.name = "Btn_CallUs"
btn_call.scale = (0.85, 0.14, 0.035)
btn_call.data.materials.append(mat_green_glow)
btn_call.parent = ui_root

# 7. Volumetric 3D Text / Price Elements
# 3D Price Text: "Rs. 200 / MO"
bpy.ops.object.text_add(location=(-0.95, -0.3, 0.85), rotation=(math.radians(75), 0, 0))
txt_price = bpy.context.active_object
txt_price.name = "Text_Price"
txt_price.data.body = "Rs. 200 / MO"
txt_price.data.size = 0.32
txt_price.data.extrude = 0.06
txt_price.data.bevel_depth = 0.015
txt_price.data.materials.append(mat_gold)

# 3D URL Text: "bizbot.zernox.net"
bpy.ops.object.text_add(location=(-1.15, -0.3, 0.38), rotation=(math.radians(75), 0, 0))
txt_url = bpy.context.active_object
txt_url.name = "Text_URL"
txt_url.data.body = "bizbot.zernox.net"
txt_url.data.size = 0.24
txt_url.data.extrude = 0.04
txt_url.data.bevel_depth = 0.01
txt_url.data.materials.append(mat_green_glow)

# 8. Animated Camera System
bpy.ops.object.camera_add(location=(0, -3.2, 1.8), rotation=(math.radians(65), 0, 0))
cam = bpy.context.active_object
scene.camera = cam
cam.data.lens = 58.0 # 58mm cinematic portrait focal length
cam.data.dof.use_dof = True
cam.data.dof.focus_object = phone
cam.data.dof.aperture_fstop = 2.8

# 9. Keyframe Choreography & Animation Engine
print("[BizBot 3D Renderer] Baking cinematic 5-shot keyframes & physics anims...", flush=True)

shots = ep_data.get("shots", [])

# Initial visibility & positions
txt_price.hide_render = True
txt_url.hide_render = True
ui_root.hide_render = True

# Continuous idle hover animation on BizBot
for f in range(1, TOTAL_FRAMES + 1):
    t_sec = f / FPS
    hover_z = 0.65 + 0.05 * math.sin(t_sec * 3.2)
    hover_rot_z = 0.08 * math.sin(t_sec * 1.8)
    hover_rot_x = 0.04 * math.cos(t_sec * 2.2)
    bot_root.location.z = hover_z
    bot_root.rotation_euler.z = hover_rot_z
    bot_root.rotation_euler.x = hover_rot_x
    bot_root.keyframe_insert(data_path="location", frame=f)
    bot_root.keyframe_insert(data_path="rotation_euler", frame=f)
    
    # Hover ring counter-spin
    bot_ring.rotation_euler.z = t_sec * 2.5
    bot_ring.keyframe_insert(data_path="rotation_euler", frame=f)

# Shot 1: [0.4s - 7.6s] (Frame 1 - 228) -> Midnight Frantic Notification Drift
f1_start, f1_end = int(0.4 * FPS), int(7.6 * FPS)
cam.location = (-0.8, -2.8, 1.6)
cam.rotation_euler = (math.radians(64), math.radians(-5), math.radians(-15))
cam.keyframe_insert(data_path="location", frame=1)
cam.keyframe_insert(data_path="rotation_euler", frame=1)

cam.location = (0.2, -2.2, 1.4)
cam.rotation_euler = (math.radians(62), math.radians(2), math.radians(5))
cam.keyframe_insert(data_path="location", frame=f1_end)
cam.keyframe_insert(data_path="rotation_euler", frame=f1_end)

# Phone vibration on notification
for f in range(int(1.2 * FPS), int(3.5 * FPS)):
    phone.location.x = 0.02 * math.sin(f * 2.2)
    phone.location.y = 0.02 * math.cos(f * 2.5)
    phone.keyframe_insert(data_path="location", frame=f)

# Shot 2: [7.9s - 14.5s] (Frame 239 - 437) -> Macro Dutch-Angle: "Lost Sale"
f2_start, f2_end = int(7.9 * FPS), int(14.5 * FPS)
cam.location = (0.45, -1.2, 0.85)
cam.rotation_euler = (math.radians(48), math.radians(-18), math.radians(22))
cam.data.lens = 72.0
cam.keyframe_insert(data_path="location", frame=f2_start)
cam.keyframe_insert(data_path="rotation_euler", frame=f2_start)
cam.data.keyframe_insert(data_path="lens", frame=f2_start)

cam.location = (0.25, -1.05, 0.75)
cam.rotation_euler = (math.radians(52), math.radians(-14), math.radians(16))
cam.keyframe_insert(data_path="location", frame=f2_end)
cam.keyframe_insert(data_path="rotation_euler", frame=f2_end)

# Red warning flash on phone screen in Shot 2
screen.data.materials[0] = mat_red_alert

# Shot 3: [14.9s - 21.5s] (Frame 448 - 647) -> Enter BizBot Hero Reveal
f3_start, f3_end = int(14.9 * FPS), int(21.5 * FPS)
screen.data.materials[0] = mat_green_glow # Screen turns WhatsApp green!
ui_root.hide_render = False

cam.location = (1.5, -2.6, 1.3)
cam.rotation_euler = (math.radians(65), math.radians(10), math.radians(35))
cam.data.lens = 50.0
cam.data.dof.focus_object = bot_head
cam.keyframe_insert(data_path="location", frame=f3_start)
cam.keyframe_insert(data_path="rotation_euler", frame=f3_start)
cam.data.keyframe_insert(data_path="lens", frame=f3_start)

cam.location = (0.8, -2.1, 1.25)
cam.rotation_euler = (math.radians(63), math.radians(4), math.radians(18))
cam.keyframe_insert(data_path="location", frame=f3_end)
cam.keyframe_insert(data_path="rotation_euler", frame=f3_end)

# Shot 4: [21.9s - 33.0s] (Frame 657 - 990) -> Interactive Buttons & Instant Reply
f4_start, f4_end = int(21.9 * FPS), int(33.0 * FPS)
cam.location = (0.0, -1.8, 1.45)
cam.rotation_euler = (math.radians(60), 0, 0)
cam.data.lens = 55.0
cam.data.dof.focus_object = wa_card
cam.keyframe_insert(data_path="location", frame=f4_start)
cam.keyframe_insert(data_path="rotation_euler", frame=f4_start)
cam.data.keyframe_insert(data_path="lens", frame=f4_start)

# Button click animation at ~26.0s (Frame 780)
f_click = int(26.0 * FPS)
btn_web.location.z = 0.25
btn_web.keyframe_insert(data_path="location", frame=f_click - 4)
btn_web.location.z = 0.21 # Button pressed down
btn_web.keyframe_insert(data_path="location", frame=f_click)
btn_web.location.z = 0.25 # Bounce back
btn_web.keyframe_insert(data_path="location", frame=f_click + 6)

# Button turns gold on confirmation
btn_web.data.materials[0] = mat_gold

cam.location = (0.1, -1.6, 1.35)
cam.keyframe_insert(data_path="location", frame=f4_end)

# Shot 5: [33.3s - 41.1s] (Frame 1000 - 1234) -> Price Slam & Grand Finale CTA
f5_start = int(33.3 * FPS)
txt_price.hide_render = False
txt_url.hide_render = False

cam.location = (0.0, -3.8, 1.9)
cam.rotation_euler = (math.radians(62), 0, 0)
cam.data.lens = 42.0 # Wide angle epic slam
cam.data.dof.focus_object = txt_price
cam.keyframe_insert(data_path="location", frame=f5_start)
cam.keyframe_insert(data_path="rotation_euler", frame=f5_start)
cam.data.keyframe_insert(data_path="lens", frame=f5_start)

# Slam text in with bounce
txt_price.scale = (1.5, 1.5, 1.5)
txt_price.keyframe_insert(data_path="scale", frame=f5_start)
txt_price.scale = (1.0, 1.0, 1.0)
txt_price.keyframe_insert(data_path="scale", frame=f5_start + 10)

cam.location = (0.0, -3.2, 1.7)
cam.keyframe_insert(data_path="location", frame=TOTAL_FRAMES)

# 10. Output & Render Configuration
out_path = Path(args.out).resolve()
out_path.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(out_path)
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'
scene.render.ffmpeg.ffmpeg_preset = 'REALTIME' if args.draft else 'GOOD'

print(f"[BizBot 3D Renderer] Starting hardware accelerated EEVEE Next 3D render -> {out_path}...", flush=True)
bpy.ops.render.render(animation=True)
print(f"[BizBot 3D Renderer] 3D Animation successfully rendered to {out_path}!", flush=True)
