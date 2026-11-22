extends Node2D

const PLAYER_SCENE := preload("res://scenes/player.tscn")
const WORLD_SCENE := preload("res://scenes/world.tscn")

const INTRO_TEXT := """[color=#9a6257]Три дня назад. Комната отдыха.[/color]

Ты помнишь её пальцы на затылке
и смех, когда ты закрывал дверь.

Потом — холод коридора и кровь
на кафеле.

В 03:12 телефон оживает:
[color=#8a6a34]«Поднимись на этаж, которого нет».[/color]"""

const LOBBY_NOTE := """[center][color=#9a6257]БОЛЬНИЦА «БЕЛЫЙ ШУМ»[/color][/center]

Внимание персоналу.

Лифт на 13-й этаж закрыт.
Не отвечайте, если по громкой связи
назовут ваше имя.

Если увидите медсестру без лица —
не смотрите на её руки."""

const RECEPTION_NOTE := """[color=#9a6257]Журнал приёма. 13 декабря.[/color]

Пациентка №13: Лера Н., 26 лет.
Диагноз: «добровольная участница».

Переведена на этаж 13.
Перевод подтвердила: Лера Н.

Внизу другими чернилами:
[color=#8a5a3c]«Она больше не выходила».[/color]"""

const FUSE_NOTE := """Электрощит обесточен.

На месте главного предохранителя — пустая
колодка и следы пальцев в саже.

Без питания лифт не поедет.
Приёмное. Верхний ящик картотеки."""

const POWER_NOTE := """[color=#9a6257]Щелчок. Гудение. Свет.[/color]

В конце коридора на секунду появляется
женская фигура в белом.

Когда ты смотришь снова, коридор пуст.

На табло лифта мигает [color=#a02a24]13[/color].
Служебный ключ должен быть в морге."""

const KEY_NOTE := """[color=#9a6257]МОРГ[/color]

Ключ лежит на столе рядом с телом.

На бирке: [color=#a02a24]«Марк В., 27 лет.
Ножевое ранение».[/color]

На запястье — твои часы.
Стрелки стоят на 03:12."""

const TAPE_NOTE := """[color=#9a6257]Запись 04. Комната отдыха. 02:47.[/color]

[i]Шорох ткани. Приглушённый смех.[/i]

Лера: «Марк... не здесь. Дверь хотя бы закрой».
Марк: «Никто не войдёт».

[i]Щелчок замка. Долгая тишина.[/i]

Незнакомый голос: «Вы забыли закрыть дверь».

[i]Удар. Короткий вскрик.
Запись обрывается.[/i]"""

const WARD_NOTE := """[color=#9a6257]Карта наблюдения. Палата 13.[/color]

Пациентка: Лера Н.
Статус: [color=#a02a24]не пациентка[/color].

После смерти Марка В. она отказалась
отпускать тело.

Этаж 13 — место, где она помнит вас.
[color=#8a5a3c]Не разбивайте стекло.[/color]"""

const WINDOW_TEXT := """За стеклом стоит Лера.
Она не стучит и не улыбается.

С твоей стороны — кровавый след.
Твоя рука уже касается его.

Если разбить стекло, она сможет выйти."""

const ELEVATOR_TEXT := """Служебный лифт вздрагивает.

Кнопки нет. Кабина уже знает, куда ехать.
За дверями слышно, как Лера произносит
твоё имя — очень тихо, будто во сне.

Можно уйти. Можно остаться."""

const ESCAPE_ENDING := """[center]Ты входишь в лифт один.[/center]

Двери закрываются. Кабина едет вниз,
хотя этажей под больницей нет.

Дома на зеркале проступает:
[color=#8a5a3c]«Ты забыл, как я дышала».[/color]

Через три дня на пороге лежит ключ.
На бирке выбито твоё имя."""

const RELEASE_ENDING := """[center]Стекло лопается внутрь.[/center]

Лера выходит босая. Живая.
Её ладонь теплее, чем должна быть.

[color=#b78968]«Ты умер в коридоре, Марк.
Я не позволила забрать тебя.
Этот этаж держит нас обоих».[/color]
Больница за окном гаснет.
Но на каждом этаже загорается свет."""

