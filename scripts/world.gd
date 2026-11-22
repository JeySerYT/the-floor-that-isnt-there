class_name HospitalWorld
extends Node2D

signal caught_player

const MAP_SIZE := Vector2(1536, 960)
const TILE := 32

const ROOMS := [
	{"title": "ПРИЁМНОЕ", "rect": Rect2(32, 32, 608, 288), "label": Vector2(56, 84), "floor": "lobby"},
	{"title": "ЩИТОВАЯ", "rect": Rect2(672, 32, 288, 288), "label": Vector2(696, 84), "floor": "utility"},
	{"title": "ПАЛАТА 13", "rect": Rect2(992, 32, 512, 288), "label": Vector2(1016, 84), "floor": "ward"},
	{"title": "КОРИДОР", "rect": Rect2(32, 352, 1472, 160), "label": Vector2(660, 388), "floor": "corridor"},
	{"title": "ХОЛЛ", "rect": Rect2(32, 544, 608, 384), "label": Vector2(56, 596), "floor": "hall"},
	{"title": "МОРГ", "rect": Rect2(672, 544, 288, 384), "label": Vector2(696, 596), "floor": "morgue"},
	{"title": "ЛИФТОВОЙ ХОЛЛ", "rect": Rect2(992, 544, 512, 384), "label": Vector2(1016, 596), "floor": "lift"},
]

const WALLS := [
	Rect2(0, 0, 1536, 32),
	Rect2(0, 928, 1536, 32),
	Rect2(0, 0, 32, 960),
	Rect2(1504, 0, 32, 960),
	Rect2(640, 32, 32, 288),
	Rect2(960, 32, 32, 288),
	Rect2(32, 320, 256, 32),
	Rect2(352, 320, 416, 32),
	Rect2(832, 320, 352, 32),
	Rect2(1248, 320, 256, 32),
	Rect2(32, 512, 256, 32),
	Rect2(352, 512, 416, 32),
	Rect2(832, 512, 352, 32),
	Rect2(1248, 512, 256, 32),
	Rect2(640, 544, 32, 384),
	Rect2(960, 544, 32, 384),
]

const FLOOR_CORRIDOR_A := preload("res://assets/textures/floors/floor_corridor_a.png")
const FLOOR_CORRIDOR_B := preload("res://assets/textures/floors/floor_corridor_b.png")
const FLOOR_CORRIDOR_C := preload("res://assets/textures/floors/floor_corridor_c.png")
const FLOOR_CORRIDOR_STAIN := preload("res://assets/textures/floors/floor_corridor_stain.png")
const FLOOR_CORRIDOR_WET := preload("res://assets/textures/floors/floor_corridor_wet.png")
const FLOOR_GRATE := preload("res://assets/textures/floors/floor_grate.png")
const FLOOR_LOBBY := preload("res://assets/textures/floors/floor_lobby.png")
const FLOOR_MORGUE := preload("res://assets/textures/floors/floor_morgue.png")
const FLOOR_WARD := preload("res://assets/textures/floors/floor_ward.png")

const WALL_CAP := preload("res://assets/textures/walls/wall_cap.png")
const WALL_PIPE := preload("res://assets/textures/walls/wall_pipe.png")

const DOOR_DOUBLE := preload("res://assets/textures/doors/door_double.png")
const DOOR_ELEVATOR := preload("res://assets/textures/doors/door_elevator.png")
const DOOR_MORGUE := preload("res://assets/textures/doors/door_morgue.png")
const DOOR_WARD := preload("res://assets/textures/doors/door_ward.png")

const PROP_RECEPTION_DESK := preload("res://assets/textures/furniture/prop_reception_desk.png")
const PROP_FILING_CABINET := preload("res://assets/textures/furniture/prop_filing_cabinet.png")
const PROP_CHAIR := preload("res://assets/textures/furniture/prop_chair.png")
const PROP_WAITING_BENCH := preload("res://assets/textures/furniture/prop_waiting_bench.png")
const PROP_HOSPITAL_BED := preload("res://assets/textures/furniture/prop_hospital_bed.png")
const PROP_METAL_CABINET := preload("res://assets/textures/furniture/prop_metal_cabinet.png")
const PROP_MORGUE_TABLE := preload("res://assets/textures/furniture/prop_morgue_table.png")
const PROP_BODY_BAG := preload("res://assets/textures/furniture/prop_body_bag.png")
const PROP_GENERATOR := preload("res://assets/textures/devices/prop_generator.png")
const PROP_FUSEBOX := preload("res://assets/textures/devices/prop_fusebox.png")
const PROP_IV_STAND := preload("res://assets/textures/devices/prop_iv_stand.png")
const PROP_WHEELCHAIR := preload("res://assets/textures/devices/prop_wheelchair.png")
const PROP_ELEVATOR_PANEL := preload("res://assets/textures/devices/prop_elevator_panel.png")
const PROP_BOARDED_DOOR := preload("res://assets/textures/barriers/prop_boarded_door.png")
const PROP_OBSERVATION_WINDOW := preload("res://assets/textures/barriers/prop_observation_window.png")

