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
var _objective_panel: PanelContainer
var _inventory_panel: PanelContainer
var _status_label: Label
var _status_text := ""
var _settings: Control
var _settings_return := "menu"
var _fullscreen_button: Button
var _volume_slider: HSlider
var _volume_value: Label
var _player: Node2D


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
	_build_settings_panel()
	_build_ending_panel()
	UserSettings.changed.connect(_refresh_settings)
	show_menu(GameState.has_save())


func _process(delta: float) -> void:
	if _game == null or not _game.visible or not is_instance_valid(_player):
		return
	var screen_pos: Vector2 = get_viewport().get_canvas_transform() * _player.global_position
	var body := Rect2(screen_pos - Vector2(7, 22), Vector2(14, 28))
	_fade_panel(_objective_panel, body.intersects(_objective_panel.get_global_rect()), delta)
	_fade_panel(_inventory_panel, body.intersects(_inventory_panel.get_global_rect()), delta)
	if _prompt_panel.visible:
		_fade_panel(_prompt_panel, body.intersects(_prompt_panel.get_global_rect()), delta)


func _fade_panel(panel: Control, blocked: bool, delta: float) -> void:
	var target := 0.16 if blocked else 1.0
	panel.modulate.a = lerpf(panel.modulate.a, target, minf(1.0, delta * 9.0))


func set_player(player: Node2D) -> void:
	_player = player


func open_settings(from: String) -> void:
	_settings_return = from
	_refresh_settings()
	_settings.visible = true
	var back := _settings.find_child("Back", true, false) as Button
	if back != null:
		back.grab_focus()


func close_settings() -> void:
	_settings.visible = false
	if _settings_return == "pause":
		var pause_settings := _pause.find_child("Settings", true, false) as Button
		if pause_settings != null:
			pause_settings.grab_focus()


func is_settings_open() -> bool:
	return _settings != null and _settings.visible


func _refresh_settings() -> void:
	if _fullscreen_button == null:
		return
	_fullscreen_button.text = "Полный экран: %s" % ("вкл" if UserSettings.fullscreen else "выкл")
	var percent := roundi(UserSettings.master_volume * 100.0)
	_volume_slider.set_value_no_signal(float(percent))
	_volume_value.text = "%d%%" % percent


func _on_fullscreen_pressed() -> void:
	UserSettings.set_fullscreen(not UserSettings.fullscreen)


func _on_volume_changed(value: float) -> void:
	UserSettings.set_master_volume(value / 100.0)


func show_menu(has_save: bool) -> void:
	_menu.visible = true
	_game.visible = false
	_note.visible = false
	_choice.visible = false
	_pause.visible = false
	_settings.visible = false
	_ending.visible = false
	_continue_button.disabled = not has_save
	_new_button.grab_focus()


func show_game() -> void:
	_menu.visible = false
	_game.visible = true
	_note.visible = false
	_choice.visible = false
	_pause.visible = false
	_settings.visible = false
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


