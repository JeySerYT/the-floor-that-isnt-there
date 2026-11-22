class_name GameUI
extends Control

signal new_game_requested
signal continue_requested
signal quit_requested
signal resume_requested
signal menu_requested
signal note_closed
signal choice_selected(index: int)
signal ending_menu_requested
signal ending_restart_requested

const PANEL_TEXTURE := preload("res://assets/textures/ui/ui_panel.png")
const PANEL_ALERT_TEXTURE := preload("res://assets/textures/ui/ui_panel_alert.png")
const PANEL_PAPER_TEXTURE := preload("res://assets/textures/ui/ui_panel_paper.png")
const BUTTON_TEXTURE := preload("res://assets/textures/ui/ui_button.png")
const BUTTON_HOVER_TEXTURE := preload("res://assets/textures/ui/ui_button_hover.png")
const BUTTON_PRESSED_TEXTURE := preload("res://assets/textures/ui/ui_button_pressed.png")
const SLOT_TEXTURE := preload("res://assets/textures/ui/ui_slot.png")
const DIVIDER_TEXTURE := preload("res://assets/textures/ui/ui_divider.png")
const ICON_FUSE := preload("res://assets/textures/ui/icon_fuse.png")
const ICON_KEY := preload("res://assets/textures/ui/icon_key.png")
const ICON_CASSETTE := preload("res://assets/textures/ui/icon_cassette.png")
const ICON_NOTE := preload("res://assets/textures/ui/icon_note.png")
const NOTE_SHEET := preload("res://assets/textures/ui/ui_note_sheet.png")
const VIGNETTE_TEXTURE := preload("res://assets/textures/ui/ui_vignette.png")
const LOGO_TEXTURE := preload("res://assets/textures/ui/ui_logo.png")
const TITLE_TEXTURE := preload("res://assets/textures/ui/ui_title_bg.png")

var _menu: Control
var _game: Control
var _pause: Control
var _note: Control
var _choice: Control
var _ending: Control
var _continue_button: Button
var _new_button: Button
var _objective_label: Label
var _inventory_icons: Dictionary = {}
var _prompt_panel: PanelContainer
var _prompt_label: Label
var _toast_panel: PanelContainer
var _toast_label: Label
var _note_title: Label
var _note_body: RichTextLabel
var _note_close_button: Button
var _choice_title: Label
var _choice_body: Label
var _choice_box: VBoxContainer
var _ending_title: Label
var _ending_body: RichTextLabel
var _caught_flash: ColorRect
var _toast_tween: Tween


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	theme = _make_base_theme()
	_build_game_hud()
	_build_menu()
	_build_note_panel()
	_build_choice_panel()
	_build_pause_panel()
	_build_ending_panel()
	show_menu(GameState.has_save())


func show_menu(has_save: bool) -> void:
	_menu.visible = true
	_game.visible = false
	_note.visible = false
	_choice.visible = false
	_pause.visible = false
	_ending.visible = false
	_continue_button.disabled = not has_save
	_new_button.grab_focus()


func show_game() -> void:
	_menu.visible = false
	_game.visible = true
	_note.visible = false
	_choice.visible = false
	_pause.visible = false
	_ending.visible = false
	_update_hud()


func set_objective(text: String) -> void:
	_objective_label.text = text


func set_inventory(items: Array[String]) -> void:
	_inventory_icons["fuse"].visible = items.has("fuse")
	_inventory_icons["lift_key"].visible = items.has("lift_key")
	_inventory_icons["cassette"].visible = GameState.has_flag("tape_heard")
	_inventory_icons["note"].visible = GameState.has_flag("ward_chart_read")


func set_prompt(text: String) -> void:
	if text.is_empty():
		_prompt_panel.visible = false
		return
	_prompt_panel.visible = true
	_prompt_label.text = "[E]  " + text


func show_toast(text: String) -> void:
	_toast_label.text = text
	_toast_panel.visible = true
	_toast_panel.modulate.a = 1.0
	if _toast_tween != null and _toast_tween.is_valid():
		_toast_tween.kill()
	_toast_tween = create_tween()
	_toast_tween.tween_interval(2.2)
	_toast_tween.tween_property(_toast_panel, "modulate:a", 0.0, 0.8)
	_toast_tween.tween_callback(func() -> void: _toast_panel.visible = false)


