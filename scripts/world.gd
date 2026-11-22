class_name HospitalWorld
extends Node2D

signal caught_player
signal room_entered(index: int)


var layout: WorldLayout
var MAP_SIZE := Vector2.ZERO
var TILE := 32
var ROOMS: Array[Dictionary] = []
var WALLS: Array[Rect2] = []
var DOORS: Array[Dictionary] = []
var PROPS: Array[Dictionary] = []
var DECALS: Array[Dictionary] = []
var ITEM_SPAWNS: Array[Dictionary] = []
var ELEVATOR_RECT := Rect2()

const FLOOR_CORRIDOR_A := preload("res://assets/textures/floors/floor_corridor_a.png")
const FLOOR_CORRIDOR_B := preload("res://assets/textures/floors/floor_corridor_b.png")
const WALL_CAP := preload("res://assets/textures/walls/wall_cap.png")
const WALL_PIPE := preload("res://assets/textures/walls/wall_pipe.png")
const WALL_FACE_A := preload("res://assets/textures/walls/wall_face_a.png")
const WALL_FACE_B := preload("res://assets/textures/walls/wall_face_b.png")
const WALL_FACE_C := preload("res://assets/textures/walls/wall_face_c.png")
const DOOR_ELEVATOR := preload("res://assets/textures/doors/door_elevator.png")
const DOOR_OPEN_DISTANCE := 66.0
const DOOR_CLOSE_DISTANCE := 82.0


class WallBand:
	extends Node2D

	const CELL := 32

	var rect := Rect2()
	var horizontal := true
	var cap: Texture2D
	var pipe: Texture2D
	var faces: Array[Texture2D] = []
	var pipe_column := -1

	func _draw() -> void:
		var origin := rect.position - position
		var start_x := int(origin.x)
		var start_y := int(origin.y)
		var end_x := int(origin.x + rect.size.x)
		var end_y := int(origin.y + rect.size.y)

		var y := start_y
		while y < end_y:
			var x := start_x
			while x < end_x:
				var texture: Texture2D = cap
				if not horizontal and pipe_column >= 0 and int(rect.position.x) == pipe_column:
					texture = pipe
				draw_texture_rect(texture, Rect2(x, y, CELL, CELL), false)
				x += CELL
			y += CELL

		var draw_faces := not faces.is_empty()
		if horizontal:
			if draw_faces:
				var face_x := start_x
				var face_index := 0
				while face_x < end_x:
					draw_texture_rect(faces[face_index % faces.size()],
						Rect2(face_x, end_y - 12, CELL, 12), false)
					face_x += CELL
					face_index += 1
			draw_rect(Rect2(origin.x, origin.y, rect.size.x, 3),
				Color(0.32, 0.35, 0.33, 0.5))
			draw_rect(Rect2(origin.x, end_y - 12, rect.size.x, 12),
				Color(0, 0, 0, 0.18))
		else:
			if draw_faces:
				var face_y := start_y
				var side_index := 0
				while face_y < end_y:
					draw_texture_rect(faces[side_index % faces.size()],
						Rect2(end_x - 12, face_y, 12, CELL), false)
					face_y += CELL
					side_index += 1
			draw_rect(Rect2(origin.x, origin.y, 3, rect.size.y),
				Color(0.32, 0.35, 0.33, 0.5))


var power_on := false
var boiler_blackout := false
var interactions: Array[Interaction] = []
var enemy: Stalker
var _player: Player
var _darkness: Darkness
var _flicker_lights: Array[PointLight2D] = []
var _stains: Array[Dictionary] = []
var _doors: Array[Dictionary] = []
var _items: Dictionary = {}
var _props: Dictionary = {}
var _fog: RoomFog
var _stairs_blocker: CollisionShape2D
var _current_room := -1
var _time := 0.0


