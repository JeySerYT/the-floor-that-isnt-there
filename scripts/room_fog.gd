class_name RoomFog
extends Node2D

## Затемняет комнаты, в которых игрок ещё не был, и подписывает их.
## Узел живёт выше мебели, персонажей и маркеров взаимодействия,
## поэтому неисследованное помещение скрыто целиком.

const FADE_SPEED := 3.2

var rooms: Array = []
var _visited: Array[bool] = []
var _alpha: Array[float] = []


func configure(room_data: Array) -> void:
	rooms = room_data.duplicate(true)
	_visited.clear()
	_alpha.clear()
	for _room: Dictionary in rooms:
		_visited.append(false)
		_alpha.append(1.0)
	z_index = 9
	queue_redraw()


func set_visited(index: int, value: bool = true) -> void:
	if index < 0 or index >= _visited.size():
		return
	_visited[index] = value


func is_visited(index: int) -> bool:
	if index < 0 or index >= _visited.size():
		return true
	return _visited[index]


func snap() -> void:
	for index in _visited.size():
		_alpha[index] = 0.0 if _visited[index] else 1.0
	queue_redraw()


func _process(delta: float) -> void:
	var changed := false
	for index in _alpha.size():
		var target := 0.0 if _visited[index] else 1.0
		if absf(_alpha[index] - target) > 0.002:
			_alpha[index] = move_toward(_alpha[index], target, delta * FADE_SPEED)
			changed = true
	if changed:
		queue_redraw()


func _draw() -> void:
	var font := ThemeDB.fallback_font
	for index in rooms.size():
		var alpha := _alpha[index]
		if alpha <= 0.005:
			continue
		var rect: Rect2 = rooms[index]["rect"]
		draw_rect(rect, Color(0.008, 0.01, 0.012, 0.95 * alpha))
		draw_rect(rect, Color(0.16, 0.18, 0.19, 0.45 * alpha), false, 2.0)
		var label: Vector2 = rooms[index]["label"]
		var title := str(rooms[index]["title"])
		draw_string(font, label + Vector2(0, 4), title, HORIZONTAL_ALIGNMENT_LEFT,
			-1, 14, Color(0.4, 0.44, 0.45, 0.9 * alpha))
		draw_string(font, label + Vector2(0, 22), "не исследовано", HORIZONTAL_ALIGNMENT_LEFT,
			-1, 9, Color(0.28, 0.3, 0.31, 0.9 * alpha))