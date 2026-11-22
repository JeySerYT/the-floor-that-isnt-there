class_name WorldLayout
extends RefCounted

## Разметка мира: комнаты, стены, двери, мебель, предметы и интеракции.
## Живёт в data/world_layout.json, чтобы уровень правился без правки кода.

const PATH := "res://data/world_layout.json"

var map_size := Vector2(1536, 1280)
var tile := 32
var elevator_rect := Rect2()
var floor_sets: Dictionary = {}
var rooms: Array[Dictionary] = []
var walls: Array[Rect2] = []
var doors: Array[Dictionary] = []
var props: Array[Dictionary] = []
var decals: Array[Dictionary] = []
var item_spawns: Array[Dictionary] = []
var interactions: Array[Dictionary] = []

var _textures: Dictionary = {}


static func load_default() -> WorldLayout:
	var layout := WorldLayout.new()
	if not layout.load_from(PATH):
		push_error("WorldLayout: не удалось прочитать %s" % PATH)
	return layout


func load_from(path: String) -> bool:
	var raw := FileAccess.get_file_as_string(path)
	if raw.is_empty():
		return false
	var parsed: Variant = JSON.parse_string(raw)
	if not parsed is Dictionary:
		return false
	var data: Dictionary = parsed
	map_size = _vec(data.get("map_size", []))
	tile = int(data.get("tile", 32))
	elevator_rect = _rect(data.get("elevator_rect", []))
	_read_floor_sets(data.get("floor_sets", {}))
	for entry: Variant in data.get("rooms", []):
		rooms.append(_room(entry))
	for entry: Variant in data.get("walls", []):
		walls.append(_rect(entry))
	for entry: Variant in data.get("doors", []):
		doors.append(_door(entry))
	for entry: Variant in data.get("props", []):
		props.append(_prop(entry))
	for entry: Variant in data.get("decals", []):
		decals.append(_prop(entry))
	for entry: Variant in data.get("item_spawns", []):
		item_spawns.append(_item(entry))
	for entry: Variant in data.get("interactions", []):
		interactions.append(_interaction(entry))
	return true


func _read_floor_sets(source: Variant) -> void:
	if not source is Dictionary:
		return
	var sets: Dictionary = source
	for kind: Variant in sets:
		var textures: Array[Texture2D] = []
		for value: Variant in sets[kind]:
			var texture := _texture(value)
			if texture != null:
				textures.append(texture)
		floor_sets[str(kind)] = textures


func _room(source: Variant) -> Dictionary:
	var entry: Dictionary = source
	return {
		"title": str(entry.get("title", "")),
		"rect": _rect(entry.get("rect", [])),
		"label": _vec(entry.get("label", [])),
		"floor": str(entry.get("floor", "corridor")),
	}


func _door(source: Variant) -> Dictionary:
	var entry: Dictionary = source
	var panels: Array[Texture2D] = []
	for value: Variant in entry.get("panels", []):
		var texture := _texture(value)
		if texture != null:
			panels.append(texture)
	return {
		"rect": _rect(entry.get("rect", [])),
		"frame": _texture(entry.get("frame", "")),
		"panels": panels,
		"label": str(entry.get("label", "")),
		"auto": bool(entry.get("auto", true)),
		"label_above": bool(entry.get("label_above", false)),
	}


func _prop(source: Variant) -> Dictionary:
	var entry: Dictionary = source
	var prop := {
		"texture": _texture(entry.get("texture", "")),
		"pos": _vec(entry.get("pos", [])),
		"solid": bool(entry.get("solid", true)),
		"hidden": bool(entry.get("hidden", false)),
	}
	if entry.has("id"):
		prop["id"] = str(entry["id"])
	return prop


func _item(source: Variant) -> Dictionary:
	var entry: Dictionary = source
	return {
		"id": str(entry.get("id", "")),
		"flag": str(entry.get("flag", "")),
		"texture": _texture(entry.get("texture", "")),
		"pos": _vec(entry.get("pos", [])),
	}


func _interaction(source: Variant) -> Dictionary:
	var entry: Dictionary = source
	var interaction := {
		"id": str(entry.get("id", "")),
		"prompt": str(entry.get("prompt", "")),
		"kind": str(entry.get("kind", "note")),
		"pos": _vec(entry.get("pos", [])),
	}
	if entry.has("absent_flag"):
		interaction["absent_flag"] = str(entry["absent_flag"])
	if entry.has("prompt_unpowered"):
		interaction["prompt_unpowered"] = str(entry["prompt_unpowered"])
	return interaction


func _texture(value: Variant) -> Texture2D:
	var path := str(value)
	if path.is_empty():
		push_error("WorldLayout: пустой путь текстуры")
		return null
	if _textures.has(path):
		return _textures[path]
	var resource := load(path)
	if resource is not Texture2D:
		push_error("WorldLayout: не текстура — %s" % path)
		return null
	_textures[path] = resource
	return resource


static func _vec(value: Variant) -> Vector2:
	if value is Array and (value as Array).size() >= 2:
		var parts: Array = value
		return Vector2(float(parts[0]), float(parts[1]))
	return Vector2.ZERO


static func _rect(value: Variant) -> Rect2:
	if value is Array and (value as Array).size() >= 4:
		var parts: Array = value
		return Rect2(float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
	return Rect2()