func _ready() -> void:
	z_index = 0
	_load_layout()
	y_sort_enabled = true
	_build_collisions()
	_build_stains()
	if GameState.has_flag("power_on"):
		power_on = true
	boiler_blackout = GameState.has_flag("boiler_scene_seen")
	_build_walls()
	_build_doors()
	_build_props()
	_build_stairs()
	_build_items()
	_build_interactions()
	_build_fog()
	_build_darkness()
	if power_on:
		_unlock_stairs(false)
		_add_power_lights()
		_spawn_enemy()
	queue_redraw()


func _process(delta: float) -> void:
	_time += delta
	for index in _flicker_lights.size():
		var light := _flicker_lights[index]
		var wave := 0.78 + 0.16 * sin(_time * 8.0 + index * 1.7)
		if fmod(_time + index * 0.19, 6.0) < 0.09:
			wave *= 0.15
		light.energy = 0.58 * wave
	_update_doors()
	refresh_items()
	_mark_current_room()
	if is_instance_valid(enemy) and is_instance_valid(_player):
		var distance := enemy.global_position.distance_to(_player.global_position)
		var tension := clampf(1.0 - distance / 480.0, 0.0, 1.0)
		if enemy.is_chasing():
			tension = 1.0
		elif enemy.is_searching():
			tension = maxf(tension, 0.6)
		AudioManager.set_tension(tension)


func set_player(player: Player) -> void:
	_player = player
	if not player.noise_made.is_connected(_on_player_noise):
		player.noise_made.connect(_on_player_noise)
	if not player.flashlight_changed.is_connected(_on_flashlight_changed):
		player.flashlight_changed.connect(_on_flashlight_changed)
	if _darkness != null:
		_darkness.bind(player)
	_on_flashlight_changed(player.flashlight_on)
	_mark_current_room()


func _on_player_noise(position: Vector2, radius: float) -> void:
	emit_noise(position, radius)


func _on_flashlight_changed(on: bool) -> void:
	if _darkness != null:
		_darkness.set_dark(not on)


func emit_noise(position: Vector2, radius: float) -> void:
	if not is_instance_valid(enemy) or not enemy.active:
		return
	if enemy.global_position.distance_to(position) <= radius:
		enemy.hear(position)


func set_power_on() -> void:
	if power_on:
		return
	power_on = true
	_unlock_stairs(true)
	_add_power_lights()
	_spawn_enemy()
	queue_redraw()


func _load_layout() -> void:
	layout = WorldLayout.load_default()
	MAP_SIZE = layout.map_size
	TILE = layout.tile
	ELEVATOR_RECT = layout.elevator_rect
	ROOMS = layout.rooms
	WALLS = layout.walls
	DOORS = layout.doors
	PROPS = layout.props
	DECALS = layout.decals
	ITEM_SPAWNS = layout.item_spawns


func _build_stairs() -> void:
	var body := StaticBody2D.new()
	body.name = "StairsBlocker"
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	var shape := RectangleShape2D.new()
	shape.size = Vector2(64, 32)
	_stairs_blocker = CollisionShape2D.new()
	_stairs_blocker.shape = shape
	_stairs_blocker.position = Vector2(320, 944)
	body.add_child(_stairs_blocker)


func _unlock_stairs(announce: bool) -> void:
	if _props.has("stairs_board"):
		(_props["stairs_board"] as Sprite2D).visible = false
	if _props.has("stairs_sprite"):
		(_props["stairs_sprite"] as Sprite2D).visible = true
	var stairs := get_interaction("stairs_down")
	if stairs != null:
		stairs.prompt = "Спуститься в подвал"
	elif announce:
		_add_interaction("stairs_down", "Спуститься в подвал", "stairs", Vector2(320, 910))


func set_boiler_blackout() -> void:
	boiler_blackout = true
	for light: PointLight2D in _flicker_lights:
		if light.position.x > 600.0 and light.position.y > 1100.0:
			light.enabled = false


func refresh_items() -> void:
	for item_id: String in _items:
		var data: Dictionary = _items[item_id]
		var sprite: Sprite2D = data["sprite"]
		sprite.visible = not GameState.has_flag(str(data["flag"]))


