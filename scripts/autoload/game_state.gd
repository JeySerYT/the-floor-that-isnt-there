extends Node

signal state_changed

const SAVE_PATH := "user://savegame.json"
const SAVE_VERSION := 3
const WORLD_SCALE := 2
const START_OBJECTIVE := "Подойти к стойке регистратуры и открыть журнал приёма."
const START_CHECKPOINT := Vector2(160.0, 840.0)

var flags: Dictionary = {}
var inventory: Array[String] = []
var objective := START_OBJECTIVE
var checkpoint := START_CHECKPOINT
var play_time := 0.0
var ending := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


func reset_new_game() -> void:
	flags.clear()
	inventory.clear()
	objective = START_OBJECTIVE
	checkpoint = START_CHECKPOINT
	play_time = 0.0
	ending = ""
	state_changed.emit()


func set_flag(flag: String, value: bool = true) -> void:
	flags[flag] = value


func has_flag(flag: String) -> bool:
	return bool(flags.get(flag, false))


func add_item(item: String) -> bool:
	if item.is_empty() or inventory.has(item):
		return false
	inventory.append(item)
	state_changed.emit()
	return true


func remove_item(item: String) -> bool:
	var index := inventory.find(item)
	if index == -1:
		return false
	inventory.remove_at(index)
	state_changed.emit()
	return true


func has_item(item: String) -> bool:
	return inventory.has(item)


func set_objective(text: String) -> void:
	if text == objective:
		return
	objective = text
	state_changed.emit()


func resolve_objective() -> String:
	if has_flag("power_on"):
		if has_flag("key_taken"):
			if has_flag("ward_chart_read"):
				return "Вернуться к смотровому стеклу в палате 13 или вызвать лифт."
			return "Прочитать карту наблюдения в палате 13."
		return "Найти служебный ключ в морге."
	if has_flag("fuse_taken"):
		return "Вставить предохранитель в электрощит в щитовой."
	if has_flag("reception_note_read"):
		return "Взять предохранитель из картотеки в приёмном покое."
	return START_OBJECTIVE


func set_checkpoint(pos: Vector2) -> void:
	checkpoint = pos


func save_game(path: String = SAVE_PATH) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("Не удалось открыть файл сохранения: %s" % path)
		return false
	var data := {
		"version": SAVE_VERSION,
		"flags": flags,
		"inventory": inventory,
		"objective": objective,
		"checkpoint": [checkpoint.x, checkpoint.y],
		"play_time": play_time,
		"ending": ending,
	}
	file.store_string(JSON.stringify(data, "\t"))
	return true


func has_save(path: String = SAVE_PATH) -> bool:
	return FileAccess.file_exists(path)


func load_game(path: String = SAVE_PATH) -> bool:
	if not has_save(path):
		return false
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return false
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_warning("Файл сохранения повреждён.")
		return false
	var data: Dictionary = parsed
	var save_version := int(data.get("version", 1))
	flags = {}
	var loaded_flags: Variant = data.get("flags", {})
	if loaded_flags is Dictionary:
		for key: Variant in loaded_flags:
			flags[str(key)] = loaded_flags[key]
	inventory.clear()
	var loaded_inventory: Variant = data.get("inventory", [])
	if loaded_inventory is Array:
		for item: Variant in loaded_inventory:
			var item_name := str(item)
			if not item_name.is_empty() and not inventory.has(item_name):
				inventory.append(item_name)
	objective = str(data.get("objective", START_OBJECTIVE))
	var loaded_checkpoint: Variant = data.get("checkpoint", [])
	checkpoint = START_CHECKPOINT
	if loaded_checkpoint is Array and loaded_checkpoint.size() >= 2:
		checkpoint = Vector2(float(loaded_checkpoint[0]), float(loaded_checkpoint[1]))
		if save_version < 2:
			# Saves from the 320x180 build stored half-size world coordinates.
			checkpoint *= WORLD_SCALE
	if save_version < 3:
		# Old saves keep a vague objective text; rebuild it from the flags.
		objective = resolve_objective()
	play_time = float(data.get("play_time", 0.0))
	ending = str(data.get("ending", ""))
	state_changed.emit()
	return true


func delete_save(path: String = SAVE_PATH) -> void:
	if has_save(path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))