const DECAL_BLOOD_POOL := preload("res://assets/textures/decals/decal_blood_pool.png")
const DECAL_BLOOD_SMEAR := preload("res://assets/textures/decals/decal_blood_smear.png")
const DECAL_MOLD := preload("res://assets/textures/decals/decal_mold.png")
const DECAL_STAIN := preload("res://assets/textures/decals/decal_stain.png")
const DECAL_WALL_CRACK := preload("res://assets/textures/decals/decal_wall_crack.png")
const DECAL_CRACK := preload("res://assets/textures/decals/decal_crack.png")

const ITEM_CASSETTE := preload("res://assets/textures/items/item_cassette.png")
const ITEM_FUSE := preload("res://assets/textures/items/item_fuse.png")
const ITEM_KEY := preload("res://assets/textures/items/item_key.png")
const ITEM_NOTE := preload("res://assets/textures/items/item_note.png")

const CORRIDOR_FLOORS := [
	FLOOR_CORRIDOR_A, FLOOR_CORRIDOR_A, FLOOR_CORRIDOR_B,
	FLOOR_CORRIDOR_C, FLOOR_CORRIDOR_WET, FLOOR_CORRIDOR_STAIN,
]
const LOBBY_FLOORS := [
	FLOOR_LOBBY, FLOOR_LOBBY, FLOOR_LOBBY, FLOOR_LOBBY, FLOOR_CORRIDOR_A,
]
const WARD_FLOORS := [
	FLOOR_WARD, FLOOR_WARD, FLOOR_WARD, FLOOR_WARD, FLOOR_CORRIDOR_A,
]
const MORGUE_FLOORS := [
	FLOOR_MORGUE, FLOOR_MORGUE, FLOOR_MORGUE, FLOOR_CORRIDOR_C,
]
const UTILITY_FLOORS := [
	FLOOR_GRATE, FLOOR_GRATE, FLOOR_CORRIDOR_B,
]
const HALL_FLOORS := [
	FLOOR_LOBBY, FLOOR_LOBBY, FLOOR_LOBBY, FLOOR_CORRIDOR_B, FLOOR_CORRIDOR_STAIN,
]
const LIFT_FLOORS := [
	FLOOR_LOBBY, FLOOR_CORRIDOR_A, FLOOR_CORRIDOR_B,
]

const DOORS := [
	{"rect": Rect2(288, 320, 64, 32), "texture": DOOR_WARD},
	{"rect": Rect2(768, 320, 64, 32), "texture": DOOR_WARD},
	{"rect": Rect2(1184, 320, 64, 32), "texture": DOOR_DOUBLE},
	{"rect": Rect2(288, 512, 64, 32), "texture": DOOR_WARD},
	{"rect": Rect2(768, 512, 64, 32), "texture": DOOR_MORGUE},
	{"rect": Rect2(1184, 512, 64, 32), "texture": DOOR_WARD},
]