func _build_collisions() -> void:
	var body := StaticBody2D.new()
	body.name = "Walls"
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	for wall: Rect2 in WALLS:
		var collision := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = wall.size
		collision.shape = shape
		collision.position = wall.get_center()
		body.add_child(collision)


func _build_walls() -> void:
	for wall: Rect2 in WALLS:
		var band := WallBand.new()
		band.name = "Wall"
		band.rect = wall
		band.horizontal = wall.size.x > wall.size.y
		band.cap = WALL_CAP
		band.pipe = WALL_PIPE
		band.faces = [WALL_FACE_A, WALL_FACE_B, WALL_FACE_C]
		band.pipe_column = 608
		band.position = Vector2(0, wall.end.y)
		add_child(band)


func _build_doors() -> void:
	var body := StaticBody2D.new()
	body.name = "Doors"
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	for door: Dictionary in DOORS:
		var rect: Rect2 = door["rect"]
		var frame := Sprite2D.new()
		frame.name = "DoorFrame"
		frame.texture = door["frame"]
		frame.centered = false
		frame.position = rect.position
		add_child(frame)

		var opening := Control.new()
		opening.name = "DoorOpening"
		opening.position = rect.position + Vector2(3, 3)
		opening.size = rect.size - Vector2(6, 6)
		opening.clip_contents = true
		opening.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(opening)

		var panels: Array = door["panels"]
		var panel_entries: Array[Dictionary] = []
		var cursor := 0.0
		for index in panels.size():
			var texture: Texture2D = panels[index]
			var width := texture.get_size().x
			var panel := Sprite2D.new()
			panel.name = "Panel"
			panel.texture = texture
			panel.centered = false
			panel.position = Vector2(cursor, 0)
			opening.add_child(panel)
			var open_x := cursor - width
			if panels.size() > 1 and index == panels.size() - 1:
				open_x = cursor + width
			panel_entries.append({
				"sprite": panel,
				"closed_x": cursor,
				"open_x": open_x,
			})
			cursor += width

		var shape := RectangleShape2D.new()
		shape.size = rect.size
		var collision := CollisionShape2D.new()
		collision.shape = shape
		collision.position = rect.get_center()
		body.add_child(collision)
		_doors.append({
			"panels": panel_entries,
			"collision": collision,
			"center": rect.get_center(),
			"open": false,
			"auto": bool(door.get("auto", true)),
			"tween": null,
		})

	var elevator := Sprite2D.new()
	elevator.name = "Elevator"
	elevator.texture = DOOR_ELEVATOR
	elevator.position = Vector2(ELEVATOR_RECT.get_center().x, ELEVATOR_RECT.end.y)
	elevator.offset = Vector2(0, -ELEVATOR_RECT.size.y * 0.5)
	add_child(elevator)
	var elevator_shape := RectangleShape2D.new()
	elevator_shape.size = ELEVATOR_RECT.size
	var elevator_collision := CollisionShape2D.new()
	elevator_collision.shape = elevator_shape
	elevator_collision.position = ELEVATOR_RECT.get_center()
	body.add_child(elevator_collision)


func _update_doors() -> void:
	for door: Dictionary in _doors:
		if not bool(door.get("auto", true)):
			continue
		var distance := 9999.0
		if is_instance_valid(_player):
			distance = _player.global_position.distance_to(door["center"])
		var is_open: bool = door["open"]
		var should_open := distance < (DOOR_CLOSE_DISTANCE if is_open else DOOR_OPEN_DISTANCE)
		if should_open == is_open:
			continue
		door["open"] = should_open
		var collision: CollisionShape2D = door["collision"]
		collision.set_deferred("disabled", should_open)
		if should_open:
			emit_noise(door["center"], Player.INTERACTION_NOISE)
		var previous: Variant = door["tween"]
		if previous is Tween and (previous as Tween).is_valid():
			(previous as Tween).kill()
		var tween := create_tween()
		tween.set_parallel(true)
		tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN_OUT)
		var panels: Array = door["panels"]
		for entry: Dictionary in panels:
			var panel: Sprite2D = entry["sprite"]
			tween.tween_property(panel, "position:x",
				entry["open_x"] if should_open else entry["closed_x"], 0.32)
		door["tween"] = tween


