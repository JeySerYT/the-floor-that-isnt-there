#!/usr/bin/env python3
"""Compose a mock corridor from batch 1 textures to judge the art in context."""

from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "assets" / "textures"
OUT = ROOT / "docs" / "previews" / "batch1_mock.png"
W, H, TILE = 640, 360, 32


def load(rel: str) -> Image.Image:
    return Image.open(TEX / rel).convert("RGBA")


def paste(scene: Image.Image, image: Image.Image, x: int, y: int) -> None:
    scene.alpha_composite(image, (x, y))


def build() -> Image.Image:
    rng = random.Random(1313)
    scene = Image.new("RGBA", (W, H), (10, 13, 14, 255))
    draw = ImageDraw.Draw(scene)

    floors = {name: load(f"floors/{name}.png") for name in (
        "floor_corridor_a", "floor_corridor_b", "floor_corridor_c",
        "floor_corridor_stain", "floor_corridor_wet", "floor_ward",
        "floor_lobby", "floor_morgue", "floor_grate",
    )}
    walls = {name: load(f"walls/{name}.png") for name in (
        "wall_cap", "wall_face_a", "wall_face_b", "wall_face_c",
        "wall_tile", "wall_pipe",
    )}
    doors = {name: load(f"doors/{name}.png") for name in (
        "door_ward", "door_morgue", "door_double", "door_elevator",
    )}
    decals = {name: load(f"decals/{name}.png") for name in (
        "decal_blood_pool", "decal_blood_smear", "decal_stain",
        "decal_crack", "decal_brick_patch", "decal_mold", "decal_wall_crack",
    )}

    # floor
    for y in range(64, 296, TILE):
        for x in range(0, W, TILE):
            roll = rng.random()
            if roll < 0.06:
                tile = floors["floor_corridor_stain"]
            elif roll < 0.1:
                tile = floors["floor_corridor_wet"]
            elif roll < 0.28:
                tile = floors["floor_corridor_b"]
            elif roll < 0.4:
                tile = floors["floor_corridor_c"]
            else:
                tile = floors["floor_corridor_a"]
            paste(scene, tile, x, y)

    # lobby patch on the left
    for y in range(64, 160, TILE):
        for x in range(0, 160, TILE):
            paste(scene, floors["floor_lobby"], x, y)
    # ward patch on the right
    for y in range(64, 160, TILE):
        for x in range(480, 640, TILE):
            paste(scene, floors["floor_ward"], x, y)
    # morgue strip at the bottom right
    for y in range(224, 296, TILE):
        for x in range(448, 640, TILE):
            paste(scene, floors["floor_morgue"], x, y)
    paste(scene, floors["floor_grate"], 480, 256)

    # top wall: cap row + face row
    for x in range(0, W, TILE):
        paste(scene, walls["wall_cap"], x, 0)
        face = walls["wall_face_b"] if 256 <= x < 416 else walls["wall_face_a"]
        if 384 <= x < 448:
            face = walls["wall_tile"]
        if 576 <= x < 640:
            face = walls["wall_pipe"]
        paste(scene, face, x, 32)
    # bottom wall: face row + cap row
    for x in range(0, W, TILE):
        face = walls["wall_face_c"] if 0 <= x < 160 else walls["wall_face_a"]
        paste(scene, face, x, 296)
        paste(scene, walls["wall_cap"], x, 328)

    # doors cut into the wall rows
    paste(scene, doors["door_ward"], 192, 32)
    paste(scene, doors["door_morgue"], 256, 296)
    paste(scene, doors["door_double"], 448, 32)

    # wall decals
    paste(scene, decals["decal_wall_crack"], 112, 34)
    paste(scene, decals["decal_brick_patch"], 300, 32)
    paste(scene, decals["decal_mold"], 528, 34)
    paste(scene, decals["decal_crack"], 80, 298)

    # floor decals
    paste(scene, decals["decal_blood_smear"], 244, 250)
    paste(scene, decals["decal_blood_pool"], 286, 200)
    paste(scene, decals["decal_stain"], 96, 190)
    paste(scene, decals["decal_stain"], 520, 230)

    # simple silhouette + flashlight cone for scale
    cone = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cone_draw = ImageDraw.Draw(cone)
    cone_draw.polygon([(300, 210), (520, 120), (540, 300)], fill=(240, 204, 142, 26))
    scene.alpha_composite(cone)
    figure = Image.new("RGBA", (16, 26), (0, 0, 0, 0))
    fd = ImageDraw.Draw(figure)
    fd.rectangle((5, 8, 10, 20), fill=(24, 29, 30, 255))
    fd.rectangle((4, 0, 11, 8), fill=(18, 22, 23, 255))
    fd.rectangle((3, 14, 4, 22), fill=(18, 22, 23, 255))
    fd.rectangle((11, 14, 12, 22), fill=(18, 22, 23, 255))
    scene.alpha_composite(figure, (286, 196))

    # lighting: ambient darkness + warm flashlight pool
    rgb = np.array(scene.convert("RGB"), dtype=np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt((xx - 300) ** 2 + (yy - 210) ** 2)
    light = np.clip(1.0 - dist / 310.0, 0.0, 1.0) ** 1.5
    light = 0.38 + 0.62 * light
    rgb *= light[:, :, None]
    warm = np.array([1.0, 0.88, 0.7], dtype=np.float32)
    rgb = rgb * (1.0 - light[:, :, None] * 0.3) + rgb * warm * light[:, :, None] * 0.3
    # vignette
    vx = np.abs(xx - W / 2) / (W / 2)
    vy = np.abs(yy - H / 2) / (H / 2)
    vignette = np.clip(1.0 - (vx ** 2.4 + vy ** 2.4) * 0.42, 0.25, 1.0)
    rgb *= vignette[:, :, None]
    # cool shadow tint
    rgb[:, :, 2] *= 1.04
    rgb[:, :, 0] *= 0.98

    result = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB")
    return result.resize((W * 2, H * 2), Image.NEAREST)


if __name__ == "__main__":
    image = build()
    image.save(OUT)
    print(f"mock -> {OUT} ({image.size[0]}x{image.size[1]})")