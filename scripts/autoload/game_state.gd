extends Node

signal state_changed

const SAVE_PATH := "user://savegame.json"
const START_OBJECTIVE := "Подойти к стойке регистратуры и открыть журнал приёма."
const START_CHECKPOINT := Vector2(160.0, 840.0)
const TRUTH_NOTES := [
	"archive_note_1", "archive_note_2", "archive_note_3",
	"basement_note", "boiler_note",
]

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
				if is_truth_unlocked():
					return "Открыть дверь «−1» в котельной или спуститься на −1 в лифте."
				if has_flag("basement_visited"):
					return "Обыскать архив и котельную: пять записок и вторая кассета."
				return "Спуститься в подвал по лестнице в холле."
			return "Прочитать карту наблюдения в палате 13."
		return "Найти служебный ключ в морге."
	if has_flag("fuse_taken"):
		return "Вставить предохранитель в электрощит в щитовой."
	if has_flag("reception_note_read"):
		return "Взять предохранитель из картотеки в приёмном покое."
	return START_OBJECTIVE


func is_truth_unlocked() -> bool:
	if not has_flag("tape_heard") or not has_flag("tape_second_heard"):
		return false
	for flag: String in TRUTH_NOTES:
		if not has_flag(flag):
			return false
	return true


func set_checkpoint(pos: Vector2) -> void:
	checkpoint = pos


func save_game(path: String = SAVE_PATH) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("Не удалось открыть файл сохранения: %s" % path)
		return false
	var data := SaveData.encode(
		flags, inventory, objective, checkpoint, play_time, ending
	)
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
	var decoded := SaveData.decode(
		JSON.parse_string(file.get_as_text()), START_OBJECTIVE, START_CHECKPOINT
	)
	if not bool(decoded["ok"]):
		push_warning("Файл сохранения повреждён.")
		return false
	flags = decoded["flags"]
	inventory.assign(decoded["inventory"])
	objective = str(decoded["objective"])
	if bool(decoded["rebuild_objective"]):
		objective = resolve_objective()
	checkpoint = decoded["checkpoint"]
	play_time = float(decoded["play_time"])
	ending = str(decoded["ending"])
	state_changed.emit()
	return true


func delete_save(path: String = SAVE_PATH) -> void:
	if has_save(path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))