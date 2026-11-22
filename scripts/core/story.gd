class_name Story
extends RefCounted

## Тексты истории лежат в data/story.json, а не в коде сцен.
## Ключ — стабильный идентификатор записи; title и lines обязательны.

const PATH := "res://data/story.json"

static var _notes: Dictionary = {}
static var _loaded := false


static func note(key: String) -> Dictionary:
	_ensure_loaded()
	if not _notes.has(key):
		push_error("Story: нет текста с ключом «%s»" % key)
		return {"title": "", "text": ""}
	return _notes[key]


static func text(key: String) -> String:
	return str(note(key).get("text", ""))


static func title(key: String) -> String:
	return str(note(key).get("title", ""))


static func has(key: String) -> bool:
	_ensure_loaded()
	return _notes.has(key)


static func keys() -> Array:
	_ensure_loaded()
	return _notes.keys()


static func reload() -> void:
	_notes.clear()
	_loaded = false
	_ensure_loaded()


static func _ensure_loaded() -> void:
	if _loaded:
		return
	_loaded = true
	var raw := FileAccess.get_file_as_string(PATH)
	if raw.is_empty():
		push_error("Story: не удалось прочитать %s" % PATH)
		return
	var parsed: Variant = JSON.parse_string(raw)
	if not parsed is Dictionary or not (parsed as Dictionary).has("notes"):
		push_error("Story: %s должен содержать объект notes" % PATH)
		return
	var source: Dictionary = (parsed as Dictionary)["notes"]
	for key: Variant in source:
		var entry: Variant = source[key]
		if not entry is Dictionary:
			push_error("Story: запись «%s» должна быть объектом" % str(key))
			continue
		var fields: Dictionary = entry
		var lines: Variant = fields.get("lines", [])
		var body := ""
		if lines is Array:
			var parts: PackedStringArray = []
			for line: Variant in lines:
				parts.append(str(line))
			body = "\n".join(parts)
		elif lines is String:
			body = lines
		_notes[str(key)] = {
			"title": str(fields.get("title", "")),
			"text": body,
		}