func _build_props() -> void:
	var body := StaticBody2D.new()
	body.name = "PropCollisions"
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	for prop: Dictionary in PROPS:
		var texture: Texture2D = prop["texture"]
		var pos: Vector2 = prop["pos"]
		var size := texture.get_size()
		var base := Node2D.new()
		base.name = "Prop"
		base.position = Vector2(pos.x + size.x * 0.5, pos.y + size.y)
		add_child(base)
		var sprite := Sprite2D.new()
		sprite.texture = texture
		sprite.offset = Vector2(0, -size.y * 0.5)
		base.add_child(sprite)
		if prop.has("id"):
			_props[str(prop["id"])] = sprite
			sprite.visible = not bool(prop.get("hidden", false))
		if not bool(prop.get("solid", true)):
			continue
		if size.x <= 6.0 or size.y <= 6.0:
			continue
		var shape := RectangleShape2D.new()
		shape.size = Vector2(maxf(size.x - 4.0, 4.0), maxf(size.y - 4.0, 4.0))
		var collision := CollisionShape2D.new()
		collision.shape = shape
		collision.position = pos + size * 0.5
		body.add_child(collision)


func _build_items() -> void:
	for entry: Dictionary in ITEM_SPAWNS:
		var texture: Texture2D = entry["texture"]
		var pos: Vector2 = entry["pos"]
		var size := texture.get_size()
		var sprite := Sprite2D.new()
		sprite.name = "Item_%s" % entry["id"]
		sprite.texture = texture
		sprite.position = Vector2(pos.x + size.x * 0.5, pos.y + size.y)
		sprite.offset = Vector2(0, -size.y * 0.5)
		sprite.z_index = 1
		add_child(sprite)
		_items[str(entry["id"])] = {
			"sprite": sprite,
			"flag": entry["flag"],
		}
	refresh_items()


func _build_fog() -> void:
	_fog = RoomFog.new()
	_fog.name = "RoomFog"
	add_child(_fog)
	_fog.configure(ROOMS)
	for index in ROOMS.size():
		if GameState.has_flag("visited_room_%d" % index):
			_fog.set_visited(index, true)
	_fog.snap()


func _build_darkness() -> void:
	_darkness = Darkness.new()
	_darkness.name = "Darkness"
	add_child(_darkness)


func _mark_current_room() -> void:
	if _fog == null or not is_instance_valid(_player):
		return
	var point := _player.global_position
	var index := -1
	for room_index in ROOMS.size():
		var rect: Rect2 = ROOMS[room_index]["rect"]
		if rect.has_point(point):
			index = room_index
			break
	if index == _current_room:
		return
	_current_room = index
	if index < 0:
		return
	if not _fog.is_visited(index):
		_fog.set_visited(index, true)
		GameState.set_flag("visited_room_%d" % index)
		queue_redraw()
	room_entered.emit(index)


func _build_stains() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 1313
	for room: Dictionary in ROOMS:
		var rect: Rect2 = room["rect"]
		for index in 9:
			_stains.append({
				"pos": Vector2(
					rng.randi_range(int(rect.position.x + 24), int(rect.end.x - 24)),
					rng.randi_range(int(rect.position.y + 24), int(rect.end.y - 24))
				),
				"size": Vector2(rng.randi_range(4, 16), rng.randi_range(2, 8)),
				"tone": rng.randf_range(0.03, 0.08),
			})


func _build_interactions() -> void:
	for entry: Dictionary in layout.interactions:
		var absent := str(entry.get("absent_flag", ""))
		if not absent.is_empty() and GameState.has_flag(absent):
			continue
		var prompt := str(entry.get("prompt", ""))
		if entry.has("prompt_unpowered") and not power_on:
			prompt = str(entry["prompt_unpowered"])
		_add_interaction(str(entry["id"]), prompt, str(entry["kind"]), entry["pos"])