func show_note(title: String, body: String) -> void:
	_choice.visible = false
	_note_title.text = title
	_note_body.text = body
	_note.visible = true
	_note_close_button.grab_focus()


func hide_note() -> void:
	_note.visible = false


func show_choice(title: String, body: String, options: Array[String]) -> void:
	_note.visible = false
	_choice_title.text = title
	_choice_body.text = body
	for child in _choice_box.get_children():
		child.queue_free()
	for index in options.size():
		var button := _make_button(options[index], 220)
		button.pressed.connect(func() -> void: choice_selected.emit(index))
		_choice_box.add_child(button)
	_choice.visible = true
	if _choice_box.get_child_count() > 0:
		(_choice_box.get_child(0) as Button).grab_focus()


func hide_choice() -> void:
	_choice.visible = false


func show_pause() -> void:
	_pause.visible = true
	var resume := _pause.find_child("Resume", true, false) as Button
	if resume != null:
		resume.grab_focus()


func hide_pause() -> void:
	_pause.visible = false


func show_ending(title: String, body: String) -> void:
	_toast_panel.visible = false
	if _toast_tween != null and _toast_tween.is_valid():
		_toast_tween.kill()
	_note.visible = false
	_choice.visible = false
	_pause.visible = false
	_ending_title.text = title
	_ending_body.text = body
	_ending.visible = true
	var menu_button := _ending.find_child("Menu", true, false) as Button
	if menu_button != null:
		menu_button.grab_focus()


func play_caught_effect() -> void:
	_caught_flash.visible = true
	_caught_flash.color = Color(0.45, 0.0, 0.0, 0.0)
	var tween := create_tween()
	tween.tween_property(_caught_flash, "color:a", 0.62, 0.05)
	tween.tween_property(_caught_flash, "color:a", 0.0, 0.65)
	tween.tween_callback(func() -> void: _caught_flash.visible = false)


func _update_hud() -> void:
	set_objective(GameState.objective)
	set_inventory(GameState.inventory)


func _build_game_hud() -> void:
	_game = Control.new()
	_game.name = "HUD"
	_game.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_game.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_game)

	var vignette := TextureRect.new()
	vignette.name = "Vignette"
	vignette.texture = VIGNETTE_TEXTURE
	vignette.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	vignette.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	vignette.stretch_mode = TextureRect.STRETCH_SCALE
	vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_game.add_child(vignette)

	var objective_panel := _make_panel("panel")
	objective_panel.name = "ObjectivePanel"
	objective_panel.position = Vector2(16, 16)
	objective_panel.size = Vector2(392, 78)
	objective_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_game.add_child(objective_panel)
	var objective_box := VBoxContainer.new()
	objective_box.add_theme_constant_override("separation", 2)
	objective_panel.add_child(objective_box)
	objective_box.add_child(_label("ЦЕЛЬ", 12, Color(0.66, 0.58, 0.4)))
	_objective_label = _label("", 16, Color(0.82, 0.81, 0.76))
	_objective_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_objective_label.custom_minimum_size = Vector2(360, 0)
	objective_box.add_child(_objective_label)

	var inventory_panel := _make_panel("panel")
	inventory_panel.name = "InventoryPanel"
	inventory_panel.anchor_left = 1.0
	inventory_panel.anchor_right = 1.0
	inventory_panel.anchor_top = 1.0
	inventory_panel.anchor_bottom = 1.0
	inventory_panel.offset_left = -222
	inventory_panel.offset_right = -16
	inventory_panel.offset_top = -100
	inventory_panel.offset_bottom = -16
	inventory_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_game.add_child(inventory_panel)
	var inventory_box := VBoxContainer.new()
	inventory_box.add_theme_constant_override("separation", 3)
	inventory_panel.add_child(inventory_box)
	inventory_box.add_child(_label("ПРЕДМЕТЫ", 10, Color(0.62, 0.64, 0.58)))
	var divider := TextureRect.new()
	divider.texture = DIVIDER_TEXTURE
	divider.custom_minimum_size = Vector2(0, 8)
	divider.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	divider.stretch_mode = TextureRect.STRETCH_SCALE
	divider.mouse_filter = Control.MOUSE_FILTER_IGNORE
	inventory_box.add_child(divider)
	var slots := HBoxContainer.new()
	slots.add_theme_constant_override("separation", 4)
	inventory_box.add_child(slots)
	_add_inventory_slot(slots, "cassette", ICON_CASSETTE)
	_add_inventory_slot(slots, "fuse", ICON_FUSE)
	_add_inventory_slot(slots, "lift_key", ICON_KEY)
	_add_inventory_slot(slots, "note", ICON_NOTE)

	_prompt_panel = _make_panel("panel")
	_prompt_panel.name = "Prompt"
	_prompt_panel.anchor_left = 0.5
	_prompt_panel.anchor_right = 0.5
	_prompt_panel.anchor_top = 1.0
	_prompt_panel.anchor_bottom = 1.0
	_prompt_panel.offset_left = -200
	_prompt_panel.offset_right = 88
	_prompt_panel.offset_top = -58
	_prompt_panel.offset_bottom = -20
	_prompt_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt_panel.visible = false
	_game.add_child(_prompt_panel)
	_prompt_label = _label("", 14, Color(0.9, 0.84, 0.66))
	_prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_prompt_panel.add_child(_prompt_label)

	_toast_panel = _make_panel("panel")
	_toast_panel.name = "Toast"
	_toast_panel.anchor_left = 0.5
	_toast_panel.anchor_right = 0.5
	_toast_panel.anchor_top = 1.0
	_toast_panel.anchor_bottom = 1.0
	_toast_panel.offset_left = -160
	_toast_panel.offset_right = 160
	_toast_panel.offset_top = -150
	_toast_panel.offset_bottom = -114
	_toast_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_toast_panel.visible = false
	_game.add_child(_toast_panel)
	_toast_label = _label("", 12, Color(0.78, 0.76, 0.68))
	_toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_toast_panel.add_child(_toast_label)

	_caught_flash = ColorRect.new()
	_caught_flash.name = "CaughtFlash"
	_caught_flash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_caught_flash.color = Color(0.45, 0.0, 0.0, 0.0)
	_caught_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_caught_flash.visible = false
	_game.add_child(_caught_flash)


