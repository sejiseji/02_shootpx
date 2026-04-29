from __future__ import annotations

from dataclasses import dataclass

import pyxel


@dataclass(frozen=True)
class SoundEvent:
    sound_id: int
    priority: int
    cooldown: int
    est_frames: int
    channel: int | None = None


class AudioSystem:
    CH_BGM_MAIN = 0
    CH_BGM_SUB = 1
    CH_IMPORTANT = 2
    CH_DECOR = 3
    BGM_CHANNELS = (CH_BGM_MAIN, CH_BGM_SUB, CH_IMPORTANT)

    PRIORITY_C = 0
    PRIORITY_B = 1
    PRIORITY_A = 2
    PRIORITY_S = 3

    def __init__(self) -> None:
        self.current_frame = 0
        self.current_bgm: str | None = None
        self.se_cooldowns: dict[str, int] = {}
        self.channel_lock_until = {
            self.CH_IMPORTANT: 0,
            self.CH_DECOR: 0,
        }
        self.channel_priority = {
            self.CH_IMPORTANT: -1,
            self.CH_DECOR: -1,
        }

        self._setup_channel_gains()
        self._define_sounds()
        self._define_music()

    def update(self, frame_count: int) -> None:
        self.current_frame = frame_count

    def play_bgm(self, name: str) -> None:
        if name == self.current_bgm:
            return

        bgm_data = self.BGM_SEQUENCES.get(name)
        if bgm_data is None:
            return

        channels, sequences = bgm_data
        self.stop_bgm()
        self._apply_bgm_mix(name)
        for channel, sequence in zip(channels, sequences):
            pyxel.play(channel, sequence, loop=True)
        self.current_bgm = name

    def stop_bgm(self) -> None:
        for channel in self.BGM_CHANNELS:
            pyxel.stop(channel)
        self._apply_bgm_mix(None)
        self.current_bgm = None

    def play_se(self, name: str) -> bool:
        event = self.SE_EVENTS.get(name)
        if event is None:
            return False

        if self.current_frame < self.se_cooldowns.get(name, -9999):
            return False

        channel = event.channel
        if channel is None:
            channel = self.CH_IMPORTANT if event.priority >= self.PRIORITY_A else self.CH_DECOR
        if self.current_bgm == "bgm_reward" and name in {"ui_move", "ui_confirm"}:
            channel = self.CH_DECOR
        if (
            self.current_frame < self.channel_lock_until[channel]
            and self.channel_priority[channel] > event.priority
        ):
            return False

        pyxel.play(channel, event.sound_id)
        self.se_cooldowns[name] = self.current_frame + event.cooldown
        self.channel_lock_until[channel] = self.current_frame + event.est_frames
        self.channel_priority[channel] = event.priority
        return True

    def _setup_channel_gains(self) -> None:
        try:
            self._apply_bgm_mix(None)
        except Exception:
            pass

    def _apply_bgm_mix(self, bgm_name: str | None) -> None:
        try:
            pyxel.channels[self.CH_BGM_MAIN].gain = 0.48
            pyxel.channels[self.CH_BGM_SUB].gain = 0.38
            pyxel.channels[self.CH_IMPORTANT].gain = 0.70
            pyxel.channels[self.CH_DECOR].gain = 0.46
            if bgm_name == "bgm_reward":
                pyxel.channels[self.CH_BGM_MAIN].gain = 0.46
                pyxel.channels[self.CH_BGM_SUB].gain = 0.34
                pyxel.channels[self.CH_IMPORTANT].gain = 0.30
                pyxel.channels[self.CH_DECOR].gain = 0.56
            elif bgm_name == "bgm_result":
                pyxel.channels[self.CH_BGM_MAIN].gain = 0.34
                pyxel.channels[self.CH_BGM_SUB].gain = 0.24
                pyxel.channels[self.CH_IMPORTANT].gain = 0.18
                pyxel.channels[self.CH_DECOR].gain = 0.42
        except Exception:
            pass

    def _set_sound(self, sound_id: int, notes: str, tones: str, volumes: str, effects: str, speed: int) -> None:
        pyxel.sounds[sound_id].set(notes, tones, volumes, effects, speed)

    def _define_sounds(self) -> None:
        # BGM: start
        self._set_sound(
            0,
            "c2e2g2e2 a2g2e2d2 f2a2g2e2 d2e2g2a2 c2e2g2e2 a2g2b2a2 g2e2f2e2 d2c2r r",
            "tt",
            "4454 6654 4454 4556 4454 6665 4454 4320",
            "nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnf",
            16,
        )
        self._set_sound(
            1,
            "g1c2e2c2 f2e2c2b1 a1c2e2c2 b1c2d2f2 g1c2e2c2 f2e2g2f2 e2c2d2c2 b1a1r r",
            "pp",
            "3343 5543 3343 3445 3343 5544 3343 3210",
            "nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnf",
            16,
        )
        self._set_sound(
            2,
            "c1r g1r a1r e1r f1r c2r g1r d2r c1r g1r a1r e1r f1r c2r d2r g1r",
            "ss",
            "2233 2233 2233 2233 2233 2233 2233 2233",
            "nfnf nfnf nfnf nfnf nfnf nfnf nfnf nfnf",
            16,
        )
        self._set_sound(
            3,
            "c1r r g1r r a1r r e1r r f1r r c2r r g1r r d2r r",
            "pp",
            "4321 4321 4321 4321 4321 4321 4321 4321",
            "nfnn nfnn nfnn nfnn nfnn nfnn nfnn nfnn",
            16,
        )

        # BGM: stage
        self._set_sound(
            4,
            "e2g2a2b2 a2g2e2g2 d2f2g2a2 b2a2g2f2 e2g2a2b2 a2c3b2a2 g2a2b2d3 c3b2a2g2",
            "tt",
            "4567 7654 4567 7765 4567 7676 4567 7765",
            "nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn",
            13,
        )
        self._set_sound(
            5,
            "b1d2e2g2 f2e2d2b1 a1c2d2f2 g2f2d2c2 b1d2e2g2 f2g2a2f2 e2g2a2c3 b2a2g2e2",
            "ss",
            "3456 6543 3456 6654 3456 6564 3456 6654",
            "nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn",
            13,
        )
        self._set_sound(
            6,
            "e1r b1r d2r a1r d1r a1r c2r g1r e1r b1r d2r a1r g1r d2r e2r b1r",
            "pp",
            "3344 3344 3344 3344 3344 3344 3344 3344",
            "nfnf nfnf nfnf nfnf nfnf nfnf nfnf nfnf",
            13,
        )
        self._set_sound(
            7,
            "e1r r b1r r d2r r a1r r d1r r a1r r c2r r g1r r",
            "pp",
            "4432 4432 4432 4432 4432 4432 4432 4432",
            "nfnn nfnn nfnn nfnn nfnn nfnn nfnn nfnn",
            13,
        )

        # BGM: boss
        self._set_sound(
            8,
            "c2c2g2a2 g2f2d2c2 c2d2f2g2 a2g2f2d2 c2c2g2a2 g2a2b2a2 g2f2e2d2 c2r c2r",
            "pp",
            "6667 7654 5667 7765 6667 7776 6654 5400",
            "nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnf",
            10,
        )
        self._set_sound(
            9,
            "g1g1c2d2 d2c2a1g1 f1g1a1c2 d2c2a1g1 g1g1c2d2 d2f2e2d2 c2b1a1g1 f1r f1r",
            "tt",
            "5556 6543 4556 6543 5556 6655 5432 3200",
            "nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnf",
            10,
        )
        self._set_sound(
            10,
            "c1r g1r c2r g1r f1r c2r d2r a1r c1r g1r c2r g1r f1r c2r g1r d2r",
            "tt",
            "4445 4445 4445 4445 4445 4445 4445 4445",
            "nfnf nfnf nfnf nfnf nfnf nfnf nfnf nfnf",
            10,
        )
        self._set_sound(
            11,
            "c1r r g1r r c2r r g1r r f1r r c2r r d2r r a1r r",
            "ss",
            "3321 3321 3321 3321 3321 3321 3321 3321",
            "nfnn nfnn nfnn nfnn nfnn nfnn nfnn nfnn",
            10,
        )

        # BGM: game over
        self._set_sound(
            34,
            "c3e3g3e3 a2c3e3c3 f2a2c3a2 g2b2d3b2",
            "tt",
            "3444 3444 3444 3444",
            "nnnn nnnn nnnn nnnf",
            30,
        )
        self._set_sound(
            35,
            "c2g2c3g2 a1e2a2e2 f1c2f2c2 g1d2g2d2",
            "pp",
            "3334 3334 3334 3334",
            "nnnn nnnn nnnn nnnf",
            30,
        )
        self._set_sound(
            36,
            "e3r g3r c3r e3r d3r f3r b2r d3r",
            "ss",
            "2223 2223 2223 2223",
            "nfnf nfnf nfnf nfnf",
            30,
        )
        self._set_sound(
            37,
            "c2r r g2r r a1r r e2r r",
            "pp",
            "3221 3221 3221 3221",
            "nfnn nfnn nfnn nfnn",
            30,
        )

        # BGM: reward
        self._set_sound(
            38,
            "e3g3b3d4 c3e3a3c4 d3f3a3d4 c3e3g3c4",
            "tt",
            "3445 4444 3445 4444",
            "nnnn nnnn nnnn nnnf",
            26,
        )
        self._set_sound(
            39,
            "c2e2g2e2 a1c2e2c2 d2f2a2f2 c2e2g2e2",
            "pp",
            "3334 3334 3334 3334",
            "nnnn nnnn nnnn nnnf",
            26,
        )
        self._set_sound(
            40,
            "b3r d4r a3r c4r g3r b3r e4r g4r",
            "pp",
            "3334 3334 3334 3334",
            "nfnf nfnf nfnf nfnf",
            26,
        )
        self._set_sound(
            41,
            "g4r r e4r r d4r r c4r r",
            "pp",
            "4443 4443 4443 4443",
            "nfnn nfnn nfnn nfnn",
            26,
        )

        # BGM: extra phrases to lengthen loops
        self._set_sound(
            42,
            "f2g2a2g2 e2d2c2e2 g2a2b2a2 g2e2d2c2",
            "tt",
            "5556 6544 5567 7654",
            "nnnn nnnn nnnn nnnf",
            16,
        )
        self._set_sound(
            43,
            "c2a1f1a1 g1e1c1e1 d1b1g1b1 c2g1e1c1",
            "pp",
            "3334 3334 3334 3334",
            "nnnn nnnn nnnn nnnf",
            16,
        )
        self._set_sound(
            44,
            "a2b2d3b2 g2a2b2g2 f2g2a2f2 e2g2a2c3",
            "tt",
            "5676 5565 4565 5677",
            "nnnn nnnn nnnn nnnf",
            13,
        )
        self._set_sound(
            45,
            "a1e2g2e2 g1d2f2d2 f1c2e2c2 e1b1d2b1",
            "ss",
            "4445 4445 4445 4445",
            "nnnn nnnn nnnn nnnf",
            13,
        )
        self._set_sound(
            46,
            "d2f2g2a2 g2f2d2c2 a1c2d2f2 g2f2e2d2",
            "pp",
            "6667 7654 5667 6654",
            "nnnn nnnn nnnn nnnf",
            10,
        )
        self._set_sound(
            47,
            "d1r a1r d2r a1r f1r c2r g1r d2r",
            "tt",
            "4445 4445 4445 4445",
            "nfnf nfnf nfnf nfnf",
            10,
        )
        self._set_sound(
            48,
            "a2g2e2c3 g2e2d2b2 f2e2c2a2 g2d2b2g2",
            "tt",
            "3444 3444 3444 3444",
            "nnnn nnnn nnnn nnnf",
            30,
        )
        self._set_sound(
            49,
            "f1c2f2c2 e1b1e2b1 d1a1d2a1 g1d2g2d2",
            "pp",
            "3334 3334 3334 3334",
            "nnnn nnnn nnnn nnnf",
            30,
        )
        self._set_sound(
            50,
            "d3f3a3c4 c3e3g3b3 e3g3b3d4 d3f3a3c4",
            "tt",
            "3445 4444 4556 4444",
            "nnnn nnnn nnnn nnnf",
            26,
        )
        self._set_sound(
            51,
            "b1d2g2d2 a1c2e2c2 c2e2g2e2 b1d2g2d2",
            "pp",
            "3334 3334 3334 3334",
            "nnnn nnnn nnnn nnnf",
            26,
        )
        self._set_sound(
            52,
            "c4b3a3g3 e4d4c4b3 d4c4b3a3 g3a3b3d4",
            "tt",
            "5554 5554 4444 4556",
            "nnnn nnnn nnnn nnnf",
            26,
        )
        self._set_sound(
            53,
            "g1b1d2b1 e1g1c2g1 f1a1d2a1 e1g1c2g1",
            "pp",
            "3334 3334 3334 3334",
            "nnnn nnnn nnnn nnnf",
            26,
        )
        self._set_sound(
            54,
            "d4r g4r c4r e4r b3r d4r a3r c4r",
            "pp",
            "3334 3334 3334 3334",
            "nfnf nfnf nfnf nfnf",
            26,
        )

        # Enemy destroy variants
        self._set_sound(55, "c4g4", "p", "54", "nf", 8)
        self._set_sound(56, "g3c4e4", "p", "544", "nnf", 8)
        self._set_sound(57, "d3a3d4", "s", "443", "nnf", 9)
        self._set_sound(58, "e4b4g4", "p", "545", "fnf", 7)
        self._set_sound(
            59,
            "c4e4g4b4",
            "p",
            "4456",
            "nnnf",
            9,
        )

        # UI / player / items / enemy / boss
        self._set_sound(12, "c4", "p", "4", "n", 8)
        self._set_sound(13, "c4e4g4", "p", "544", "nnf", 10)
        self._set_sound(14, "c4", "p", "5", "n", 6)
        self._set_sound(15, "c4e4g4a4 g4e4d4c4", "t", "4456 6544", "nnnn nnnf", 18)
        self._set_sound(16, "a2c3e3c3 g2b2d3b2", "p", "4444 4444", "nnnn nnnf", 18)
        self._set_sound(17, "a2f2d2", "n", "766", "vff", 10)
        self._set_sound(18, "c4", "p", "5", "f", 5)
        self._set_sound(19, "c4e4g4b4", "p", "4567", "nnvf", 10)
        self._set_sound(20, "c4g4e4", "p", "742", "vff", 12)
        self._set_sound(21, "c2g2c3", "p", "765", "nnf", 10)
        self._set_sound(22, "c2f2a2c3 a2f2c2a1", "n", "7765 6654", "vfff vvff", 11)
        self._set_sound(23, "g4b4", "s", "75", "nf", 8)
        self._set_sound(24, "a2d3a2d3 g2c3g2c3", "s", "7777 7777", "vvvv vvvf", 7)
        self._set_sound(25, "c2g2", "t", "65", "nf", 12)
        self._set_sound(26, "c2", "p", "4", "n", 4)
        self._set_sound(27, "c3e3g3c4 g3e3c3", "p", "5677 7654", "nnvf nnnf", 12)
        self._set_sound(28, "b3a3g3", "s", "666", "vvf", 8)
        self._set_sound(29, "g3f3d3", "p", "666", "vff", 8)
        self._set_sound(30, "c4g3", "n", "65", "ff", 8)
        self._set_sound(31, "c3g3c4e4", "t", "5777", "nnvf", 6)
        self._set_sound(32, "c2g2c3", "n", "776", "vff", 9)
        self._set_sound(33, "g2d3", "p", "76", "vf", 7)
        self._set_sound(60, "c4", "p", "5", "f", 5)
        self._set_sound(61, "e4", "p", "5", "f", 5)
        self._set_sound(62, "g4", "p", "5", "f", 5)
        self._set_sound(63, "g4a4b4d4 c4b4a4g4", "s", "4456 6544", "nnnn nnnf", 18)

    def _define_music(self) -> None:
        self.BGM_SEQUENCES = {
            "bgm_start": ((self.CH_BGM_MAIN, self.CH_BGM_SUB), ([0, 1, 42], [2, 3, 43])),
            "bgm_stage": ((self.CH_BGM_MAIN, self.CH_BGM_SUB), ([4, 5, 44], [6, 7, 45])),
            "bgm_boss": ((self.CH_BGM_MAIN, self.CH_BGM_SUB), ([8, 9, 46], [10, 11, 47])),
            "bgm_game_over": ((self.CH_BGM_MAIN, self.CH_BGM_SUB), ([34, 35, 48], [36, 37, 49])),
            "bgm_result": ((self.CH_BGM_MAIN, self.CH_BGM_SUB), ([34, 35, 48], [36, 37, 49])),
            "bgm_reward": (
                (self.CH_BGM_MAIN, self.CH_BGM_SUB, self.CH_IMPORTANT),
                ([38, 50, 52], [39, 51, 53], [40, 41, 54]),
            ),
            "bgm_fever_arrival": (
                (self.CH_BGM_MAIN, self.CH_BGM_SUB, self.CH_IMPORTANT),
                ([15], [16], [63]),
            ),
        }

        self.SE_EVENTS = {
            "ui_move": SoundEvent(12, self.PRIORITY_B, 4, 6),
            "ui_confirm": SoundEvent(13, self.PRIORITY_A, 6, 12),
            "ui_invalid": SoundEvent(14, self.PRIORITY_A, 6, 6),
            "player_hit": SoundEvent(17, self.PRIORITY_S, 20, 18),
            "item_tea_get": SoundEvent(18, self.PRIORITY_A, 1, 4),
            "weapon_level_up": SoundEvent(19, self.PRIORITY_A, 8, 16),
            "enemy_destroy": SoundEvent(20, self.PRIORITY_B, 3, 8),
            "enemy_destroy_light": SoundEvent(55, self.PRIORITY_B, 3, 8),
            "enemy_destroy_swirl": SoundEvent(56, self.PRIORITY_B, 3, 8),
            "enemy_destroy_heavy": SoundEvent(57, self.PRIORITY_B, 4, 9),
            "enemy_destroy_sharp": SoundEvent(58, self.PRIORITY_B, 3, 7),
            "enemy_destroy_rare": SoundEvent(59, self.PRIORITY_A, 5, 10),
            "bomb_fire": SoundEvent(21, self.PRIORITY_S, 10, 14),
            "bomb_burst": SoundEvent(22, self.PRIORITY_S, 10, 24),
            "laser_fire": SoundEvent(23, self.PRIORITY_S, 10, 10),
            "boss_warning": SoundEvent(24, self.PRIORITY_S, 20, 24),
            "boss_entry": SoundEvent(25, self.PRIORITY_A, 20, 14),
            "boss_hit": SoundEvent(26, self.PRIORITY_A, 2, 4),
            "boss_defeat": SoundEvent(27, self.PRIORITY_S, 20, 24),
            "boss_laser_telegraph": SoundEvent(28, self.PRIORITY_S, 12, 14),
            "boss_dash_telegraph": SoundEvent(29, self.PRIORITY_S, 10, 14),
            "boss_summon": SoundEvent(30, self.PRIORITY_A, 10, 10),
            "weapon_cutin": SoundEvent(31, self.PRIORITY_S, 2, 14),
            "boss_burst_pop": SoundEvent(32, self.PRIORITY_A, 2, 10),
            "boss_burst_low": SoundEvent(33, self.PRIORITY_B, 3, 8),
            "boss_cancel_1": SoundEvent(60, self.PRIORITY_B, 1, 4),
            "boss_cancel_2": SoundEvent(61, self.PRIORITY_B, 1, 4),
            "boss_cancel_3": SoundEvent(62, self.PRIORITY_B, 1, 4),
        }