func _add_interaction(id: String, prompt: String, kind: String, pos: Vector2) -> void:
	var interaction := Interaction.new()
	interaction.name = "Interaction_%s" % id
	interaction.position = pos
	interaction.configure(id, prompt, kind)
	add_child(interaction)
	interactions.append(interaction)


func get_interaction(id: String) -> Interaction:
	for interaction in interactions:
		if interaction.interaction_id == id:
			return interaction
	return null


func _spawn_enemy() -> void:
	if is_instance_valid(enemy):
		return
	enemy = Stalker.new()
	enemy.name = "TheNurse"
	enemy.caught_player.connect(_on_enemy_caught)
	add_child(enemy)
	enemy.activate(Vector2(420, 436))
	if is_instance_valid(_player):
		enemy.set_physics_process(true)


func _on_enemy_caught() -> void:
	caught_player.emit()


func enemy_chase_position() -> Vector2:
	if is_instance_valid(enemy):
		return enemy.global_position
	return Vector2.ZERO


func _add_power_lights() -> void:
	if not _flicker_lights.is_empty():
		return
	var positions := [
		Vector2(320, 372), Vector2(840, 372), Vector2(1380, 372),
		Vector2(320, 680), Vector2(840, 680), Vector2(1380, 680),
		Vector2(160, 1024), Vector2(560, 1024), Vector2(960, 1024), Vector2(1200, 1024),
		Vector2(200, 1184), Vector2(440, 1184),
	]
	if not boiler_blackout:
		positions.append(Vector2(760, 1184))
		positions.append(Vector2(1000, 1184))
	for pos: Vector2 in positions:
		var light := PointLight2D.new()
		light.name = "CeilingLight"
		light.position = pos
		light.texture = _make_light_texture()
		light.texture_scale = 1.9
		light.energy = 0.55
		light.color = Color(0.78, 0.85, 0.74)
		add_child(light)
		_flicker_lights.append(light)


func _make_light_texture() -> GradientTexture2D:
	var gradient := Gradient.new()
	gradient.set_color(0, Color(1, 1, 1, 0.85))
	gradient.set_color(1, Color(1, 1, 1, 0))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.width = 256
	texture.height = 256
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(1.0, 0.5)
	return texture


func _hash01(x: int, y: int, salt: int) -> float:
	var h := x * 374761393 + y * 668265263 + salt * 144269504
	h = (h ^ (h >> 13)) * 1274126177
	h &= 0x7fffffff
	return float(h % 10007) / 10007.0


func _floor_textures(kind: String) -> Array:
	return layout.floor_sets.get(kind, layout.floor_sets.get("corridor", []))


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, MAP_SIZE), Color(0.012, 0.014, 0.017))
	for room: Dictionary in ROOMS:
		_draw_room(room)
	for stain: Dictionary in _stains:
		var pos: Vector2 = stain["pos"]
		var size: Vector2 = stain["size"]
		var tone: float = stain["tone"]
		draw_rect(Rect2(pos, size), Color(tone, tone * 1.03, tone * 1.1, 0.55))
	_draw_door_thresholds()
	for wall: Rect2 in WALLS:
		_draw_wall_shadow(wall)
	_draw_decals()
	_draw_prop_shadows()
	_draw_labels()
	_draw_door_labels()
	_draw_blood_text()


func _draw_room(room: Dictionary) -> void:
	var rect: Rect2 = room["rect"]
	var tiles := _floor_textures(str(room["floor"]))
	var start_x := int(rect.position.x)
	var start_y := int(rect.position.y)
	var end_x := int(rect.end.x)
	var end_y := int(rect.end.y)
	for y in range(start_y, end_y, TILE):
		for x in range(start_x, end_x, TILE):
			var index := int(_hash01(x, y, 11) * float(tiles.size()))
			index = clampi(index, 0, tiles.size() - 1)
			var texture: Texture2D = tiles[index]
			draw_texture_rect(texture, Rect2(x, y, TILE, TILE), false)
	# room outline keeps the floor grid legible against the walls
	draw_rect(rect, Color(0.22, 0.26, 0.27, 0.25), false, 2.0)


