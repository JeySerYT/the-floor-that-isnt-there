#!/usr/bin/env python3
"""Compose a morgue/ward mock scene from batch 1 + batch 2 assets.

Purpose: judge scale, silhouette and readability of the props in a real
gameplay frame (640x360 internal, exported at 2x).
"""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "assets" / "textures"
OUT = ROOT / "assets" / "previews" / "batch2_mock.png"
W, H, TILE = 640, 360, 32


def load(rel: str) -> Image.Image:
    return Image.open(TEX / rel).convert("RGBA")


def paste(scene: Image.Image, image: Image.Image, x: int, y: int) -> None:
    scene.alpha_composite(image, (x, y))


def build_scene() -> Image.Image:
    rng = random.Random(4242)
    scene = Image.new("RGBA", (W, H), (10, 13, 14, 255))

    floors = {name: load(f"floors/{name}.png") for name in (
        "floor_corridor_a", "floor_corridor_b", "floor_corridor_c",
        "floor_corridor_stain", "floor_corridor_wet", "floor_ward",
        "floor_morgue", "floor_grate",
    )}
    walls = {name: load(f"walls/{name}.png") for name in (
        "wall_cap", "wall_face_a", "wall_face_b", "wall_tile", "wall_pipe",
    )}
    decals = {name: load(f"decals/{name}.png") for name in (
        "decal_blood_pool", "decal_blood_smear", "decal_stain",
        "decal_crack", "decal_mold", "decal_wall_crack", "decal_brick_patch",
    )}

    # floor: corridor tiles, a ward strip in the middle, concrete in the morgue
    for y in range(64, 296, TILE):
        for x in range(0, W, TILE):
            roll = rng.random()
            if 288 <= y < 256 + TILE and 384 <= x < 544:
                tile = floors["floor_morgue"]
            elif 64 <= y < 160 and 64 <= x < 288:
                tile = floors["floor_ward"]
            elif roll < 0.05:
                tile = floors["floor_corridor_stain"]
            elif roll < 0.09:
                tile = floors["floor_corridor_wet"]
            elif roll < 0.26:
                tile = floors["floor_corridor_b"]
            elif roll < 0.38:
                tile = floors["floor_corridor_c"]
            else:
                tile = floors["floor_corridor_a"]
            paste(scene, tile, x, y)
    paste(scene, floors["floor_grate"], 480, 256)

    # walls: cap + face on the top, face + cap on the bottom
    for x in range(0, W, TILE):
        paste(scene, walls["wall_cap"], x, 0)
        face = walls["wall_face_b"] if 288 <= x < 512 else walls["wall_face_a"]
        if 128 <= x < 192:
            face = walls["wall_tile"]
        if 544 <= x < 608:
            face = walls["wall_pipe"]
        paste(scene, face, x, 32)
        paste(scene, walls["wall_face_a"], x, 296)
        paste(scene, walls["wall_cap"], x, 328)

    # wall-mounted props sit directly on the wall face row
    paste(scene, load("barriers/prop_boarded_door.png"), 224, 32)
    paste(scene, load("barriers/prop_observation_window.png"), 96, 296)
    paste(scene, load("devices/prop_fusebox.png"), 544, 32)
    paste(scene, load("devices/prop_elevator_panel.png"), 600, 40)

    # wall decals
    paste(scene, decals["decal_wall_crack"], 32, 34)
    paste(scene, decals["decal_mold"], 480, 36)
    paste(scene, decals["decal_brick_patch"], 352, 32)
    paste(scene, decals["decal_crack"], 520, 298)

    # furniture
    paste(scene, load("furniture/prop_reception_desk.png"), 24, 72)
    paste(scene, load("furniture/prop_filing_cabinet.png"), 136, 68)
    paste(scene, load("furniture/prop_waiting_bench.png"), 32, 152)
    paste(scene, load("furniture/prop_waiting_bench.png"), 32, 192)
    paste(scene, load("furniture/prop_chair.png"), 128, 152)
    paste(scene, load("furniture/prop_metal_cabinet.png"), 288, 64)
    paste(scene, load("furniture/prop_sink.png"), 328, 68)
    paste(scene, load("furniture/prop_hospital_bed.png"), 384, 88)
    paste(scene, load("devices/prop_iv_stand.png"), 488, 92)
    paste(scene, load("devices/prop_wheelchair.png"), 400, 176)
    paste(scene, load("devices/prop_generator.png"), 336, 224)
    paste(scene, load("furniture/prop_morgue_table.png"), 432, 232)
    paste(scene, load("furniture/prop_body_bag.png"), 448, 236)

    # items on the floor / desk
    paste(scene, load("items/item_cassette.png"), 276, 216)
    paste(scene, load("items/item_key.png"), 300, 228)
    paste(scene, load("items/item_fuse.png"), 320, 212)
    paste(scene, load("items/item_note.png"), 68, 108)

    # floor decals (kept clear of props so nothing reads as damage to them)
    paste(scene, decals["decal_blood_smear"], 208, 246)
    paste(scene, decals["decal_blood_pool"], 364, 258)
    paste(scene, decals["decal_stain"], 192, 224)
    paste(scene, decals["decal_stain"], 552, 200)

    return scene


