extends Node2D

const PLAYER_SCENE := preload("res://scenes/player.tscn")
const WORLD_SCENE := preload("res://scenes/world.tscn")


var world: HospitalWorld
var player: Player
var state := "menu"
var _nearest: Interaction
var _choice_context := ""
var _note_is_intro := false
var _save_timer := 0.0
var _input_lock := 0.0

@onready var ui: GameUI = $UI/GameUI


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_setup_input()
	ui.new_game_requested.connect(_on_new_game)
	ui.continue_requested.connect(_on_continue)
	ui.quit_requested.connect(_on_quit)
	ui.resume_requested.connect(_on_resume)
	ui.menu_requested.connect(_on_return_to_menu)
	ui.note_closed.connect(_close_note)
	ui.choice_selected.connect(_on_choice_selected)
	ui.ending_menu_requested.connect(_on_ending_menu)
	ui.ending_restart_requested.connect(_on_ending_restart)
	AudioManager.play_ambient("menu")
	ui.show_menu(GameState.has_save())


func _process(delta: float) -> void:
	_input_lock = maxf(_input_lock - delta, 0.0)
	if state != "playing" or not is_instance_valid(player):
		return
	GameState.play_time += delta
	_save_timer += delta
	if _save_timer >= 30.0:
		_save_timer = 0.0
		_autosave()

	_nearest = player.find_nearest_interaction()
	ui.set_prompt(_nearest.prompt if _nearest != null else "")
	ui.set_status(player.flashlight_on, Input.is_action_pressed("sneak"), player.hiding)
	if _input_lock <= 0.0 and _nearest != null and Input.is_action_just_pressed("interact"):
		_interact(_nearest)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey:
		var key_event := event as InputEventKey
		if key_event.pressed and not key_event.echo and (key_event.keycode == KEY_F11 or key_event.physical_keycode == KEY_F11):
			_toggle_fullscreen()
			get_viewport().set_input_as_handled()
			return
	if event.is_action_pressed("fullscreen"):
		_toggle_fullscreen()
		get_viewport().set_input_as_handled()
		return
	if state == "ending" and ui.is_credits_open() and event.is_action_pressed("pause"):
		ui.hide_credits()
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("pause") and ui.is_settings_open():
		ui.close_settings()
		get_viewport().set_input_as_handled()
		return
	if state == "playing" and event.is_action_pressed("flashlight"):
		_toggle_flashlight()
		get_viewport().set_input_as_handled()
		return
	if state == "playing" and event.is_action_pressed("pause"):
		_open_pause()
		get_viewport().set_input_as_handled()
	elif state == "paused" and event.is_action_pressed("pause"):
		_on_resume()
		get_viewport().set_input_as_handled()
	elif state == "note" and (event.is_action_pressed("pause") or event.is_action_pressed("interact")):
		_close_note()
		get_viewport().set_input_as_handled()
	elif state == "choice" and event.is_action_pressed("pause"):
		_close_choice()
		get_viewport().set_input_as_handled()


func _setup_input() -> void:
	var bindings := {
		"move_left": [KEY_A, KEY_LEFT],
		"move_right": [KEY_D, KEY_RIGHT],
		"move_up": [KEY_W, KEY_UP],
		"move_down": [KEY_S, KEY_DOWN],
		"interact": [KEY_E],
		"pause": [KEY_ESCAPE],
		"fullscreen": [KEY_F11],
		"flashlight": [KEY_F],
		"sneak": [KEY_SHIFT],
	}
	for action_name: String in bindings:
		if not InputMap.has_action(action_name):
			InputMap.add_action(action_name)
		if not InputMap.action_get_events(action_name).is_empty():
			continue
		var keys: Array = bindings[action_name]
		for key: int in keys:
			var key_event := InputEventKey.new()
			key_event.physical_keycode = key
			InputMap.action_add_event(action_name, key_event)


func _on_new_game() -> void:
	GameState.reset_new_game()
	_begin_session()
	_show_note_key("intro", true)


func _on_continue() -> void:
	if not GameState.load_game():
		_on_new_game()
		return
	_begin_session()


func _begin_session() -> void:
	get_tree().paused = false
	_cleanup_world()
	_choice_context = ""
	_save_timer = 0.0
	world = WORLD_SCENE.instantiate() as HospitalWorld
	add_child(world)
	world.room_entered.connect(_on_room_entered)
	player = PLAYER_SCENE.instantiate() as Player
	world.add_child(player)
	player.global_position = GameState.checkpoint
	world.set_player(player)
	world.caught_player.connect(_on_player_caught)
	ui.set_player(player)
	ui.show_game()
	ui.set_objective(GameState.objective)
	ui.set_inventory(GameState.inventory)
	ui.set_prompt("")
	ui.set_status(true, false, false)
	state = "playing"
	AudioManager.play_ambient("hospital")


