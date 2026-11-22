#!/usr/bin/env python3
"""Preview sheet and in-context mocks for batch 4 (UI).

The contact sheet shows every asset at a readable zoom, and the mocks show
the HUD and the title screen composed at 640x360 and exported at 2x.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_textures as g
import mock_props as mp

ROOT = g.ROOT
TEX = g.TEX
UI = TEX / "ui"
PREVIEW = g.PREVIEW
W, H = 640, 360

BG = (14, 17, 18)
PANEL_BG = (22, 26, 27)
BONE = (216, 210, 192)
MUTED = (128, 136, 130)
AMBER = (196, 160, 100)

TITLE_FONT = ImageFont.truetype(g.FONT_PATH, 26)
HEAD_FONT = ImageFont.truetype(g.FONT_PATH, 17)
MONO_14 = ImageFont.truetype(g.FONT_PATH, 14)
MONO_12 = ImageFont.truetype(g.FONT_PATH, 12)
MONO_10 = ImageFont.truetype(g.FONT_PATH, 10)
MONO_9 = ImageFont.truetype(g.FONT_PATH, 9)
MONO_16 = ImageFont.truetype(g.FONT_PATH, 16)


def load(name: str, folder: Path = UI) -> Image.Image:
    return Image.open(folder / f"{name}.png").convert("RGBA")


def nine_patch(img: Image.Image, width: int, height: int,
               left: int, right: int, top: int, bottom: int) -> Image.Image:
    """Stretch a nine-patch exactly like Godot StyleBoxTexture does."""
    iw, ih = img.size
    out = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    out.paste(img.crop((0, 0, left, top)), (0, 0))
    out.paste(img.crop((iw - right, 0, iw, top)), (width - right, 0))
    out.paste(img.crop((0, ih - bottom, left, ih)), (0, height - bottom))
    out.paste(img.crop((iw - right, ih - bottom, iw, ih)), (width - right, height - bottom))
    if width - left - right > 0:
        out.paste(img.crop((left, 0, iw - right, top)).resize(
            (width - left - right, top), Image.NEAREST), (left, 0))
        out.paste(img.crop((left, ih - bottom, iw - right, ih)).resize(
            (width - left - right, bottom), Image.NEAREST), (left, height - bottom))
    if height - top - bottom > 0:
        out.paste(img.crop((0, top, left, ih - bottom)).resize(
            (left, height - top - bottom), Image.NEAREST), (0, top))
        out.paste(img.crop((iw - right, top, iw, ih - bottom)).resize(
            (right, height - top - bottom), Image.NEAREST), (width - right, top))
    if width - left - right > 0 and height - top - bottom > 0:
        out.paste(img.crop((left, top, iw - right, ih - bottom)).resize(
            (width - left - right, height - top - bottom), Image.NEAREST), (left, top))
    return out


def panel_img(name: str, width: int, height: int) -> Image.Image:
    return nine_patch(load(name), width, height, 12, 12, 12, 12)


def button_img(name: str, width: int, height: int) -> Image.Image:
    return nine_patch(load(name), width, height, 10, 10, 8, 8)


def slot_img(width: int, height: int) -> Image.Image:
    return nine_patch(load("ui_slot"), width, height, 8, 8, 8, 8)


def zoom(image: Image.Image, factor: int) -> Image.Image:
    return image.resize((image.width * factor, image.height * factor), Image.NEAREST)


# --- gameplay HUD mock ------------------------------------------------------

def game_frame() -> Image.Image:
    scene = mp.build_scene()
    player = Image.open(TEX / "characters/player_sheet.png").convert("RGBA").crop((2 * 20, 0, 3 * 20, 32))
    nurse = Image.open(TEX / "characters/nurse_chase_sheet.png").convert("RGBA").crop((1 * 24, 0, 2 * 24, 38))
    scene.alpha_composite(player, (214, 200))
    scene.alpha_composite(nurse, (470, 186))
    lit = mp.apply_lighting(scene, (240, 216), export_scale=1).convert("RGBA")
    lit.alpha_composite(load("ui_vignette"))

    # objective panel
    lit.alpha_composite(panel_img("ui_panel", 392, 68), (16, 16))
    draw = ImageDraw.Draw(lit)
    draw.text((32, 26), "ЦЕЛЬ", font=MONO_12, fill=(150, 138, 104))
    draw.text((32, 42), "Спуститься в морг", font=MONO_16, fill=(206, 204, 190))
    draw.text((32, 60), "и найти Леру", font=MONO_16, fill=(206, 204, 190))

    # interaction prompt, below the player and clear of the inventory
    lit.alpha_composite(panel_img("ui_panel", 288, 38), (120, 242))
    draw.text((136, 252), "[E]  прочитать запись", font=MONO_14, fill=(214, 196, 148))

    # inventory strip
    lit.alpha_composite(panel_img("ui_panel", 206, 74), (418, 272))
    draw.text((432, 281), "ПРЕДМЕТЫ", font=MONO_10, fill=(146, 150, 138))
    lit.alpha_composite(load("ui_divider").resize((178, 8), Image.NEAREST), (432, 293))
    icons = ["icon_cassette", "icon_fuse", "icon_key", "icon_note"]
    for index, icon in enumerate(icons):
        x = 432 + index * 46
        lit.alpha_composite(slot_img(40, 40), (x, 300))
        art = load(icon)
        lit.alpha_composite(art, (x + 8, 300 + 8))

    return zoom(lit, 2)


# --- title mock -------------------------------------------------------------

def title_frame() -> Image.Image:
    frame = load("ui_title_bg").copy()
    logo = load("ui_logo")
    frame.alpha_composite(logo, ((W - logo.width) // 2, 34))
    draw = ImageDraw.Draw(frame)
    subtitle = "психологический хоррор"
    width = draw.textlength(subtitle, font=MONO_14)
    draw.text(((W - width) / 2, 102), subtitle, font=MONO_14, fill=(150, 152, 146))
    warning = "18+   кровь · смерть · психологическое насилие · намёки на близость"
    width = draw.textlength(warning, font=MONO_10)
    draw.text(((W - width) / 2, 122), warning, font=MONO_10, fill=(140, 88, 84))

    labels = ["НОВАЯ ИГРА", "ПРОДОЛЖИТЬ", "НАСТРОЙКИ"]
    for index, label in enumerate(labels):
        y = 152 + index * 38
        state = "ui_button_hover" if index == 0 else "ui_button"
        frame.alpha_composite(button_img(state, 220, 30), (210, y))
        width = draw.textlength(label, font=MONO_14)
        draw.text((320 - width / 2, y + 8), label, font=MONO_14,
                  fill=(238, 226, 196) if index == 0 else (196, 194, 182))

    controls = "WASD / стрелки — идти    ·    E — действие    ·    Esc — пауза"
    width = draw.textlength(controls, font=MONO_10)
    draw.text(((W - width) / 2, 316), controls, font=MONO_10, fill=(110, 116, 112))
    version = "v0.1.0-alpha.1   ·   локальная альфа"
    width = draw.textlength(version, font=MONO_9)
    draw.text(((W - width) / 2, 336), version, font=MONO_9, fill=(84, 90, 88))
    return zoom(frame, 2)


# --- contact sheet ----------------------------------------------------------

def make_sheet() -> Image.Image:
    width, pad = 1600, 28
    sheet = Image.new("RGBA", (width, 1500), BG + (255,))
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 20), "ЭТАЖ, КОТОРОГО НЕТ — texture pack / batch 4", font=TITLE_FONT, fill=BONE)
    draw.text((pad, 54), "UI, бумага, иконки, виньетка, логотип, титульный фон · 640×360 · nine-patch",
              font=MONO_12, fill=MUTED)

    def caption(x: int, y: int, name: str, note: str) -> None:
        draw.text((x, y), name, font=MONO_12, fill=(202, 196, 178))
        draw.text((x, y + 15), note, font=MONO_10, fill=(118, 126, 122))

    # panels
    y = 100
    draw.text((pad, y), "ПАНЕЛИ  nine-patch 12 px", font=HEAD_FONT, fill=AMBER)
    y += 30
    x = pad
    for name, note in (
        ("ui_panel", "HUD: пластик, латунь"),
        ("ui_panel_alert", "тревога, ржавая рамка"),
        ("ui_panel_paper", "бумага: сгиб, пятно"),
    ):
        art = load(name).resize((128, 128), Image.NEAREST)
        sheet.alpha_composite(art, (x, y))
        caption(x, y + 134, name, note)
        x += 190
    demo = panel_img("ui_panel", 300, 96)
    sheet.alpha_composite(demo, (x + 12, y + 16))
    caption(x + 12, y + 134, "панель 300×96", "уголки и линия не плывут")

    # buttons
    y += 200
    draw.text((pad, y), "КНОПКИ  nine-patch 10 / 8 px", font=HEAD_FONT, fill=AMBER)
    y += 30
    x = pad
    for name, note in (
        ("ui_button", "обычное"),
        ("ui_button_hover", "наведение"),
        ("ui_button_pressed", "нажатие"),
    ):
        art = button_img(name, 220, 30)
        art = art.resize((art.width * 2, art.height * 2), Image.NEAREST)
        sheet.alpha_composite(art, (x, y))
        caption(x, y + art.height + 8, name, note)
        x += 460

    # slot, divider, icons
    y += 130
    draw.text((pad, y), "ИНВЕНТАРЬ И ИКОНКИ", font=HEAD_FONT, fill=AMBER)
    y += 30
    slot = slot_img(40, 40)
    icons = ["icon_cassette", "icon_fuse", "icon_key", "icon_note"]
    for index, icon in enumerate(icons):
        sx = pad + index * 116
        sheet.alpha_composite(slot.resize((80, 80), Image.NEAREST), (sx, y))
        sheet.alpha_composite(load(icon).resize((48, 48), Image.NEAREST), (sx + 16, y + 16))
        caption(sx, y + 88, icon, "24×24")
    divider = load("ui_divider").resize((384, 32), Image.NEAREST)
    sheet.alpha_composite(divider, (pad + 4 * 116 + 30, y + 24))
    caption(pad + 4 * 116 + 30, y + 88, "ui_divider", "32×8, тянется по X")

    # logo and vignette
    y += 140
    draw.text((pad, y), "ЛОГОТИП  пиксельный шрифт 5×7, шкала 3×", font=HEAD_FONT, fill=AMBER)
    draw.text((pad + 520, y), "ВИНЬЕТКА 640×360", font=HEAD_FONT, fill=AMBER)
    y += 30
    logo = load("ui_logo")
    logo_bg = Image.new("RGBA", (logo.width * 2 + 40, logo.height * 2 + 40), PANEL_BG + (255,))
    logo_bg.alpha_composite(logo.resize((logo.width * 2, logo.height * 2), Image.NEAREST), (20, 20))
    sheet.alpha_composite(logo_bg, (pad, y))
    caption(pad, y + logo_bg.height + 6, "ui_logo", f"{logo.width}×{logo.height} · без квантования")

    card = mp.build_scene()
    card = mp.apply_lighting(card, (300, 214), export_scale=1).convert("RGBA")
    card.alpha_composite(load("ui_vignette"))
    sheet.alpha_composite(card.resize((480, 270), Image.NEAREST), (pad + 520, y))
    caption(pad + 520, y + 276, "ui_vignette", "затемнение краёв + сканлайны, alpha-слой")

    # note sheet and title art
    y += 320
    draw.text((pad, y), "ЗАПИСКА 520×260", font=HEAD_FONT, fill=AMBER)
    draw.text((pad + 580, y), "ТИТУЛЬНЫЙ ФОН 640×360", font=HEAD_FONT, fill=AMBER)
    y += 30
    note = load("ui_note_sheet")
    sheet.alpha_composite(note, (pad, y))
    lines = [
        "Лера,",
        "если ты это читаешь — не спускайся в морг.",
        "Я слышу, как лифт едет сам.",
        "",
        "М.",
    ]
    for index, line in enumerate(lines):
        draw.text((pad + 58, y + 44 + index * 21), line, font=MONO_14,
                  fill=(44, 38, 32))
    caption(pad, y + note.height + 6, "ui_note_sheet",
            "520×260 · сгиб, кофейный круг, штамп, дырокол")

    title = load("ui_title_bg").resize((320, 180), Image.NEAREST)
    sheet.alpha_composite(title, (pad + 580, y))
    caption(pad + 580, y + 186, "ui_title_bg",
            "коридор с дверью, лампой и фигурой · 64 цвета")

    bottom = y + note.height + 40
    return sheet.crop((0, 0, width, bottom)).convert("RGB")


def make_title(path: Path) -> None:
    frame = title_frame()
    frame.convert("RGB").save(path)
    print(f"mock -> {path} ({frame.width}x{frame.height})")


def make_game_mock(path: Path) -> None:
    frame = game_frame()
    frame.convert("RGB").save(path)
    print(f"mock -> {path} ({frame.width}x{frame.height})")


if __name__ == "__main__":
    sheet = make_sheet()
    sheet.save(PREVIEW / "batch4_ui.png")
    print(f"preview -> {PREVIEW / 'batch4_ui.png'} ({sheet.width}x{sheet.height})")
    make_game_mock(PREVIEW / "batch4_mock.png")
    make_title(PREVIEW / "batch4_title.png")