def add_flashlight_cone(scene: Image.Image, origin: tuple[int, int]) -> None:
    cone = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cone_draw = ImageDraw.Draw(cone)
    ox, oy = origin
    cone_draw.polygon([(ox, oy), (ox + 170, oy - 64), (ox + 200, oy + 86)],
                      fill=(240, 204, 142, 24))
    scene.alpha_composite(cone)


def add_silhouette(scene: Image.Image) -> None:
    figure = Image.new("RGBA", (16, 26), (0, 0, 0, 0))
    fd = ImageDraw.Draw(figure)
    fd.rectangle((5, 8, 10, 20), fill=(24, 29, 30, 255))
    fd.rectangle((4, 0, 11, 8), fill=(18, 22, 23, 255))
    fd.rectangle((3, 14, 4, 22), fill=(18, 22, 23, 255))
    fd.rectangle((11, 14, 12, 22), fill=(18, 22, 23, 255))
    scene.alpha_composite(figure, (286, 198))


def apply_lighting(scene: Image.Image, focus: tuple[int, int],
                   warmth: float = 0.32, export_scale: int = 2) -> Image.Image:
    # lighting: cold ambient, a weak ceiling light and a warm flashlight pool
    rgb = np.array(scene.convert("RGB"), dtype=np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W]
    fx, fy = focus
    dist = np.sqrt((xx - fx) ** 2 + (yy - fy) ** 2)
    flash = np.clip(1.0 - dist / 300.0, 0.0, 1.0) ** 1.5
    ceil_dist = np.sqrt((xx - 320) ** 2 + (yy - 40) ** 2)
    ceiling = np.clip(1.0 - ceil_dist / 340.0, 0.0, 1.0) ** 1.2
    light = np.clip(0.3 + 0.58 * flash + 0.3 * ceiling, 0.0, 1.05)
    rgb *= light[:, :, None]
    warm = np.array([1.0, 0.88, 0.7], dtype=np.float32)
    warm_weight = (flash * warmth)[:, :, None]
    rgb = rgb * (1.0 - warm_weight) + rgb * warm * warm_weight
    vx = np.abs(xx - W / 2) / (W / 2)
    vy = np.abs(yy - H / 2) / (H / 2)
    vignette = np.clip(1.0 - (vx ** 2.4 + vy ** 2.4) * 0.45, 0.24, 1.0)
    rgb *= vignette[:, :, None]
    rgb[:, :, 2] *= 1.04
    rgb[:, :, 0] *= 0.98

    result = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB")
    if export_scale == 1:
        return result
    return result.resize((W * export_scale, H * export_scale), Image.NEAREST)


def build() -> Image.Image:
    scene = build_scene()
    add_flashlight_cone(scene, (300, 214))
    add_silhouette(scene)
    return apply_lighting(scene, (300, 214))


if __name__ == "__main__":
    image = build()
    image.save(OUT)
    print(f"mock -> {OUT} ({image.size[0]}x{image.size[1]})")