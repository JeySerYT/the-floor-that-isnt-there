extends SceneTree

var _main: Node
var _passed := 0
var _failed := 0
var _had_save := false


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


func _read(id: String) -> void:
	var target = _main.world.get_interaction(id)
	_check(target != null, "interaction_%s" % id)
	if target == null:
		return
	_main._interact(target)
	_check(_main.state == "note", "note_open_%s" % id)
	_main._close_note()
	_check(_main.state == "playing", "note_closed_%s" % id)


func _run() -> void:
	await _wait(5)
	var state = root.get_node("/root/GameState")
	_had_save = state.has_save()
	state.reset_new_game()
	_main._begin_session()
	await _wait(4)
	var world = _main.world
	var player = _main.player
	_check(world != null and player != null, "session_started")
	_check(world.ROOMS.size() == 10, "ten_rooms")
	_check(world.get_interaction("stairs_down") != null, "stairs_down_exists")
	_check(world.get_interaction("stairs_up") != null, "stairs_up_exists")
	_check(world.get_interaction("boiler_door") != null, "boiler_door_exists")
	_check(world.enemy == null, "no_enemy_before_power")

	# Stairs are locked without power.
	_main._try_stairs_down()
	_check(_main.state == "note", "stairs_locked_note")
	_check(not state.has_flag("basement_visited"), "no_basement_without_power")
	_main._close_note()
	_check(player.global_position.y < 960.0, "player_stays_upstairs")

	# Restore power and check the basement door opens.
	state.set_flag("power_on")
	world.set_power_on()
	await _wait(3)
	_check(world.enemy != null and world.enemy.active, "enemy_spawned_with_power")
	world.enemy.set_physics_process(false)
	world.enemy.global_position = Vector2(160, 120)
	_check(world.get_interaction("stairs_down").prompt == "Спуститься в подвал",
		"stairs_prompt_unlocked")

	_main._try_stairs_down()
	await _wait(3)
	_check(player.global_position.y > 960.0, "player_in_basement")
	_check(state.has_flag("basement_visited"), "basement_visited_flag")
	_check(world.get_interaction("archive_note_1") != null, "archive_note_1_exists")
	_check(world.get_interaction("tape_second") != null, "tape_second_exists")

	# Partial collection does not unlock the third ending.
	state.set_flag("key_taken")
	state.set_flag("ward_chart_read")
	state.set_flag("tape_heard")
	_read("archive_note_1")
	_read("archive_note_2")
	_check(not state.is_truth_unlocked(), "truth_locked_partial")
	_main._interact(world.get_interaction("boiler_door"))
	_check(_main.state == "note", "boiler_door_locked_note")
	_main._close_note()

	# Enter the boiler: the light goes out once and the nurse moves in.
	player.global_position = Vector2(800, 1180)
	await _wait(5)
	_check(state.has_flag("boiler_scene_seen"), "boiler_scene_flag")
	_check(_main.state == "note", "boiler_scene_note")
	_check(not player.flashlight_on, "boiler_scene_kills_flashlight")
	_check(world.boiler_blackout, "boiler_lights_off")
	_main._close_note()
	_check(_main.state == "playing", "boiler_scene_closed")

	# Finish the collection.
	_read("archive_note_3")
	_read("basement_note")
	_read("boiler_note")
	_read("tape_second")
	_check(state.is_truth_unlocked(), "truth_unlocked")
	_check(state.objective.contains("−1"), "objective_truth")
	_check(_main.ui._inventory_icons["cassette"].visible, "hud_cassette_icon")

	# The elevator gains the third option.
	_main._try_elevator()
	_check(_main.state == "choice", "elevator_choice")
	_check(_main.ui._choice_box.get_child_count() == 3, "elevator_three_options")
	_main._close_choice()

	# Stairs up return to the hall.
	_main._use_stairs_up()
	await _wait(2)
	_check(player.global_position.y < 960.0, "player_back_in_hall")
	_main._try_stairs_down()
	await _wait(2)

	# The boiler door leads to the truth ending with credits.
	_main._interact(world.get_interaction("boiler_door"))
	_check(_main.state == "choice", "boiler_door_choice")
	await _wait(1)
	_check(_main.ui._choice_box.get_child_count() == 2, "boiler_door_two_options")
	_main._on_choice_selected(0)
	await _wait(3)
	_check(state.ending == "truth", "truth_ending")
	_check(_main.state == "ending", "ending_state")
	_check(_main.ui._ending.visible, "ending_panel_visible")
	_check(_main.ui._credits_button.visible, "credits_button_visible")
	_main.ui.show_credits()
	_check(_main.ui._credits.visible, "credits_panel_visible")
	_main.ui.hide_credits()
	_check(_main.ui._ending.visible and not _main.ui._credits.visible, "credits_close_returns")

	if not _had_save:
		state.delete_save()

	print("Basement: %d passed, %d failed" % [_passed, _failed])
	quit(1 if _failed > 0 else 0)