var world: HospitalWorld
var player: Player
var state := "menu"
var _nearest: Interaction
var _choice_context := ""
var _note_is_intro := false
var _save_timer := 0.0
var _is_fullscreen := false

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
	if state != "playing" or not is_instance_valid(player):
		return
	GameState.play_time += delta
	_save_timer += delta
	if _save_timer >= 30.0:
		_save_timer = 0.0
		_autosave()

	_nearest = player.find_nearest_interaction()
	ui.set_prompt(_nearest.prompt if _nearest != null else "")
	if _nearest != null and Input.is_action_just_pressed("interact"):
		_interact(_nearest)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("fullscreen"):
		_toggle_fullscreen()
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
	_show_note("ПОСЛЕДНЯЯ НОЧЬ", INTRO_TEXT, true)


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
	player = PLAYER_SCENE.instantiate() as Player
	world.add_child(player)
	player.global_position = GameState.checkpoint
	world.set_player(player)
	world.caught_player.connect(_on_player_caught)
	ui.show_game()
	ui.set_objective(GameState.objective)
	ui.set_inventory(GameState.inventory)
	ui.set_prompt("")
	state = "playing"
	AudioManager.play_ambient("hospital")


func _cleanup_world() -> void:
	if is_instance_valid(world):
		world.queue_free()
	world = null
	player = null
	_nearest = null


func _show_note(title: String, body: String, is_intro: bool = false) -> void:
	if state == "note" or state == "choice" or state == "ending":
		return
	state = "note"
	_note_is_intro = is_intro
	_nearest = null
	ui.set_prompt("")
	ui.show_note(title, body)
	get_tree().paused = true


func _close_note() -> void:
	if state != "note":
		return
	ui.hide_note()
	state = "playing"
	get_tree().paused = false
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
	match target.interaction_id:
		"lobby_note":
			target.enabled = false
			GameState.set_flag("lobby_note_read")
			_autosave()
			_show_note("ОБЪЯВЛЕНИЕ", LOBBY_NOTE)
		"reception_note":
			target.enabled = false
			GameState.set_flag("reception_note_read")
			if GameState.has_flag("fuse_taken"):
				GameState.set_objective("Восстановить питание в щитовой.")
			else:
				GameState.set_objective("Найти предохранитель. Проверить приёмное.")
			ui.set_objective(GameState.objective)
			_autosave()
			_show_note("ЖУРНАЛ ПРИЁМА", RECEPTION_NOTE)
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
			_show_note("ЗАПИСЬ 04", TAPE_NOTE)
		"ward_chart":
			target.enabled = false
			GameState.set_flag("ward_chart_read")
			if GameState.has_flag("key_taken"):
				GameState.set_objective("Вернуться к стеклу или уйти на лифте.")
			else:
				GameState.set_objective("Найти ключ в морге или подойти к стеклу.")
			ui.set_objective(GameState.objective)
			_autosave()
			_show_note("КАРТА НАБЛЮДЕНИЯ", WARD_NOTE)
		"window":
			_try_window()
		"elevator":
			_try_elevator()


func _collect_fuse(target: Interaction) -> void:
	if not GameState.add_item("fuse"):
		return
	target.enabled = false
	GameState.set_flag("fuse_taken")
	GameState.set_objective("Восстановить питание в щитовой.")
	ui.set_inventory(GameState.inventory)
	ui.set_objective(GameState.objective)
	ui.show_toast("В инвентаре: предохранитель")
	AudioManager.play_sfx("pickup", -6.0)
	_autosave()


func _use_fusebox() -> void:
	if world.power_on:
		_show_note("ЭЛЕКТРОЩИТ", "Питание уже восстановлено.\n\nВ коридоре кто-то ходит.")
		return
	if not GameState.has_flag("fuse_taken"):
		_show_note("ЭЛЕКТРОЩИТ", FUSE_NOTE)
		return
	if not GameState.remove_item("fuse"):
		return
	GameState.set_flag("power_on")
	world.set_power_on()
	ui.set_inventory(GameState.inventory)
	GameState.set_objective("Найти ключ от служебного лифта. Проверить морг.")
	ui.set_objective(GameState.objective)
	AudioManager.play_sfx("power", -3.0)
	AudioManager.play_sfx("stinger", -9.0, 0.02)
	_autosave()
	_show_note("ПИТАНИЕ ВОССТАНОВЛЕНО", POWER_NOTE)


