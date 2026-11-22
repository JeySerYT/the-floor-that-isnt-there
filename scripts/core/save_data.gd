class_name SaveData
extends RefCounted

## Формат сохранения и миграции старых версий.
## Рантайм игры живёт в GameState; этот класс знает только про JSON-поля.

const VERSION := 3
## Сейвы из сборки 320×180 хранили половинные координаты мира.
const WORLD_SCALE := 2


static func encode(
	flags: Dictionary,
	inventory: Array[String],
	objective: String,
	checkpoint: Vector2,
	play_time: float,
	ending: String
) -> Dictionary:
	return {
		"version": VERSION,
		"flags": flags,
		"inventory": inventory,
		"objective": objective,
		"checkpoint": [checkpoint.x, checkpoint.y],
		"play_time": play_time,
		"ending": ending,
	}


static func decode(parsed: Variant, default_objective: String, default_checkpoint: Vector2) -> Dictionary:
	if not parsed is Dictionary:
		return {"ok": false, "error": "not_a_dictionary"}
	var raw: Dictionary = parsed
	var version := int(raw.get("version", 1))

	var flags: Dictionary = {}
	var loaded_flags: Variant = raw.get("flags", {})
	if loaded_flags is Dictionary:
		for key: Variant in loaded_flags:
			flags[str(key)] = loaded_flags[key]

	var inventory: Array[String] = []
	var loaded_inventory: Variant = raw.get("inventory", [])
	if loaded_inventory is Array:
		for item: Variant in loaded_inventory:
			var item_name := str(item)
			if not item_name.is_empty() and not inventory.has(item_name):
				inventory.append(item_name)

	var checkpoint := _parse_checkpoint(raw.get("checkpoint", []), default_checkpoint)
	if version < 2:
		checkpoint *= WORLD_SCALE

	return {
		"ok": true,
		"error": "",
		"version": version,
		"flags": flags,
		"inventory": inventory,
		"objective": str(raw.get("objective", default_objective)),
		"checkpoint": checkpoint,
		"play_time": float(raw.get("play_time", 0.0)),
		"ending": str(raw.get("ending", "")),
		## До v3 цель была размытой; её нужно пересобрать из флагов.
		"rebuild_objective": version < 3,
	}


static func _parse_checkpoint(value: Variant, fallback: Vector2) -> Vector2:
	if value is Array and (value as Array).size() >= 2:
		var parts: Array = value
		return Vector2(float(parts[0]), float(parts[1]))
	return fallback