class_name Player
extends CharacterBody2D

const SPEED := 168.0
const INTERACTION_RANGE := 50.0
const MAP_BOUNDS := Rect2(32, 32, 1472, 896)

const SHEET := preload("res://assets/textures/characters/player_sheet.png")
const FRAME_W := 20
const FRAME_H := 32
const DIRECTIONS := ["down", "left", "right", "up"]

@onready var flashlight: PointLight2D = $Flashlight
@onready var camera: Camera2D = $Camera2D

var _sprite: AnimatedSprite2D
var _facing := Vector2.DOWN
var _facing_row := 0
var _walk_time := 0.0
var _footstep_timer := 0.0
var _focused_interaction: Interaction


func _ready() -> void:
	add_to_group("player")
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	z_index = 4
	_build_sprite()
	_build_flashlight_texture()
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = 1536
	camera.limit_bottom = 960
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 6.0
	camera.reset_smoothing()


func _physics_process(delta: float) -> void:
	var input := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = input * SPEED
	var moving := input.length_squared() > 0.01
	if moving:
		_facing = input.normalized()
		_facing_row = _row_for(_facing)
		_walk_time += delta
		_footstep_timer -= delta
		if _footstep_timer <= 0.0:
			_footstep_timer = 0.34
			AudioManager.play_sfx("step", -22.0, 0.12)
	else:
		_walk_time = 0.0
		_footstep_timer = 0.0
	flashlight.position = _facing * 22.0
	_play_animation(moving)
	move_and_slide()
	global_position.x = clampf(global_position.x, MAP_BOUNDS.position.x, MAP_BOUNDS.end.x)
	global_position.y = clampf(global_position.y, MAP_BOUNDS.position.y, MAP_BOUNDS.end.y)


func find_nearest_interaction() -> Interaction:
	var best: Interaction = null
	var best_distance := INTERACTION_RANGE
	for node: Node in get_tree().get_nodes_in_group("interactions"):
		var interaction := node as Interaction
		if interaction == null or not interaction.enabled:
			continue
		var distance := global_position.distance_to(interaction.global_position)
		if distance < best_distance:
			best_distance = distance
			best = interaction
	if _focused_interaction != best:
		if is_instance_valid(_focused_interaction):
			_focused_interaction.set_focused(false)
		_focused_interaction = best
		if is_instance_valid(_focused_interaction):
			_focused_interaction.set_focused(true)
	return best


func respawn_at(pos: Vector2) -> void:
	global_position = pos
	velocity = Vector2.ZERO
	camera.reset_smoothing()
	_play_animation(false)
	AudioManager.play_sfx("heartbeat", -8.0)


func _row_for(direction: Vector2) -> int:
	if absf(direction.x) > absf(direction.y):
		return 2 if direction.x > 0.0 else 1
	return 0 if direction.y > 0.0 else 3


func _play_animation(moving: bool) -> void:
	var anim: String = ("walk_" if moving else "idle_") + str(DIRECTIONS[_facing_row])
	if String(_sprite.animation) != anim:
		_sprite.play(anim)


func _build_sprite() -> void:
	_sprite = AnimatedSprite2D.new()
	_sprite.name = "Sprite"
	_sprite.sprite_frames = _build_frames()
	_sprite.offset = Vector2(0, -16)
	_sprite.play("idle_down")
	add_child(_sprite)


func _build_frames() -> SpriteFrames:
	var frames := SpriteFrames.new()
	frames.remove_animation("default")
	for row in DIRECTIONS.size():
		var idle: String = "idle_" + str(DIRECTIONS[row])
		frames.add_animation(idle)
		frames.set_animation_loop(idle, false)
		frames.set_animation_speed(idle, 1.0)
		frames.add_frame(idle, _atlas(row, 0))
		var walk: String = "walk_" + str(DIRECTIONS[row])
		frames.add_animation(walk)
		frames.set_animation_loop(walk, true)
		frames.set_animation_speed(walk, 8.0)
		for column in range(1, 5):
			frames.add_frame(walk, _atlas(row, column))
	return frames


func _atlas(row: int, column: int) -> AtlasTexture:
	var atlas := AtlasTexture.new()
	atlas.atlas = SHEET
	atlas.region = Rect2(column * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H)
	return atlas


func _build_flashlight_texture() -> void:
	var gradient := Gradient.new()
	gradient.set_color(0, Color(1.0, 0.92, 0.74, 1.0))
	gradient.set_color(1, Color(1.0, 0.76, 0.48, 0.0))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.width = 256
	texture.height = 256
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(1.0, 0.5)
	flashlight.texture = texture
	flashlight.texture_scale = 2.3
	flashlight.energy = 1.25
	flashlight.color = Color(1.0, 0.9, 0.72)