func _cleanup_world() -> void:
	if is_instance_valid(world):
		world.queue_free()
	world = null
	player = null
	_nearest = null
	ui.set_player(null)


func _show_note(title: String, body: String, is_intro: bool = false) -> void:
	if state == "note" or state == "choice" or state == "ending":
		return
	state = "note"
	_note_is_intro = is_intro
	_nearest = null
	ui.set_prompt("")
	ui.show_note(title, body)
	get_tree().paused = true


func _show_note_key(key: String, is_intro: bool = false) -> void:
	var entry := Story.note(key)
	_show_note(entry["title"], entry["text"], is_intro)


func _close_note() -> void:
	if state != "note":
		return
	ui.hide_note()
	state = "playing"
	get_tree().paused = false
	_input_lock = 0.25
	if _note_is_intro:
		_note_is_intro = false
		GameState.set_flag("intro_seen")
		_autosave()


func _open_pause() -> void:
	if state != "playing":
		return
	state = "paused"
	_nearest = null
	ui.set_prompt("")
	ui.show_pause()
	get_tree().paused = true


func _on_resume() -> void:
	if state != "paused":
		return
	ui.hide_pause()
	state = "playing"
	get_tree().paused = false
	_input_lock = 0.25


func _on_return_to_menu() -> void:
	_autosave()
	get_tree().paused = false
	_cleanup_world()
	state = "menu"
	AudioManager.play_ambient("menu")
	ui.show_menu(GameState.has_save())


func _on_quit() -> void:
	_autosave()
	get_tree().quit()


func _interact(target: Interaction) -> void:
	if is_instance_valid(world):
		world.emit_noise(player.global_position, Player.INTERACTION_NOISE)
	match target.interaction_id:
		"lobby_note":
			target.enabled = false
			GameState.set_flag("lobby_note_read")
			_autosave()
			_show_note_key("lobby")
		"reception_note":
			target.enabled = false
			GameState.set_flag("reception_note_read")
			if GameState.has_flag("fuse_taken"):
				GameState.set_objective("Вставить предохранитель в электрощит в щитовой.")
			else:
				GameState.set_objective("Взять предохранитель из картотеки в приёмном покое.")
			ui.set_objective(GameState.objective)
			_autosave()
			_show_note_key("reception")
		"fuse":
			_collect_fuse(target)
		"fusebox":
			_use_fusebox()
		"morgue_key":
			_collect_key(target)
		"tape":
			target.enabled = false
			GameState.set_flag("tape_heard")
			AudioManager.play_sfx("stinger", -12.0, 0.03)
			_autosave()
			_show_note_key("tape")
		"ward_chart":
			target.enabled = false
			GameState.set_flag("ward_chart_read")
			if GameState.has_flag("key_taken"):
				GameState.set_objective("Спуститься в подвал по лестнице в холле или вернуться к смотровому стеклу.")
			else:
				GameState.set_objective("Найти служебный ключ в морге.")
			ui.set_objective(GameState.objective)
			_autosave()
			_show_note_key("ward")
		"window":
			_try_window()
		"elevator":
			_try_elevator()
		"cover_cabinet", "cover_bed":
			_toggle_cover(target)
		"stairs_down":
			_try_stairs_down()
		"stairs_up":
			_use_stairs_up()
		"archive_note_1":
			_read_collectible(target, "archive_note_1")
		"archive_note_2":
			_read_collectible(target, "archive_note_2")
		"archive_note_3":
			_read_collectible(target, "archive_note_3")
		"basement_note":
			_read_collectible(target, "basement_note")
		"boiler_note":
			_read_collectible(target, "boiler_note")
		"tape_second":
			target.enabled = false
			GameState.set_flag("tape_second_heard")
			AudioManager.play_sfx("stinger", -12.0, 0.03)
			_autosave()
			_check_truth_progress()
			_show_note_key("tape_second")
		"boiler_door":
			_try_boiler_door()


func _toggle_cover(target: Interaction) -> void:
	if not is_instance_valid(player):
		return
	if player.hiding:
		player.exit_cover()
		target.prompt = _cover_enter_prompt(target.interaction_id)
		ui.set_prompt(target.prompt)
		ui.set_status(player.flashlight_on, Input.is_action_pressed("sneak"), false)
		AudioManager.play_sfx("interact", -12.0)
		return
	var seen := false
	if is_instance_valid(world) and is_instance_valid(world.enemy) and world.enemy.active:
		seen = world.enemy.can_see_player()
	player.enter_cover(target.global_position)
	target.prompt = "Выйти из укрытия"
	ui.set_prompt(target.prompt)
	ui.set_status(false, Input.is_action_pressed("sneak"), true)
	AudioManager.play_sfx("interact", -12.0)
	if seen and is_instance_valid(world.enemy):
		world.enemy.investigate(target.global_position, 3.0)
		ui.show_toast("Она видела, куда ты спрятался.")


