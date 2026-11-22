#!/usr/bin/env python3
"""Generate batch 3: character sprite sheets (Mark and the nurse).

Frame layout for every sheet: 4 rows (down, left, right, up) x 5 columns
(idle, walk_1..walk_4). Frames are drawn at native game resolution and
quantized with the same palette language as batches 1-2.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_textures as g

ROOT = g.ROOT
TEX = g.TEX
MANIFEST: list[dict] = []

DIRECTIONS = ["down", "left", "right", "up"]
COLUMNS = ["idle", "walk_1", "walk_2", "walk_3", "walk_4"]

OUTLINE = (16, 19, 20)

PLAYER = {
    "hair": (38, 33, 28),
    "hair_hi": (62, 53, 44),
    "skin": (198, 168, 136),
    "skin_l": (220, 192, 158),
    "skin_d": (160, 130, 102),
    "coat": (66, 80, 77),
    "coat_l": (92, 108, 102),
    "coat_d": (43, 55, 54),
    "shirt": (128, 134, 124),
    "pants": (56, 61, 68),
    "pants_l": (78, 84, 92),
    "shoe": (26, 28, 30),
    "steel": (132, 140, 136),
    "steel_d": (78, 86, 84),
    "lens": (226, 188, 116),
    "badge": (150, 50, 40),
    "paper": (190, 186, 170),
    "lip": (150, 112, 100),
    "eye": (24, 25, 27),
}

NURSE = {
    "hair": (40, 33, 28),
    "hair_hi": (66, 55, 46),
    "skin": (196, 170, 146),
    "skin_l": (218, 194, 170),
    "skin_d": (160, 134, 112),
    "dress": (172, 186, 190),
    "dress_l": (204, 214, 216),
    "dress_d": (132, 146, 152),
    "shoe": (52, 54, 52),
    "blood": (104, 20, 20),
    "blood_d": (60, 10, 11),
    "cap": (212, 220, 222),
    "cap_l": (236, 240, 240),
    "lip": (152, 114, 106),
    "eye": (26, 26, 28),
    "eye_red": (204, 50, 38),
}


def frame(w: int, h: int) -> np.ndarray:
    return np.zeros((h, w, 4), dtype=np.float32)


def rect(arr: np.ndarray, x: int, y: int, w: int, h: int,
         color: tuple[int, int, int], alpha: int = 255) -> None:
    g.draw_rect(arr, x, y, w, h, color, alpha)


def hline(arr: np.ndarray, x: int, y: int, w: int,
          color: tuple[int, int, int], alpha: int = 255) -> None:
    rect(arr, x, y, w, 1, color, alpha)


def vline(arr: np.ndarray, x: int, y: int, h: int,
          color: tuple[int, int, int], alpha: int = 255) -> None:
    rect(arr, x, y, 1, h, color, alpha)


def add_outline(char: np.ndarray) -> None:
    alpha = char[:, :, 3] > 0
    grown = alpha.copy()
    grown[1:, :] |= alpha[:-1, :]
    grown[:-1, :] |= alpha[1:, :]
    grown[:, 1:] |= alpha[:, :-1]
    grown[:, :-1] |= alpha[:, 1:]
    edge = grown & ~alpha
    char[edge, :3] = OUTLINE
    char[edge, 3] = 255


def add_shadow(arr: np.ndarray, cx: float, cy: float, rx: float, ry: float,
               alpha: int = 90, softness: float = 0.55) -> None:
    """Soft elliptical contact shadow; hard-edged ellipses read as a plinth."""
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    radius = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    falloff = np.clip((1.0 - radius) / softness, 0.0, 1.0) ** 1.5
    mask = falloff > 0.03
    arr[mask, :3] = (0, 0, 0)
    arr[mask, 3] = falloff[mask] * alpha


def compose(char: np.ndarray, shadow: tuple[float, float, float, float]) -> np.ndarray:
    w, h = char.shape[1], char.shape[0]
    out = frame(w, h)
    add_shadow(out, *shadow)
    add_outline(char)
    mask = char[:, :, 3] > 0
    out[mask] = char[mask]
    return out


# --- player -----------------------------------------------------------------

def player_legs(char: np.ndarray, direction: str, pose: int, bob: int) -> None:
    p = PLAYER
    swing = (0, 2, 0, -2, 0)[pose]
    if direction in ("down", "up"):
        for lx, fwd in ((5, swing), (12, -swing)):
            top = 20 - bob
            bottom = 25 + fwd
            rect(char, lx, top, 4, bottom - top + 1, p["pants"])
            vline(char, lx, top, bottom - top + 1, p["pants_l"])
            hline(char, lx, top + 2, 4, p["pants_l"], 120)
            rect(char, lx - 1, bottom + 1, 5, 3, p["shoe"])
            hline(char, lx - 1, bottom + 1, 5, (68, 72, 74))
    else:
        for lx, shift in ((5, -swing), (10, swing)):
            top = 20 - bob
            rect(char, lx + shift, top, 4, 8, p["pants"])
            vline(char, lx + shift, top, 8, p["pants_l"])
            rect(char, lx - 1 + shift, 28, 6, 3, p["shoe"])
            hline(char, lx - 1 + shift, 28, 6, (68, 72, 74))


def player_torso(char: np.ndarray, direction: str, pose: int, bob: int) -> None:
    p = PLAYER
    top = 12 - bob
    if direction in ("down", "up"):
        rect(char, 4, top, 12, 11, p["coat"])
        vline(char, 3, top + 1, 9, p["coat_l"])
        vline(char, 16, top + 1, 9, p["coat_d"])
        hline(char, 4, top, 12, p["coat_l"])
        rect(char, 5, top, 3, 2, p["coat_l"])
        rect(char, 12, top, 3, 2, p["coat_l"])
        rect(char, 8, top, 4, 2, p["shirt"])
        # zip: a broken line, not a solid stripe
        for y in range(top + 3, top + 10, 2):
            rect(char, 9, y, 1, 1, p["coat_d"])
        hline(char, 4, top + 10, 12, p["coat_d"])
        # pockets
        hline(char, 5, top + 7, 3, p["coat_d"])
        hline(char, 12, top + 7, 3, p["coat_d"])
        if direction == "down":
            # visitor badge: white card with a red dot
            rect(char, 12, top + 3, 2, 2, p["paper"])
            rect(char, 12, top + 3, 1, 1, p["badge"])
        else:
            vline(char, 9, top + 1, 8, p["coat_d"])
            hline(char, 5, top + 6, 10, p["coat_d"])
    else:
        rect(char, 5, top, 10, 11, p["coat"])
        vline(char, 5, top + 1, 9, p["coat_l"])
        vline(char, 14, top + 1, 9, p["coat_d"])
        hline(char, 5, top, 10, p["coat_l"])
        rect(char, 8, top, 3, 2, p["coat_l"])
        vline(char, 9, top + 2, 8, p["coat_d"])
        hline(char, 5, top + 10, 10, p["coat_d"])
        hline(char, 6, top + 7, 8, p["coat_d"])
        rect(char, 8, top + 3, 2, 2, p["paper"])
        rect(char, 8, top + 3, 1, 1, p["badge"])


def player_arms(char: np.ndarray, direction: str, pose: int, bob: int) -> None:
    p = PLAYER
    top = 12 - bob
    swing = (0, 1, 0, -1, 0)[pose]
    if direction in ("down", "up"):
        # left arm (viewer left) swings, right arm holds the flashlight steady
        left_hand = top + 9 + swing
        rect(char, 2, top + 2, 2, 7, p["coat"])
        vline(char, 2, top + 2, 7, p["coat_l"])
        rect(char, 2, left_hand, 2, 2, p["skin"])
        rect(char, 2, left_hand, 2, 1, p["skin_l"])
        rect(char, 16, top + 2, 2, 6, p["coat"])
        vline(char, 16, top + 2, 6, p["coat_d"])
    else:
        hand_x = 6 + swing
        rect(char, 7, top + 2, 3, 8, p["coat"])
        vline(char, 7, top + 2, 8, p["coat_l"])
        rect(char, hand_x, top + 9, 3, 2, p["skin"])
        rect(char, hand_x, top + 9, 3, 1, p["skin_l"])


def player_flashlight(char: np.ndarray, direction: str, pose: int, bob: int) -> None:
    p = PLAYER
    top = 12 - bob
    if direction in ("down", "up"):
        # short barrel seen from above, lens pointing away from the body
        rect(char, 15, top + 9, 3, 3, p["steel_d"])
        vline(char, 16, top + 9, 3, p["steel"])
        hline(char, 15, top + 11, 3, p["steel"])
        rect(char, 16, top + 12, 1, 1, p["lens"])
        # hand wrapped around the grip
        rect(char, 16, top + 8, 2, 2, p["skin"])
        hline(char, 16, top + 8, 2, p["skin_l"])
    else:
        rect(char, 2, top + 9, 5, 2, p["steel_d"])
        rect(char, 1, top + 9, 1, 2, p["lens"])
        hline(char, 2, top + 9, 4, p["steel"])
        rect(char, 5, top + 9, 2, 2, p["skin"])
        hline(char, 5, top + 9, 2, p["skin_l"])


def player_head(char: np.ndarray, direction: str, pose: int, bob: int) -> None:
    p = PLAYER
    top = 4 - bob
    # neck and ears
    rect(char, 9, top + 8, 3, 3, p["skin_d"])
    rect(char, 3, top + 5, 1, 2, p["skin_d"])
    rect(char, 16, top + 5, 1, 2, p["skin_d"])
    # face: wide temples, narrower jaw
    rect(char, 5, top + 2, 10, 3, p["skin"])
    rect(char, 6, top + 5, 8, 5, p["skin"])
    rect(char, 7, top + 10, 6, 1, p["skin"])
    hline(char, 5, top + 2, 10, p["skin_l"])
    vline(char, 5, top + 3, 5, p["skin_l"])
    vline(char, 14, top + 3, 5, p["skin_d"])
    hline(char, 7, top + 10, 6, p["skin_d"])
    # hair
    rect(char, 4, top, 12, 3, p["hair"])
    hline(char, 4, top, 12, p["hair_hi"])
    rect(char, 4, top + 2, 2, 7, p["hair"])
    rect(char, 14, top + 2, 2, 7, p["hair"])
    rect(char, 5, top + 2, 10, 1, p["hair"])
    rect(char, 5, top + 3, 1, 2, p["hair"])
    rect(char, 14, top + 3, 1, 2, p["hair"])
    rect(char, 6, top + 3, 2, 1, p["hair"])
    if direction == "down":
        rect(char, 8, top + 4, 1, 1, p["hair"])
        rect(char, 12, top + 4, 1, 1, p["hair"])
        rect(char, 8, top + 5, 1, 1, p["eye"])
        rect(char, 12, top + 5, 1, 1, p["eye"])
        rect(char, 9, top + 6, 2, 1, p["skin_d"])
        rect(char, 10, top + 7, 1, 1, p["skin_d"])
        hline(char, 9, top + 8, 2, p["lip"])
    elif direction == "up":
        rect(char, 5, top + 2, 10, 8, p["hair"])
        rect(char, 6, top + 2, 1, 5, p["hair_hi"])
        rect(char, 11, top + 1, 2, 1, p["hair_hi"])
        rect(char, 6, top + 9, 8, 1, p["hair"])
        rect(char, 8, top + 10, 4, 2, p["skin_d"])
    else:
        # profile, facing left; right row is mirrored
        rect(char, 10, top + 2, 5, 9, p["hair"])
        rect(char, 11, top + 2, 1, 8, p["hair_hi"])
        rect(char, 5, top + 2, 7, 1, p["hair"])
        rect(char, 5, top + 3, 1, 2, p["hair"])
        rect(char, 5, top + 3, 6, 1, p["skin_l"])
        rect(char, 5, top + 4, 5, 7, p["skin"])
        vline(char, 5, top + 4, 6, p["skin_l"])
        rect(char, 4, top + 6, 1, 2, p["skin_d"])
        rect(char, 6, top + 4, 1, 1, p["hair"])
        rect(char, 7, top + 5, 1, 1, p["eye"])
        rect(char, 6, top + 7, 1, 1, p["skin_d"])
        hline(char, 5, top + 8, 3, p["skin_d"])
        rect(char, 9, top + 6, 1, 2, p["skin_d"])
        rect(char, 9, top + 10, 3, 2, p["skin_d"])


def player_frame(direction: str, pose: int) -> np.ndarray:
    char = frame(20, 32)
    bob = 1 if pose in (2, 4) else 0
    player_legs(char, direction, pose, bob)
    player_torso(char, direction, pose, bob)
    player_arms(char, direction, pose, bob)
    player_flashlight(char, direction, pose, bob)
    player_head(char, direction, pose, bob)
    if direction == "right":
        char = np.fliplr(char)
    return compose(char, (10.0, 29.2, 8.0, 1.8))


# --- nurse ------------------------------------------------------------------

def nurse_legs(char: np.ndarray, direction: str, pose: int, bob: int) -> None:
    n = NURSE
    swing = (0, 2, 0, -2, 0)[pose]
    top = 30 - bob
    if direction in ("down", "up"):
        for lx, fwd in ((7, swing), (13, -swing)):
            bottom = top + 2 + fwd // 2
            rect(char, lx, top, 4, bottom - top + 1, n["skin"])
            vline(char, lx, top, bottom - top + 1, n["skin_l"])
            vline(char, lx + 3, top, bottom - top + 1, n["skin_d"])
            # separate shoes so the feet never merge into one dark slab
            rect(char, lx - 1, bottom + 1, 5, 2, n["shoe"])
            hline(char, lx - 1, bottom + 1, 5, (74, 76, 74))
    else:
        for lx, shift in ((6, -swing), (11, swing)):
            rect(char, lx + shift, top, 4, 3, n["skin"])
            vline(char, lx + shift, top, 3, n["skin_l"])
            rect(char, lx - 1 + shift, top + 3, 6, 2, n["shoe"])
            hline(char, lx - 1 + shift, top + 3, 6, (74, 76, 74))


def nurse_dress(char: np.ndarray, direction: str, pose: int, bob: int,
                chase: bool) -> None:
    n = NURSE
    top = 17 - bob
    if direction in ("down", "up"):
        # bodice
        rect(char, 6, top, 12, 9, n["dress"])
        vline(char, 6, top + 1, 8, n["dress_l"])
        vline(char, 17, top + 1, 8, n["dress_d"])
        hline(char, 6, top, 12, n["dress_l"])
        rect(char, 8, top, 2, 1, n["dress_l"])
        rect(char, 14, top, 2, 1, n["dress_l"])
        # waist and flared skirt
        rect(char, 5, top + 8, 14, 2, n["dress"])
        rect(char, 4, top + 10, 16, 4, n["dress"])
        vline(char, 4, top + 10, 4, n["dress_l"])
        vline(char, 19, top + 10, 4, n["dress_d"])
        hline(char, 4, top + 13, 16, n["dress_d"])
        if direction == "down":
            # narrow apron panel: keep it from turning the dress into a white box
            rect(char, 9, top + 2, 6, 7, n["dress_l"])
            hline(char, 8, top + 9, 8, n["dress_d"], 190)
            rect(char, 11, top + 9, 2, 2, n["dress_d"])
            vline(char, 8, top + 11, 3, n["dress_d"], 150)
            vline(char, 15, top + 11, 3, n["dress_d"], 150)
        else:
            # back of the dress: centre seam and waist tie, no apron
            hline(char, 7, top + 1, 10, n["dress_l"], 150)
            vline(char, 12, top + 3, 6, n["dress_d"], 130)
            hline(char, 8, top + 9, 8, n["dress_d"], 190)
        if direction == "down":
            # blood runs down the left side of the skirt, never the centre
            rect(char, 6, top + 8, 2, 2, n["blood"])
            rect(char, 5, top + 10, 1, 3, n["blood"])
            rect(char, 7, top + 12, 1, 1, n["blood_d"])
            rect(char, 6, top + 11, 1, 1, n["blood_d"])
            rect(char, 16, top + 6, 1, 2, n["blood_d"])
            rect(char, 15, top + 12, 1, 1, n["blood_d"])
        else:
            # back of the dress: a long dried streak down the hem
            rect(char, 9, top + 9, 2, 3, n["blood_d"])
            rect(char, 8, top + 11, 1, 2, n["blood"])
            rect(char, 14, top + 10, 1, 1, n["blood_d"])
            # back ties
            rect(char, 9, top + 8, 1, 2, n["dress_l"])
            rect(char, 16, top + 8, 1, 2, n["dress_l"])
        if chase:
            rect(char, 7, top + 4, 2, 2, n["blood"])
            rect(char, 16, top + 11, 2, 2, n["blood_d"])
    else:
        # profile: slimmer body, apron on the camera side
        rect(char, 6, top, 11, 9, n["dress"])
        vline(char, 6, top + 1, 8, n["dress_l"])
        vline(char, 16, top + 1, 8, n["dress_d"])
        hline(char, 6, top, 11, n["dress_l"])
        rect(char, 5, top + 8, 13, 2, n["dress"])
        rect(char, 4, top + 10, 15, 4, n["dress"])
        vline(char, 4, top + 10, 4, n["dress_l"])
        vline(char, 18, top + 10, 4, n["dress_d"])
        hline(char, 4, top + 13, 15, n["dress_d"])
        rect(char, 8, top + 3, 4, 8, n["dress_l"])
        hline(char, 6, top + 9, 11, n["dress_d"], 190)
        vline(char, 10, top + 11, 3, n["dress_d"], 150)
        rect(char, 11, top + 10, 3, 3, n["blood"])
        rect(char, 10, top + 12, 2, 2, n["blood_d"])
        rect(char, 12, top + 9, 1, 1, n["blood_d"])
        if chase:
            rect(char, 15, top + 6, 2, 2, n["blood_d"])
            rect(char, 7, top + 12, 1, 1, n["blood"])


def nurse_arms(char: np.ndarray, direction: str, pose: int, bob: int,
               chase: bool) -> None:
    n = NURSE
    top = 17 - bob
    swing = (0, 1, 0, -1, 0)[pose]
    if direction in ("down", "up"):
        for ax, side in ((4, -1), (18, 1)):
            hand_y = top + 10 + swing * side
            rect(char, ax, top + 1, 2, 3, n["dress"])
            vline(char, ax, top + 1, 3, n["dress_l"] if side < 0 else n["dress_d"])
            rect(char, ax, top + 4, 2, 5, n["skin"])
            vline(char, ax, top + 4, 5, n["skin_l"] if side < 0 else n["skin_d"])
            rect(char, ax, hand_y, 2, 2, n["skin_l"] if side < 0 else n["skin"])
            hline(char, ax, hand_y, 2, n["skin_l"] if side < 0 else n["skin_d"])
            if chase:
                hline(char, ax, hand_y + 1, 2, n["blood"])
    else:
        hand_x = 5 + swing
        rect(char, 8, top + 1, 3, 3, n["dress"])
        vline(char, 8, top + 1, 3, n["dress_l"])
        rect(char, 8, top + 4, 3, 6, n["skin"])
        vline(char, 8, top + 4, 6, n["skin_l"])
        vline(char, 10, top + 4, 6, n["skin_d"])
        rect(char, hand_x, top + 10, 3, 2, n["skin"])
        hline(char, hand_x, top + 10, 3, n["skin_l"])
        if chase:
            hline(char, hand_x, top + 11, 3, n["blood"])


def nurse_head(char: np.ndarray, direction: str, pose: int, bob: int,
               chase: bool) -> None:
    n = NURSE
    top = 4 - bob
    # neck and ears
    rect(char, 9, top + 12, 5, 3, n["skin_d"])
    rect(char, 4, top + 7, 1, 3, n["skin_d"])
    rect(char, 19, top + 7, 1, 3, n["skin_d"])
    # face, narrower at the jaw
    rect(char, 6, top + 4, 12, 4, n["skin"])
    rect(char, 7, top + 8, 10, 5, n["skin"])
    rect(char, 8, top + 12, 8, 2, n["skin"])
    hline(char, 6, top + 4, 12, n["skin_l"])
    vline(char, 6, top + 5, 7, n["skin_l"])
    vline(char, 17, top + 5, 7, n["skin_d"])
    hline(char, 8, top + 13, 8, n["skin_d"])
    # hair
    rect(char, 5, top + 1, 14, 4, n["hair"])
    hline(char, 5, top + 1, 14, n["hair_hi"])
    rect(char, 5, top + 4, 2, 8, n["hair"])
    rect(char, 17, top + 4, 2, 8, n["hair"])
    rect(char, 6, top + 4, 12, 1, n["hair"])
    rect(char, 6, top + 5, 1, 2, n["hair"])
    rect(char, 17, top + 5, 1, 2, n["hair"])
    # cap with a red cross, centered and unclipped
    rect(char, 7, top - 2, 10, 3, n["cap"])
    hline(char, 7, top - 2, 10, n["cap_l"])
    rect(char, 11, top - 2, 2, 2, n["blood"])
    rect(char, 10, top - 1, 4, 1, n["blood"])
    # dried blood at the hairline
    rect(char, 16, top + 3, 2, 1, n["blood_d"])
    if direction == "down":
        rect(char, 8, top + 6, 2, 1, n["skin_d"])
        rect(char, 14, top + 6, 2, 1, n["skin_d"])
        rect(char, 8, top + 7, 1, 1, n["hair"])
        rect(char, 15, top + 7, 1, 1, n["hair"])
        rect(char, 9, top + 7, 1, 1, n["eye_red"] if chase else n["eye"])
        rect(char, 14, top + 7, 1, 1, n["eye_red"] if chase else n["eye"])
        rect(char, 8, top + 8, 2, 1, n["skin_d"])
        rect(char, 14, top + 8, 2, 1, n["skin_d"])
        rect(char, 11, top + 9, 2, 1, n["skin_d"])
        rect(char, 7, top + 11, 1, 1, n["skin_d"])
        rect(char, 16, top + 11, 1, 1, n["skin_d"])
        if chase:
            rect(char, 10, top + 11, 4, 2, (38, 12, 12))
            rect(char, 10, top + 11, 4, 1, (156, 146, 126))
        else:
            hline(char, 10, top + 11, 3, n["lip"])
    elif direction == "up":
        rect(char, 6, top + 4, 12, 9, n["hair"])
        rect(char, 7, top + 4, 10, 1, n["hair_hi"])
        vline(char, 8, top + 6, 6, n["hair_hi"])
        rect(char, 9, top + 12, 6, 2, n["skin_d"])
        # bun under the cap
        rect(char, 10, top + 5, 4, 4, n["hair"])
        hline(char, 11, top + 5, 2, n["hair_hi"])
    else:
        rect(char, 12, top + 4, 6, 9, n["hair"])
        rect(char, 13, top + 4, 1, 8, n["hair_hi"])
        rect(char, 6, top + 4, 7, 1, n["hair"])
        rect(char, 6, top + 5, 1, 2, n["hair"])
        rect(char, 6, top + 5, 6, 1, n["skin_l"])
        rect(char, 6, top + 6, 6, 7, n["skin"])
        vline(char, 6, top + 6, 6, n["skin_l"])
        rect(char, 5, top + 8, 1, 2, n["skin_d"])
        rect(char, 7, top + 6, 1, 1, n["hair"])
        rect(char, 8, top + 7, 1, 1, n["eye_red"] if chase else n["eye"])
        rect(char, 7, top + 9, 1, 1, n["skin_d"])
        hline(char, 6, top + 10, 3, n["lip"])
        rect(char, 10, top + 7, 1, 2, n["skin_d"])
        rect(char, 10, top + 12, 3, 2, n["skin_d"])
        # bun at the back of the head
        rect(char, 14, top + 6, 3, 3, n["hair"])
        hline(char, 14, top + 6, 2, n["hair_hi"])
        if chase:
            rect(char, 6, top + 12, 2, 1, (38, 12, 12))


def nurse_frame(direction: str, pose: int, chase: bool) -> np.ndarray:
    char = frame(24, 38)
    bob = 1 if pose in (2, 4) else 0
    nurse_legs(char, direction, pose, bob)
    nurse_dress(char, direction, pose, bob, chase)
    nurse_arms(char, direction, pose, bob, chase)
    nurse_head(char, direction, pose, bob, chase)
    if direction == "right":
        char = np.fliplr(char)
    return compose(char, (12.0, 35.0, 9.0, 1.8))


# --- sheets -----------------------------------------------------------------

def build_sheet(draw, w: int, h: int, name: str, description: str,
                animations: dict[str, list[int]] | None = None) -> None:
    sheet = np.zeros((h * 4, w * 5, 4), dtype=np.float32)
    for row, direction in enumerate(DIRECTIONS):
        for column in range(5):
            sheet[row * h:(row + 1) * h, column * w:(column + 1) * w] = draw(direction, column)
    image = g.to_image(sheet)
    folder = TEX / "characters"
    folder.mkdir(parents=True, exist_ok=True)
    image.save(folder / f"{name}.png")
    MANIFEST.append({
        "id": name,
        "file": f"assets/textures/characters/{name}.png",
        "size": list(image.size),
        "category": "characters",
        "tileable": False,
        "batch": 3,
        "description": description,
        "frames": {
            "frame_size": [w, h],
            "columns": 5,
            "rows": 4,
            "row_order": DIRECTIONS,
            "column_order": COLUMNS,
            "animations": animations or {
                "idle": {"frames": [0], "fps": 1.0},
                "walk": {"frames": [1, 2, 3, 4], "fps": 8.0},
            },
        },
    })


def write_manifest(entries: list[dict]) -> None:
    path = TEX / "manifest.json"
    existing: list[dict] = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8")).get("assets", [])
        except json.JSONDecodeError:
            existing = []
    ids = {entry["id"] for entry in entries}
    merged = [entry for entry in existing if entry["id"] not in ids]
    merged.extend(entries)
    batches = sorted({entry.get("batch", 1) for entry in merged} | {3})
    path.write_text(
        json.dumps({"version": 1, "batches": batches, "assets": merged},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def make_preview() -> None:
    from PIL import Image, ImageDraw, ImageFont

    preview = g.PREVIEW
    preview.mkdir(parents=True, exist_ok=True)
    title_font = ImageFont.truetype(g.FONT_PATH, 26)
    head_font = ImageFont.truetype(g.FONT_PATH, 18)
    font = ImageFont.truetype(g.FONT_PATH, 12)
    small = ImageFont.truetype(g.FONT_PATH, 11)
    bg = (14, 17, 18)
    width, pad = 1600, 24
    zoom = 5
    label_w = 64
    gap = 12

    rows_ru = ["ВНИЗ", "ВЛЕВО", "ВПРАВО", "ВВЕРХ"]
    rows_en = ["DOWN", "LEFT", "RIGHT", "UP"]
    cols = ["СТОЙКА", "1", "2", "3", "4"]

    by_id = {entry["id"]: entry for entry in MANIFEST}

    def sheet_size(entry: dict) -> tuple[int, int]:
        fw, fh = entry["frames"]["frame_size"]
        return label_w + fw * zoom * 5 + gap * 4, fh * zoom * 4 + 10 * 3 + 22

    def draw_sheet(sheet: Image.Image, x: int, y: int, entry: dict) -> int:
        draw = ImageDraw.Draw(sheet)
        fw, fh = entry["frames"]["frame_size"]
        draw.text((x, y), entry["id"], font=head_font, fill=(222, 218, 204))
        draw.text((x, y + 22), entry["description"], font=small, fill=(120, 128, 123))
        info = f"кадр {fw}×{fh} · 5×4 · 20 кадров"
        draw.text((x + sheet_size(entry)[0] - 200, y + 4), info, font=small, fill=(140, 130, 104))
        grid_y = y + 52
        grid_x = x + label_w
        for col, label in enumerate(cols):
            draw.text((grid_x + col * (fw * zoom + gap), grid_y), label,
                      font=small, fill=(130, 138, 132))
        frame_y = grid_y + 20
        image = Image.open(ROOT / entry["file"]).convert("RGBA")
        for row in range(4):
            draw.text((x, frame_y + row * (fh * zoom + 10) + fh * zoom // 2 - 9),
                      rows_ru[row], font=font, fill=(198, 190, 168))
            draw.text((x, frame_y + row * (fh * zoom + 10) + fh * zoom // 2 + 5),
                      rows_en[row], font=small, fill=(104, 112, 108))
            for col in range(5):
                px = grid_x + col * (fw * zoom + gap)
                py = frame_y + row * (fh * zoom + 10)
                for cy in range(py, py + fh * zoom, 8):
                    for cx in range(px, px + fw * zoom, 8):
                        tone = (28, 32, 33) if ((cx - px) // 8 + (cy - py) // 8) % 2 == 0 else (22, 26, 27)
                        draw.rectangle((cx, cy, min(cx + 7, px + fw * zoom - 1),
                                        min(cy + 7, py + fh * zoom - 1)), fill=tone)
                crop = image.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))
                crop = crop.resize((fw * zoom, fh * zoom), Image.NEAREST)
                sheet.alpha_composite(crop, (px, py)) if sheet.mode == "RGBA" else sheet.paste(crop, (px, py), crop)
                draw.rectangle((px - 1, py - 1, px + fw * zoom, py + fh * zoom), outline=(58, 64, 62))
        return frame_y + 4 * (fh * zoom + 10)

    player = by_id["player_sheet"]
    nurse = by_id["nurse_sheet"]
    chase = by_id["nurse_chase_sheet"]

    pw, ph = sheet_size(player)
    nw, nh = sheet_size(nurse)
    top_h = 92 + max(ph, nh) + 44
    cw, ch = sheet_size(chase)
    total_h = top_h + max(ch, 300) + 90

    sheet = Image.new("RGBA", (width, total_h), bg + (255,))
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 18), "ЭТАЖ, КОТОРОГО НЕТ — texture pack / batch 3",
              font=title_font, fill=(220, 216, 203))
    draw.text((pad, 50),
              "Марк и медсестра · 4 направления × (стойка + 4 кадра шага) · 4x preview",
              font=small, fill=(118, 126, 122))

    draw_sheet(sheet, pad, 92, player)
    draw_sheet(sheet, pad + pw + 64, 92, nurse)

    second_y = top_h
    draw_sheet(sheet, pad, second_y, chase)

    # legend panel
    lx, ly = pad + cw + 64, second_y
    lw, lh = 430, max(ch, 300)
    draw.rectangle((lx, ly, lx + lw, ly + lh), fill=(18, 22, 23), outline=(56, 62, 60))
    draw.text((lx + 16, ly + 14), "ЛЕГЕНДА", font=head_font, fill=(198, 190, 168))
    lines = [
        "Сетка листа: 5 колонок × 4 строки.",
        "Колонка 0 — стойка, 1–4 — цикл шага.",
        "Строки: вниз, влево, вправо, вверх.",
        "Правая сторона — зеркало левой.",
        "",
        "Марк: 20×32 px, тёмная куртка,",
        "фонарик в правой руке.",
        "Медсестра: 24×38 px, выше Марка.",
        "Погоня: красные глаза и кровь.",
        "",
        "Мягкая тень встроена в кадр.",
        "Прозрачный фон, палитра 48 цветов.",
    ]
    for index, text in enumerate(lines):
        draw.text((lx + 16, ly + 46 + index * 18), text, font=small, fill=(150, 156, 148))

    # palette used by both characters
    palette_y = ly + 46 + len(lines) * 18 + 8
    draw.text((lx + 16, palette_y), "ПАЛИТРА", font=small, fill=(140, 130, 104))
    swatches = [
        ("куртка", PLAYER["coat"]),
        ("халат", NURSE["dress"]),
        ("кожа", PLAYER["skin"]),
        ("кровь", NURSE["blood"]),
        ("волосы", PLAYER["hair"]),
    ]
    for index, (label, color) in enumerate(swatches):
        sx = lx + 16 + index * 80
        sy = palette_y + 18
        draw.rectangle((sx, sy, sx + 22, sy + 22), fill=color, outline=(78, 84, 80))
        draw.text((sx, sy + 26), label, font=small, fill=(140, 146, 138))

    # close-up comparison at 6x
    close_y = palette_y + 66
    draw.text((lx + 16, close_y), "КРУПНО 6x", font=small, fill=(140, 130, 104))
    pimg = Image.open(ROOT / player["file"]).convert("RGBA").crop((0, 0, 20, 32))
    nimg = Image.open(ROOT / nurse["file"]).convert("RGBA").crop((0, 0, 24, 38))
    pimg = pimg.resize((20 * 6, 32 * 6), Image.NEAREST)
    nimg = nimg.resize((24 * 6, 38 * 6), Image.NEAREST)
    sheet.alpha_composite(pimg, (lx + 20, close_y + 16))
    sheet.alpha_composite(nimg, (lx + 20 + 20 * 6 + 40, close_y + 16))
    draw.text((lx + 20, close_y + 16 + 32 * 6 + 4), "МАРК", font=small, fill=(150, 156, 148))
    draw.text((lx + 20 + 20 * 6 + 40, close_y + 16 + 32 * 6 + 4), "МЕДСЕСТРА", font=small, fill=(150, 156, 148))

    sheet.convert("RGB").save(preview / "batch3_characters.png")
    print(f"preview -> {preview / 'batch3_characters.png'} ({sheet.size[0]}x{sheet.size[1]})")


def build() -> None:
    build_sheet(lambda d, p: player_frame(d, p), 20, 32,
                "player_sheet", "Марк: 4 направления, стойка и 4 кадра ходьбы")
    build_sheet(lambda d, p: nurse_frame(d, p, False), 24, 38,
                "nurse_sheet", "Медсестра: 4 направления, стойка и 4 кадра ходьбы")
    build_sheet(lambda d, p: nurse_frame(d, p, True), 24, 38,
                "nurse_chase_sheet", "Медсестра в погоне: красные глаза, кровь на руках")
    write_manifest(MANIFEST)
    make_preview()


if __name__ == "__main__":
    build()
    for entry in MANIFEST:
        print(f"{entry['id']} -> {entry['file']} ({entry['size'][0]}x{entry['size'][1]})")