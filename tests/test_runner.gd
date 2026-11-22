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
	test_v2_objective_migration()
	test_user_settings_round_trip()
	test_light_and_noise_rules()
	test_truth_unlock()
	test_basement_objective()
	test_manifest_assets_exist()
	test_save_data_format()
	test_story_data()
	test_world_layout()
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
	assert_eq(state.objective, "Подойти к стойке регистратуры и открыть журнал приёма.", "new_game_objective")
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
	state.set_flag("tape_second_heard")
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
	assert_true(loaded.has_flag("tape_second_heard"), "save_basement_flag")
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


func test_v2_objective_migration() -> void:
	var path := "user://alpha_test_v2_save.json"
	var legacy := {
		"version": 2,
		"flags": {"power_on": true, "key_taken": true},
		"inventory": ["lift_key"],
		"objective": "Проверить палату 13. Найти, кого здесь держат.",
		"checkpoint": [700.0, 430.0],
		"play_time": 20.0,
		"ending": "",
	}
	var file := FileAccess.open(path, FileAccess.WRITE)
	assert_true(file != null, "v2_save_created")
	if file == null:
		return
	file.store_string(JSON.stringify(legacy))
	file.close()

	var loaded: Node = _state_script.new()
	assert_true(loaded.load_game(path), "v2_save_loaded")
	assert_eq(loaded.objective, "Прочитать карту наблюдения в палате 13.", "v2_objective_rebuilt")
	assert_eq(loaded.checkpoint, Vector2(700, 430), "v2_checkpoint_not_rescaled")
	loaded.delete_save(path)
	loaded.free()


func test_user_settings_round_trip() -> void:
	var path := "user://alpha_test_settings.json"
	var script: Script = load("res://scripts/autoload/user_settings.gd")
	var settings: Node = script.new()
	settings.fullscreen = true
	settings.master_volume = 0.35
	assert_true(settings.save_settings(path), "settings_saved")
	var loaded: Node = script.new()
	loaded.load_settings(path)
	assert_true(loaded.fullscreen, "settings_fullscreen_round_trip")
	assert_eq(loaded.master_volume, 0.35, "settings_volume_round_trip")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	assert_true(not FileAccess.file_exists(path), "settings_deleted")
	settings.free()
	loaded.free()


func test_light_and_noise_rules() -> void:
	var player_script: Script = load("res://scripts/player.gd")
	var enemy_script: Script = load("res://scripts/enemy.gd")
	assert_true(is_equal_approx(float(player_script.call("speed_for", false)), 168.0),
		"walk_speed")
	assert_true(is_equal_approx(float(player_script.call("speed_for", true)), 100.8),
		"sneak_speed")
	assert_true(is_equal_approx(float(player_script.call("noise_radius_for", false)), 170.0),
		"walk_noise")
	assert_true(is_equal_approx(float(player_script.call("noise_radius_for", true)), 60.0),
		"sneak_noise")
	assert_true(is_equal_approx(float(enemy_script.call("sight_range_for", true)), 300.0),
		"sight_light")
	assert_true(is_equal_approx(float(enemy_script.call("sight_range_for", false)), 80.0),
		"sight_dark")


func test_truth_unlock() -> void:
	var state: Node = _state_script.new()
	var notes := [
		"archive_note_1", "archive_note_2", "archive_note_3",
		"basement_note", "boiler_note",
	]
	assert_true(not state.is_truth_unlocked(), "truth_empty")
	for flag: String in notes:
		state.set_flag(flag)
	assert_true(not state.is_truth_unlocked(), "truth_without_tapes")
	state.set_flag("tape_heard")
	assert_true(not state.is_truth_unlocked(), "truth_one_tape")
	state.set_flag("tape_second_heard")
	assert_true(state.is_truth_unlocked(), "truth_complete")
	state.set_flag("archive_note_2", false)
	assert_true(not state.is_truth_unlocked(), "truth_needs_every_note")
	state.free()


func test_basement_objective() -> void:
	var state: Node = _state_script.new()
	state.set_flag("power_on")
	state.set_flag("key_taken")
	state.set_flag("ward_chart_read")
	assert_eq(state.resolve_objective(),
		"Спуститься в подвал по лестнице в холле.", "objective_basement_hint")
	state.set_flag("basement_visited")
	assert_eq(state.resolve_objective(),
		"Обыскать архив и котельную: пять записок и вторая кассета.",
		"objective_basement_search")
	state.free()


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


