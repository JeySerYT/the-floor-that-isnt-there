extends Node

signal changed

const SETTINGS_PATH := "user://settings.json"
const DEFAULT_VOLUME := 0.8
const WINDOWED_SIZE := Vector2i(1280, 720)
const BASE_SIZE := Vector2i(640, 360)

var fullscreen := true
var master_volume := DEFAULT_VOLUME


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	load_settings()
	fullscreen = true
	call_deferred("apply")


func load_settings(path: String = SETTINGS_PATH) -> void:
	fullscreen = true
	master_volume = DEFAULT_VOLUME
	if not FileAccess.file_exists(path):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not parsed is Dictionary:
		return
	fullscreen = bool(parsed.get("fullscreen", true))
	master_volume = clampf(float(parsed.get("master_volume", DEFAULT_VOLUME)), 0.0, 1.0)


func save_settings(path: String = SETTINGS_PATH) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify({
		"fullscreen": fullscreen,
		"master_volume": master_volume,
	}))
	file.close()
	return true


func set_fullscreen(value: bool) -> void:
	fullscreen = value
	apply_fullscreen()
	save_settings()
	changed.emit()


func toggle_fullscreen() -> void:
	var window := get_window()
	var is_fullscreen := window != null and window.mode == Window.MODE_FULLSCREEN
	set_fullscreen(not is_fullscreen)


func set_master_volume(value: float) -> void:
	master_volume = clampf(value, 0.0, 1.0)
	apply_volume()
	save_settings()
	changed.emit()


func apply() -> void:
	apply_fullscreen()
	apply_volume()


func apply_fullscreen() -> void:
	if DisplayServer.get_name() == "headless":
		return
	var window := get_window()
	if window == null:
		return
	if fullscreen:
		window.mode = Window.MODE_FULLSCREEN
		await get_tree().process_frame
		if fullscreen:
			_fit_screen(window)
	else:
		window.mode = Window.MODE_WINDOWED
		window.content_scale_size = BASE_SIZE
		window.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
		window.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_FRACTIONAL
		window.size = WINDOWED_SIZE


func _fit_screen(window: Window) -> void:
	var screen := DisplayServer.screen_get_size(
		DisplayServer.window_get_current_screen(window.get_window_id()))
	if screen.x < BASE_SIZE.x or screen.y < BASE_SIZE.y:
		return
	var scale := maxi(1, mini(
		floori(screen.x / float(BASE_SIZE.x)),
		floori(screen.y / float(BASE_SIZE.y))))
	var content := Vector2i(ceili(screen.x / float(scale)), ceili(screen.y / float(scale)))
	if content.x * scale == screen.x and content.y * scale == screen.y:
		window.content_scale_size = content
		window.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP
		window.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_INTEGER
	else:
		window.content_scale_size = BASE_SIZE
		window.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
		window.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_FRACTIONAL


func apply_volume() -> void:
	var bus := AudioServer.get_bus_index("Master")
	if bus < 0:
		return
	AudioServer.set_bus_mute(bus, master_volume <= 0.001)
	AudioServer.set_bus_volume_db(bus, linear_to_db(maxf(master_volume, 0.001)))