func _collect_key(target: Interaction) -> void:
	if not GameState.add_item("lift_key"):
		return
	target.enabled = false
	GameState.set_flag("key_taken")
	if GameState.has_flag("ward_chart_read"):
		GameState.set_objective("Вернуться к стеклу или уйти на лифте.")
	else:
		GameState.set_objective("Проверить палату 13. Найти, кого здесь держат.")
	ui.set_inventory(GameState.inventory)
	ui.set_objective(GameState.objective)
	AudioManager.play_sfx("pickup", -6.0)
	AudioManager.play_sfx("stinger", -11.0, 0.02)
	_autosave()
	_show_note("СЛУЖЕБНЫЙ КЛЮЧ", KEY_NOTE)


func _try_window() -> void:
	if not world.power_on:
		_show_note("СМОТРОВОЕ СТЕКЛО", "За стеклом темно.\n\nНо темнота дышит.")
		return
	if not GameState.has_flag("ward_chart_read"):
		GameState.set_objective("Прочитать карту наблюдения в палате 13.")
		ui.set_objective(GameState.objective)
		_show_note("СМОТРОВОЕ СТЕКЛО", "За стеклом стоит женский силуэт.\n\nЕё лицо скрыто отражением.\nСначала нужно понять, кого ты видишь.")
		return
	_choice_context = "window"
	state = "choice"
	_nearest = null
	ui.set_prompt("")
	ui.show_choice("ЗА СТЕКЛОМ", WINDOW_TEXT, ["Разбить стекло", "Отойти"])
	get_tree().paused = true


func _try_elevator() -> void:
	if not world.power_on:
		_show_note("ЛИФТ", "Кнопка не горит.\n\nСлужебный лифт обесточен.")
		return
	if not GameState.has_flag("key_taken"):
		_show_note("ЛИФТ", "Кнопка не работает.\n\nПод панелью — замочная скважина.\nКлюч может быть в морге.")
		return
	_choice_context = "elevator"
	state = "choice"
	_nearest = null
	ui.set_prompt("")
	ui.show_choice("СЛУЖЕБНЫЙ ЛИФТ", ELEVATOR_TEXT, ["Войти в лифт", "Отойти"])
	get_tree().paused = true


func _on_choice_selected(index: int) -> void:
	if state != "choice":
		return
	var context := _choice_context
	ui.hide_choice()
	_choice_context = ""
	state = "playing"
	get_tree().paused = false
	if index != 0:
		return
	if context == "window":
		_show_ending("release")
	elif context == "elevator":
		_show_ending("escape")


func _close_choice() -> void:
	if state != "choice":
		return
	ui.hide_choice()
	_choice_context = ""
	state = "playing"
	get_tree().paused = false


func _show_ending(ending_id: String) -> void:
	state = "ending"
	GameState.ending = ending_id
	GameState.set_flag("ending_%s" % ending_id)
	ui.set_prompt("")
	AudioManager.stop_all()
	if ending_id == "escape":
		AudioManager.play_sfx("stinger", -8.0)
		ui.show_ending("ЛИФТ ИДЁТ ВНИЗ", ESCAPE_ENDING)
	else:
		AudioManager.play_sfx("heartbeat", -4.0)
		ui.show_ending("ЭТАЖ, КОТОРЫЙ ДЫШИТ", RELEASE_ENDING)
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
	ui.show_toast("Ты приходишь в себя у входа. Она всё ещё здесь.")
	player.respawn_at(GameState.checkpoint)
	if is_instance_valid(world.enemy):
		world.enemy.reset_to_home()
	_nearest = null
	ui.set_prompt("")


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
	_is_fullscreen = not _is_fullscreen
	var mode := DisplayServer.WINDOW_MODE_FULLSCREEN if _is_fullscreen else DisplayServer.WINDOW_MODE_WINDOWED
	DisplayServer.window_set_mode(mode)