func _add_inventory_slot(parent: Control, item_id: String, icon_texture: Texture2D) -> void:
	var slot := Control.new()
	slot.custom_minimum_size = Vector2(40, 40)
	parent.add_child(slot)
	var frame := TextureRect.new()
	frame.texture = SLOT_TEXTURE
	frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	frame.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	frame.stretch_mode = TextureRect.STRETCH_SCALE
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	slot.add_child(frame)
	var icon := TextureRect.new()
	icon.texture = icon_texture
	icon.position = Vector2(8, 8)
	icon.size = Vector2(24, 24)
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon.stretch_mode = TextureRect.STRETCH_SCALE
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	icon.visible = false
	slot.add_child(icon)
	_inventory_icons[item_id] = icon


func _build_menu() -> void:
	_menu = Control.new()
	_menu.name = "Menu"
	_menu.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_menu)

	var backdrop := TextureRect.new()
	backdrop.name = "Backdrop"
	backdrop.texture = TITLE_TEXTURE
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	backdrop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	backdrop.stretch_mode = TextureRect.STRETCH_SCALE
	backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_menu.add_child(backdrop)

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_menu.add_child(center)

	var margin := _make_margin(24, 10)
	center.add_child(margin)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	box.custom_minimum_size = Vector2(440, 0)
	margin.add_child(box)

	var logo := TextureRect.new()
	logo.texture = LOGO_TEXTURE
	logo.custom_minimum_size = Vector2(217, 64)
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	logo.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(logo)

	var subtitle := _label("психологический хоррор", 14, Color(0.45, 0.47, 0.48))
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(subtitle)

	var warning := _label("18+  кровь · смерть · психологическое насилие · намёки на близость", 10, Color(0.5, 0.32, 0.31))
	warning.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(warning)

	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, 10)
	box.add_child(spacer)

	var button_box := VBoxContainer.new()
	button_box.add_theme_constant_override("separation", 4)
	button_box.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	box.add_child(button_box)

	_continue_button = _make_button("Продолжить", 220)
	_continue_button.pressed.connect(func() -> void: continue_requested.emit())
	button_box.add_child(_continue_button)

	_new_button = _make_button("Новая игра", 220)
	_new_button.pressed.connect(func() -> void: new_game_requested.emit())
	button_box.add_child(_new_button)

	var quit_button := _make_button("Выход", 220)
	quit_button.pressed.connect(func() -> void: quit_requested.emit())
	button_box.add_child(quit_button)

	var controls := _label("WASD / стрелки — идти   ·   E — действие\nEsc — пауза   ·   F11 — полный экран", 10, Color(0.42, 0.44, 0.45))
	controls.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(controls)

	var version := FileAccess.get_file_as_string("res://VERSION").strip_edges()
	var version_label := _label("v%s   ·   локальная альфа" % version, 9, Color(0.33, 0.35, 0.36))
	version_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(version_label)