func test_save_data_format() -> void:
	var save_script: Script = load("res://scripts/core/save_data.gd")
	var defaults := {"objective": "Старт", "checkpoint": Vector2(1, 2)}

	var current: Dictionary = save_script.call("decode", {
		"version": 3,
		"flags": {"power_on": true},
		"inventory": ["fuse", "fuse"],
		"objective": "Найти ключ",
		"checkpoint": [10.0, 20.0],
		"play_time": 4.5,
		"ending": "truth",
	}, defaults["objective"], defaults["checkpoint"])
	assert_true(bool(current["ok"]), "save_v3_ok")
	assert_eq(current["checkpoint"], Vector2(10, 20), "save_v3_checkpoint")
	assert_eq(current["inventory"].size(), 1, "save_inventory_deduplicated")
	assert_true(not bool(current["rebuild_objective"]), "save_v3_keeps_objective")
	assert_eq(current["ending"], "truth", "save_v3_ending")

	var legacy: Dictionary = save_script.call("decode", {
		"version": 1,
		"flags": {"power_on": true},
		"checkpoint": [80.0, 420.0],
	}, defaults["objective"], defaults["checkpoint"])
	assert_eq(legacy["checkpoint"], Vector2(160, 840), "save_v1_checkpoint_scaled")
	assert_true(bool(legacy["rebuild_objective"]), "save_v1_rebuilds_objective")

	var broken: Dictionary = save_script.call("decode", "не словарь", defaults["objective"], defaults["checkpoint"])
	assert_true(not bool(broken["ok"]), "save_rejects_garbage")

	var empty: Dictionary = save_script.call("decode", {"version": 3}, defaults["objective"], defaults["checkpoint"])
	assert_eq(empty["objective"], "Старт", "save_defaults_objective")
	assert_eq(empty["checkpoint"], Vector2(1, 2), "save_defaults_checkpoint")


func test_story_data() -> void:
	var story_script: Script = load("res://scripts/core/story.gd")
	var keys: Array = story_script.call("keys")
	assert_true(keys.size() >= 20, "story_has_entries")
	var required := [
		"intro", "lobby", "reception", "fuse", "power", "key", "tape", "ward",
		"archive_note_1", "archive_note_2", "archive_note_3", "basement_note",
		"boiler_note", "tape_second", "boiler_scene", "truth", "escape", "release",
	]
	var missing: Array[String] = []
	for key: String in required:
		if not bool(story_script.call("has", key)):
			missing.append(key)
	assert_eq(missing.size(), 0, "story_required_keys: %s" % str(missing))
	var empty: Array[String] = []
	for key: Variant in keys:
		var text := str(story_script.call("text", str(key)))
		if text.strip_edges().is_empty():
			empty.append(str(key))
	assert_eq(empty.size(), 0, "story_no_empty_text: %s" % str(empty))
	assert_true(not story_script.call("title", "intro").is_empty(), "story_title")
	assert_true(not story_script.call("text", "intro").contains("\\n"), "story_newlines_joined")


func test_world_layout() -> void:
	var layout_script: Script = load("res://scripts/world_layout.gd")
	var layout: RefCounted = layout_script.call("load_default")
	assert_eq(layout.map_size, Vector2(1536, 1280), "layout_map_size")
	assert_eq(layout.rooms.size(), 10, "layout_rooms")
	assert_eq(layout.walls.size(), 24, "layout_walls")
	assert_eq(layout.doors.size(), 9, "layout_doors")
	assert_eq(layout.props.size(), 29, "layout_props")
	assert_eq(layout.decals.size(), 10, "layout_decals")
	assert_eq(layout.item_spawns.size(), 12, "layout_items")
	assert_eq(layout.interactions.size(), 20, "layout_interactions")

	var missing: Array[String] = []
	for kind: Variant in layout.floor_sets:
		var textures: Array = layout.floor_sets[kind]
		if textures.is_empty():
			missing.append("floors:%s" % str(kind))
		for texture: Variant in textures:
			if texture == null:
				missing.append("floors:%s" % str(kind))
	for door: Dictionary in layout.doors:
		if door["frame"] == null or (door["panels"] as Array).is_empty():
			missing.append("door:%s" % str(door["label"]))
	for prop: Dictionary in layout.props + layout.decals + layout.item_spawns:
		if prop["texture"] == null:
			missing.append("texture:%s" % str(prop.get("id", prop["pos"])))
	assert_eq(missing.size(), 0, "layout_textures_resolved: %s" % str(missing))

	var ids: Dictionary = {}
	var duplicates: Array[String] = []
	for entry: Dictionary in layout.interactions:
		var id := str(entry["id"])
		if ids.has(id):
			duplicates.append(id)
		ids[id] = true
	assert_eq(duplicates.size(), 0, "layout_interaction_ids_unique: %s" % str(duplicates))

	var outside: Array[String] = []
	for room: Dictionary in layout.rooms:
		var rect: Rect2 = room["rect"]
		if not Rect2(Vector2.ZERO, layout.map_size).encloses(rect):
			outside.append(str(room["title"]))
	assert_eq(outside.size(), 0, "layout_rooms_inside_map: %s" % str(outside))