func _cover_enter_prompt(id: String) -> String:
	return "Спрятаться под кровать" if id == "cover_bed" else "Спрятаться в шкаф"


func _toggle_flashlight() -> void:
	if not is_instance_valid(player) or player.hiding:
		return
	player.toggle_flashlight()
	ui.set_status(player.flashlight_on, Input.is_action_pressed("sneak"), player.hiding)
	if not player.flashlight_on and not GameState.has_flag("flashlight_hint_seen"):
		GameState.set_flag("flashlight_hint_seen")
		ui.show_toast("Фонарь выключен: тебя хуже видно, но и ты видишь меньше.")


func _read_collectible(target: Interaction, key: String) -> void:
	if target != null:
		target.enabled = false
	GameState.set_flag(key)
	AudioManager.play_sfx("interact", -12.0)
	_autosave()
	_check_truth_progress()
	_show_note_key(key)


func _check_truth_progress() -> void:
	if not is_instance_valid(player):
		return
	if GameState.is_truth_unlocked():
		if not GameState.has_flag("truth_ready_announced"):
			GameState.set_flag("truth_ready_announced")
			ui.show_toast("Все записи собраны. Дверь «−1» в котельной открыта.")
		GameState.set_objective("Открыть дверь «−1» в котельной или спуститься на −1 в лифте.")
	else:
		GameState.set_objective("Обыскать архив и котельную: пять записок и вторая кассета.")
	ui.set_objective(GameState.objective)
	ui.set_inventory(GameState.inventory)


func _try_stairs_down() -> void:
	if not world.power_on:
		_show_note_key("stairs_locked")
		return
	ui.play_transition()
	AudioManager.play_sfx("power", -14.0)
	player.teleport_to(Vector2(320, 1016))
	GameState.set_flag("basement_visited")
	GameState.set_checkpoint(Vector2(320, 1016))
	if not GameState.is_truth_unlocked():
		GameState.set_objective("Обыскать архив и котельную: пять записок и вторая кассета.")
	ui.set_objective(GameState.objective)
	_autosave()


func _use_stairs_up() -> void:
	ui.play_transition()
	AudioManager.play_sfx("step", -18.0)
	player.teleport_to(Vector2(320, 904))
	GameState.set_checkpoint(Vector2(320, 904))
	_autosave()


func _on_room_entered(index: int) -> void:
	if state != "playing" or not is_instance_valid(world) or not is_instance_valid(player):
		return
	if index != 9 or not world.power_on:
		return
	if GameState.has_flag("boiler_scene_seen"):
		return
	_trigger_boiler_scene()


func _trigger_boiler_scene() -> void:
	GameState.set_flag("boiler_scene_seen")
	world.set_boiler_blackout()
	player.set_flashlight(false)
	ui.set_status(false, false, false)
	if is_instance_valid(world.enemy):
		world.enemy.set_home(Vector2(800, 1096))
		world.enemy.global_position = Vector2(800, 1096)
		world.enemy.investigate(player.global_position, 6.0)
	if GameState.is_truth_unlocked():
		GameState.set_objective("Открыть дверь «−1» в котельной.")
	else:
		GameState.set_objective("Обыскать архив и котельную: пять записок и вторая кассета.")
	ui.set_objective(GameState.objective)
	AudioManager.play_sfx("stinger", -6.0, 0.01)
	_autosave()
	_show_note_key("boiler_scene")


func _try_boiler_door() -> void:
	if not GameState.is_truth_unlocked():
		_show_note_key("boiler_locked")
		return
	_choice_context = "boiler_door"
	state = "choice"
	_nearest = null
	ui.set_prompt("")
	ui.show_choice(Story.title("boiler_door"), Story.text("boiler_door"), ["Спуститься", "Отойти"])
	get_tree().paused = true


func _collect_fuse(target: Interaction) -> void:
	if not GameState.add_item("fuse"):
		return
	target.enabled = false
	GameState.set_flag("fuse_taken")
	GameState.set_objective("Вставить предохранитель в электрощит в щитовой.")
	ui.set_inventory(GameState.inventory)
	ui.set_objective(GameState.objective)
	ui.show_toast("В инвентаре: предохранитель")
	AudioManager.play_sfx("pickup", -6.0)
	_autosave()


func _use_fusebox() -> void:
	if world.power_on:
		_show_note_key("fusebox_on")
		return
	if not GameState.has_flag("fuse_taken"):
		_show_note_key("fuse")
		return
	if not GameState.remove_item("fuse"):
		return
	GameState.set_flag("power_on")
	world.set_power_on()
	ui.set_inventory(GameState.inventory)
	GameState.set_objective("Найти служебный ключ в морге.")
	ui.set_objective(GameState.objective)
	AudioManager.play_sfx("power", -3.0)
	AudioManager.play_sfx("stinger", -9.0, 0.02)
	_autosave()
	_show_note_key("power")