func set_status(flashlight_on: bool, sneaking: bool, hiding: bool) -> void:
	if _status_label == null:
		return
	var parts: Array[String] = []
	if hiding:
		parts.append("В УКРЫТИИ")
	else:
		parts.append("ФОНАРЬ: %s" % ("ВКЛ" if flashlight_on else "ВЫКЛ"))
		parts.append("ШАГ: %s" % ("ТИХИЙ" if sneaking else "ОБЫЧНЫЙ"))
	var text := "   ".join(parts)
	if text == _status_text:
		return
	_status_text = text
	_status_label.text = text


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
	_settings.visible = false
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
	objective_panel.position = Vector2(12, 12)
	objective_panel.size = Vector2(300, 62)
	objective_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_game.add_child(objective_panel)
	_objective_panel = objective_panel
	var objective_box := VBoxContainer.new()
	objective_box.add_theme_constant_override("separation", 1)
	objective_panel.add_child(objective_box)
	objective_box.add_child(_label("ЦЕЛЬ", 10, Color(0.66, 0.58, 0.4)))
	_objective_label = _label("", 12, Color(0.82, 0.81, 0.76))
	_objective_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_objective_label.custom_minimum_size = Vector2(272, 0)
	objective_box.add_child(_objective_label)

	var inventory_panel := _make_panel("panel")
	inventory_panel.name = "InventoryPanel"
	inventory_panel.anchor_left = 1.0
	inventory_panel.anchor_right = 1.0
	inventory_panel.anchor_top = 1.0
	inventory_panel.anchor_bottom = 1.0
	inventory_panel.offset_left = -172
	inventory_panel.offset_right = -12
	inventory_panel.offset_top = -78
	inventory_panel.offset_bottom = -12
	inventory_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_game.add_child(inventory_panel)
	_inventory_panel = inventory_panel
	var inventory_box := VBoxContainer.new()
	inventory_box.add_theme_constant_override("separation", 2)
	inventory_panel.add_child(inventory_box)
	inventory_box.add_child(_label("ПРЕДМЕТЫ", 9, Color(0.62, 0.64, 0.58)))
	var divider := TextureRect.new()
	divider.texture = DIVIDER_TEXTURE
	divider.custom_minimum_size = Vector2(0, 6)
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

	var status_panel := _make_panel("panel")
	status_panel.name = "StatusPanel"
	status_panel.anchor_top = 1.0
	status_panel.anchor_bottom = 1.0
	status_panel.offset_left = 12
	status_panel.offset_right = 200
	status_panel.offset_top = -34
	status_panel.offset_bottom = -12
	status_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_game.add_child(status_panel)
	_status_label = _label("", 9, Color(0.68, 0.7, 0.64))
	_status_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	status_panel.add_child(_status_label)

	_prompt_panel = _make_panel("panel")
	_prompt_panel.name = "Prompt"
	_prompt_panel.anchor_left = 0.5
	_prompt_panel.anchor_right = 0.5
	_prompt_panel.anchor_top = 1.0
	_prompt_panel.anchor_bottom = 1.0
	_prompt_panel.offset_left = -110
	_prompt_panel.offset_right = 110
	_prompt_panel.offset_top = -44
	_prompt_panel.offset_bottom = -16
	_prompt_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt_panel.visible = false
	_game.add_child(_prompt_panel)
	_prompt_label = _label("", 12, Color(0.9, 0.84, 0.66))
	_prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_prompt_panel.add_child(_prompt_label)

	_toast_panel = _make_panel("panel")
	_toast_panel.name = "Toast"
	_toast_panel.anchor_left = 0.5
	_toast_panel.anchor_right = 0.5
	_toast_panel.anchor_top = 1.0
	_toast_panel.anchor_bottom = 1.0
	_toast_panel.offset_left = -140
	_toast_panel.offset_right = 140
	_toast_panel.offset_top = -84
	_toast_panel.offset_bottom = -54
	_toast_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_toast_panel.visible = false
	_game.add_child(_toast_panel)
	_toast_label = _label("", 10, Color(0.78, 0.76, 0.68))
	_toast_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
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
	slot.custom_minimum_size = Vector2(30, 30)
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
	icon.position = Vector2(6, 6)
	icon.size = Vector2(18, 18)
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

	var frame := MarginContainer.new()
	frame.name = "Column"
	frame.anchor_right = 0.0
	frame.anchor_bottom = 1.0
	frame.offset_left = 38
	frame.offset_right = 300
	frame.offset_top = 18
	frame.offset_bottom = -16
	_menu.add_child(frame)

	var box := VBoxContainer.new()
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_theme_constant_override("separation", 4)
	frame.add_child(box)

	var logo := TextureRect.new()
	logo.texture = LOGO_TEXTURE
	logo.custom_minimum_size = Vector2(217, 64)
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(logo)

	var subtitle := _label("психологический хоррор", 11, Color(0.52, 0.54, 0.54))
	box.add_child(subtitle)

	var warning := _label("18+  ·  кровь  ·  смерть  ·  психологическое насилие", 9,
		Color(0.55, 0.33, 0.32))
	box.add_child(warning)

	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, 14)
	box.add_child(spacer)

	var button_box := VBoxContainer.new()
	button_box.add_theme_constant_override("separation", 3)
	button_box.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	box.add_child(button_box)

	_continue_button = _make_button("Продолжить", 180)
	_continue_button.pressed.connect(func() -> void: continue_requested.emit())
	button_box.add_child(_continue_button)

	_new_button = _make_button("Новая игра", 180)
	_new_button.pressed.connect(func() -> void: new_game_requested.emit())
	button_box.add_child(_new_button)

	var settings_button := _make_button("Настройки", 180)
	settings_button.pressed.connect(func() -> void: open_settings("menu"))
	button_box.add_child(settings_button)

	var quit_button := _make_button("Выход", 180)
	quit_button.pressed.connect(func() -> void: quit_requested.emit())
	button_box.add_child(quit_button)

	var spacer_bottom := Control.new()
	spacer_bottom.custom_minimum_size = Vector2(0, 10)
	box.add_child(spacer_bottom)

	var controls := _label("WASD / стрелки — идти   ·   E — действие\nEsc — пауза   ·   F11 — полный экран", 9,
		Color(0.42, 0.44, 0.45))
	box.add_child(controls)

	var version := FileAccess.get_file_as_string("res://VERSION").strip_edges()
	var version_label := _label("v%s   ·   локальная альфа" % version, 8, Color(0.32, 0.34, 0.35))
	box.add_child(version_label)


