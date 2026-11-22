extends SceneTree

var _main: Node
var _passed := 0
var _failed := 0


func _initialize() -> void:
	_main = load("res://scenes/main.tscn").instantiate()
	root.add_child(_main)
	_run()


func _check(value: bool, label: String) -> void:
	if value:
		_passed += 1
		print("PASS ", label)
	else:
		_failed += 1
		print("FAIL ", label)


func _wait(frames: int) -> void:
	for _index in frames:
		await process_frame


func _run() -> void:
	await _wait(5)
	var state = root.get_node("/root/GameState")
	state.reset_new_game()
	state.set_flag("power_on")
	_main._begin_session()
	await _wait(6)

	var world = _main.world
	var player = _main.player
	var enemy = world.enemy
	_check(world != null and player != null, "session_started")
	_check(enemy != null and enemy.active, "enemy_spawned_with_power")
	var darkness = world.get_node_or_null("Darkness")
	_check(darkness != null, "darkness_node_exists")

	# A1: flashlight toggles and drives darkness.
	_check(player.flashlight_on, "flashlight_starts_on")
	_main._toggle_flashlight()
	await _wait(4)
	_check(not player.flashlight_on, "flashlight_off_after_toggle")
	_check(darkness.is_dark(), "darkness_targets_dark")
	_check("ВЫКЛ" in _main.ui._status_text, "hud_reports_flashlight_off")
	_main._toggle_flashlight()
	await _wait(2)
	_check(player.flashlight_on and not darkness.is_dark(), "flashlight_back_on")

	# Sight range depends on the light.
	player.global_position = Vector2(700, 430)
	enemy.global_position = Vector2(790, 430)
	enemy.set_physics_process(false)
	await _wait(2)
	_check(enemy.can_see_player(), "enemy_sees_lit_player_at_90px")
	_main._toggle_flashlight()
	await _wait(2)
	_check(not enemy.can_see_player(), "enemy_misses_dark_player_at_90px")
	_main._toggle_flashlight()

	# A4: noise pulls her into a search.
	enemy.reset_to_home()
	enemy.global_position = Vector2(700, 430)
	enemy._pause_timer = 0.0
	world.emit_noise(Vector2(740, 430), 170.0)
	_check(enemy.is_searching(), "noise_starts_search")
	world.emit_noise(Vector2(700, 430), 60.0)
	_check(enemy.is_searching(), "quiet_noise_inside_radius")

	# A2: search times out and she goes back to patrol.
	player.global_position = Vector2(160, 840)
	var guard := 0
	while enemy.is_searching() and guard < 90:
		enemy._physics_process(0.1)
		guard += 1
	_check(not enemy.is_searching(), "search_times_out")
	_check(not enemy.is_chasing(), "search_is_not_chase")

	# A3: covers hide the player from sight, and exit restores.
	player.global_position = Vector2(1088, 270)
	var cover = world.get_interaction("cover_bed")
	_check(cover != null, "bed_cover_exists")
	enemy.global_position = Vector2(1088, 340)
	enemy.set_physics_process(false)
	_main._toggle_cover(cover)
	await _wait(3)
	_check(player.hiding, "player_enters_cover")
	_check(not enemy.can_see_player(), "enemy_cannot_see_hidden_player")
	_check(darkness.is_dark(), "cover_forces_flashlight_off")
	_check("УКРЫТИИ" in _main.ui._status_text, "hud_reports_cover")
	_check(cover.prompt == "Выйти из укрытия", "cover_prompt_switches")
	_main._toggle_cover(cover)
	await _wait(3)
	_check(not player.hiding, "player_leaves_cover")
	_check(player.flashlight_on, "flashlight_restored_after_cover")

	# Covers are wired into the world.
	_check(world.get_interaction("cover_cabinet") != null, "cabinet_cover_exists")

	print("Light: %d passed, %d failed" % [_passed, _failed])
	quit(1 if _failed > 0 else 0)