const PROPS := [
	{"texture": PROP_RECEPTION_DESK, "pos": Vector2(440, 176)},
	{"texture": PROP_FILING_CABINET, "pos": Vector2(88, 160)},
	{"texture": PROP_CHAIR, "pos": Vector2(464, 144)},
	{"texture": PROP_METAL_CABINET, "pos": Vector2(836, 56)},
	{"texture": PROP_FUSEBOX, "pos": Vector2(844, 166)},
	{"texture": PROP_GENERATOR, "pos": Vector2(912, 204)},
	{"texture": PROP_HOSPITAL_BED, "pos": Vector2(1040, 164)},
	{"texture": PROP_HOSPITAL_BED, "pos": Vector2(1240, 164)},
	{"texture": PROP_IV_STAND, "pos": Vector2(1200, 190)},
	{"texture": PROP_OBSERVATION_WINDOW, "pos": Vector2(1432, 36)},
	{"texture": PROP_MORGUE_TABLE, "pos": Vector2(704, 620)},
	{"texture": PROP_MORGUE_TABLE, "pos": Vector2(832, 620)},
	{"texture": PROP_BODY_BAG, "pos": Vector2(720, 628)},
	{"texture": PROP_BODY_BAG, "pos": Vector2(848, 628)},
	{"texture": PROP_METAL_CABINET, "pos": Vector2(832, 704)},
	{"texture": PROP_RECEPTION_DESK, "pos": Vector2(140, 680)},
	{"texture": PROP_WAITING_BENCH, "pos": Vector2(64, 640)},
	{"texture": PROP_WAITING_BENCH, "pos": Vector2(64, 760)},
	{"texture": PROP_WHEELCHAIR, "pos": Vector2(360, 820)},
	{"texture": PROP_BOARDED_DOOR, "pos": Vector2(280, 896)},
	{"texture": PROP_ELEVATOR_PANEL, "pos": Vector2(1468, 764)},
]

const DECALS := [
	{"texture": DECAL_WALL_CRACK, "pos": Vector2(80, 68)},
	{"texture": DECAL_STAIN, "pos": Vector2(480, 88)},
	{"texture": DECAL_MOLD, "pos": Vector2(1056, 72)},
	{"texture": DECAL_BLOOD_SMEAR, "pos": Vector2(592, 468)},
	{"texture": DECAL_BLOOD_POOL, "pos": Vector2(232, 560)},
	{"texture": DECAL_CRACK, "pos": Vector2(1330, 700)},
]

var power_on := false
var interactions: Array[Interaction] = []
var enemy: Stalker
var _player: Player
var _flicker_lights: Array[PointLight2D] = []
var _stains: Array[Dictionary] = []
var _time := 0.0


func _ready() -> void:
	z_index = 0
	_build_collisions()
	_build_stains()
	if GameState.has_flag("power_on"):
		power_on = true
	_build_interactions()
	if power_on:
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
	if is_instance_valid(enemy) and is_instance_valid(_player):
		var distance := enemy.global_position.distance_to(_player.global_position)
		AudioManager.set_tension(clampf(1.0 - distance / 480.0, 0.0, 1.0))


func set_player(player: Player) -> void:
	_player = player


func set_power_on() -> void:
	if power_on:
		return
	power_on = true
	_add_power_lights()
	_spawn_enemy()
	queue_redraw()


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
	if not GameState.has_flag("intro_note_read"):
		_add_interaction("lobby_note", "Прочитать объявление", "note", Vector2(184, 712))
	if not GameState.has_flag("reception_note_read"):
		_add_interaction("reception_note", "Открыть журнал приёма", "note", Vector2(500, 278))
	if not GameState.has_flag("fuse_taken"):
		_add_interaction("fuse", "Взять предохранитель", "item", Vector2(112, 208))
	_add_interaction("fusebox", "Осмотреть электрощит", "device", Vector2(860, 182))
	if not GameState.has_flag("key_taken"):
		_add_interaction("morgue_key", "Взять служебный ключ", "item", Vector2(840, 734))
	if not GameState.has_flag("tape_heard"):
		_add_interaction("tape", "Прослушать запись", "note", Vector2(664, 470))
	if not GameState.has_flag("ward_chart_read"):
		_add_interaction("ward_chart", "Прочитать карту наблюдения", "note", Vector2(1400, 252))
	_add_interaction("window", "Подойти к смотровому стеклу", "window", Vector2(1464, 104))
	_add_interaction("elevator", "Вызвать лифт", "elevator", Vector2(1456, 764))


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
	enemy.activate(Vector2(1300, 444))
	enemy.caught_player.connect(_on_enemy_caught)
	add_child(enemy)
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
	]
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
	match kind:
		"corridor":
			return CORRIDOR_FLOORS
		"lobby":
			return LOBBY_FLOORS
		"ward":
			return WARD_FLOORS
		"morgue":
			return MORGUE_FLOORS
		"utility":
			return UTILITY_FLOORS
		"hall":
			return HALL_FLOORS
		"lift":
			return LIFT_FLOORS
		_:
			return CORRIDOR_FLOORS


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, MAP_SIZE), Color(0.012, 0.014, 0.017))
	for room: Dictionary in ROOMS:
		_draw_room(room)
	for stain: Dictionary in _stains:
		var pos: Vector2 = stain["pos"]
		var size: Vector2 = stain["size"]
		var tone: float = stain["tone"]
		draw_rect(Rect2(pos, size), Color(tone, tone * 1.03, tone * 1.1, 0.55))
	for wall: Rect2 in WALLS:
		_draw_wall(wall)
	for wall: Rect2 in WALLS:
		_draw_wall_shadow(wall)
	_draw_doors()
	_draw_decals()
	_draw_props()
	_draw_items()
	_draw_labels()
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


