class_name Interaction
extends Node2D

const COLORS := {
	"note": Color(0.88, 0.84, 0.72),
	"item": Color(0.8, 0.65, 0.25),
	"device": Color(0.64, 0.2, 0.2),
	"window": Color(0.55, 0.68, 0.72),
	"elevator": Color(0.72, 0.72, 0.7),
	"cover": Color(0.5, 0.62, 0.5),
	"stairs": Color(0.66, 0.58, 0.38),
}

var interaction_id := ""
var prompt := ""
var kind := "note"
var enabled := true
var focused := false

var _time := 0.0


func configure(id: String, new_prompt: String, new_kind: String) -> void:
	interaction_id = id
	prompt = new_prompt
	kind = new_kind
	add_to_group("interactions")
	z_index = 5


func _process(delta: float) -> void:
	_time += delta
	if enabled:
		queue_redraw()


func set_focused(value: bool) -> void:
	if focused == value:
		return
	focused = value
	queue_redraw()


func _draw() -> void:
	if not enabled:
		return
	var color: Color = COLORS.get(kind, Color.WHITE)
	var bob := roundf(sin(_time * 2.6)) * 2.0
	if focused:
		draw_circle(Vector2(0, -18), 16.0, Color(color, 0.1))
	var base := Rect2(-8, -2 + bob, 16, 4)
	draw_rect(base, Color(0.03, 0.03, 0.04, 0.85))
	draw_rect(Rect2(-6, -6 + bob, 12, 10), Color(0.09, 0.1, 0.12, 0.95))
	draw_rect(Rect2(-4, -4 + bob, 8, 6), color)
	if focused:
		draw_rect(Rect2(-2, -28 + bob, 4, 4), Color(1.0, 0.92, 0.65))
		draw_rect(Rect2(-2, -22 + bob, 4, 8), Color(1.0, 0.92, 0.65))