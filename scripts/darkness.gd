class_name Darkness
extends Node2D

## Мир-оверлей тьмы: заливает карту чёрным и оставляет «дыру»
## вокруг игрока. Живёт в мировых координатах, поэтому радиус
## обзора масштабируется вместе с камерой.

const MAP_SIZE := Vector2(1536, 960)
const VISUAL_RADIUS := 150.0
const FADE_SPEED := 3.2

var target: Node2D
var strength := 0.0

var _target_strength := 0.0
var _texture: GradientTexture2D


func _ready() -> void:
	z_index = 900
	_texture = _build_texture()
	set_process(false)


func bind(node: Node2D) -> void:
	target = node
	set_process(true)
	queue_redraw()


func set_dark(value: bool) -> void:
	_target_strength = 1.0 if value else 0.0


func is_dark() -> bool:
	return _target_strength > 0.5


func _process(delta: float) -> void:
	if not is_instance_valid(target):
		return
	if absf(strength - _target_strength) > 0.002:
		strength = move_toward(strength, _target_strength, delta * FADE_SPEED)
	queue_redraw()


func _draw() -> void:
	if strength <= 0.005:
		return
	var center := target.global_position if is_instance_valid(target) else Vector2.ZERO
	var extent := VISUAL_RADIUS
	var shade := Color(0.0, 0.0, 0.0, strength)
	var top := maxf(center.y - extent, 0.0)
	var bottom := minf(center.y + extent, MAP_SIZE.y)
	var left := maxf(center.x - extent, 0.0)
	var right := minf(center.x + extent, MAP_SIZE.x)
	_draw_band(Rect2(0.0, 0.0, MAP_SIZE.x, top), shade)
	_draw_band(Rect2(0.0, bottom, MAP_SIZE.x, MAP_SIZE.y - bottom), shade)
	_draw_band(Rect2(0.0, top, left, bottom - top), shade)
	_draw_band(Rect2(right, top, MAP_SIZE.x - right, bottom - top), shade)
	draw_texture_rect(_texture,
		Rect2(center - Vector2(extent, extent), Vector2(extent, extent) * 2.0),
		false, Color(1.0, 1.0, 1.0, strength))


func _draw_band(rect: Rect2, color: Color) -> void:
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	draw_rect(rect, color)


func _build_texture() -> GradientTexture2D:
	var gradient := Gradient.new()
	gradient.set_color(0, Color(0.0, 0.0, 0.0, 0.0))
	gradient.set_color(1, Color(0.0, 0.0, 0.0, 1.0))
	gradient.add_point(0.48, Color(0.0, 0.0, 0.0, 0.0))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.width = 256
	texture.height = 256
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(1.0, 0.5)
	return texture