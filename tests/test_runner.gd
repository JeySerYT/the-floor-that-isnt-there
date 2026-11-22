extends SceneTree

var passed := 0
var failed := 0
var _state_script: Script = load("res://scripts/autoload/game_state.gd")


func _initialize() -> void:
	test_new_game()
	test_flags_and_items()
	test_save_round_trip()
	test_missing_save()
	test_v1_checkpoint_migration()
	test_manifest_assets_exist()
	print("Results: %d passed, %d failed" % [passed, failed])
	quit(1 if failed > 0 else 0)


func assert_eq(actual: Variant, expected: Variant, label: String) -> void:
	if actual == expected:
		passed += 1
	else:
		failed += 1
		push_error("FAIL %s: expected %s, got %s" % [label, expected, actual])


func assert_true(value: bool, label: String) -> void:
	assert_eq(value, true, label)


func test_new_game() -> void:
	var state: Node = _state_script.new()
	state.add_item("fuse")
	state.set_flag("power_on")
	state.set_objective("test")
	state.set_checkpoint(Vector2(100, 200))
	state.reset_new_game()
	assert_eq(state.objective, "Найти Леру. Осмотреть регистратуру.", "new_game_objective")
	assert_eq(state.inventory.size(), 0, "new_game_inventory_empty")
	assert_true(not state.has_flag("power_on"), "new_game_flags_cleared")
	assert_eq(state.checkpoint, Vector2(160, 840), "new_game_checkpoint")
	state.free()


func test_flags_and_items() -> void:
	var state: Node = _state_script.new()
	assert_true(state.add_item("fuse"), "add_item")
	assert_true(state.has_item("fuse"), "has_item")
	assert_true(not state.add_item("fuse"), "duplicate_item_rejected")
	assert_eq(state.inventory.size(), 1, "inventory_unique")
	state.set_flag("power_on")
	assert_true(state.has_flag("power_on"), "flag_set")
	state.set_flag("power_on", false)
	assert_true(not state.has_flag("power_on"), "flag_unset")
	assert_true(state.remove_item("fuse"), "remove_item")
	assert_true(not state.has_item("fuse"), "item_removed")
	state.free()


func test_save_round_trip() -> void:
	var path := "user://alpha_test_save.json"
	var state: Node = _state_script.new()
	state.set_flag("power_on")
	state.set_flag("ward_chart_read")
	state.add_item("lift_key")
	state.set_objective("Проверить палатку")
	state.set_checkpoint(Vector2(123, 456))
	state.play_time = 81.5
	state.ending = "release"
	assert_true(state.save_game(path), "save_written")
	assert_true(state.has_save(path), "save_exists")

	var loaded: Node = _state_script.new()
	assert_true(loaded.load_game(path), "save_loaded")
	assert_true(loaded.has_flag("power_on"), "save_flag_round_trip")
	assert_true(loaded.has_flag("ward_chart_read"), "save_second_flag")
	assert_true(loaded.has_item("lift_key"), "save_item_round_trip")
	assert_eq(loaded.objective, "Проверить палатку", "save_objective_round_trip")
	assert_eq(loaded.checkpoint, Vector2(123, 456), "save_checkpoint_round_trip")
	assert_eq(loaded.play_time, 81.5, "save_play_time_round_trip")
	assert_eq(loaded.ending, "release", "save_ending_round_trip")
	loaded.delete_save(path)
	assert_true(not loaded.has_save(path), "save_deleted")
	state.free()
	loaded.free()


func test_missing_save() -> void:
	var state: Node = _state_script.new()
	assert_true(not state.load_game("user://definitely_missing_alpha_save.json"), "missing_save_rejected")
	state.free()

func test_v1_checkpoint_migration() -> void:
	var path := "user://alpha_test_v1_save.json"
	var legacy := {
		"version": 1,
		"flags": {"power_on": true},
		"inventory": ["fuse"],
		"objective": "Старая цель",
		"checkpoint": [80.0, 420.0],
		"play_time": 12.0,
		"ending": "",
	}
	var file := FileAccess.open(path, FileAccess.WRITE)
	assert_true(file != null, "v1_save_created")
	if file == null:
		return
	file.store_string(JSON.stringify(legacy))
	file.close()

	var loaded: Node = _state_script.new()
	assert_true(loaded.load_game(path), "v1_save_loaded")
	assert_eq(loaded.checkpoint, Vector2(160, 840), "v1_checkpoint_scaled")
	assert_true(loaded.has_flag("power_on"), "v1_flags_kept")
	loaded.delete_save(path)
	loaded.free()


func test_manifest_assets_exist() -> void:
	var manifest_text := FileAccess.get_file_as_string("res://assets/textures/manifest.json")
	assert_true(not manifest_text.is_empty(), "manifest_exists")
	var parsed: Variant = JSON.parse_string(manifest_text)
	assert_true(parsed is Dictionary, "manifest_parses")
	if not parsed is Dictionary:
		return
	var assets: Array = parsed.get("assets", [])
	assert_true(assets.size() > 0, "manifest_has_assets")
	var missing: Array[String] = []
	for asset: Dictionary in assets:
		var rel := str(asset.get("file", ""))
		if rel.is_empty() or not FileAccess.file_exists(rel):
			missing.append(str(asset.get("id", "?")))
	assert_eq(missing.size(), 0, "manifest_files_present: %s" % str(missing))