func _build_note_panel() -> void:
	_note = _make_overlay("Note")
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_note.add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(600, 320)
	var style := StyleBoxTexture.new()
	style.texture = NOTE_SHEET
	style.texture_margin_left = 12
	style.texture_margin_right = 12
	style.texture_margin_top = 12
	style.texture_margin_bottom = 12
	style.content_margin_left = 38
	style.content_margin_right = 38
	style.content_margin_top = 30
	style.content_margin_bottom = 24
	panel.add_theme_stylebox_override("panel", style)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	panel.add_child(box)
	_note_title = _label("", 16, Color(0.2, 0.16, 0.12))
	_note_title.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0))
	box.add_child(_note_title)
	var line := ColorRect.new()
	line.color = Color(0.4, 0.34, 0.27, 0.45)
	line.custom_minimum_size = Vector2(0, 2)
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(line)
	_note_body = RichTextLabel.new()
	_note_body.bbcode_enabled = true
	_note_body.fit_content = false
	_note_body.scroll_active = false
	_note_body.custom_minimum_size = Vector2(524, 200)
	_note_body.add_theme_font_size_override("normal_font_size", 12)
	_note_body.add_theme_constant_override("line_separation", 1)
	_note_body.add_theme_color_override("default_color", Color(0.18, 0.15, 0.11))
	_note_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(_note_body)
	_note_close_button = _make_button("Закрыть  [E]", 150)
	_note_close_button.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_note_close_button.pressed.connect(func() -> void: note_closed.emit())
	box.add_child(_note_close_button)


func _build_choice_panel() -> void:
	_choice = _make_overlay("Choice")
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_choice.add_child(center)
	var panel := _make_panel("alert")
	panel.custom_minimum_size = Vector2(540, 0)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	panel.add_child(box)
	_choice_title = _label("", 18, Color(0.86, 0.66, 0.55))
	box.add_child(_choice_title)
	_choice_body = _label("", 13, Color(0.8, 0.79, 0.74))
	_choice_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_choice_body.custom_minimum_size = Vector2(480, 0)
	box.add_child(_choice_body)
	_choice_box = VBoxContainer.new()
	_choice_box.add_theme_constant_override("separation", 4)
	box.add_child(_choice_box)


func _build_pause_panel() -> void:
	_pause = _make_overlay("Pause")
	_pause.name = "Pause"
	var center := CenterContainer.new()
	center.name = "Center"
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_pause.add_child(center)
	var panel := _make_panel("panel")
	panel.custom_minimum_size = Vector2(400, 0)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.name = "VBox"
	box.add_theme_constant_override("separation", 10)
	panel.add_child(box)
	var title := _label("ПАУЗА", 28, Color(0.68, 0.66, 0.61))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)
	var resume := _make_button("Продолжить", 260)
	resume.name = "Resume"
	resume.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	resume.pressed.connect(func() -> void: resume_requested.emit())
	box.add_child(resume)
	var save := _make_button("Сохранить и выйти в меню", 260)
	save.name = "Menu"
	save.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	save.pressed.connect(func() -> void: menu_requested.emit())
	box.add_child(save)
	var quit := _make_button("Завершить игру", 260)
	quit.name = "Quit"
	quit.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	quit.pressed.connect(func() -> void: quit_requested.emit())
	box.add_child(quit)
	var hint := _label("Прогресс сохраняется автоматически", 12, Color(0.4, 0.41, 0.42))
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(hint)


