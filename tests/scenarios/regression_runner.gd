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
	await _wait(4)
	var state = root.get_node("/root/GameState")
	state.reset_new_game()
	_main._on_new_game()
	await _wait(3)
	_main._close_note()
	await _wait(3)
	var world = _main.world

	_check(world.ROOMS.size() == 10, "ten_rooms")
	_check(world.get_interaction("cover_cabinet") != null, "cabinet_cover")
	_check(world.get_interaction("cover_bed") != null, "bed_cover")
	_check(InputMap.has_action("flashlight"), "flashlight_action")
	_check(InputMap.has_action("sneak"), "sneak_action")
	_check(world.enemy == null, "no_enemy_before_power")

	_main._interact(world.get_interaction("lobby_note"))
	_check(state.has_flag("lobby_note_read"), "lobby_note_flag")
	_main._close_note()
	_main._interact(world.get_interaction("reception_note"))
	_check(state.has_flag("reception_note_read"), "reception_note_flag")
	_check(state.objective.contains("предохранитель"), "objective_fuse")
	_main._close_note()

	_main._interact(world.get_interaction("fuse"))
	_check(state.has_item("fuse"), "fuse_taken")
	_main._interact(world.get_interaction("fusebox"))
	_check(state.has_flag("power_on"), "power_on")
	_check(world.enemy != null and world.enemy.active, "enemy_after_power")
	_main._close_note()

	_main._interact(world.get_interaction("morgue_key"))
	_check(state.has_item("lift_key"), "key_taken")
	_main._close_note()
	_main._interact(world.get_interaction("ward_chart"))
	_check(state.has_flag("ward_chart_read"), "ward_chart_flag")
	_check(state.objective.contains("стеклу"), "objective_window")
	_main._close_note()

	_main._interact(world.get_interaction("window"))
	_check(_main.state == "choice", "window_choice")
	_main._on_choice_selected(0)
	await _wait(2)
	_check(state.ending == "release", "release_ending")
	_check(_main.state == "ending", "ending_state")
	print("Regression: %d passed, %d failed" % [_passed, _failed])
	quit(1 if _failed > 0 else 0)