func _draw_door_thresholds() -> void:
	for door: Dictionary in DOORS:
		var rect: Rect2 = door["rect"]
		var x := int(rect.position.x)
		var index := 0
		while x < int(rect.end.x):
			var texture: Texture2D = FLOOR_CORRIDOR_A if index % 2 == 0 else FLOOR_CORRIDOR_B
			draw_texture_rect(texture, Rect2(x, rect.position.y, TILE, TILE), false)
			x += TILE
			index += 1
		draw_rect(Rect2(rect.position.x, rect.end.y - 3, rect.size.x, 3), Color(0, 0, 0, 0.32))
	# stairwell opening between the hall and the basement
	for index in 2:
		var texture: Texture2D = FLOOR_CORRIDOR_A if index % 2 == 0 else FLOOR_CORRIDOR_B
		draw_texture_rect(texture, Rect2(288 + index * TILE, 928, TILE, TILE), false)


func _draw_wall_shadow(wall: Rect2) -> void:
	if wall.size.x > wall.size.y:
		if wall.end.y < MAP_SIZE.y:
			draw_rect(Rect2(wall.position.x, wall.end.y, wall.size.x, 8), Color(0, 0, 0, 0.26))
	else:
		if wall.end.x < MAP_SIZE.x:
			draw_rect(Rect2(wall.end.x, wall.position.y, 8, wall.size.y), Color(0, 0, 0, 0.26))


func _draw_decals() -> void:
	for decal: Dictionary in DECALS:
		var texture: Texture2D = decal["texture"]
		var pos: Vector2 = decal["pos"]
		draw_texture(texture, pos)


func _draw_prop_shadows() -> void:
	for prop: Dictionary in PROPS:
		var texture: Texture2D = prop["texture"]
		var pos: Vector2 = prop["pos"]
		var size := texture.get_size()
		var width := maxf(size.x - 12.0, 2.0)
		draw_rect(Rect2(pos.x + 6, pos.y + size.y - 5, width, 5), Color(0, 0, 0, 0.22))


func _draw_labels() -> void:
	var font := ThemeDB.fallback_font
	for index in ROOMS.size():
		if _fog != null and not _fog.is_visited(index):
			continue
		var title: String = ROOMS[index]["title"]
		var pos: Vector2 = ROOMS[index]["label"]
		draw_string(font, pos, title, HORIZONTAL_ALIGNMENT_LEFT, -1, 14,
			Color(0.47, 0.51, 0.53, 0.78))
		draw_rect(Rect2(pos.x, pos.y + 6, maxf(title.length() * 8.0, 36.0), 2),
			Color(0.32, 0.12, 0.12, 0.6))


func _draw_door_labels() -> void:
	var font := ThemeDB.fallback_font
	for door: Dictionary in DOORS:
		var rect: Rect2 = door["rect"]
		var text: String = door["label"]
		var text_size := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 8)
		var width := maxf(text_size.x + 10.0, 28.0)
		var y: float = rect.position.y - 11.0 if bool(door.get("label_above", false)) else rect.end.y + 1.0
		var pos := Vector2(rect.get_center().x - width * 0.5, y)
		draw_rect(Rect2(pos, Vector2(width, 11)), Color(0.055, 0.07, 0.07, 0.88))
		draw_rect(Rect2(pos, Vector2(width, 11)), Color(0.28, 0.32, 0.3, 0.9), false, 1.0)
		draw_string(font, pos + Vector2(5, 8), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 8,
			Color(0.62, 0.64, 0.58, 0.92))


func _draw_blood_text() -> void:
	if power_on:
		var font := ThemeDB.fallback_font
		draw_string(font, Vector2(1352, 560), "ОНА УЖЕ ВНУТРИ",
			HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.44, 0.04, 0.04, 0.85))