func _build_ending_panel() -> void:
	_ending = _make_overlay("Ending")
	var center := CenterContainer.new()
	center.name = "Center"
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_ending.add_child(center)
	var panel := _make_panel("alert")
	panel.custom_minimum_size = Vector2(560, 0)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.name = "VBox"
	box.add_theme_constant_override("separation", 10)
	panel.add_child(box)
	_ending_title = _label("", 28, Color(0.72, 0.3, 0.27))
	_ending_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(_ending_title)
	_ending_body = RichTextLabel.new()
	_ending_body.bbcode_enabled = true
	_ending_body.fit_content = false
	_ending_body.scroll_active = false
	_ending_body.custom_minimum_size = Vector2(500, 220)
	_ending_body.add_theme_font_size_override("normal_font_size", 13)
	_ending_body.add_theme_constant_override("line_separation", 2)
	_ending_body.add_theme_color_override("default_color", Color(0.72, 0.71, 0.66))
	_ending_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(_ending_body)
	var buttons := HBoxContainer.new()
	buttons.name = "Buttons"
	buttons.add_theme_constant_override("separation", 6)
	buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_child(buttons)
	var restart := _make_button("Начать заново", 170)
	restart.name = "Restart"
	restart.pressed.connect(func() -> void: ending_restart_requested.emit())
	buttons.add_child(restart)
	var menu := _make_button("В главное меню", 170)
	menu.name = "Menu"
	menu.pressed.connect(func() -> void: ending_menu_requested.emit())
	buttons.add_child(menu)


func _make_overlay(overlay_name: String) -> Control:
	var overlay := Control.new()
	overlay.name = overlay_name
	overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	overlay.visible = false
	add_child(overlay)
	var dim := ColorRect.new()
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.005, 0.006, 0.008, 0.94)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	overlay.add_child(dim)
	return overlay


func _make_base_theme() -> Theme:
	var result := Theme.new()
	result.set_color("font_color", "Label", Color(0.76, 0.75, 0.7))
	result.set_color("font_shadow_color", "Label", Color(0, 0, 0, 0.8))
	result.set_constant("shadow_offset_x", "Label", 1)
	result.set_constant("shadow_offset_y", "Label", 1)
	result.set_color("default_color", "RichTextLabel", Color(0.74, 0.73, 0.68))
	result.set_font_size("normal_font_size", "RichTextLabel", 13)
	return result


func _make_panel(kind: String = "panel") -> PanelContainer:
	var panel := PanelContainer.new()
	var style := StyleBoxTexture.new()
	match kind:
		"alert":
			style.texture = PANEL_ALERT_TEXTURE
		"paper":
			style.texture = PANEL_PAPER_TEXTURE
		_:
			style.texture = PANEL_TEXTURE
	style.texture_margin_left = 12
	style.texture_margin_right = 12
	style.texture_margin_top = 12
	style.texture_margin_bottom = 12
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	panel.add_theme_stylebox_override("panel", style)
	return panel


func _make_margin(horizontal: int, vertical: int) -> MarginContainer:
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", horizontal)
	margin.add_theme_constant_override("margin_right", horizontal)
	margin.add_theme_constant_override("margin_top", vertical)
	margin.add_theme_constant_override("margin_bottom", vertical)
	return margin


func _label(text: String, size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label


func _make_button(text: String, min_width: float = 168.0) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(min_width, 30)
	button.add_theme_font_size_override("font_size", 14)
	button.focus_mode = Control.FOCUS_ALL
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	var normal := _button_style(BUTTON_TEXTURE)
	var hover := _button_style(BUTTON_HOVER_TEXTURE)
	var pressed := _button_style(BUTTON_PRESSED_TEXTURE)
	var focus := _button_style(BUTTON_HOVER_TEXTURE)

	button.add_theme_stylebox_override("normal", normal)
	button.add_theme_stylebox_override("hover", hover)
	button.add_theme_stylebox_override("pressed", pressed)
	button.add_theme_stylebox_override("focus", focus)
	button.add_theme_color_override("font_color", Color(0.76, 0.75, 0.69))
	button.add_theme_color_override("font_hover_color", Color(0.94, 0.88, 0.7))
	button.add_theme_color_override("font_focus_color", Color(0.94, 0.88, 0.7))
	button.add_theme_color_override("font_pressed_color", Color(1.0, 0.95, 0.8))
	button.add_theme_color_override("font_disabled_color", Color(0.32, 0.32, 0.31))
	return button


func _button_style(texture: Texture2D) -> StyleBoxTexture:
	var style := StyleBoxTexture.new()
	style.texture = texture
	style.texture_margin_left = 10
	style.texture_margin_right = 10
	style.texture_margin_top = 8
	style.texture_margin_bottom = 8
	style.content_margin_left = 12
	style.content_margin_right = 12
	style.content_margin_top = 6
	style.content_margin_bottom = 6
	return style