func _build_note_panel() -> void:
	_note = _make_overlay("Note")
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_note.add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(540, 320)
	var style := StyleBoxTexture.new()
	style.texture = NOTE_SHEET
	style.texture_margin_left = 12
	style.texture_margin_right = 12
	style.texture_margin_top = 12
	style.texture_margin_bottom = 12
	style.content_margin_left = 30
	style.content_margin_right = 30
	style.content_margin_top = 22
	style.content_margin_bottom = 20
	panel.add_theme_stylebox_override("panel", style)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	panel.add_child(box)
	_note_title = _label("", 14, Color(0.2, 0.16, 0.12))
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
	_note_body.custom_minimum_size = Vector2(460, 218)
	_note_body.add_theme_font_size_override("normal_font_size", 11)
	_note_body.add_theme_constant_override("line_separation", 1)
	_note_body.add_theme_color_override("default_color", Color(0.18, 0.15, 0.11))
	_note_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(_note_body)
	_note_close_button = _make_button("Закрыть  [E]", 130)
	_note_close_button.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_note_close_button.pressed.connect(func() -> void: note_closed.emit())
	box.add_child(_note_close_button)


func _build_choice_panel() -> void:
	_choice = _make_overlay("Choice")
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_choice.add_child(center)
	var panel := _make_panel("alert")
	panel.custom_minimum_size = Vector2(440, 0)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	panel.add_child(box)
	_choice_title = _label("", 15, Color(0.86, 0.66, 0.55))
	box.add_child(_choice_title)
	_choice_body = _label("", 12, Color(0.8, 0.79, 0.74))
	_choice_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_choice_body.custom_minimum_size = Vector2(392, 0)
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
	panel.custom_minimum_size = Vector2(300, 0)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.name = "VBox"
	box.add_theme_constant_override("separation", 6)
	panel.add_child(box)
	var title := _label("ПАУЗА", 22, Color(0.68, 0.66, 0.61))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)
	var resume := _make_button("Продолжить", 200)
	resume.name = "Resume"
	resume.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	resume.pressed.connect(func() -> void: resume_requested.emit())
	box.add_child(resume)
	var settings := _make_button("Настройки", 200)
	settings.name = "Settings"
	settings.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	settings.pressed.connect(func() -> void: open_settings("pause"))
	box.add_child(settings)
	var save := _make_button("Сохранить и выйти в меню", 200)
	save.name = "Menu"
	save.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	save.pressed.connect(func() -> void: menu_requested.emit())
	box.add_child(save)
	var quit := _make_button("Завершить игру", 200)
	quit.name = "Quit"
	quit.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	quit.pressed.connect(func() -> void: quit_requested.emit())
	box.add_child(quit)
	var hint := _label("Прогресс сохраняется автоматически", 10, Color(0.4, 0.41, 0.42))
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(hint)


func _build_settings_panel() -> void:
	_settings = _make_overlay("Settings")
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_settings.add_child(center)
	var panel := _make_panel("panel")
	panel.custom_minimum_size = Vector2(340, 0)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 7)
	panel.add_child(box)

	var title := _label("НАСТРОЙКИ", 20, Color(0.68, 0.66, 0.61))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)

	_fullscreen_button = _make_button("Полный экран: выкл", 240)
	_fullscreen_button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_fullscreen_button.pressed.connect(_on_fullscreen_pressed)
	box.add_child(_fullscreen_button)

	var volume_caption := _label("ГРОМКОСТЬ", 10, Color(0.62, 0.64, 0.58))
	volume_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(volume_caption)

	_volume_slider = HSlider.new()
	_volume_slider.min_value = 0.0
	_volume_slider.max_value = 100.0
	_volume_slider.step = 1.0
	_volume_slider.custom_minimum_size = Vector2(240, 16)
	_volume_slider.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_volume_slider.value_changed.connect(_on_volume_changed)
	_style_slider(_volume_slider)
	box.add_child(_volume_slider)

	_volume_value = _label("80%", 10, Color(0.75, 0.73, 0.66))
	_volume_value.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(_volume_value)

	var back := _make_button("Назад  [Esc]", 160)
	back.name = "Back"
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	back.pressed.connect(close_settings)
	box.add_child(back)

	var hint := _label("Настройки сохраняются автоматически", 9, Color(0.4, 0.41, 0.42))
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(hint)
	_refresh_settings()