func _collect_key(target: Interaction) -> void:
	if not GameState.add_item("lift_key"):
		return
	target.enabled = false
	GameState.set_flag("key_taken")
	if GameState.has_flag("ward_chart_read"):
		GameState.set_objective("Спуститься в подвал по лестнице в холле или вернуться к смотровому стеклу.")
	else:
		GameState.set_objective("Прочитать карту наблюдения в палате 13.")
	ui.set_inventory(GameState.inventory)
	ui.set_objective(GameState.objective)
	AudioManager.play_sfx("pickup", -6.0)
	AudioManager.play_sfx("stinger", -11.0, 0.02)
	_autosave()
	_show_note_key("key")


func _try_window() -> void:
	if not world.power_on:
		_show_note_key("window_dark")
		return
	if not GameState.has_flag("ward_chart_read"):
		GameState.set_objective("Прочитать карту наблюдения в палате 13.")
		ui.set_objective(GameState.objective)
		_show_note_key("window_unknown")
		return
	_choice_context = "window"
	state = "choice"
	_nearest = null
	ui.set_prompt("")
	ui.show_choice(Story.title("window"), Story.text("window"), ["Разбить стекло", "Отойти"])
	get_tree().paused = true


func _try_elevator() -> void:
	if not world.power_on:
		_show_note_key("elevator_dark")
		return
	if not GameState.has_flag("key_taken"):
		_show_note_key("elevator_no_key")
		return
	_choice_context = "elevator"
	state = "choice"
	_nearest = null
	ui.set_prompt("")
	var body := Story.text("elevator")
	var options: Array[String] = ["Войти в лифт"]
	if GameState.is_truth_unlocked():
		body += "\n\n" + Story.text("elevator_truth_hint")
		options.append("Спуститься на −1")
	options.append("Отойти")
	ui.show_choice(Story.title("elevator"), body, options)
	get_tree().paused = true


func _on_choice_selected(index: int) -> void:
	if state != "choice":
		return
	var context := _choice_context
	ui.hide_choice()
	_choice_context = ""
	state = "playing"
	get_tree().paused = false
	_input_lock = 0.25
	if index != 0:
		return
	if context == "window":
		_show_ending("release")
	elif context == "elevator":
		if index == 0:
			_show_ending("escape")
		elif index == 1 and GameState.is_truth_unlocked():
			_show_ending("truth")
	elif context == "boiler_door":
		if index == 0:
			_show_ending("truth")


func _close_choice() -> void:
	if state != "choice":
		return
	ui.hide_choice()
	_choice_context = ""
	state = "playing"
	get_tree().paused = false
	_input_lock = 0.25


func _show_ending(ending_id: String) -> void:
	state = "ending"
	GameState.ending = ending_id
	GameState.set_flag("ending_%s" % ending_id)
	ui.set_prompt("")
	AudioManager.stop_all()
	if ending_id == "escape":
		AudioManager.play_sfx("stinger", -8.0)
	elif ending_id == "truth":
		AudioManager.play_sfx("heartbeat", -4.0)
	else:
		AudioManager.play_sfx("heartbeat", -4.0)
	var entry := Story.note(ending_id)
	ui.show_ending(entry["title"], entry["text"], ending_id == "truth")
	GameState.delete_save()
	get_tree().paused = true


func _on_ending_menu() -> void:
	get_tree().paused = false
	_cleanup_world()
	state = "menu"
	AudioManager.play_ambient("menu")
	ui.show_menu(GameState.has_save())


func _on_ending_restart() -> void:
	get_tree().paused = false
	_on_new_game()


func _on_player_caught() -> void:
	if state != "playing":
		return
	AudioManager.play_sfx("stinger", -1.0, 0.0)
	ui.play_caught_effect()
	ui.show_toast("Ты приходишь в себя. Где-то рядом — её шаги.")
	player.respawn_at(GameState.checkpoint)
	if is_instance_valid(world.enemy):
		world.enemy.reset_to_home()
	_nearest = null
	ui.set_prompt("")
	ui.set_status(player.flashlight_on, false, player.hiding)


func _autosave() -> void:
	if state == "menu" or state == "ending" or not is_instance_valid(player):
		return
	var player_position := player.global_position
	var enemy_far := true
	if is_instance_valid(world) and is_instance_valid(world.enemy):
		enemy_far = player_position.distance_to(world.enemy.global_position) > 220.0
	if enemy_far:
		GameState.set_checkpoint(player_position)
	GameState.save_game()


func _toggle_fullscreen() -> void:
	UserSettings.toggle_fullscreen()