func _draw_wall(wall: Rect2) -> void:
	var x := int(wall.position.x)
	var y := int(wall.position.y)
	var end_x := int(wall.end.x)
	var end_y := int(wall.end.y)
	while y < end_y:
		var cell_x := x
		while cell_x < end_x:
			var texture := WALL_CAP
			if wall.size.y > wall.size.x and x == 640:
				texture = WALL_PIPE
			draw_texture_rect(texture, Rect2(cell_x, y, TILE, TILE), false)
			cell_x += TILE
		y += TILE
	if wall.size.x > wall.size.y:
		draw_rect(Rect2(wall.position, Vector2(wall.size.x, 4)), Color(0.3, 0.33, 0.31, 0.45))
		draw_rect(Rect2(wall.position.x, wall.end.y - 4, wall.size.x, 4), Color(0, 0, 0, 0.35))
	else:
		draw_rect(Rect2(wall.position, Vector2(4, wall.size.y)), Color(0.3, 0.33, 0.31, 0.45))
		draw_rect(Rect2(wall.end.x - 4, wall.position.y, 4, wall.size.y), Color(0, 0, 0, 0.35))


func _draw_wall_shadow(wall: Rect2) -> void:
	if wall.size.x > wall.size.y:
		if wall.end.y < MAP_SIZE.y:
			draw_rect(Rect2(wall.position.x, wall.end.y, wall.size.x, 8), Color(0, 0, 0, 0.26))
	else:
		if wall.end.x < MAP_SIZE.x:
			draw_rect(Rect2(wall.end.x, wall.position.y, 8, wall.size.y), Color(0, 0, 0, 0.26))


func _draw_doors() -> void:
	for door: Dictionary in DOORS:
		var rect: Rect2 = door["rect"]
		var texture: Texture2D = door["texture"]
		draw_texture_rect(texture, rect, false)
		draw_rect(Rect2(rect.position.x, rect.end.y - 2, rect.size.x, 2), Color(0, 0, 0, 0.45))
	draw_texture(DOOR_ELEVATOR, Vector2(1400, 612))


func _draw_decals() -> void:
	for decal: Dictionary in DECALS:
		var texture: Texture2D = decal["texture"]
		var pos: Vector2 = decal["pos"]
		draw_texture(texture, pos)


func _draw_props() -> void:
	for prop: Dictionary in PROPS:
		var texture: Texture2D = prop["texture"]
		var pos: Vector2 = prop["pos"]
		draw_texture(texture, pos)


func _draw_items() -> void:
	if not GameState.has_flag("lobby_note_read"):
		draw_texture(ITEM_NOTE, Vector2(176, 704))
	if not GameState.has_flag("reception_note_read"):
		draw_texture(ITEM_NOTE, Vector2(492, 270))
	if not GameState.has_flag("fuse_taken"):
		draw_texture(ITEM_FUSE, Vector2(104, 200))
	if not GameState.has_flag("key_taken"):
		draw_texture(ITEM_KEY, Vector2(832, 726))
	if not GameState.has_flag("tape_heard"):
		draw_texture(ITEM_CASSETTE, Vector2(656, 462))
	if not GameState.has_flag("ward_chart_read"):
		draw_texture(ITEM_NOTE, Vector2(1392, 244))


func _draw_labels() -> void:
	var font := ThemeDB.fallback_font
	for room: Dictionary in ROOMS:
		var title: String = room["title"]
		var pos: Vector2 = room["label"]
		draw_string(font, pos, title, HORIZONTAL_ALIGNMENT_LEFT, -1, 14,
			Color(0.47, 0.51, 0.53, 0.78))
		draw_rect(Rect2(pos.x, pos.y + 6, maxf(title.length() * 8.0, 36.0), 2),
			Color(0.32, 0.12, 0.12, 0.6))


func _draw_blood_text() -> void:
	if power_on:
		var font := ThemeDB.fallback_font
		draw_string(font, Vector2(1352, 560), "ОНА УЖЕ ВНУТРИ",
			HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.44, 0.04, 0.04, 0.85))