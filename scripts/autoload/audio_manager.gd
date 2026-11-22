extends Node

const SOUND_PATHS := {
	"menu": "res://audio/ambient_menu.wav",
	"hospital": "res://audio/ambient_hospital.wav",
	"step": "res://audio/step.wav",
	"interact": "res://audio/interact.wav",
	"pickup": "res://audio/pickup.wav",
	"power": "res://audio/power.wav",
	"stinger": "res://audio/stinger.wav",
	"heartbeat": "res://audio/heartbeat.wav",
}

var _streams: Dictionary = {}
var _ambient: AudioStreamPlayer
var _sfx_pool: Array[AudioStreamPlayer] = []
var _last_ambient := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for sound_name: String in SOUND_PATHS:
		var path: String = SOUND_PATHS[sound_name]
		var stream: AudioStream = load(path)
		if stream == null:
			push_warning("Не удалось загрузить звук: %s" % path)
			continue
		if loop_sound(sound_name) and stream is AudioStreamWAV:
			var wav := stream as AudioStreamWAV
			wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
			wav.loop_begin = 0
			wav.loop_end = int(wav.get_length() * wav.mix_rate)
		_streams[sound_name] = stream

	_ambient = AudioStreamPlayer.new()
	_ambient.name = "Ambient"
	_ambient.volume_db = -14.0
	add_child(_ambient)
	_ambient.finished.connect(_on_ambient_finished)

	for index in 8:
		var player := AudioStreamPlayer.new()
		player.name = "Sfx%d" % index
		add_child(player)
		_sfx_pool.append(player)


func loop_sound(sound_name: String) -> bool:
	return sound_name == "menu" or sound_name == "hospital"


func play_ambient(sound_name: String) -> void:
	var stream: AudioStream = _streams.get(sound_name)
	if stream == null or _last_ambient == sound_name:
		return
	_last_ambient = sound_name
	_ambient.stop()
	_ambient.stream = stream
	_ambient.pitch_scale = 1.0
	_ambient.volume_db = -22.0
	_ambient.play()
	var tween := create_tween()
	tween.tween_property(_ambient, "volume_db", -12.0, 1.4)


func set_tension(amount: float) -> void:
	if _ambient == null or not _ambient.playing:
		return
	var clamped := clampf(amount, 0.0, 1.0)
	_ambient.pitch_scale = lerpf(0.98, 1.04, clamped)
	_ambient.volume_db = lerpf(-12.0, -5.0, clamped)


func play_sfx(sound_name: String, volume_db: float = -4.0, pitch_variation: float = 0.0) -> void:
	var stream: AudioStream = _streams.get(sound_name)
	if stream == null:
		return
	var player := _free_sfx_player()
	player.stream = stream
	player.volume_db = volume_db
	player.pitch_scale = 1.0 + randf_range(-pitch_variation, pitch_variation)
	player.play()


func stop_all() -> void:
	_ambient.stop()
	_last_ambient = ""
	for player in _sfx_pool:
		player.stop()


func _free_sfx_player() -> AudioStreamPlayer:
	for player in _sfx_pool:
		if not player.playing:
			return player
	return _sfx_pool[0]


func _on_ambient_finished() -> void:
	if _last_ambient != "":
		_ambient.play()