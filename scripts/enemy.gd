class_name Stalker
extends CharacterBody2D

signal caught_player

const CHASE_SPEED := 132.0
const WANDER_SPEED := 34.0
const SIGHT_RANGE := 380.0
const NORMAL_SHEET := preload("res://assets/textures/characters/nurse_sheet.png")
const CHASE_SHEET := preload("res://assets/textures/characters/nurse_chase_sheet.png")
const FRAME_W := 24
const FRAME_H := 38
const DIRECTIONS := ["down", "left", "right", "up"]

var active := false
var _player: Player
var _home := Vector2(1300, 428)
var _wander_target := Vector2.ZERO
var _wander_timer := 0.0
var _catch_cooldown := 0.0
var _time := 0.0
var _chasing := false
var _facing_row := 0
var _sprite: AnimatedSprite2D
var _normal_frames: SpriteFrames
var _chase_frames: SpriteFrames


func _ready() -> void:
	add_to_group("enemies")
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	z_index = 0
	_build_sprite()
	_build_collision()
	_build_light()
	_player = get_tree().get_first_node_in_group("player") as Player
	visible = false
	set_physics_process(false)


func activate(start_position: Vector2) -> void:
	_home = start_position
	global_position = start_position
	active = true
	visible = true
	set_physics_process(true)
	AudioManager.play_sfx("stinger", -12.0, 0.05)


func deactivate() -> void:
	active = false
	visible = false
	set_physics_process(false)


func reset_to_home() -> void:
	global_position = _home
	velocity = Vector2.ZERO
	_catch_cooldown = 2.5


func _physics_process(delta: float) -> void:
	if not active:
		return
	_time += delta
	_catch_cooldown = maxf(_catch_cooldown - delta, 0.0)

	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Player
		return

	var distance := global_position.distance_to(_player.global_position)
	var can_see := distance < SIGHT_RANGE and _has_line_of_sight()
	_set_chasing(can_see)

	if can_see:
		velocity = global_position.direction_to(_player.global_position) * CHASE_SPEED
		if distance < 22.0 and _catch_cooldown <= 0.0:
			_catch_cooldown = 4.0
			caught_player.emit()
	else:
		_wander_timer -= delta
		if _wander_timer <= 0.0 or global_position.distance_to(_wander_target) < 16.0:
			_wander_timer = randf_range(2.0, 4.5)
			_wander_target = _home + Vector2(randf_range(-120, 120), randf_range(-44, 44))
		velocity = global_position.direction_to(_wander_target) * WANDER_SPEED

	move_and_slide()
	_play_animation()


func _has_line_of_sight() -> bool:
	var params := PhysicsRayQueryParameters2D.create(global_position, _player.global_position, 1)
	params.exclude = [get_rid(), _player.get_rid()]
	var hit := get_world_2d().direct_space_state.intersect_ray(params)
	return hit.is_empty()


func _set_chasing(value: bool) -> void:
	if _chasing == value:
		return
	_chasing = value
	_sprite.sprite_frames = _chase_frames if value else _normal_frames
	_sprite.play("idle_" + DIRECTIONS[_facing_row])


func _play_animation() -> void:
	if velocity.length_squared() > 16.0:
		_facing_row = _row_for(velocity)
	var anim: String = ("walk_" if velocity.length_squared() > 16.0 else "idle_") + str(DIRECTIONS[_facing_row])
	if String(_sprite.animation) != anim:
		_sprite.play(anim)


func _row_for(direction: Vector2) -> int:
	if absf(direction.x) > absf(direction.y):
		return 2 if direction.x > 0.0 else 1
	return 0 if direction.y > 0.0 else 3


func _build_sprite() -> void:
	_normal_frames = _build_frames(NORMAL_SHEET)
	_chase_frames = _build_frames(CHASE_SHEET)
	_sprite = AnimatedSprite2D.new()
	_sprite.name = "Sprite"
	_sprite.sprite_frames = _normal_frames
	_sprite.offset = Vector2(0, -19)
	_sprite.play("idle_down")
	add_child(_sprite)


func _build_frames(sheet: Texture2D) -> SpriteFrames:
	var frames := SpriteFrames.new()
	frames.remove_animation("default")
	for row in DIRECTIONS.size():
		var idle: String = "idle_" + str(DIRECTIONS[row])
		frames.add_animation(idle)
		frames.set_animation_loop(idle, false)
		frames.set_animation_speed(idle, 1.0)
		frames.add_frame(idle, _atlas(sheet, row, 0))
		var walk: String = "walk_" + str(DIRECTIONS[row])
		frames.add_animation(walk)
		frames.set_animation_loop(walk, true)
		frames.set_animation_speed(walk, 8.0)
		for column in range(1, 5):
			frames.add_frame(walk, _atlas(sheet, row, column))
	return frames


func _atlas(sheet: Texture2D, row: int, column: int) -> AtlasTexture:
	var atlas := AtlasTexture.new()
	atlas.atlas = sheet
	atlas.region = Rect2(column * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H)
	return atlas


func _build_collision() -> void:
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 12.0
	shape.shape = circle
	shape.position = Vector2(0, 6)
	add_child(shape)


func _build_light() -> void:
	var gradient := Gradient.new()
	gradient.set_color(0, Color(0.7, 0.08, 0.06, 0.75))
	gradient.set_color(1, Color(0.25, 0.0, 0.0, 0.0))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.width = 128
	texture.height = 128
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(1.0, 0.5)
	var light := PointLight2D.new()
	light.texture = texture
	light.texture_scale = 1.6
	light.energy = 0.55
	light.color = Color(0.8, 0.18, 0.16)
	add_child(light)