func _build_ending_panel() -> void:
	_ending = _make_overlay("Ending")
	var center := CenterContainer.new()
	center.name = "Center"
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_ending.add_child(center)
	var panel := _make_panel("alert")
	panel.custom_minimum_size = Vector2(460, 0)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.name = "VBox"
	box.add_theme_constant_override("separation", 7)
	panel.add_child(box)
	_ending_title = _label("", 22, Color(0.72, 0.3, 0.27))
	_ending_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(_ending_title)
	_ending_body = RichTextLabel.new()
	_ending_body.bbcode_enabled = true
	_ending_body.fit_content = false
	_ending_body.scroll_active = false
	_ending_body.custom_minimum_size = Vector2(412, 190)
	_ending_body.add_theme_font_size_override("normal_font_size", 12)
	_ending_body.add_theme_constant_override("line_separation", 2)
	_ending_body.add_theme_color_override("default_color", Color(0.72, 0.71, 0.66))
	_ending_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(_ending_body)
	var buttons := HBoxContainer.new()
	buttons.name = "Buttons"
	buttons.add_theme_constant_override("separation", 6)
	buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_child(buttons)
	var restart := _make_button("Начать заново", 150)
	restart.name = "Restart"
	restart.pressed.connect(func() -> void: ending_restart_requested.emit())
	buttons.add_child(restart)
	var menu := _make_button("В главное меню", 150)
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
	style.content_margin_left = 10
	style.content_margin_right = 10
	style.content_margin_top = 8
	style.content_margin_bottom = 8
	panel.add_theme_stylebox_override("panel", style)
	return panel


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
	button.custom_minimum_size = Vector2(min_width, 26)
	button.add_theme_font_size_override("font_size", 12)
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


func _style_slider(slider: HSlider) -> void:
	var track := StyleBoxFlat.new()
	track.bg_color = Color(0.07, 0.08, 0.085)
	track.border_color = Color(0.26, 0.28, 0.27)
	track.set_border_width_all(2)
	track.content_margin_top = 4
	track.content_margin_bottom = 4
	slider.add_theme_stylebox_override("slider", track)

	var filled := StyleBoxFlat.new()
	filled.bg_color = Color(0.42, 0.14, 0.14)
	filled.border_color = Color(0.58, 0.22, 0.2)
	filled.set_border_width_all(2)
	filled.content_margin_top = 4
	filled.content_margin_bottom = 4
	slider.add_theme_stylebox_override("grabber_area", filled)
	slider.add_theme_stylebox_override("grabber_area_highlight", filled)

	var grabber := _make_grabber_texture()
	slider.add_theme_icon_override("grabber", grabber)
	slider.add_theme_icon_override("grabber_highlight", grabber)
	slider.add_theme_icon_override("grabber_disabled", grabber)


func _make_grabber_texture() -> ImageTexture:
	var image := Image.create(10, 16, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	for y in range(1, 15):
		for x in range(1, 9):
			image.set_pixel(x, y, Color(0.13, 0.14, 0.145))
	for y in range(2, 14):
		for x in range(2, 8):
			image.set_pixel(x, y, Color(0.74, 0.72, 0.64))
	for y in range(4, 12):
		image.set_pixel(4, y, Color(0.42, 0.14, 0.14))
		image.set_pixel(5, y, Color(0.42, 0.14, 0.14))
	return ImageTexture.create_from_image(image)


func _button_style(texture: Texture2D) -> StyleBoxTexture:
	var style := StyleBoxTexture.new()
	style.texture = texture
	style.texture_margin_left = 10
	style.texture_margin_right = 10
	style.texture_margin_top = 8
	style.texture_margin_bottom = 8
	style.content_margin_left = 12
	style.content_margin_right = 12
	style.content_margin_top = 4
	style.content_margin_bottom = 4
	return style