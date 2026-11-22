extends Node

signal changed

const SETTINGS_PATH := "user://settings.json"
const DEFAULT_VOLUME := 0.8
const WINDOWED_SIZE := Vector2i(1280, 720)

var fullscreen := false
var master_volume := DEFAULT_VOLUME


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	load_settings()
	call_deferred("apply")


func load_settings(path: String = SETTINGS_PATH) -> void:
	fullscreen = false
	master_volume = DEFAULT_VOLUME
	if not FileAccess.file_exists(path):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not parsed is Dictionary:
		return
	fullscreen = bool(parsed.get("fullscreen", false))
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
	if fullscreen == value:
		return
	fullscreen = value
	apply_fullscreen()
	save_settings()
	changed.emit()


func toggle_fullscreen() -> void:
	set_fullscreen(not fullscreen)


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
	else:
		window.mode = Window.MODE_WINDOWED
		window.size = WINDOWED_SIZE


func apply_volume() -> void:
	var bus := AudioServer.get_bus_index("Master")
	if bus < 0:
		return
	AudioServer.set_bus_mute(bus, master_volume <= 0.001)
	AudioServer.set_bus_volume_db(bus, linear_to_db(maxf(master_volume, 0.001)))