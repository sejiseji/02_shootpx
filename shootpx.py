from __future__ import annotations

import math
import random
import sys

import pyxel

from audio_system import AudioSystem
from bitmap_font import (
    big_text_width,
    draw_big_text,
    draw_hud_value_text,
    draw_scaled_text,
    hud_value_text_width,
    scaled_text_width,
)
from boss_system import boss_phase, spawn_boss, update_boss
from effects import EffectManager
from enemy_system import create_enemy, pick_enemy_type, update_enemies
from fireworks import (
    BackgroundFirework,
)
from game_models import (
    ActiveBombVisual,
    BombSpark3D,
    BombField,
    Boss,
    BossDefeatCheer,
    BossDefeatSushi,
    BossBuffState,
    Bullet,
    DrawItem,
    Enemy,
    EnemyBullet,
    EchoShot,
    FeverArrivalEffect,
    FeverArrivalSushi,
    GamePhase,
    BitItem,
    HealItem,
    HomingLaser,
    OrbitPattern,
    OrbitSample,
    OrbitSushiEntry,
    PrecomputedBombFrame,
    PrecomputedBombPattern,
    PrecomputedParticleFrame,
    Player,
    RewardChoice,
    RetreatShadow,
    SettlingSushi,
    SushiSettleEffect,
    WasabiItem,
    WeaponItem,
)
from quaternion_utils import normalize_vector, quaternion_from_axis_angle, rotate_vector_by_quaternion


class ShootGame:
    WIDTH = 360
    HEIGHT = 640
    DISPLAY_SCALE = 2

    HUD_H = 112
    PLAY_TOP = HUD_H + 2
    SIDE_MARGIN = 24

    PLAYER_W = 16
    PLAYER_H = 16
    PLAYER_HALF_W = PLAYER_W // 2
    PLAYER_HALF_H = PLAYER_H // 2
    PLAYER_EDGE_OVERHANG_X = PLAYER_W // 3

    ENEMY_W = 16
    ENEMY_H = 16
    ENEMY_HALF_W = ENEMY_W // 2
    ENEMY_HALF_H = ENEMY_H // 2

    BULLET_R = 3

    PLAYER_START_Y = HEIGHT - 84
    PLAYER_MIN_Y = PLAY_TOP + PLAYER_HALF_H + 10
    PLAYER_MAX_Y = HEIGHT - PLAYER_HALF_H - 18

    PLAYER_MAX_HP = 3
    PLAYER_HP_CAP = 5
    PLAYER_INVINCIBLE_FRAMES = 45

    ENEMY_BULLET_MARGIN = 56
    ENEMY_BULLET_MAX_COUNT = 160
    ENEMY_BULLET_MIN_LIFE = 90
    ENEMY_BULLET_MAX_LIFE = 220

    SHOW_BACKGROUND_FIREWORKS = False

    ENEMY_SPRITE_BANK = 0
    ENEMY_SPRITE_SIZE = 16
    ENEMY_SPRITE_FRAMES = 8
    ENEMY_SPRITE_COLKEY = 11
    ENEMY_ANIM_SEQUENCE = (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 6, 6, 7, 7, 7)
    RESULT_ENEMY_ANIM_SEQUENCE = (
        0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 3,
        3, 3, 4, 4, 4, 4, 5, 5, 5, 6, 6, 6,
        7, 7, 7, 7, 6, 6, 6, 5, 5, 5, 4, 4,
        4, 3, 3, 3, 2, 2, 2, 1, 1, 1, 1, 0,
    )
    ENEMY_ANIM_LINEAR_TYPES = frozenset({"sprint", "aimer"})
    SOURCE_FISH_SPRITE_U = 112
    SOURCE_FISH_SPRITE_V = 0
    SOURCE_FISH_SPRITE_FRAMES = 2
    SOURCE_FISH_ANIM_SEQUENCE = (0, 0, 0, 1, 1, 1, 1, 0, 0, 1)
    RESULT_SOURCE_FISH_ANIM_SEQUENCE = (
        0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
        0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0,
    )
    SOURCE_FISH_ANIM_LINEAR_TYPES = frozenset({"rare", "sprint_fish", "aimer_fish"})
    WASABI_SPRITE_BANK = 0
    WASABI_SPRITE_U = 128
    WASABI_SPRITE_V = 32
    WASABI_SPRITE_SIZE = 16
    WASABI_SPRITE_FRAMES = 4
    WASABI_SPRITE_COLKEY = 0
    SOURCE_FISH_SPRITE_COLUMNS = {
        "tuna_fish": 0,
        "salmon_fish": 1,
        "egg_fish": 2,
        "shrimp_fish": 3,
        "sprint_fish": 4,
        "gunkan_fish": 5,
        "aimer_fish": 6,
    }
    SETTLE_SPARKLE_BANK = 0
    SETTLE_SPARKLE_U = 112
    SETTLE_SPARKLE_V = 32
    SETTLE_SPARKLE_SIZE = 16
    SETTLE_SPARKLE_FRAMES = 4
    SETTLE_SPARKLE_COLKEY = 11
    SETTLE_SPARKLE_COUNT = 10
    SETTLE_SPARKLE_LARGE_COUNT_PER_LAYER = 2
    ORBIT_SPRITE_SIZE = 16
    ORBIT_SHELL_SPARKLE_SCALE = 0.375
    ORBIT_SHELL_SPARKLE_SLOT_COUNT = 18
    ORBIT_SHELL_SPARKLE_DRAW_OFFSET = 4.0
    ORBIT_SHELL_SPARKLE_DRAW_X_OFFSET = -5.0
    ORBIT_SHELL_SPARKLE_DRAW_Y_OFFSET = -5.0

    BOSS_SPRITE_BANK = 1
    BOSS_SPRITE_U = 144
    BOSS_SPRITE_V = 0
    BOSS_SPRITE_W = 32
    BOSS_SPRITE_H = 32
    BOSS_SPRITE_FRAMES = 8
    BOSS_SPRITE_COLKEY = 15
    BOSS_ANIM_SEQUENCE = (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 6, 6, 7, 7)
    RESULT_BOSS_ANIM_SEQUENCE = (
        0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 3,
        3, 3, 4, 4, 4, 4, 5, 5, 5, 6, 6, 6,
        7, 7, 7, 7, 6, 6, 6, 5, 5, 5, 4, 4,
        4, 3, 3, 3, 2, 2, 2, 1, 1, 1, 0, 0,
    )
    BOSS_AURA_CENTER_X_OFFSET = -16
    BOSS_AURA_CENTER_Y_OFFSET = -8
    BOSS_HITBOX_CENTER_X_OFFSET = -4
    BOSS_HITBOX_CENTER_Y_OFFSET = 0
    BOSS_HITBOX_EXTRA_W = 4

    BOSS_TRIGGER_SCORE = 1000
    BOSS_TRIGGER_KILLS = 40
    BOSS_WARNING_TIME = 90
    BOSS_ENTRY_TARGET_Y = PLAY_TOP + 104
    BOSS_MAX_HP = 140
    BOSS_SCORE_VALUE = 1000
    BOSS_DAMAGE_COOLDOWN_FRAMES = 2
    BOSS_DEFEAT_SEQUENCE_FRAMES = 86
    BOSS_PATTERN_INTRO_FRAMES = 56
    BOSS_PATTERN_LABEL_FRAMES = 84
    BOSS_PATTERN_CONFETTI_FRAMES = 104
    BOSS_DEFEAT_CONFETTI_FRAMES = 118
    BOSS_DEFEAT_SUSHI_COUNT = 122
    BOSS_DEFEAT_CHEER_TEXTS = (
        "ARIGATO!!",
        "ARIGATO!!",
        "ARIGATO!!",
        "DAISUKI!!",
        "YATTA---!!",
        "HYAHHO--!!",
        "TASUKATTA!!",
        "WEEEEEI!!",
        "HYAHHO--!!",
        "TASUKATTA!!",
        "THANK YOU!!",
    )
    BOSS_DEFEAT_CHEER_COUNT = 14
    SEIGAIHA_DAMAGE_TAKEN_MULT = 0.88
    ASANOHA_HP_MULT = 1.15
    YAGASURI_MOVE_SPEED_MULT = 1.15
    KARAKUSA_SLOW_FACTOR = 0.85
    KARAKUSA_SLOW_FRAMES = 30
    SHIPPO_SIZE_SCALES = (0.82, 1.0, 1.22)
    START_DEBUG_BOMB_POWER_MENU = False
    START_DEBUG_LASER_COUNT_MENU = False
    START_DEBUG_FEVER_MENU = False
    START_DEBUG_PREFEVER_MENU = False
    START_DEBUG_BOSS_PATTERN_MENU = False
    START_DEBUG_SUB_WEAPON_MENU = False
    DESKTOP_DEBUG_MOBILE_CONTROLS = False

    BOMB_RESTOCK_FLASH_FRAMES = 24
    GAME_OVER_FRAMES = 45

    MOBILE_CTRL_RADIUS = 110
    MOBILE_CTRL_CX = 0
    MOBILE_CTRL_CY = HEIGHT - 1

    MOBILE_RING_INNER_RADIUS = 34
    MOBILE_RING_OUTER_RADIUS = 104
    MOBILE_LASER_ANGLE_START = 52
    MOBILE_LASER_ANGLE_END = 88
    MOBILE_BOMB_ANGLE_START = 10
    MOBILE_BOMB_ANGLE_END = 46

    MOBILE_BTN_R = 18
    MOBILE_LASER_CX = 30
    MOBILE_LASER_CY = HEIGHT - 74
    MOBILE_BOMB_CX = 56
    MOBILE_BOMB_CY = HEIGHT - 38
    MOBILE_PANEL_X = 8
    MOBILE_PANEL_Y = HEIGHT - 50
    MOBILE_PANEL_W = 168
    MOBILE_PANEL_H = 34
    MOBILE_BUTTON_W = 70
    MOBILE_BUTTON_H = 24
    MOBILE_BUTTON_GAP = 8

    TEA_DROP_CHANCE = 0.07
    TEA_FALL_SPEED = 1.35
    TEA_BOB_SPEED = 0.10
    TEA_PICKUP_RADIUS = 13
    TEA_FLASH_FRAMES = 22
    TEA_DROP_BONUS_STEP = 0.03
    HOMING_LASER_DROP_BONUS = 0.025
    WEAPON_ITEM_SWITCH_LOCK_FRAMES = 72
    HEAL_DROP_CANCEL_CHANCE = 0.0025
    HEAL_SPRITE_BANK = 1
    HEAL_SPRITE_U = 80
    HEAL_SPRITE_V = 0
    HEAL_SPRITE_SIZE = 16
    HEAL_SPRITE_FRAMES = 8
    HEAL_SPRITE_COLKEY = 0
    BIT_ITEM_SPRITE_BANK = 1
    BIT_ITEM_SPRITE_U = 96
    BIT_ITEM_SPRITE_V = 0
    BIT_ITEM_SPRITE_SIZE = 16
    BIT_ITEM_SPRITE_FRAMES = 8
    BIT_ITEM_SPRITE_COLKEY = 0
    BIT_ITEM_DROP_CHANCE_ON_RARE = 0.24
    WASABI_ITEM_DROP_CHANCE = 0.028
    WASABI_ITEM_DROP_CHANCE_ON_FISH = 0.055
    WASABI_ITEM_DROP_CHANCE_ON_RARE = 0.24
    BIT_POWER_LEVEL_MAX = 3
    BIT_SLOT_COUNT_MAX = 2
    PLAYER_BIT_SPRITE_BANK = 1
    PLAYER_BIT_SPRITE_U = 16
    PLAYER_BIT_ALT_SPRITE_U = 32
    PLAYER_BIT_SPRITE_V = 0
    PLAYER_BIT_SPRITE_SIZE = 16
    PLAYER_BIT_SPRITE_FRAMES = 8
    PLAYER_BIT_SPRITE_COLKEY = 3
    PLAYER_BIT_X_OFFSET = 28
    PLAYER_BIT_Y_OFFSET = -2
    PLAYER_BIT_LASER_SIDE_ANGLE = 0.0
    PLAYER_BIT_LASER_SIDE_OFFSET_X = 7.0
    PLAYER_BIT_LASER_STEER_DELAY = 4
    WEAPON_OVERDRIVE_CAP = 2

    REWARD_OPTION_COUNT = 4
    REWARD_BOX_W = 292
    REWARD_BOX_H = 68
    REWARD_BOX_GAP = 10
    REWARD_BOX_X = (WIDTH - REWARD_BOX_W) // 2
    REWARD_BOX_START_Y = HUD_H + 106
    REWARD_NOTICE_FRAMES = 72
    REWARD_CUTIN_W = 236
    REWARD_CUTIN_H = 68
    REWARD_CUTIN_Y = HUD_H + 12
    REWARD_CUTIN_SLANT = 28
    REWARD_CUTIN_IN_FRAMES = 10
    REWARD_CUTIN_OUT_FRAMES = 12
    REWARD_DISSOLVE_FRAMES = 18

    PLAYER_SPEED_CAP = 8
    LASER_COOLDOWN_REWARD_STEP = 3
    LASER_COOLDOWN_MIN = 8
    LASER_SHOT_COUNT_MIN = 1
    LASER_SHOT_COUNT_MAX = 3

    WEAPON_FAMILY_FAN = "fan"
    WEAPON_FAMILY_LANCE = "lance"
    WEAPON_FAMILY_RAIN = "rain"
    WEAPON_FAMILY_BEAM = "beam"
    WEAPON_FAMILY_ECHO = "echo"
    WEAPON_FAMILY_ORDER = (
        WEAPON_FAMILY_FAN,
        WEAPON_FAMILY_LANCE,
        WEAPON_FAMILY_RAIN,
        WEAPON_FAMILY_BEAM,
        WEAPON_FAMILY_ECHO,
    )
    BUFF_IDS = ["power", "speed", "rapid", "wide", "guard"]
    BUFF_LABELS = {
        "power": "PWR",
        "speed": "SPD",
        "rapid": "RPD",
        "wide": "WID",
        "guard": "GRD",
    }
    BUFF_NOTICE_DATA = {
        "power": {"accent": 8, "title": "PWR ABSORBED", "desc": "Attack bonus stored"},
        "speed": {"accent": 12, "title": "SPD ABSORBED", "desc": "Move bonus stored"},
        "rapid": {"accent": 10, "title": "RPD ABSORBED", "desc": "Rapid bonus stored"},
        "wide": {"accent": 11, "title": "WID ABSORBED", "desc": "Spread bonus stored"},
        "guard": {"accent": 13, "title": "GRD ABSORBED", "desc": "Guard bonus stored"},
    }
    OVERLOAD_DURATION_FRAMES = 60 * 12
    FEVER_EXTRA_KILL_TARGET = 60
    FEVER_EXTRA_SCORE_TARGET = 2600
    FEVER_SPAWN_INTERVAL_MULT = 0.62
    DEBUG_FEVER_START_LOOP_DEPTH = 5
    FEVER_DECOR_LOOP_FRAMES = 32
    FEVER_DECOR_SIDE_W = 112
    FEVER_DECOR_VISIBLE_W = 46
    FEVER_DECOR_OVERFLOW_W = 34
    FEVER_DECOR_PETAL_COUNT = 18
    FEVER_DECOR_CONFETTI_COUNT = 24
    FEVER_ARRIVAL_FRAMES = 420
    FEVER_ARRIVAL_GATHER_FRAMES = 96
    FEVER_ARRIVAL_HOP_FRAMES = 234
    FEVER_ARRIVAL_SUSHI_COUNT = 72
    FEVER_ARRIVAL_ALIGNED_COUNT = 36
    FEVER_ARRIVAL_WAVE_BANK = 0
    FEVER_ARRIVAL_WAVE_U = 0
    FEVER_ARRIVAL_WAVE_V = 128
    FEVER_ARRIVAL_WAVE_W = 216
    FEVER_ARRIVAL_WAVE_H = 120
    FEVER_ARRIVAL_WAVE_COLKEY = 0
    FEVER_ARRIVAL_WAVE_SCALE = 1.38
    FEVER_ARRIVAL_WAVE_EXTRA_H = 12
    FEVER_ARRIVAL_WAVE_LOOP_FRAMES = 64
    FEVER_ARRIVAL_WAVE_LEFT_X = -112
    FEVER_ARRIVAL_WAVE_OVERFLOW_X = 112
    FEVER_ARRIVAL_WAVE_Y_PAD = 24
    FEVER_ARRIVAL_WAVE_ORBIT_X = 11.0
    FEVER_ARRIVAL_WAVE_ORBIT_Y = 8.0
    FEVER_ARRIVAL_CHEER_TEXTS = (
        ("WASSYOI!", -150, -30, 0),
        ("WASSYOI!", 106, -26, 7),
        ("PACHIPACHI", -162, 2, 12),
        ("GANBAE--!!", 126, 6, 18),
        ("YATTANE!!", -138, 36, 24),
        ("SAIKOU!", 120, 40, 30),
        ("PACHIPACHI", -94, 78, 36),
        ("YATTANE!!", 84, 82, 42),
        ("WASSYOI!", -28, 104, 48),
        ("SAIKOU!", 138, 108, 56),
        ("GANBAE--!!", -158, 112, 64),
        ("PACHIPACHI", 26, 126, 72),
    )
    ECHO_SPEED = 8.0
    ECHO_DAMAGE = 8
    ECHO_MAX_BOUNCE = 3
    ECHO_LIFETIME = 38
    ECHO_LENGTH = 18
    ECHO_COOLDOWN = 11
    ECHO_SPLIT_SPEED = 6.2
    ECHO_SPLIT_LIFETIME = 18
    ECHO_SPLIT_LENGTH = 13
    BOMB_PATTERN_FRAMES = 56
    BOMB_PATTERN_COUNT = 3
    BOMB_VISUAL_DURATION_FRAMES = 96
    BOMB_VISUAL_PLAYBACK_FRAMES = 56
    BOMB_BASE_RADIUS = 30.0
    BOMB_EXPANSION_RADIUS = 128.0
    BOMB_POWER_MIN_LEVEL = 0
    BOMB_POWER_MAX_LEVEL = 2
    BOMB_POWER_SCALES = (0.60, 0.80, 1.0)
    BOMB_PARTICLE_COUNT_OUTER = 88
    BOMB_PARTICLE_COUNT_INNER = 24
    BOMB_PARTICLE_COUNT_TWINKLE = 18
    BOMB_PARTICLE_COUNT_FLOW = 22
    BOMB_PARTICLE_COUNT_RED_SPARKLE = 42
    BOMB_ENABLE_OUTER_LAYER = True
    BOMB_ENABLE_INNER_LAYER = False
    BOMB_ENABLE_TWINKLE_LAYER = False
    BOMB_ENABLE_FLOW_LAYER = True
    BOMB_ENABLE_RED_SPARKLE_LAYER = True
    BOMB_KIND_SPARKLE_FILL = 0
    BOMB_KIND_SPARKLE_OUTLINE = 1
    BOMB_KIND_CROSS = 2
    BOMB_KIND_SQUARE_FILL = 3
    BOMB_KIND_CIRCLE_FILL = 4
    BOMB_KIND_CIRCLE_OUTLINE = 5
    SHOT_LEVEL_SINGLE = 0
    SHOT_LEVEL_DOUBLE = 1
    SHOT_LEVEL_TRIPLE = 2
    SHOT_LEVEL_POWER_SINGLE = 3
    SHOT_LEVEL_POWER_DOUBLE = 4
    SHOT_LEVEL_POWER_TRIPLE = 5
    SHOT_LEVEL_MAX = 5

    WEAPON_FAMILY_DATA = {
        WEAPON_FAMILY_FAN: {
            "name": "FAN",
            "accent": 11,
            "core": 10,
            "outer": 6,
        },
        WEAPON_FAMILY_LANCE: {
            "name": "LANCE",
            "accent": 8,
            "core": 8,
            "outer": 7,
        },
        WEAPON_FAMILY_RAIN: {
            "name": "RAIN",
            "accent": 12,
            "core": 12,
            "outer": 5,
        },
        WEAPON_FAMILY_BEAM: {
            "name": "BEAM",
            "accent": 14,
            "core": 14,
            "outer": 7,
        },
        WEAPON_FAMILY_ECHO: {
            "name": "ECHO",
            "accent": 15,
            "core": 12,
            "outer": 7,
        },
    }

    BOSS_PATTERN_DATA = {
        "seigaiha": {
            "name": "SEIGAIHA",
            "buff": "BOSS TAKES LESS DAMAGE",
            "accent": 12,
            "bg": 1,
            "tile": (2, 0, 80, 32, 32),
            "line": 7,
            "sub": 12,
        },
        "karakusa": {
            "name": "KARAKUSA",
            "buff": "BOSS HITS CAN SLOW YOU",
            "accent": 11,
            "bg": 11,
            "tile": (2, 32, 80, 32, 32),
            "line": 7,
            "sub": 6,
        },
        "shippo": {
            "name": "SHIPPO",
            "buff": "BOSS BULLETS CHANGE SIZE",
            "accent": 10,
            "bg": 7,
            "tile": (2, 64, 80, 32, 32),
            "line": 10,
            "sub": 9,
        },
        "asanoha": {
            "name": "ASANOHA",
            "buff": "BOSS HAS MORE HP",
            "accent": 8,
            "bg": 7,
            "tile": (2, 96, 80, 32, 32),
            "line": 13,
            "sub": 5,
        },
        "yagasuri": {
            "name": "YAGASURI",
            "buff": "BOSS MOVES FASTER",
            "accent": 14,
            "bg": 12,
            "tile": (2, 128, 80, 14, 32),
            "line": 7,
            "sub": 6,
        },
    }

    SUSHI_SCORE = {
        "tuna": 100,
        "salmon": 120,
        "egg": 80,
        "shrimp": 140,
        "gunkan": 160,
        "wasabi": 0,
    }
    SUSHI_DRAW_DATA = {
        "tuna": {"top": 8, "rice": 7, "accent": 15},
        "salmon": {"top": 9, "rice": 7, "accent": 15},
        "egg": {"top": 10, "rice": 7, "accent": 5},
        "shrimp": {"top": 15, "rice": 7, "accent": 8},
        "gunkan": {"top": 2, "rice": 7, "accent": 10},
    }
    ORBIT_PATTERN_COUNT = 2
    ORBIT_PATTERN_LENGTH = 96
    ORBIT_ROTATION_FRAME_COUNT = 96
    ORBIT_BASE_CAPACITY = 10
    ORBIT_BONUS_CAPACITY = 10
    ORBIT_RADIUS_X = 42
    ORBIT_RADIUS_Y = 20
    ORBIT_SETTLE_RADIUS = 36
    ORBIT_SETTLE_INNER_RADIUS = 36
    ORBIT_SETTLE_OUTER_RADIUS = 58
    ORBIT_ORTHO_PHASE_OFFSET_DEG = 18.0
    ORBIT_SETTLE_THRESHOLD = 10
    BARRIER_STOCK_CAP = 3
    SETTLE_PHASE_PREALIGN = 0
    SETTLE_PHASE_ALIGN = 1
    SETTLE_PHASE_GLOW = 2
    SETTLE_PHASE_STOP = 3
    SETTLE_PHASE_BOUNCE = 4
    SETTLE_PHASE_SHAKE = 5
    SETTLE_PHASE_EXPLODE = 6
    SETTLE_PHASE_FINISH = 7
    SETTLE_PREALIGN_FRAMES = 8
    SETTLE_ALIGN_FRAMES = 8
    SETTLE_GLOW_FRAMES = 14
    SETTLE_STOP_FRAMES = 8
    SETTLE_BOUNCE_FRAMES = 22
    SETTLE_SHAKE_FRAMES = 12
    SETTLE_EXPLODE_FRAMES = 24
    SUSHI_COMBO_DEFINITIONS = (
        ("three_piece_set", "THREE PIECE SET"),
        ("red_meat_festival", "RED MEAT FESTIVAL"),
        ("gunkan_festival", "GUNKAN FESTIVAL"),
        ("colorful_set", "COLORFUL SET"),
        ("sea_quintet", "SEA QUINTET"),
    )
    DRIFT_STATE_NORMAL = "normal"
    DRIFT_STATE_ENTERING = "entering"
    DRIFT_STATE_ACTIVE = "active"
    DRIFT_STATE_EXITING = "exiting"
    DRIFT_DIR_NONE = 0
    DRIFT_DIR_LEFT = -1
    DRIFT_DIR_RIGHT = 1
    DRIFT_MAX_ANGLE_DEG = 16.0
    DRIFT_ENTER_FRAMES = 60
    DRIFT_EXIT_FRAMES = 60
    DRIFT_TRIGGER_PROGRESS_RATIO = 0.48
    DRIFT_SPAWN_X_SHIFT = 52
    DRIFT_PLAYER_TILT_X = 3
    DRIFT_PLAYER_BULLET_VX = 0.16
    DRIFT_ENEMY_BULLET_VX = 0.12
    BOSS_RETREAT_FRAMES = 44
    BOSS_RETREAT_SHADOW_COUNT = 6

    ENEMY_SPRITE_COLUMNS = {
        "basic": 0,
        "zigzag": 1,
        "shooter": 2,
        "tank": 3,
        "sprint": 4,
        "spreader": 5,
        "aimer": 6,
        "rare": 2,
    }
    ORBIT_SPRITE_TYPES = (
        "basic",
        "zigzag",
        "shooter",
        "tank",
        "sprint",
        "spreader",
        "aimer",
        "rare",
    )
    RESULT_ENEMY_TYPE_ORDER = (
        "boss",
        "tuna_fish",
        "salmon_fish",
        "egg_fish",
        "shrimp_fish",
        "sprint_fish",
        "gunkan_fish",
        "aimer_fish",
        "basic",
        "zigzag",
        "shooter",
        "tank",
        "sprint",
        "spreader",
        "aimer",
        "rare",
    )
    RESULT_ENEMY_LABELS = {
        "boss": "SUSHI OKE",
        "tuna_fish": "MAGURO FISH",
        "salmon_fish": "HAMACHI FISH",
        "egg_fish": "EGG",
        "shrimp_fish": "NORIMAKI",
        "sprint_fish": "SALMON FISH",
        "gunkan_fish": "SHRIMP",
        "aimer_fish": "SABA FISH",
        "basic": "TORO",
        "zigzag": "HAMACHI",
        "shooter": "TAMAGO",
        "tank": "MAGURO GUNKAN",
        "sprint": "SALMON",
        "spreader": "EBI",
        "aimer": "SABA",
        "rare": "TOKIDOKI BONUS",
    }

    THEMES = {
        "classic_dark": {
            "display_name": "CLASSIC DARK",
            "hud_bg": 2,
            "play_bg": 1,
            "frame": 12,
            "divider": 5,
            "hud_text": 7,
            "hud_accent": 11,
            "star_colors": [7, 10, 11, 12, 13, 14],
        },
        "fresh_night": {
            "display_name": "FRESH NIGHT",
            "hud_bg": 1,
            "play_bg": 5,
            "frame": 6,
            "divider": 11,
            "hud_text": 7,
            "hud_accent": 11,
            "star_colors": [7, 10, 11, 12, 14, 15],
        },
        "violet_sky": {
            "display_name": "VIOLET SKY",
            "hud_bg": 13,
            "play_bg": 2,
            "frame": 12,
            "divider": 6,
            "hud_text": 7,
            "hud_accent": 10,
            "star_colors": [7, 8, 10, 11, 12, 15],
        },
    }

    def __init__(self):
        pyxel.init(
            self.WIDTH,
            self.HEIGHT,
            title="Vertical Shooter Mobile Spec",
            display_scale=self.DISPLAY_SCALE,
        )
        pyxel.mouse(True)
        pyxel.load("shootpx.pyxres")

        self.frame_count = 0
        self.phase = GamePhase.START
        self.audio = AudioSystem()

        self.start_theme_keys = list(self.THEMES.keys())
        self.start_theme_index = self.start_theme_keys.index("fresh_night")
        self.start_weapon_index = 0
        self.start_sub_weapon_index = 0
        self.start_sub_weapon_menu_unlocked = False
        self.carryover_unlocked_weapon_families: list[str] = []
        self.carryover_weapon_levels = {family: -1 for family in self.WEAPON_FAMILY_ORDER}
        self.carryover_current_weapon_family: str | None = None
        self.carryover_active_weapon_slots: list[str] = []
        self.start_bomb_power_index = self.BOMB_POWER_MAX_LEVEL
        self.start_laser_count_index = 0
        self.start_fever_enabled = False
        self.start_prefever_enabled = False
        self.start_boss_pattern_index = 0
        self.start_menu_focus = 0
        self.theme_name = self.start_theme_keys[self.start_theme_index]
        self._apply_theme(self.theme_name)

        self.stars = self._build_stars(84)
        self.fireworks: list[BackgroundFirework] = []
        self.firework_spawn_timer = random.randrange(50, 100)
        self.max_fireworks = 3

        self.effects = EffectManager(max_effects=96)
        self.fever_decor_sheet_image = None
        self.fever_decor_frame_w = 0
        self.fever_decor_frame_h = 0
        self.fever_decor_sheet_cols = 0
        self.fever_arrival_wave_left_sheet = None
        self.fever_arrival_wave_right_sheet = None
        self.fever_arrival_wave_frame_w = 0
        self.fever_arrival_wave_frame_h = 0
        self.fever_arrival_wave_sheet_cols = 0
        self.settle_sparkle_back_sheet_image = None
        self.settle_sparkle_front_sheet_image = None
        self.settle_sparkle_frame_w = 0
        self.settle_sparkle_frame_h = 0
        self.settle_sparkle_sheet_cols = 0
        self.orbit_enemy_sprite_sheet = None
        self._build_fever_decor_sheet()
        self._build_fever_arrival_wave_sheet()
        self._build_settle_sparkle_sheet()
        self._build_orbit_enemy_sprite_sheet()
        self.orbit_patterns: list[OrbitPattern] = []
        self.current_orbit_pattern_id = 0
        self.pending_orbit_pattern_build = 0

        self._reset_play_state()
        self.audio.play_bgm("bgm_start")
        pyxel.run(self.update, self.draw)

    def _reset_play_state(self) -> None:
        self.player = Player(
            x=self.WIDTH // 2,
            y=self.PLAYER_START_Y,
            hp=self.PLAYER_MAX_HP,
            max_hp=self.PLAYER_MAX_HP,
            speed_x=5,
            speed_y=5,
            shoot_cooldown=0,
            is_hit=False,
            invincible_timer=0,
        )

        self.bullets: list[Bullet] = []
        self.enemy_bullets: list[EnemyBullet] = []
        self.enemies: list[Enemy] = []
        self.bombs: list[BombField] = []
        self.homing_lasers: list[HomingLaser] = []
        self.echo_shots: list[EchoShot] = []
        self.weapon_items: list[WeaponItem] = []
        self.heal_items: list[HealItem] = []
        self.bit_items: list[BitItem] = []
        self.wasabi_items: list[WasabiItem] = []
        self.boss: Boss | None = None

        self.effects.clear()

        self.score = 0
        self.enemy_kill_count = 0
        self.boss_defeat_count = 0
        self.kill_counts_by_type: dict[str, int] = {}

        self.touch_active = False
        self.prev_touch_down = False
        self.touch_drag_active = False
        self.shoot_suppressed = False

        self.spawn_timer = 0
        self.spawn_interval_sec = 0.62
        self.shoot_interval_frames = 6
        self.bullet_speed = 10

        self.base_bomb_cap = 3
        self.bomb_bonus_cap = 0
        self.bomb_power_level = self._selected_start_bomb_power_level()
        self.bomb_stock = self._bomb_capacity()
        self.bomb_active_limit = 1
        self.bomb_restock_flash_timer = 0

        self.laser_shot_count = self._selected_start_laser_count()
        self.laser_active_limit = 6
        self.laser_cooldown_frames = 24
        self.laser_cooldown = 0
        self.echo_cooldown = 0
        self.player_bit_levels = [0, 0]

        self.prev_mobile_bomb_pressed = False
        self.prev_mobile_laser_pressed = False

        self.boss_intro_timer = 0
        self.boss_event_started = False
        self.boss_defeated = False
        self.game_over_timer = self.GAME_OVER_FRAMES

        self.boss_hp_display = 0.0
        self.boss_hp_trail = 0.0
        self.boss_hp_shake_timer = 0
        self.boss_hp_flash_timer = 0
        self.boss_damage_cooldown = 0
        self.boss_cancel_chain_timer = 0
        self.boss_cancel_chain_step = 0
        self.boss_defeat_timer = 0
        self.boss_defeat_confetti_timer = 0
        self.boss_defeat_x = 0.0
        self.boss_defeat_y = 0.0
        self.boss_defeat_scale = 1.0
        self.boss_defeat_sushis: list[BossDefeatSushi] = []
        self.boss_defeat_cheers: list[BossDefeatCheer] = []
        self.fever_arrival_pending = False
        self.fever_arrival_effect = FeverArrivalEffect()
        self.boss_pattern_id: str | None = None
        self.boss_pattern_transition_timer = 0
        self.boss_pattern_label_timer = 0
        self.boss_pattern_confetti_timer = 0
        self.boss_pattern_name = ""
        self.boss_pattern_buff = ""
        self.boss_pattern_accent = 10
        self.boss_damage_taken_multiplier = 1.0
        self.boss_move_speed_multiplier = 1.0
        self.boss_shippo_enabled = False
        self.boss_slow_inflict_enabled = False
        self.player_slow_timer = 0
        self.player_slow_factor = 1.0
        self.orbit_sushi_queue: list[OrbitSushiEntry] = []
        self.orbit_acquire_counter = 0
        self.orbit_base_index = 0
        self.orbit_rotation_speed_index = 1
        self.orbit_spin_phase = 0.0
        self.orbit_spin_speed = 0.24
        self.wasabi_capacity_boost_active = False
        self.current_orbit_capacity = self.ORBIT_BASE_CAPACITY
        self.sushi_settle_threshold = self.current_orbit_capacity
        self.sushi_settle_effect = SushiSettleEffect(active=False, sushis=[])
        self.combo_counts: dict[str, int] = {}
        self.wasabi_pickup_count = 0
        self.barrier_stock = 0
        self.combat_progress_score = 0
        self.retreat_shadows: list[RetreatShadow] = []
        self.drift_state = self.DRIFT_STATE_NORMAL
        self.drift_direction = self.DRIFT_DIR_NONE
        self.drift_amount = 0.0
        self.drift_triggered_this_loop = False
        self.drift_exit_pending = False
        self.enemy_loop_start_kills = self.enemy_kill_count
        self.enemy_loop_start_score = self.combat_progress_score
        self.boss_retreat_timer = 0
        if not self.orbit_patterns:
            self.orbit_patterns = [self.build_orbit_pattern(1000, "orbit_a")]
            self.pending_orbit_pattern_build = max(0, self.ORBIT_PATTERN_COUNT - len(self.orbit_patterns))
        else:
            self.pending_orbit_pattern_build = max(0, self.ORBIT_PATTERN_COUNT - len(self.orbit_patterns))
        self.boss_buff_state = BossBuffState()
        if self.START_DEBUG_FEVER_MENU and self.start_fever_enabled:
            self.boss_buff_state.overload_active = True
            self.boss_buff_state.overload_timer = 0
            self.boss_buff_state.fever_barrier_hits = 2
            self.boss_buff_state.acquired_cycle_buffs = set(self.BUFF_IDS)
        elif self.START_DEBUG_PREFEVER_MENU and self.start_prefever_enabled:
            self.boss_buff_state.overload_active = False
            self.boss_buff_state.overload_timer = 0
            self.boss_buff_state.fever_barrier_hits = 0
            self.boss_buff_state.acquired_cycle_buffs = set(self.BUFF_IDS[:4])
            self.player_bit_levels = [1, 1]

        self.boss_spawn_count = 0
        self.next_boss_kill_threshold = self.BOSS_TRIGGER_KILLS
        self.next_boss_score_threshold = self.BOSS_TRIGGER_SCORE
        if self.START_DEBUG_FEVER_MENU and self.start_fever_enabled:
            self.boss_spawn_count = self.DEBUG_FEVER_START_LOOP_DEPTH
            self.next_boss_kill_threshold = self.BOSS_TRIGGER_KILLS * (self.DEBUG_FEVER_START_LOOP_DEPTH + 1)
            self.next_boss_score_threshold = self.BOSS_TRIGGER_SCORE
            for step in range(1, self.DEBUG_FEVER_START_LOOP_DEPTH + 1):
                self.next_boss_score_threshold += (step + 1) * 1000
            self.spawn_interval_sec = max(0.28, self.spawn_interval_sec - 0.04 * self.DEBUG_FEVER_START_LOOP_DEPTH)
        elif self.START_DEBUG_PREFEVER_MENU and self.start_prefever_enabled:
            pref_depth = max(0, self.DEBUG_FEVER_START_LOOP_DEPTH - 1)
            self.boss_spawn_count = pref_depth
            self.next_boss_kill_threshold = self.BOSS_TRIGGER_KILLS * (pref_depth + 1)
            self.next_boss_score_threshold = self.BOSS_TRIGGER_SCORE
            for step in range(1, pref_depth + 1):
                self.next_boss_score_threshold += (step + 1) * 1000
            self.spawn_interval_sec = max(0.28, self.spawn_interval_sec - 0.04 * pref_depth)

        self._sync_start_preview_weapon_state()
        self.shot_pick_flash_timer = 0
        self.tea_drop_bonus = 0.0

        self.reward_choices: list[RewardChoice] = []
        self.reward_selection_index = 0
        self.reward_notice_label = "REWARD GET"
        self.reward_notice_text = ""
        self.reward_notice_desc = ""
        self.reward_notice_accent = 10
        self.reward_notice_kind = "reward"
        self.reward_notice_timer = 0
        self.reward_intro_timer = 0
        self.reward_pair_preview_index = 0
        self.bomb_pattern_seed_cursor = 0
        self.next_bomb_pattern_cursor = 0
        self.bomb_patterns: list[PrecomputedBombPattern] = []
        self.active_bomb_visuals: list[ActiveBombVisual] = []
        self.pending_bomb_pattern_build = 0
        self._rebuild_bomb_patterns(build_all=True)
        self.debug_forced_boss_pattern = self._selected_start_boss_pattern()
        self._begin_enemy_loop(after_boss=False)

    def _apply_theme(self, theme_name: str) -> None:
        theme = self.THEMES.get(theme_name, self.THEMES["fresh_night"])
        self.theme_name = theme_name
        self.theme_display_name = theme["display_name"]
        self.hud_bg_color = theme["hud_bg"]
        self.play_bg_color = theme["play_bg"]
        self.frame_color = theme["frame"]
        self.divider_color = theme["divider"]
        self.hud_text_color = theme["hud_text"]
        self.hud_accent_color = theme["hud_accent"]
        self.star_colors = list(theme["star_colors"])

    def _set_theme_by_index(self, index: int) -> None:
        wrapped = index % len(self.start_theme_keys)
        self.start_theme_index = wrapped
        self._apply_theme(self.start_theme_keys[wrapped])
        self._recolor_stars()

    def _move_theme_selection(self, delta: int) -> None:
        self._set_theme_by_index(self.start_theme_index + delta)
        self.audio.play_se("ui_move")

    def _debug_mode_active(self) -> bool:
        return (
            self.DESKTOP_DEBUG_MOBILE_CONTROLS
            or self.START_DEBUG_SUB_WEAPON_MENU
            or self.START_DEBUG_BOMB_POWER_MENU
            or self.START_DEBUG_LASER_COUNT_MENU
            or self.START_DEBUG_FEVER_MENU
            or self.START_DEBUG_PREFEVER_MENU
            or self.START_DEBUG_BOSS_PATTERN_MENU
        )

    def _has_weapon_progress_carryover(self) -> bool:
        return bool(self.carryover_unlocked_weapon_families)

    def _start_weapon_choices(self) -> list[str]:
        if self._debug_mode_active():
            return list(self.WEAPON_FAMILY_ORDER)
        if self._has_weapon_progress_carryover():
            return list(self.carryover_unlocked_weapon_families)
        return list(self.WEAPON_FAMILY_ORDER)

    def _selected_start_weapon_family(self) -> str:
        choices = self._start_weapon_choices()
        if not choices:
            return self.WEAPON_FAMILY_FAN
        return choices[self.start_weapon_index % len(choices)]

    def _set_start_weapon_by_index(self, index: int) -> None:
        choices = self._start_weapon_choices()
        if not choices:
            self.start_weapon_index = 0
            return
        self.start_weapon_index = index % len(choices)

    def _move_start_weapon_selection(self, delta: int) -> None:
        self._set_start_weapon_by_index(self.start_weapon_index + delta)
        self._sync_start_preview_weapon_state()
        self.audio.play_se("ui_move")

    def _start_sub_weapon_menu_enabled(self) -> bool:
        return self.START_DEBUG_SUB_WEAPON_MENU and (
            self.start_sub_weapon_menu_unlocked or self._debug_mode_active()
        )

    def _start_sub_weapon_choices(self) -> list[str | None]:
        return [None, *self._start_weapon_choices()]

    def _selected_start_sub_weapon(self) -> str | None:
        choices = self._start_sub_weapon_choices()
        selected = choices[self.start_sub_weapon_index % len(choices)]
        main_family = self._selected_start_weapon_family()
        if selected == main_family:
            return None
        return selected

    def _start_sub_weapon_label(self) -> str:
        family = self._selected_start_sub_weapon()
        return "-----" if family is None else self._weapon_name(family)

    def _start_sub_weapon_accent(self) -> int:
        family = self._selected_start_sub_weapon()
        return 5 if family is None else self._weapon_accent(family)

    def _move_start_sub_weapon_selection(self, delta: int) -> None:
        choices = self._start_sub_weapon_choices()
        self.start_sub_weapon_index = (self.start_sub_weapon_index + delta) % len(choices)
        self._sync_start_preview_weapon_state()
        self.audio.play_se("ui_move")

    def _sync_start_preview_weapon_state(self) -> None:
        start_family = self._selected_start_weapon_family()
        start_sub_family = self._selected_start_sub_weapon()
        if self._has_weapon_progress_carryover():
            self.current_weapon_family = start_family
            if self._debug_mode_active():
                self.unlocked_weapon_families = list(self.WEAPON_FAMILY_ORDER)
                self.weapon_levels = {
                    family: max(self.SHOT_LEVEL_SINGLE, self.carryover_weapon_levels.get(family, -1))
                    for family in self.WEAPON_FAMILY_ORDER
                }
            else:
                self.unlocked_weapon_families = list(self.carryover_unlocked_weapon_families)
                self.weapon_levels = {
                    family: self.carryover_weapon_levels.get(family, -1)
                    for family in self.WEAPON_FAMILY_ORDER
                }
            self.active_weapon_slots = [start_family]
            if start_sub_family is not None:
                self.active_weapon_slots.append(start_sub_family)
        else:
            self.current_weapon_family = start_family
            if self._debug_mode_active():
                self.unlocked_weapon_families = list(self.WEAPON_FAMILY_ORDER)
                self.weapon_levels = {
                    family: self.SHOT_LEVEL_SINGLE
                    for family in self.WEAPON_FAMILY_ORDER
                }
            else:
                self.unlocked_weapon_families = [start_family]
                self.weapon_levels = {
                    family: (self.SHOT_LEVEL_SINGLE if family == start_family else -1)
                    for family in self.WEAPON_FAMILY_ORDER
                }
            self.active_weapon_slots = [start_family]
            if start_sub_family is not None:
                if start_sub_family not in self.unlocked_weapon_families:
                    self.unlocked_weapon_families.append(start_sub_family)
                self.weapon_levels[start_sub_family] = self.SHOT_LEVEL_SINGLE
                self.active_weapon_slots.append(start_sub_family)

        if self.START_DEBUG_PREFEVER_MENU and self.start_prefever_enabled:
            self.current_weapon_family = self.WEAPON_FAMILY_FAN
            self.active_weapon_slots = [self.WEAPON_FAMILY_FAN]
            if self.WEAPON_FAMILY_FAN not in self.unlocked_weapon_families:
                self.unlocked_weapon_families.insert(0, self.WEAPON_FAMILY_FAN)
            self.weapon_levels[self.WEAPON_FAMILY_FAN] = self.SHOT_LEVEL_MAX
        self.weapon_overdrive_bonus = {family: 0 for family in self.WEAPON_FAMILY_ORDER}
        self.laser_shot_count = (
            3
            if self.START_DEBUG_PREFEVER_MENU and self.start_prefever_enabled
            else self._selected_start_laser_count()
        )

    def _save_weapon_progress_for_restart(self) -> None:
        self.carryover_unlocked_weapon_families = list(self.unlocked_weapon_families)
        self.carryover_weapon_levels = {
            family: self.weapon_levels.get(family, -1)
            for family in self.WEAPON_FAMILY_ORDER
        }
        self.carryover_current_weapon_family = self.current_weapon_family
        self.carryover_active_weapon_slots = list(self.active_weapon_slots[:2])

    def _sync_start_menu_from_carryover(self) -> None:
        if not self._has_weapon_progress_carryover():
            return
        start_choices = self._start_weapon_choices()
        if self.carryover_current_weapon_family in start_choices:
            self.start_weapon_index = start_choices.index(self.carryover_current_weapon_family)
        else:
            self.start_weapon_index = 0

        sub_choices = self._start_sub_weapon_choices()
        sub_family = next(
            (family for family in self.carryover_active_weapon_slots if family != self._selected_start_weapon_family()),
            None,
        )
        if sub_family in sub_choices:
            self.start_sub_weapon_index = sub_choices.index(sub_family)
        else:
            self.start_sub_weapon_index = 0

    def _start_menu_max_focus(self) -> int:
        focus = 1
        if self._start_sub_weapon_menu_enabled():
            focus += 1
        if self.START_DEBUG_BOMB_POWER_MENU:
            focus += 1
        if self.START_DEBUG_LASER_COUNT_MENU:
            focus += 1
        if self.START_DEBUG_FEVER_MENU:
            focus += 1
        if self.START_DEBUG_BOSS_PATTERN_MENU:
            focus += 1
        return focus

    def _start_sub_weapon_focus_index(self) -> int | None:
        if not self._start_sub_weapon_menu_enabled():
            return None
        return 2

    def _start_bomb_power_focus_index(self) -> int | None:
        if not self.START_DEBUG_BOMB_POWER_MENU:
            return None
        index = 2
        if self._start_sub_weapon_menu_enabled():
            index += 1
        return index

    def _start_fever_focus_index(self) -> int | None:
        if not self.START_DEBUG_FEVER_MENU:
            return None
        index = 2
        if self._start_sub_weapon_menu_enabled():
            index += 1
        if self.START_DEBUG_BOMB_POWER_MENU:
            index += 1
        if self.START_DEBUG_LASER_COUNT_MENU:
            index += 1
        return index

    def _start_boss_pattern_focus_index(self) -> int | None:
        if not self.START_DEBUG_BOSS_PATTERN_MENU:
            return None
        index = 2
        if self._start_sub_weapon_menu_enabled():
            index += 1
        if self.START_DEBUG_BOMB_POWER_MENU:
            index += 1
        if self.START_DEBUG_LASER_COUNT_MENU:
            index += 1
        if self.START_DEBUG_FEVER_MENU:
            index += 1
        if self.START_DEBUG_PREFEVER_MENU:
            index += 1
        return index

    def _start_debug_extra_rows(self) -> int:
        return (
            int(self._start_sub_weapon_menu_enabled())
            + int(self.START_DEBUG_BOMB_POWER_MENU)
            + int(self.START_DEBUG_LASER_COUNT_MENU)
            + int(self.START_DEBUG_FEVER_MENU)
            + int(self.START_DEBUG_PREFEVER_MENU)
            + int(self.START_DEBUG_BOSS_PATTERN_MENU)
        )

    def _start_bomb_power_choices(self) -> list[int]:
        return list(range(self.BOMB_POWER_MIN_LEVEL, self.BOMB_POWER_MAX_LEVEL + 1))

    def _selected_start_bomb_power_level(self) -> int:
        choices = self._start_bomb_power_choices()
        return choices[self.start_bomb_power_index % len(choices)]

    def _start_bomb_power_label(self) -> str:
        level = self._selected_start_bomb_power_level()
        return f"LV {level + 1}"

    def _start_bomb_power_accent(self) -> int:
        return (9, 10, 8)[self._selected_start_bomb_power_level()]

    def _move_start_bomb_power_selection(self, delta: int) -> None:
        choices = self._start_bomb_power_choices()
        self.start_bomb_power_index = (self.start_bomb_power_index + delta) % len(choices)
        self.audio.play_se("ui_move")

    def _start_laser_count_focus_index(self) -> int | None:
        if not self.START_DEBUG_LASER_COUNT_MENU:
            return None
        index = 2
        if self._start_sub_weapon_menu_enabled():
            index += 1
        if self.START_DEBUG_BOMB_POWER_MENU:
            index += 1
        return index

    def _start_laser_count_choices(self) -> list[int]:
        return list(range(self.LASER_SHOT_COUNT_MIN, self.LASER_SHOT_COUNT_MAX + 1))

    def _selected_start_laser_count(self) -> int:
        choices = self._start_laser_count_choices()
        return choices[self.start_laser_count_index % len(choices)]

    def _start_laser_count_label(self) -> str:
        return str(self._selected_start_laser_count())

    def _start_laser_count_accent(self) -> int:
        return (12, 10, 8)[self._selected_start_laser_count() - 1]

    def _move_start_laser_count_selection(self, delta: int) -> None:
        choices = self._start_laser_count_choices()
        self.start_laser_count_index = (self.start_laser_count_index + delta) % len(choices)
        self.laser_shot_count = self._selected_start_laser_count()
        self.audio.play_se("ui_move")

    def _toggle_start_fever(self) -> None:
        self.start_fever_enabled = not self.start_fever_enabled
        if self.start_fever_enabled:
            self.start_prefever_enabled = False
        self.audio.play_se("ui_move")

    def _start_prefever_focus_index(self) -> int | None:
        if not self.START_DEBUG_PREFEVER_MENU:
            return None
        index = 2
        if self._start_sub_weapon_menu_enabled():
            index += 1
        if self.START_DEBUG_BOMB_POWER_MENU:
            index += 1
        if self.START_DEBUG_LASER_COUNT_MENU:
            index += 1
        if self.START_DEBUG_FEVER_MENU:
            index += 1
        return index

    def _toggle_start_prefever(self) -> None:
        self.start_prefever_enabled = not self.start_prefever_enabled
        if self.start_prefever_enabled:
            self.start_fever_enabled = False
        self.audio.play_se("ui_move")

    def _start_boss_pattern_choices(self) -> list[str | None]:
        return [None, *self.BOSS_PATTERN_DATA.keys()]

    def _selected_start_boss_pattern(self) -> str | None:
        choices = self._start_boss_pattern_choices()
        return choices[self.start_boss_pattern_index % len(choices)]

    def _start_boss_pattern_label(self) -> str:
        pattern_id = self._selected_start_boss_pattern()
        if pattern_id is None:
            return "RANDOM"
        return self.BOSS_PATTERN_DATA[pattern_id]["name"]

    def _start_boss_pattern_accent(self) -> int:
        pattern_id = self._selected_start_boss_pattern()
        if pattern_id is None:
            return 6
        return self.BOSS_PATTERN_DATA[pattern_id]["accent"]

    def _move_start_boss_pattern_selection(self, delta: int) -> None:
        choices = self._start_boss_pattern_choices()
        self.start_boss_pattern_index = (self.start_boss_pattern_index + delta) % len(choices)
        self.audio.play_se("ui_move")

    def _recolor_stars(self) -> None:
        for star in self.stars:
            star[3] = self._random_star_color()

    def _begin_enemy_loop(self, *, after_boss: bool) -> None:
        self.enemy_loop_start_kills = self.enemy_kill_count
        self.enemy_loop_start_score = self.combat_progress_score
        self.drift_triggered_this_loop = False
        if after_boss and self.drift_exit_pending and self.drift_state in {self.DRIFT_STATE_ENTERING, self.DRIFT_STATE_ACTIVE}:
            self.drift_state = self.DRIFT_STATE_EXITING
        elif not after_boss and self.drift_state == self.DRIFT_STATE_EXITING and self.drift_amount <= 0.0:
            self.drift_state = self.DRIFT_STATE_NORMAL

    def _drift_angle_rad(self) -> float:
        return math.radians(self.DRIFT_MAX_ANGLE_DEG) * self.drift_amount * self.drift_direction

    def _drift_x_bias(self, scale: float = 1.0) -> float:
        return math.sin(self._drift_angle_rad()) * scale

    def _update_drift_shift(self) -> None:
        if self.phase != GamePhase.PLAYING:
            return
        if self._is_boss_active():
            if self.drift_state == self.DRIFT_STATE_ENTERING and self.drift_amount >= 0.995:
                self.drift_state = self.DRIFT_STATE_ACTIVE
            return
        if self.boss_intro_timer > 0:
            return

        if self.drift_state == self.DRIFT_STATE_ENTERING:
            self.drift_amount = min(1.0, self.drift_amount + 1.0 / self.DRIFT_ENTER_FRAMES)
            if self.drift_amount >= 0.995:
                self.drift_amount = 1.0
                self.drift_state = self.DRIFT_STATE_ACTIVE
            return

        if self.drift_state == self.DRIFT_STATE_EXITING:
            self.drift_amount = max(0.0, self.drift_amount - 1.0 / self.DRIFT_EXIT_FRAMES)
            if self.drift_amount <= 0.005:
                self.drift_amount = 0.0
                self.drift_direction = self.DRIFT_DIR_NONE
                self.drift_state = self.DRIFT_STATE_NORMAL
                self.drift_exit_pending = False
            return

        if self.drift_state == self.DRIFT_STATE_ACTIVE:
            return

        if self.drift_triggered_this_loop or self.boss_event_started:
            return

        kill_span = max(1, self.next_boss_kill_threshold - self.enemy_loop_start_kills)
        score_span = max(1, self.next_boss_score_threshold - self.enemy_loop_start_score)
        kill_progress = self.enemy_kill_count - self.enemy_loop_start_kills
        score_progress = self.combat_progress_score - self.enemy_loop_start_score
        if (
            kill_progress >= max(4, int(kill_span * self.DRIFT_TRIGGER_PROGRESS_RATIO))
            or score_progress >= max(800, int(score_span * self.DRIFT_TRIGGER_PROGRESS_RATIO))
        ):
            self.drift_triggered_this_loop = True
            self.drift_state = self.DRIFT_STATE_ENTERING
            self.drift_direction = random.choice((self.DRIFT_DIR_LEFT, self.DRIFT_DIR_RIGHT))

    def _boss_retreat_direction(self, index: int) -> tuple[float, float]:
        if self.drift_direction != self.DRIFT_DIR_NONE:
            x_sign = float(self.drift_direction)
        else:
            x_sign = -1.0 if index % 2 == 0 else 1.0
        return (x_sign * random.uniform(1.6, 2.6), -random.uniform(2.4, 3.4))

    def _spawn_boss_retreat_shadows(self) -> None:
        self.retreat_shadows.clear()
        for idx in range(self.BOSS_RETREAT_SHADOW_COUNT):
            vx, vy = self._boss_retreat_direction(idx)
            self.retreat_shadows.append(
                RetreatShadow(
                    x=random.uniform(32.0, self.WIDTH - 32.0),
                    y=random.uniform(self.PLAY_TOP + 24.0, self.PLAY_TOP + 120.0),
                    vx=vx * 0.82,
                    vy=vy * 0.82,
                    enemy_type=random.choice(self.ORBIT_SPRITE_TYPES[:-1]),
                    anim_offset=random.randrange(0, self.ENEMY_SPRITE_FRAMES),
                    anim_dir=random.choice((-1, 1)),
                    display_scale=random.uniform(0.86, 1.10),
                    sprite_variant=random.randrange(0, 7),
                )
            )

    def _start_enemy_retreat_for_boss(self) -> None:
        if not self.enemies:
            return
        for idx, enemy in enumerate(self.enemies):
            enemy.state = "retreating"
            enemy.retreat_vx, enemy.retreat_vy = self._boss_retreat_direction(idx)
            enemy.shoot_cooldown = 999
        self._spawn_boss_retreat_shadows()

    def _update_retreat_shadows(self) -> None:
        if not self.retreat_shadows:
            return
        next_shadows: list[RetreatShadow] = []
        for shadow in self.retreat_shadows:
            if not shadow.active:
                continue
            shadow.x += shadow.vx
            shadow.y += shadow.vy
            if shadow.x < -24 or shadow.x > self.WIDTH + 24 or shadow.y < self.PLAY_TOP - 28:
                continue
            next_shadows.append(shadow)
        self.retreat_shadows = next_shadows

    def _bomb_capacity(self) -> int:
        return self.base_bomb_cap + self.bomb_bonus_cap

    def _fever_active(self) -> bool:
        return self.boss_buff_state.overload_active

    def _bomb_power_scale(self, level: int | None = None) -> float:
        bomb_level = self.bomb_power_level if level is None else level
        bomb_level = max(self.BOMB_POWER_MIN_LEVEL, min(self.BOMB_POWER_MAX_LEVEL, bomb_level))
        return self.BOMB_POWER_SCALES[bomb_level]

    def _bomb_pattern_target_count(self) -> int:
        return max(1, self._bomb_capacity())

    def _rebuild_bomb_patterns(self, *, build_all: bool) -> None:
        target_count = self._bomb_pattern_target_count()
        self.bomb_patterns = []
        self.next_bomb_pattern_cursor = 0

        build_count = target_count if build_all else 1
        for _ in range(build_count):
            self.bomb_patterns.append(self.build_bomb_pattern(self._next_bomb_pattern_seed()))

        self.pending_bomb_pattern_build = max(0, target_count - len(self.bomb_patterns))

    def _on_bomb_capacity_changed(self) -> None:
        self._rebuild_bomb_patterns(build_all=True)

    def _on_bomb_power_changed(self) -> None:
        self.bomb_power_level = max(self.BOMB_POWER_MIN_LEVEL, min(self.BOMB_POWER_MAX_LEVEL, self.bomb_power_level))
        self._rebuild_bomb_patterns(build_all=True)

    def _restock_bombs_full(self) -> None:
        self.bomb_stock = self._bomb_capacity()
        self.bomb_restock_flash_timer = self.BOMB_RESTOCK_FLASH_FRAMES

    def _update_ui_timers(self) -> None:
        if self.bomb_restock_flash_timer > 0:
            self.bomb_restock_flash_timer -= 1
        if self.shot_pick_flash_timer > 0:
            self.shot_pick_flash_timer -= 1
        if self.reward_notice_timer > 0:
            self.reward_notice_timer -= 1
        if self.boss_pattern_transition_timer > 0:
            self.boss_pattern_transition_timer -= 1
        if self.boss_pattern_label_timer > 0:
            self.boss_pattern_label_timer -= 1
        if self.boss_pattern_confetti_timer > 0:
            self.boss_pattern_confetti_timer -= 1

    def build_orbit_pattern(self, seed: int, name: str) -> OrbitPattern:
        rng = random.Random(seed)
        rotation_frames: list[list[OrbitSample]] = []
        shell_rotation_frames: list[list[OrbitSample]] = []
        phase = rng.uniform(0.0, math.tau)
        ring_radius = float(self.ORBIT_RADIUS_X - 6 + rng.randint(-2, 2))
        tilt_axis = normalize_vector(
            rng.uniform(0.72, 0.96),
            rng.uniform(-0.24, 0.24),
            rng.uniform(-0.18, 0.18),
        )
        tilt_angle = rng.uniform(0.46, 0.58)
        tilt_q = quaternion_from_axis_angle(tilt_axis, tilt_angle)
        spin_axis = normalize_vector(
            rng.uniform(0.20, 0.55),
            rng.uniform(0.64, 0.94),
            rng.uniform(0.26, 0.62),
        )
        spin_phase = rng.uniform(0.0, math.tau)
        spin_speed = rng.uniform(0.85, 1.18)
        orbit_phase = rng.uniform(0.0, math.tau)
        projection_scale = rng.uniform(0.012, 0.017)
        vertical_bias = 1.0
        shell_init_q = quaternion_from_axis_angle((1.0, 0.0, 0.0), math.pi * 0.5)
        local_main_points: list[tuple[float, float, float]] = []
        local_shell_points: list[tuple[float, float, float]] = []

        for idx in range(self.ORBIT_PATTERN_LENGTH):
            angle = phase + math.tau * idx / self.ORBIT_PATTERN_LENGTH
            orbit_x = math.cos(orbit_phase + angle) * ring_radius
            orbit_y = math.sin(orbit_phase + angle) * ring_radius
            main_local = (orbit_x, orbit_y, 0.0)
            shell_local = rotate_vector_by_quaternion(main_local, shell_init_q)
            local_main_points.append(main_local)
            local_shell_points.append(shell_local)

        for frame_idx in range(self.ORBIT_ROTATION_FRAME_COUNT):
            frame_samples: list[OrbitSample] = []
            shell_frame_samples: list[OrbitSample] = []
            ring_spin_angle = spin_phase + math.tau * (frame_idx / self.ORBIT_ROTATION_FRAME_COUNT) * spin_speed
            spin_q = quaternion_from_axis_angle(spin_axis, ring_spin_angle)
            for idx in range(self.ORBIT_PATTERN_LENGTH):
                tilted_x, tilted_y, tilted_z = rotate_vector_by_quaternion(local_main_points[idx], tilt_q)
                rotated_x, rotated_y, rotated_z = rotate_vector_by_quaternion(
                    (tilted_x, tilted_y, tilted_z),
                    spin_q,
                )
                perspective = 1.0 / (1.0 + max(-22.0, rotated_z) * projection_scale)
                dx = int(round(rotated_x * perspective))
                dy = int(round(rotated_y * perspective * vertical_bias))
                depth = max(-1.3, min(1.3, rotated_z / max(12.0, ring_radius * 0.48)))
                scale = 0.78 + ((depth + 1.0) * 0.18)
                if depth < -0.16:
                    brightness_rank = 0
                elif depth > 0.16:
                    brightness_rank = 2
                else:
                    brightness_rank = 1
                frame_samples.append(
                    OrbitSample(
                        dx=dx,
                        dy=dy,
                        depth=depth,
                        scale=scale,
                        brightness_rank=brightness_rank,
                    )
                )
                tilted_shell_x, tilted_shell_y, tilted_shell_z = rotate_vector_by_quaternion(local_shell_points[idx], tilt_q)
                rotated_shell_x, rotated_shell_y, rotated_shell_z = rotate_vector_by_quaternion(
                    (tilted_shell_x, tilted_shell_y, tilted_shell_z),
                    spin_q,
                )
                shell_perspective = 1.0 / (1.0 + max(-22.0, rotated_shell_z) * projection_scale)
                shell_dx = int(round(rotated_shell_x * shell_perspective))
                shell_dy = int(round(rotated_shell_y * shell_perspective * vertical_bias))
                shell_depth = max(-1.3, min(1.3, rotated_shell_z / max(12.0, ring_radius * 0.48)))
                shell_scale = 0.92 + ((shell_depth + 1.0) * 0.08)
                if shell_depth < -0.16:
                    shell_brightness = 0
                elif shell_depth > 0.16:
                    shell_brightness = 2
                else:
                    shell_brightness = 1
                shell_frame_samples.append(
                    OrbitSample(
                        dx=shell_dx,
                        dy=shell_dy,
                        depth=shell_depth,
                        scale=shell_scale,
                        brightness_rank=shell_brightness,
                    )
                )
            rotation_frames.append(frame_samples)
            shell_rotation_frames.append(shell_frame_samples)

        base_samples = rotation_frames[0] if rotation_frames else []
        return OrbitPattern(
            samples=base_samples,
            rotation_frames=rotation_frames,
            shell_rotation_frames=shell_rotation_frames,
            length=len(base_samples),
            rotation_length=len(rotation_frames),
            name=name,
        )

    def maybe_build_orbit_pattern_in_nonbattle(self) -> None:
        if self.phase != GamePhase.REWARD_SELECT:
            return
        if self.pending_orbit_pattern_build <= 0:
            return
        seed = 2000 + len(self.orbit_patterns) * 173
        self.orbit_patterns.append(self.build_orbit_pattern(seed, f"orbit_{len(self.orbit_patterns)}"))
        self.pending_orbit_pattern_build -= 1

    def add_orbit_sushi(self, enemy: Enemy) -> None:
        self.orbit_sushi_queue.append(
            OrbitSushiEntry(
                sushi_type=enemy.sushi_type,
                enemy_type=enemy.enemy_type,
                acquire_order=self.orbit_acquire_counter,
                anim_offset=enemy.anim_offset,
                anim_dir=enemy.anim_dir,
                display_scale=enemy.display_scale,
                has_wasabi=False,
            )
        )
        self.orbit_acquire_counter += 1

    def _add_wasabi_orbit_entry(self) -> None:
        self.orbit_sushi_queue.append(
            OrbitSushiEntry(
                sushi_type="wasabi",
                enemy_type="rare",
                acquire_order=self.orbit_acquire_counter,
                anim_offset=0,
                anim_dir=1,
                display_scale=1.0,
                has_wasabi=True,
            )
        )
        self.orbit_acquire_counter += 1

    def _set_orbit_capacity(self, capacity: int) -> None:
        self.current_orbit_capacity = max(self.ORBIT_BASE_CAPACITY, capacity)
        self.sushi_settle_threshold = self.current_orbit_capacity

    def _apply_post_settlement_capacity_rules(self, has_wasabi: bool) -> None:
        self.wasabi_capacity_boost_active = has_wasabi
        if has_wasabi:
            self._set_orbit_capacity(self.ORBIT_BASE_CAPACITY + self.ORBIT_BONUS_CAPACITY)
        else:
            self._set_orbit_capacity(self.ORBIT_BASE_CAPACITY)

    def _settlement_combo_ids(self, consumed: list[OrbitSushiEntry]) -> list[str]:
        count_by_type: dict[str, int] = {}
        for entry in consumed:
            count_by_type[entry.sushi_type] = count_by_type.get(entry.sushi_type, 0) + 1

        combo_ids: list[str] = []
        if count_by_type.get("salmon", 0) >= 1 and count_by_type.get("shrimp", 0) >= 1 and count_by_type.get("egg", 0) >= 1:
            combo_ids.append("three_piece_set")
        if count_by_type.get("tuna", 0) >= 3:
            combo_ids.append("red_meat_festival")
        if count_by_type.get("gunkan", 0) >= 2:
            combo_ids.append("gunkan_festival")
        if len([s for s, c in count_by_type.items() if c > 0]) >= 4:
            combo_ids.append("colorful_set")
        if all(count_by_type.get(s, 0) >= 1 for s in ("tuna", "salmon", "egg", "shrimp", "gunkan")):
            combo_ids.append("sea_quintet")
        return combo_ids

    def _record_settlement_combos(self, combo_ids: list[str]) -> None:
        for combo_id in combo_ids:
            self.combo_counts[combo_id] = self.combo_counts.get(combo_id, 0) + 1

    def update_orbit_sushi(self) -> None:
        pattern = self._current_orbit_pattern()
        if pattern.length <= 0:
            return
        self.orbit_base_index = (self.orbit_base_index + self.orbit_rotation_speed_index) % pattern.length
        if pattern.rotation_length > 0:
            self.orbit_spin_phase = (self.orbit_spin_phase + self.orbit_spin_speed) % pattern.rotation_length

    def _current_orbit_pattern(self) -> OrbitPattern:
        if not self.orbit_patterns:
            self.orbit_patterns = [self.build_orbit_pattern(1000, "orbit_a")]
        return self.orbit_patterns[self.current_orbit_pattern_id % len(self.orbit_patterns)]

    def _orbit_render_states(
        self,
        entries: list[OrbitSushiEntry],
        *,
        base_index: int | None = None,
    ) -> list[tuple[OrbitSushiEntry, OrbitSample, float, float, str]]:
        pattern = self._current_orbit_pattern()
        if pattern.length <= 0 or not entries:
            return []

        count = len(entries)
        slot_count = max(1, self.ORBIT_BASE_CAPACITY)
        spacing = max(1, pattern.length // slot_count)
        ortho_offset = int(round((pattern.length / slot_count) * 0.5))
        start = self.orbit_base_index if base_index is None else base_index
        use_interpolated_rotation = bool(pattern.rotation_frames and pattern.rotation_length > 1)
        spin_index = 0
        next_spin_index = 0
        spin_blend = 0.0
        frame_samples = pattern.samples
        next_frame_samples = pattern.samples
        if use_interpolated_rotation:
            spin_pos = self.orbit_spin_phase % pattern.rotation_length
            spin_index = int(math.floor(spin_pos)) % pattern.rotation_length
            next_spin_index = (spin_index + 1) % pattern.rotation_length
            spin_blend = spin_pos - math.floor(spin_pos)
            frame_samples = pattern.rotation_frames[spin_index]
            next_frame_samples = pattern.rotation_frames[next_spin_index]
        elif pattern.rotation_frames:
            frame_samples = pattern.rotation_frames[0]
            next_frame_samples = frame_samples
        if pattern.shell_rotation_frames:
            shell_frame_samples = pattern.shell_rotation_frames[spin_index]
            shell_next_frame_samples = pattern.shell_rotation_frames[next_spin_index]
        else:
            shell_frame_samples = frame_samples
            shell_next_frame_samples = next_frame_samples

        states: list[tuple[OrbitSushiEntry, OrbitSample, float, float, str]] = []

        for idx, entry in enumerate(entries):
            ring_idx = idx % self.ORBIT_BASE_CAPACITY
            use_ortho_ring = idx >= self.ORBIT_BASE_CAPACITY
            ring_kind = "ortho" if use_ortho_ring else "main"
            sample_index = (start + ring_idx * spacing) % pattern.length
            if use_ortho_ring:
                sample_index = (sample_index + ortho_offset) % pattern.length
                sample = shell_frame_samples[sample_index]
                next_sample = shell_next_frame_samples[sample_index]
            else:
                sample = frame_samples[sample_index]
                next_sample = next_frame_samples[sample_index]
            if use_interpolated_rotation:
                dx = sample.dx + (next_sample.dx - sample.dx) * spin_blend
                dy = sample.dy + (next_sample.dy - sample.dy) * spin_blend
                depth = sample.depth + (next_sample.depth - sample.depth) * spin_blend
                scale = sample.scale + (next_sample.scale - sample.scale) * spin_blend
                if depth < -0.16:
                    brightness_rank = 0
                elif depth > 0.16:
                    brightness_rank = 2
                else:
                    brightness_rank = 1
                sample = OrbitSample(
                    dx=int(round(dx)),
                    dy=int(round(dy)),
                    depth=depth,
                    scale=scale,
                    brightness_rank=brightness_rank,
                )
            x = self.player.x + sample.dx
            y = self.player.y + sample.dy
            states.append((entry, sample, x, y, ring_kind))

        return states

    def _orbit_shell_sparkle_states(self) -> list[tuple[OrbitSample, float, float, int]]:
        if self.phase != GamePhase.PLAYING:
            return []
        pattern = self._current_orbit_pattern()
        if pattern.length <= 0 or not pattern.shell_rotation_frames:
            return []

        slot_count = self.ORBIT_SHELL_SPARKLE_SLOT_COUNT
        spacing = max(1, pattern.length // slot_count)
        use_interpolated_rotation = pattern.rotation_length > 1
        spin_pos = self.orbit_spin_phase % max(1, pattern.rotation_length)
        spin_index = int(math.floor(spin_pos)) % max(1, pattern.rotation_length)
        next_spin_index = (spin_index + 1) % max(1, pattern.rotation_length)
        spin_blend = spin_pos - math.floor(spin_pos)
        frame_samples = pattern.shell_rotation_frames[spin_index]
        next_frame_samples = pattern.shell_rotation_frames[next_spin_index]
        states: list[tuple[OrbitSample, float, float, int]] = []

        for idx in range(slot_count):
            sample_index = (self.orbit_base_index + idx * spacing) % pattern.length
            sample = frame_samples[sample_index]
            if use_interpolated_rotation:
                next_sample = next_frame_samples[sample_index]
                dx = sample.dx + (next_sample.dx - sample.dx) * spin_blend
                dy = sample.dy + (next_sample.dy - sample.dy) * spin_blend
                depth = sample.depth + (next_sample.depth - sample.depth) * spin_blend
                scale = sample.scale + (next_sample.scale - sample.scale) * spin_blend
                if depth < -0.16:
                    brightness_rank = 0
                elif depth > 0.16:
                    brightness_rank = 2
                else:
                    brightness_rank = 1
                sample = OrbitSample(
                    dx=int(round(dx)),
                    dy=int(round(dy)),
                    depth=depth,
                    scale=scale,
                    brightness_rank=brightness_rank,
                )
            x = self.player.x + sample.dx
            y = self.player.y + sample.dy
            states.append((sample, x, y, idx))

        return states

    def try_start_sushi_settlement(self) -> None:
        if self.sushi_settle_effect.active:
            return
        if len(self.orbit_sushi_queue) < self.sushi_settle_threshold:
            return

        consumed = list(self.orbit_sushi_queue[: self.sushi_settle_threshold])
        start_states = self._orbit_render_states(consumed)
        self.orbit_sushi_queue = self.orbit_sushi_queue[self.sushi_settle_threshold :]
        self.start_sushi_settle_effect(consumed, start_states)

    def start_sushi_settle_effect(
        self,
        consumed: list[OrbitSushiEntry],
        start_states: list[tuple[OrbitSushiEntry, OrbitSample, float, float, str]],
    ) -> None:
        if not consumed:
            return

        n = len(consumed)
        settle_sushis: list[SettlingSushi] = []
        center_x = self.player.x
        center_y = self.player.y - 2
        base_rotation = -math.pi / 2
        expanded_settlement = n > self.ORBIT_BASE_CAPACITY
        outer_phase_offset = math.radians(self.ORBIT_ORTHO_PHASE_OFFSET_DEG)
        combo_ids = self._settlement_combo_ids(consumed)

        for idx, entry in enumerate(consumed):
            is_outer = expanded_settlement and idx >= self.ORBIT_BASE_CAPACITY
            local_idx = idx % self.ORBIT_BASE_CAPACITY
            theta = base_rotation + (local_idx / self.ORBIT_BASE_CAPACITY) * math.tau
            if is_outer:
                theta += outer_phase_offset
            start_x = center_x
            start_y = center_y
            source_ring = "main"
            if idx < len(start_states):
                _entry, _sample, start_x, start_y, source_ring = start_states[idx]
            target_radius = self.ORBIT_SETTLE_OUTER_RADIUS if is_outer else self.ORBIT_SETTLE_INNER_RADIUS
            target_x = center_x + math.cos(theta) * target_radius
            target_y = center_y + math.sin(theta) * target_radius
            speed = 2.6 + idx * 0.07
            settle_sushis.append(
                SettlingSushi(
                    sushi_type=entry.sushi_type,
                    enemy_type=entry.enemy_type,
                    has_wasabi=entry.has_wasabi,
                    start_x=start_x,
                    start_y=start_y,
                    target_x=target_x,
                    target_y=target_y,
                    current_x=start_x,
                    current_y=start_y,
                    circle_angle=theta,
                    anim_offset=entry.anim_offset,
                    anim_dir=entry.anim_dir,
                    display_scale=entry.display_scale,
                    source_ring=source_ring,
                    radius_group="outer" if is_outer else "inner",
                    jump_delay=idx * 2,
                    explode_vx=math.cos(theta) * speed,
                    explode_vy=math.sin(theta) * speed,
                )
            )

        self.sushi_settle_effect = SushiSettleEffect(
            active=True,
            phase=self.SETTLE_PHASE_PREALIGN,
            timer=0,
            sushis=settle_sushis,
            gained_score=self.calc_sushi_settle_score([entry.sushi_type for entry in consumed]),
            gained_barrier=1,
            center_x=center_x,
            center_y=center_y,
            consumed_has_wasabi=any(entry.has_wasabi for entry in consumed),
            combo_ids=combo_ids,
            expanded_settlement=expanded_settlement,
        )

    def calc_sushi_settle_score(self, consumed_types: list[str]) -> int:
        return sum(self.SUSHI_SCORE.get(sushi_type, 100) for sushi_type in consumed_types)

    def update_sushi_settle_effect(self) -> None:
        effect = self.sushi_settle_effect
        if not effect.active or not effect.sushis:
            return

        effect.timer += 1

        if effect.phase == self.SETTLE_PHASE_PREALIGN:
            t = min(1.0, effect.timer / max(1, self.SETTLE_PREALIGN_FRAMES))
            u = 1.0 - (1.0 - t) * (1.0 - t)
            for sushi in effect.sushis:
                sushi.current_x = sushi.start_x + (sushi.target_x - sushi.start_x) * (0.16 * u)
                sushi.current_y = sushi.start_y + (sushi.target_y - sushi.start_y) * (0.16 * u)
                sushi.offset_x = 0.0
                sushi.offset_y = 0.0
            if effect.timer >= self.SETTLE_PREALIGN_FRAMES:
                effect.phase = self.SETTLE_PHASE_ALIGN
                effect.timer = 0
            return

        if effect.phase == self.SETTLE_PHASE_ALIGN:
            t = min(1.0, effect.timer / self.SETTLE_ALIGN_FRAMES)
            u = 1.0 - (1.0 - t) * (1.0 - t)
            for sushi in effect.sushis:
                sushi.current_x = sushi.start_x + (sushi.target_x - sushi.start_x) * u
                sushi.current_y = sushi.start_y + (sushi.target_y - sushi.start_y) * u
                sushi.offset_x = 0.0
                sushi.offset_y = 0.0
            if effect.timer >= self.SETTLE_ALIGN_FRAMES:
                effect.phase = self.SETTLE_PHASE_GLOW
                effect.timer = 0
            return

        if effect.phase == self.SETTLE_PHASE_GLOW:
            if not effect.score_applied:
                self.score += effect.gained_score
                effect.score_applied = True
            if effect.timer >= self.SETTLE_GLOW_FRAMES:
                effect.phase = self.SETTLE_PHASE_STOP
                effect.timer = 0
            return

        if effect.phase == self.SETTLE_PHASE_STOP:
            if effect.timer >= self.SETTLE_STOP_FRAMES:
                effect.phase = self.SETTLE_PHASE_BOUNCE
                effect.timer = 0
            return

        if effect.phase == self.SETTLE_PHASE_BOUNCE:
            all_done = True
            for sushi in effect.sushis:
                local_timer = effect.timer - sushi.jump_delay
                if local_timer < 0:
                    all_done = False
                    sushi.offset_y = 0.0
                    continue
                if local_timer < self.SETTLE_BOUNCE_FRAMES:
                    all_done = False
                    bounce_ratio = local_timer / self.SETTLE_BOUNCE_FRAMES
                    sushi.offset_y = -abs(math.sin(bounce_ratio * math.tau * 2.0)) * 5.0
                else:
                    sushi.offset_y = 0.0
            if all_done:
                effect.phase = self.SETTLE_PHASE_SHAKE
                effect.timer = 0
            return

        if effect.phase == self.SETTLE_PHASE_SHAKE:
            for idx, sushi in enumerate(effect.sushis):
                sushi.offset_x = -1.0 if (effect.timer + idx) % 2 == 0 else 1.0
                sushi.offset_y = 1.0 if (effect.timer + idx * 2) % 3 == 0 else -1.0
            if effect.timer >= self.SETTLE_SHAKE_FRAMES:
                effect.phase = self.SETTLE_PHASE_EXPLODE
                effect.timer = 0
                for sushi in effect.sushis:
                    sushi.offset_x = 0.0
                    sushi.offset_y = 0.0
            return

        if effect.phase == self.SETTLE_PHASE_EXPLODE:
            for sushi in effect.sushis:
                sushi.current_x += sushi.explode_vx
                sushi.current_y += sushi.explode_vy
            if effect.timer >= self.SETTLE_EXPLODE_FRAMES:
                effect.phase = self.SETTLE_PHASE_FINISH
                effect.timer = 0
            return

        if effect.phase == self.SETTLE_PHASE_FINISH:
            self._record_settlement_combos(effect.combo_ids)
            if self.barrier_stock < self.BARRIER_STOCK_CAP:
                self.add_barrier_stock(effect.gained_barrier)
                self.audio.play_se("weapon_level_up")
            else:
                self.score += effect.gained_score
                self.audio.play_se("item_tea_get")
            self._apply_post_settlement_capacity_rules(effect.consumed_has_wasabi)
            self.sushi_settle_effect = SushiSettleEffect(active=False, sushis=[])

    def add_barrier_stock(self, amount: int) -> None:
        self.barrier_stock = min(self.BARRIER_STOCK_CAP, self.barrier_stock + amount)

    def consume_barrier_if_possible(self) -> bool:
        if self.barrier_stock <= 0:
            return False
        self.barrier_stock -= 1
        self.player.invincible_timer = max(self.player.invincible_timer, 18)
        self._spawn_hit_spark(self.player.x, self.player.y - 2, scale=1.1)
        self.audio.play_se("weapon_level_up")
        return True

    def _random_star_color(self) -> int:
        return random.choice(self.star_colors)

    def _build_stars(self, count: int) -> list[list[int]]:
        stars: list[list[int]] = []
        for _ in range(count):
            stars.append(
                [
                    pyxel.rndi(0, self.WIDTH - 1),
                    pyxel.rndi(0, self.HEIGHT - 1),
                    pyxel.rndi(1, 3),
                    self._random_star_color(),
                ]
            )
        return stars

    def _build_orbit_enemy_sprite_sheet(self) -> None:
        cell = self.ORBIT_SPRITE_SIZE
        rows = len(self.ORBIT_SPRITE_TYPES)
        cols = self.ENEMY_SPRITE_FRAMES
        sheet = pyxel.Image(cell * cols, cell * rows)
        sheet.cls(0)
        src = pyxel.image(self.ENEMY_SPRITE_BANK)

        for row, enemy_type in enumerate(self.ORBIT_SPRITE_TYPES):
            src_u = self.ENEMY_SPRITE_COLUMNS.get(enemy_type, 0) * self.ENEMY_SPRITE_SIZE
            for frame in range(self.ENEMY_SPRITE_FRAMES):
                src_v = frame * self.ENEMY_SPRITE_SIZE
                dst_x = frame * cell
                dst_y = row * cell
                for sy in range(cell):
                    sample_y = min(self.ENEMY_SPRITE_SIZE - 1, int((sy + 0.5) * self.ENEMY_SPRITE_SIZE / cell))
                    for sx in range(cell):
                        sample_x = min(self.ENEMY_SPRITE_SIZE - 1, int((sx + 0.5) * self.ENEMY_SPRITE_SIZE / cell))
                        color = src.pget(src_u + sample_x, src_v + sample_y)
                        if color == self.ENEMY_SPRITE_COLKEY:
                            continue
                        sheet.pset(dst_x + sx, dst_y + sy, color)

        self.orbit_enemy_sprite_sheet = sheet

    def _build_settle_sparkle_sheet(self) -> None:
        total_frames = (
            self.SETTLE_ALIGN_FRAMES
            + self.SETTLE_GLOW_FRAMES
            + self.SETTLE_STOP_FRAMES
            + self.SETTLE_BOUNCE_FRAMES
            + self.SETTLE_SHAKE_FRAMES
            + self.SETTLE_EXPLODE_FRAMES
        )
        frame_w = self.ORBIT_SETTLE_RADIUS * 2 + 64
        frame_h = self.ORBIT_SETTLE_RADIUS * 2 + 64
        origin_x = frame_w // 2
        origin_y = frame_h // 2
        cols = 8
        rows = max(1, math.ceil(total_frames / cols))
        back_sheet = pyxel.Image(frame_w * cols, frame_h * rows)
        front_sheet = pyxel.Image(frame_w * cols, frame_h * rows)
        back_sheet.cls(0)
        front_sheet.cls(0)
        explode_start_frame = (
            self.SETTLE_ALIGN_FRAMES
            + self.SETTLE_GLOW_FRAMES
            + self.SETTLE_STOP_FRAMES
            + self.SETTLE_BOUNCE_FRAMES
            + self.SETTLE_SHAKE_FRAMES
        )

        rng = random.Random(20260315)
        sparkle_specs: list[dict[str, float | int | str]] = []
        slot_count = self.ORBIT_SETTLE_THRESHOLD
        base_rotation = -math.pi / 2
        inner_radius = self.ORBIT_SETTLE_RADIUS - 6.0
        for idx in range(slot_count):
            angle = base_rotation + (idx / max(1, slot_count)) * math.tau
            sparkle_specs.append(
                {
                    "group": "back",
                    "base_angle": angle,
                    "radius": inner_radius + rng.uniform(-0.6, 0.6),
                    "radius_wobble": rng.uniform(0.25, 0.65),
                    "drift": rng.uniform(-0.002, 0.002),
                    "phase": rng.uniform(0.0, math.tau),
                    "anim_phase": idx % self.SETTLE_SPARKLE_FRAMES,
                    "scale": rng.uniform(0.90, 1.0),
                    "sway_x": rng.uniform(0.2, 0.6),
                    "sway_y": rng.uniform(0.2, 0.6),
                    "start_frame": idx,
                    "end_padding": rng.randrange(0, 4),
                    "explode_delay": rng.randrange(0, 2),
                    "explode_push": rng.uniform(16.0, 24.0),
                }
            )

        src = pyxel.image(self.SETTLE_SPARKLE_BANK)
        for frame_idx in range(total_frames):
            cell_x = (frame_idx % cols) * frame_w
            cell_y = (frame_idx // cols) * frame_h
            progress = frame_idx / max(1, total_frames - 1)

            for spec in sparkle_specs:
                start_frame = int(spec["start_frame"])
                end_frame = total_frames - int(spec["end_padding"])
                if frame_idx < start_frame or frame_idx >= end_frame:
                    continue
                base_angle = float(spec["base_angle"])
                angle = (
                    base_angle
                    + math.sin(float(spec["phase"]) + progress * math.tau * 1.20) * 0.10
                    + frame_idx * float(spec["drift"])
                )
                radius = float(spec["radius"]) + math.sin(float(spec["phase"]) + progress * math.tau * 2.1) * float(spec["radius_wobble"])
                radius = max(self.ORBIT_SETTLE_RADIUS * 0.80, min(self.ORBIT_SETTLE_RADIUS * 1.18, radius))
                explode_elapsed = frame_idx - explode_start_frame - int(spec["explode_delay"])
                if explode_elapsed > 0:
                    explode_t = min(1.0, explode_elapsed / max(1, self.SETTLE_EXPLODE_FRAMES - int(spec["explode_delay"])))
                    explode_u = 1.0 - (1.0 - explode_t) * (1.0 - explode_t) * (1.0 - explode_t)
                    radius += float(spec["explode_push"]) * explode_u
                local_x = math.cos(angle) * radius + math.sin(progress * math.tau + float(spec["phase"])) * float(spec["sway_x"])
                local_y = math.sin(angle) * radius + math.cos(progress * math.tau * 0.8 + float(spec["phase"])) * float(spec["sway_y"])
                draw_x = int(round(cell_x + origin_x + local_x))
                draw_y = int(round(cell_y + origin_y + local_y))
                sparkle_frame = ((frame_idx // 2) + int(spec["anim_phase"])) % self.SETTLE_SPARKLE_FRAMES
                src_u = self.SETTLE_SPARKLE_U
                src_v = self.SETTLE_SPARKLE_V + sparkle_frame * self.SETTLE_SPARKLE_SIZE
                scale = float(spec["scale"])
                dest = front_sheet if spec["group"] == "front" else back_sheet
                self._stamp_scaled_sprite_to_image(
                    dest,
                    src,
                    src_u,
                    src_v,
                    self.SETTLE_SPARKLE_SIZE,
                    self.SETTLE_SPARKLE_SIZE,
                    draw_x - int(round((self.SETTLE_SPARKLE_SIZE * scale) / 2)),
                    draw_y - int(round((self.SETTLE_SPARKLE_SIZE * scale) / 2)),
                    scale,
                    self.SETTLE_SPARKLE_COLKEY,
                )
                if explode_elapsed > 0:
                    trail_count = 2
                    trail_scale = 0.5
                    trail_step = 7.0 + explode_u * 8.0
                    for trail_idx in range(trail_count):
                        trail_back = (trail_idx + 1) * trail_step
                        trail_x = draw_x - int(round(math.cos(angle) * trail_back))
                        trail_y = draw_y - int(round(math.sin(angle) * trail_back))
                        self._stamp_scaled_sprite_to_image(
                            dest,
                            src,
                            src_u,
                            src_v,
                            self.SETTLE_SPARKLE_SIZE,
                            self.SETTLE_SPARKLE_SIZE,
                            trail_x - int(round((self.SETTLE_SPARKLE_SIZE * trail_scale) / 2)),
                            trail_y - int(round((self.SETTLE_SPARKLE_SIZE * trail_scale) / 2)),
                            trail_scale,
                            self.SETTLE_SPARKLE_COLKEY,
                        )

        self.settle_sparkle_back_sheet_image = back_sheet
        self.settle_sparkle_front_sheet_image = front_sheet
        self.settle_sparkle_frame_w = frame_w
        self.settle_sparkle_frame_h = frame_h
        self.settle_sparkle_sheet_cols = cols

    def _stamp_scaled_sprite_to_image(
        self,
        dest: pyxel.Image,
        src: pyxel.Image,
        src_u: int,
        src_v: int,
        src_w: int,
        src_h: int,
        dst_x: int,
        dst_y: int,
        scale: float,
        colkey: int,
    ) -> None:
        draw_w = max(1, int(round(src_w * scale)))
        draw_h = max(1, int(round(src_h * scale)))
        for dy in range(draw_h):
            sy = min(src_h - 1, int((dy + 0.5) * src_h / draw_h))
            for dx in range(draw_w):
                sx = min(src_w - 1, int((dx + 0.5) * src_w / draw_w))
                color = src.pget(src_u + sx, src_v + sy)
                if color == colkey:
                    continue
                dest_x = dst_x + dx
                dest_y = dst_y + dy
                if 0 <= dest_x < dest.width and 0 <= dest_y < dest.height:
                    dest.pset(dest_x, dest_y, color)

    def _settle_total_elapsed_frames(self, effect: SushiSettleEffect) -> int:
        phase_offsets = {
            self.SETTLE_PHASE_PREALIGN: 0,
            self.SETTLE_PHASE_ALIGN: self.SETTLE_PREALIGN_FRAMES,
            self.SETTLE_PHASE_GLOW: self.SETTLE_PREALIGN_FRAMES + self.SETTLE_ALIGN_FRAMES,
            self.SETTLE_PHASE_STOP: self.SETTLE_PREALIGN_FRAMES + self.SETTLE_ALIGN_FRAMES + self.SETTLE_GLOW_FRAMES,
            self.SETTLE_PHASE_BOUNCE: self.SETTLE_PREALIGN_FRAMES + self.SETTLE_ALIGN_FRAMES + self.SETTLE_GLOW_FRAMES + self.SETTLE_STOP_FRAMES,
            self.SETTLE_PHASE_SHAKE: self.SETTLE_PREALIGN_FRAMES + self.SETTLE_ALIGN_FRAMES + self.SETTLE_GLOW_FRAMES + self.SETTLE_STOP_FRAMES + self.SETTLE_BOUNCE_FRAMES,
            self.SETTLE_PHASE_EXPLODE: self.SETTLE_PREALIGN_FRAMES + self.SETTLE_ALIGN_FRAMES + self.SETTLE_GLOW_FRAMES + self.SETTLE_STOP_FRAMES + self.SETTLE_BOUNCE_FRAMES + self.SETTLE_SHAKE_FRAMES,
            self.SETTLE_PHASE_FINISH: self.SETTLE_PREALIGN_FRAMES + self.SETTLE_ALIGN_FRAMES + self.SETTLE_GLOW_FRAMES + self.SETTLE_STOP_FRAMES + self.SETTLE_BOUNCE_FRAMES + self.SETTLE_SHAKE_FRAMES + self.SETTLE_EXPLODE_FRAMES,
        }
        return phase_offsets.get(effect.phase, 0) + effect.timer

    def _anim_frame_from_sequence(
        self,
        sequence: tuple[int, ...],
        frame_count_total: int,
        anim_offset: int = 0,
        anim_dir: int = 1,
    ) -> int:
        base_frame = sequence[self.frame_count % len(sequence)]
        return (base_frame * anim_dir + anim_offset) % frame_count_total

    def _anim_frame_linear(
        self,
        step_frames: int,
        frame_count_total: int,
        anim_offset: int = 0,
        anim_dir: int = 1,
    ) -> int:
        base_frame = (self.frame_count // step_frames) % frame_count_total
        return (base_frame * anim_dir + anim_offset) % frame_count_total

    def _orbit_enemy_sprite_uv(self, enemy_type: str, anim_offset: int, anim_dir: int) -> tuple[int, int]:
        try:
            row = self.ORBIT_SPRITE_TYPES.index(enemy_type)
        except ValueError:
            row = 0
        if enemy_type in self.ENEMY_ANIM_LINEAR_TYPES:
            frame = self._anim_frame_linear(4, self.ENEMY_SPRITE_FRAMES, anim_offset, anim_dir)
        else:
            frame = self._anim_frame_from_sequence(
                self.ENEMY_ANIM_SEQUENCE,
                self.ENEMY_SPRITE_FRAMES,
                anim_offset,
                anim_dir,
            )
        return frame * self.ORBIT_SPRITE_SIZE, row * self.ORBIT_SPRITE_SIZE

    def _draw_orbit_enemy_sprite(
        self,
        x: float,
        y: float,
        *,
        enemy_type: str,
        anim_offset: int,
        anim_dir: int,
        scale: float,
    ) -> None:
        if self.orbit_enemy_sprite_sheet is None:
            self._build_orbit_enemy_sprite_sheet()
        u, v = self._orbit_enemy_sprite_uv(enemy_type, anim_offset, anim_dir)
        draw_w = self.ORBIT_SPRITE_SIZE * scale
        draw_h = self.ORBIT_SPRITE_SIZE * scale
        draw_x = int(round(x - draw_w / 2))
        draw_y = int(round(y - draw_h / 2))
        pyxel.blt(
            draw_x,
            draw_y,
            self.orbit_enemy_sprite_sheet,
            u,
            v,
            self.ORBIT_SPRITE_SIZE,
            self.ORBIT_SPRITE_SIZE,
            0,
            0.0,
            scale,
        )

    def _draw_wasabi_sprite(self, x: float, y: float, *, scale: float) -> None:
        frame = (self.frame_count // 3) % self.WASABI_SPRITE_FRAMES
        draw_w = self.WASABI_SPRITE_SIZE * scale
        draw_h = self.WASABI_SPRITE_SIZE * scale
        draw_x = int(round(x - draw_w / 2))
        draw_y = int(round(y - draw_h / 2))
        pyxel.blt(
            draw_x,
            draw_y,
            self.WASABI_SPRITE_BANK,
            self.WASABI_SPRITE_U,
            self.WASABI_SPRITE_V + frame * self.WASABI_SPRITE_SIZE,
            self.WASABI_SPRITE_SIZE,
            self.WASABI_SPRITE_SIZE,
            self.WASABI_SPRITE_COLKEY,
            0.0,
            scale,
        )

    def _make_fever_particle_specs(self) -> list[dict[str, float | int | str]]:
        rng = random.Random(20260314)
        specs: list[dict[str, float | int | str]] = []
        side_w = float(self.FEVER_DECOR_SIDE_W)

        for side in ("left", "right"):
            for _ in range(self.FEVER_DECOR_PETAL_COUNT):
                specs.append(
                    {
                        "side": side,
                        "kind": "petal",
                        "phase": rng.uniform(0.0, 1.0),
                        "base_x": rng.uniform(10.0, side_w - 14.0),
                        "sway": rng.uniform(5.0, 13.0),
                        "wobble": rng.uniform(1.1, 2.0),
                        "inward": rng.uniform(8.0, 30.0),
                        "spin": rng.uniform(0.0, math.tau),
                        "fall_offset": rng.uniform(-18.0, 28.0),
                        "size": rng.choice((1, 1, 2)),
                    }
                )

            confetti_kinds = ["spark_cross", "spark_star", "spark_diamond"] * (self.FEVER_DECOR_CONFETTI_COUNT // 3)
            while len(confetti_kinds) < self.FEVER_DECOR_CONFETTI_COUNT:
                confetti_kinds.append(rng.choice(("spark_cross", "spark_star", "spark_diamond")))
            rng.shuffle(confetti_kinds)

            for idx in range(self.FEVER_DECOR_CONFETTI_COUNT):
                specs.append(
                    {
                        "side": side,
                        "kind": confetti_kinds[idx],
                        "phase": rng.uniform(0.0, 1.0),
                        "base_x": rng.uniform(8.0, side_w - 10.0),
                        "sway": rng.uniform(4.0, 11.0),
                        "wobble": rng.uniform(1.3, 2.4),
                        "inward": rng.uniform(10.0, 34.0),
                        "spin": rng.uniform(0.0, math.tau),
                        "fall_offset": rng.uniform(-24.0, 34.0),
                        "size": rng.choice((1, 1, 2, 2, 3)),
                    }
                )

        return specs

    def _draw_fever_mask(
        self,
        image: pyxel.Image,
        x: int,
        y: int,
        rows: tuple[str, ...],
        color: int,
    ) -> None:
        offset_y = len(rows) // 2
        for row_idx, row in enumerate(rows):
            offset_x = len(row) // 2
            for col_idx, cell in enumerate(row):
                if cell != "#":
                    continue
                image.pset(x + col_idx - offset_x, y + row_idx - offset_y, color)

    def _draw_fever_petal_to_image(
        self,
        image: pyxel.Image,
        x: int,
        y: int,
        size: int,
        fill_color: int,
        accent_color: int,
    ) -> None:
        if size <= 1:
            self._draw_fever_mask(image, x, y, (".#.", "###", ".#."), fill_color)
            image.pset(x, y, accent_color)
            return
        if size == 2:
            self._draw_fever_mask(image, x, y, ("..##.", ".####", "#####", ".####", "..##."), fill_color)
            image.pset(x, y, accent_color)
            image.pset(x + 1, y, accent_color)
            return
        self._draw_fever_mask(image, x, y, ("...##..", "..####.", ".######", "#######", ".######", "..####.", "...##.."), fill_color)
        image.line(x - 1, y, x + 1, y, accent_color)

    def _draw_fever_confetti_to_image(
        self,
        image: pyxel.Image,
        x: int,
        y: int,
        kind: str,
        size: int,
        color: int,
        accent: int,
        phase: float,
    ) -> None:
        if kind == "spark_cross":
            arm = 1 if size <= 1 else (2 if size == 2 else 3)
            image.line(x - arm, y, x + arm, y, color)
            image.line(x, y - arm, x, y + arm, color)
            image.line(x - arm, y + 1, x + arm, y + 1, accent)
            image.line(x + 1, y - arm, x + 1, y + arm, accent)
            image.pset(x, y, 15)
            return

        if kind == "spark_star":
            arm = 2 if size <= 1 else (3 if size == 2 else 4)
            image.line(x - arm, y, x + arm, y, color)
            image.line(x, y - arm, x, y + arm, color)
            image.line(x - arm, y - arm, x + arm, y + arm, accent)
            image.line(x - arm, y + arm, x + arm, y - arm, accent)
            image.pset(x, y, 15)
            return

        span = 2 if size <= 1 else (3 if size == 2 else 4)
        image.line(x - span, y, x, y - span, color)
        image.line(x, y - span, x + span, y, color)
        image.line(x + span, y, x, y + span, color)
        image.line(x, y + span, x - span, y, color)
        image.line(x - span + 1, y, x, y - span + 1, accent)
        image.line(x, y - span + 1, x + span - 1, y, accent)
        image.line(x + span - 1, y, x, y + span - 1, accent)
        image.line(x, y + span - 1, x - span + 1, y, accent)
        if phase > 0.5:
            image.pset(x, y, 15)

    def _build_fever_decor_sheet(self) -> None:
        area_h = self.HEIGHT - self.PLAY_TOP
        side_w = self.FEVER_DECOR_SIDE_W
        frame_w = side_w * 2
        frame_h = area_h
        total_frames = self.FEVER_DECOR_LOOP_FRAMES
        cols = 4
        rows = max(1, math.ceil(total_frames / cols))
        sheet = pyxel.Image(frame_w * cols, frame_h * rows)
        sheet.cls(0)
        specs = self._make_fever_particle_specs()

        for frame_idx in range(total_frames):
            cell_x = (frame_idx % cols) * frame_w
            cell_y = (frame_idx // cols) * frame_h
            loop_t = frame_idx / max(1, total_frames - 1)

            for spec in specs:
                progress = (loop_t + float(spec["phase"])) % 1.0
                depth = 0.30 + 0.70 * progress
                local_y = int(float(spec["fall_offset"]) + progress * (frame_h + 36))
                if local_y < -10 or local_y > frame_h + 10:
                    continue

                sway = math.sin(float(spec["spin"]) + progress * math.tau * float(spec["wobble"])) * float(spec["sway"])
                inward = float(spec["inward"]) * (0.18 + 0.82 * progress)

                if spec["side"] == "left":
                    local_x = int(float(spec["base_x"]) + inward + sway)
                    draw_x = cell_x + max(4, min(side_w - 4, local_x))
                else:
                    local_x = int(frame_w - float(spec["base_x"]) - inward + sway)
                    draw_x = cell_x + max(side_w + 4, min(frame_w - 4, local_x))
                draw_y = cell_y + local_y

                front_size = int(spec["size"])
                size = front_size + 1 if progress > 0.74 and front_size < 3 else front_size

                if spec["kind"] == "petal":
                    fill = 7 if depth < 0.48 else (14 if depth < 0.76 else 15)
                    accent = 8 if depth < 0.60 else 10
                    self._draw_fever_petal_to_image(sheet, draw_x, draw_y, size, fill, accent)
                    continue

                color_pairs = ((7, 1), (10, 7), (11, 1), (14, 7), (15, 10))
                palette_idx = int((float(spec["spin"]) * 10.0) + frame_idx * 0.35) % len(color_pairs)
                base_color, edge_color = color_pairs[palette_idx]
                accent = 15 if depth > 0.72 else edge_color
                self._draw_fever_confetti_to_image(
                    sheet,
                    draw_x,
                    draw_y,
                    str(spec["kind"]),
                    size,
                    base_color,
                    accent,
                    (float(spec["spin"]) + frame_idx * 0.16) % 1.0,
                )

        self.fever_decor_sheet_image = sheet
        self.fever_decor_frame_w = frame_w
        self.fever_decor_frame_h = frame_h
        self.fever_decor_sheet_cols = cols

    def _build_fever_arrival_wave_sheet(self) -> None:
        src = pyxel.image(self.FEVER_ARRIVAL_WAVE_BANK)
        src_u = self.FEVER_ARRIVAL_WAVE_U
        src_v = self.FEVER_ARRIVAL_WAVE_V
        src_w = self.FEVER_ARRIVAL_WAVE_W
        src_h = self.FEVER_ARRIVAL_WAVE_H
        scaled_w = max(1, int(round(src_w * self.FEVER_ARRIVAL_WAVE_SCALE)))
        scaled_h = max(1, int(round(src_h * self.FEVER_ARRIVAL_WAVE_SCALE)) + self.FEVER_ARRIVAL_WAVE_EXTRA_H)
        orbit_x = int(math.ceil(self.FEVER_ARRIVAL_WAVE_ORBIT_X))
        orbit_y = int(math.ceil(self.FEVER_ARRIVAL_WAVE_ORBIT_Y))
        frame_w = scaled_w + orbit_x * 2 + 4
        frame_h = scaled_h + orbit_y * 2 + 4
        cols = 4
        rows = max(1, math.ceil(self.FEVER_ARRIVAL_WAVE_LOOP_FRAMES / cols))
        left_sheet = pyxel.Image(frame_w * cols, frame_h * rows)
        right_sheet = pyxel.Image(frame_w * cols, frame_h * rows)
        left_sheet.cls(0)
        right_sheet.cls(0)

        for frame_idx in range(self.FEVER_ARRIVAL_WAVE_LOOP_FRAMES):
            cell_x = (frame_idx % cols) * frame_w
            cell_y = (frame_idx // cols) * frame_h
            phase = (frame_idx / max(1, self.FEVER_ARRIVAL_WAVE_LOOP_FRAMES)) * math.tau
            left_dx = int(round(math.cos(phase) * self.FEVER_ARRIVAL_WAVE_ORBIT_X))
            left_dy = int(round(math.sin(phase * 1.17) * self.FEVER_ARRIVAL_WAVE_ORBIT_Y))
            right_dx = int(round(math.cos(-phase + 1.35) * self.FEVER_ARRIVAL_WAVE_ORBIT_X))
            right_dy = int(round(math.sin(-phase * 1.11 + 0.55) * self.FEVER_ARRIVAL_WAVE_ORBIT_Y))
            left_x0 = cell_x + orbit_x + 2 + left_dx
            left_y0 = cell_y + orbit_y + 2 + left_dy
            right_x0 = cell_x + orbit_x + 2 + right_dx
            right_y0 = cell_y + orbit_y + 2 + right_dy

            for sy in range(scaled_h):
                sample_y = min(src_h - 1, int((sy + 0.5) * src_h / scaled_h))
                for sx in range(scaled_w):
                    sample_x = min(src_w - 1, int((sx + 0.5) * src_w / scaled_w))
                    color_left = src.pget(src_u + sample_x, src_v + sample_y)
                    if color_left != self.FEVER_ARRIVAL_WAVE_COLKEY:
                        left_sheet.pset(left_x0 + sx, left_y0 + sy, color_left)
                    mirror_x = src_w - 1 - sample_x
                    color_right = src.pget(src_u + mirror_x, src_v + sample_y)
                    if color_right != self.FEVER_ARRIVAL_WAVE_COLKEY:
                        right_sheet.pset(right_x0 + sx, right_y0 + sy, color_right)

        self.fever_arrival_wave_left_sheet = left_sheet
        self.fever_arrival_wave_right_sheet = right_sheet
        self.fever_arrival_wave_frame_w = frame_w
        self.fever_arrival_wave_frame_h = frame_h
        self.fever_arrival_wave_sheet_cols = cols

    def choose_next_boss_buff(self, acquired_cycle_buffs: set[str]) -> str:
        remaining = [buff_id for buff_id in self.BUFF_IDS if buff_id not in acquired_cycle_buffs]
        if not remaining:
            remaining = list(self.BUFF_IDS)
        return random.choice(remaining)

    def _end_fever_cycle(self) -> None:
        self.boss_buff_state.overload_active = False
        self.boss_buff_state.overload_timer = 0
        self.boss_buff_state.fever_barrier_hits = 0
        self.boss_buff_state.acquired_cycle_buffs.clear()

    def assign_buff_to_current_boss(self) -> None:
        if self.boss is None:
            self.boss_buff_state.current_boss_buff = None
            return
        chosen_buff = self.choose_next_boss_buff(self.boss_buff_state.acquired_cycle_buffs)
        self.boss_buff_state.current_boss_buff = chosen_buff
        self.boss.buff_id = chosen_buff

    def absorb_current_boss_buff(self) -> None:
        buff_id = self.boss_buff_state.current_boss_buff
        if not buff_id:
            return
        if self._fever_active():
            self._end_fever_cycle()
        self.boss_buff_state.acquired_cycle_buffs.add(buff_id)
        notice = self.BUFF_NOTICE_DATA.get(
            buff_id,
            {"accent": 10, "title": f"{self.BUFF_LABELS.get(buff_id, 'BUFF')} ABSORBED", "desc": "Boss buff stored"},
        )
        self.audio.play_se("weapon_cutin")
        self._show_notice(
            label="BOSS BUFF",
            title=notice["title"],
            description=notice["desc"],
            accent=notice["accent"],
            kind=f"boss_buff_{buff_id}",
        )
        self.boss_buff_state.current_boss_buff = None
        if len(self.boss_buff_state.acquired_cycle_buffs) >= len(self.BUFF_IDS):
            self.trigger_overload()

    def trigger_overload(self) -> None:
        self.boss_buff_state.overload_active = True
        self.boss_buff_state.overload_timer = 0
        self.boss_buff_state.fever_barrier_hits = 2
        self.fever_arrival_pending = True
        self.audio.play_se("weapon_level_up")

    def update_overload(self) -> None:
        return

    def has_buff(self, buff_id: str) -> bool:
        return self.buff_scale(buff_id) > 0.0

    def buff_scale(self, buff_id: str) -> float:
        if self.boss_buff_state.overload_active:
            return 2.0
        if buff_id in self.boss_buff_state.acquired_cycle_buffs:
            return 1.0
        return 0.0

    def _player_move_bonus(self) -> float:
        return 0.5 * self.buff_scale("speed")

    def _player_damage_multiplier(self) -> float:
        return 1.0 + 0.20 * self.buff_scale("power")

    def _rapid_cooldown_reduction(self) -> int:
        return int(2 * self.buff_scale("rapid"))

    def _wide_scale(self) -> float:
        return 1.0 + 0.20 * self.buff_scale("wide")

    def _guard_damage_ratio(self) -> float:
        return 0.15 * self.buff_scale("guard")

    def _scaled_player_damage(self, base_damage: int) -> int:
        return max(1, int(round(base_damage * self._player_damage_multiplier())))

    def random_point_on_sphere(self, radius: float, rng: random.Random) -> tuple[float, float, float]:
        z = rng.uniform(-1.0, 1.0)
        theta = rng.uniform(0.0, math.tau)
        r_xy = math.sqrt(max(0.0, 1.0 - z * z))
        return (
            radius * r_xy * math.cos(theta),
            radius * r_xy * math.sin(theta),
            radius * z,
        )

    def random_unit_vector_rng(self, rng: random.Random) -> tuple[float, float, float]:
        return self.random_point_on_sphere(1.0, rng)

    def build_size_pool(self, count_small: int, count_mid: int, count_large: int) -> list[int]:
        return [1] * count_small + [2] * count_mid + [3] * count_large

    def build_particle_spec_pool(self, entries: list[tuple[int, int, int]]) -> list[tuple[int, int]]:
        specs: list[tuple[int, int]] = []
        for kind, size, count in entries:
            specs.extend([(kind, size)] * count)
        return specs

    def project_point(self, x: float, y: float, z: float) -> tuple[int, int, float]:
        depth = 1.0 / (1.0 + z * 0.02)
        return int(x * depth), int(y * depth), depth

    def particle_color_and_size(
        self,
        depth: float,
        base_size: int,
        kind: int,
        twinkle: float,
    ) -> tuple[int, int]:
        if kind in {
            self.BOMB_KIND_SPARKLE_FILL,
            self.BOMB_KIND_SPARKLE_OUTLINE,
            self.BOMB_KIND_CROSS,
        }:
            if twinkle > 0.78:
                color = 15
            elif twinkle > 0.52:
                color = 10 if depth > 0.95 else 7
            else:
                color = 6 if depth < 0.92 else 7
        elif kind == self.BOMB_KIND_SQUARE_FILL:
            color = 7 if depth > 0.99 else 10 if depth > 0.94 else 12
        elif kind == self.BOMB_KIND_CIRCLE_OUTLINE:
            color = 11 if depth > 0.97 else 10 if depth > 0.92 else 6
        else:
            color = 7 if depth > 1.00 else 10 if depth > 0.94 else 12

        return color, base_size

    def _bomb_particle_extent(self, particle: PrecomputedParticleFrame) -> int:
        if particle.kind == self.BOMB_KIND_SQUARE_FILL:
            return 1 if particle.size >= 2 else 0
        return max(1, particle.size // 2)

    def _draw_bomb_mask(
        self,
        image: pyxel.Image,
        x: int,
        y: int,
        rows: tuple[str, ...],
        color: int,
    ) -> None:
        offset_y = len(rows) // 2
        for row_idx, row in enumerate(rows):
            offset_x = len(row) // 2
            for col_idx, cell in enumerate(row):
                if cell != "#":
                    continue
                image.pset(x + col_idx - offset_x, y + row_idx - offset_y, color)

    def _draw_bomb_particle_to_image(
        self,
        image: pyxel.Image,
        x: int,
        y: int,
        particle: PrecomputedParticleFrame,
    ) -> None:
        if particle.kind == self.BOMB_KIND_SPARKLE_FILL:
            arm = max(1, particle.size // 2)
            image.line(x - arm, y, x + arm, y, particle.color)
            image.line(x, y - arm, x, y + arm, particle.color)
            image.line(x - arm, y - arm, x + arm, y + arm, particle.color)
            image.line(x - arm, y + arm, x + arm, y - arm, particle.color)
            image.pset(x, y, 15)
            return

        if particle.kind == self.BOMB_KIND_SPARKLE_OUTLINE:
            arm = max(1, particle.size // 2)
            image.line(x - arm, y - arm, x + arm, y + arm, particle.color)
            image.line(x - arm, y + arm, x + arm, y - arm, particle.color)
            image.pset(x - arm, y, particle.color)
            image.pset(x + arm, y, particle.color)
            image.pset(x, y - arm, particle.color)
            image.pset(x, y + arm, particle.color)
            image.pset(x, y, 15)
            return

        if particle.kind == self.BOMB_KIND_CROSS:
            arm = max(1, particle.size // 2)
            image.line(x - arm, y, x + arm, y, particle.color)
            image.line(x, y - arm, x, y + arm, particle.color)
            image.pset(x, y, 15)
            return

        if particle.kind == self.BOMB_KIND_SQUARE_FILL:
            if particle.size <= 1:
                image.pset(x, y, particle.color)
            else:
                image.rect(x - 1, y - 1, 2, 2, particle.color)
            return

        if particle.kind == self.BOMB_KIND_CIRCLE_FILL:
            if particle.size <= 4:
                self._draw_bomb_mask(image, x, y, (".##.", "####", "####", ".##."), particle.color)
            else:
                self._draw_bomb_mask(image, x, y, ("..##..", ".####.", "######", "######", ".####.", "..##.."), particle.color)
            return

        if particle.kind == self.BOMB_KIND_CIRCLE_OUTLINE:
            if particle.size <= 4:
                self._draw_bomb_mask(image, x, y, (".##.", "#..#", "#..#", ".##."), particle.color)
            else:
                self._draw_bomb_mask(image, x, y, ("..##..", ".#..#.", "#....#", "#....#", ".#..#.", "..##.."), particle.color)
            return

    def _build_bomb_frame_sheet(
        self,
        pattern: PrecomputedBombPattern,
        *,
        use_flow_particles: bool,
    ) -> None:
        max_extent = 0
        for frame in pattern.frames:
            particles = frame.flow_particles if use_flow_particles else frame.particles
            for particle in particles:
                pad = self._bomb_particle_extent(particle)
                max_extent = max(max_extent, abs(particle.dx) + pad, abs(particle.dy) + pad)

        frame_pad = 3
        frame_w = max(16, max_extent * 2 + frame_pad * 2 + 1)
        frame_h = max(16, max_extent * 2 + frame_pad * 2 + 1)
        origin_x = frame_w // 2
        origin_y = frame_h // 2

        sheet_cols = min(6, max(1, pattern.total_frames))
        sheet_rows = max(1, math.ceil(pattern.total_frames / sheet_cols))
        sheet = pyxel.Image(frame_w * sheet_cols, frame_h * sheet_rows)
        sheet.cls(0)

        for frame_idx, frame in enumerate(pattern.frames):
            cell_x = (frame_idx % sheet_cols) * frame_w
            cell_y = (frame_idx // sheet_cols) * frame_h
            if use_flow_particles:
                frame.flow_sheet_x = cell_x
                frame.flow_sheet_y = cell_y
                particles = frame.flow_particles
            else:
                frame.sheet_x = cell_x
                frame.sheet_y = cell_y
                particles = frame.particles

            for particle in particles:
                if use_flow_particles:
                    if particle.kind == self.BOMB_KIND_SQUARE_FILL:
                        dx = particle.dx
                        dy = particle.dy
                        start_ratio = 0.10 if particle.size >= 2 else 0.18
                        x0 = cell_x + origin_x + int(dx * start_ratio)
                        y0 = cell_y + origin_y + int(dy * start_ratio)
                        x1 = cell_x + origin_x + dx
                        y1 = cell_y + origin_y + dy
                        sheet.line(x0, y0, x1, y1, particle.color)
                        if particle.size >= 2:
                            sheet.line(x0, y0 + 1, x1, y1 + 1, 7 if particle.color == 15 else particle.color)
                    else:
                        self._draw_bomb_particle_to_image(
                            sheet,
                            cell_x + origin_x + particle.dx,
                            cell_y + origin_y + particle.dy,
                            particle,
                        )
                else:
                    self._draw_bomb_particle_to_image(
                        sheet,
                        cell_x + origin_x + particle.dx,
                        cell_y + origin_y + particle.dy,
                        particle,
                    )

        if use_flow_particles:
            pattern.flow_sheet_image = sheet
            pattern.flow_frame_w = frame_w
            pattern.flow_frame_h = frame_h
            pattern.flow_origin_x = origin_x
            pattern.flow_origin_y = origin_y
        else:
            pattern.sheet_image = sheet
            pattern.frame_w = frame_w
            pattern.frame_h = frame_h
            pattern.origin_x = origin_x
            pattern.origin_y = origin_y

    def _build_bomb_pattern_sheet(self, pattern: PrecomputedBombPattern) -> None:
        self._build_bomb_frame_sheet(pattern, use_flow_particles=False)
        self._build_bomb_frame_sheet(pattern, use_flow_particles=True)

    def build_bomb_pattern(self, seed: int) -> PrecomputedBombPattern:
        rng = random.Random(seed)
        power_scale = self._bomb_power_scale()
        particles: list[BombSpark3D] = []
        flow_particles: list[BombSpark3D] = []

        if self.BOMB_ENABLE_OUTER_LAYER:
            outer_specs = self.build_particle_spec_pool([
                (self.BOMB_KIND_SQUARE_FILL, 2, 20),
                (self.BOMB_KIND_CIRCLE_FILL, 4, 26),
                (self.BOMB_KIND_CIRCLE_OUTLINE, 4, 20),
                (self.BOMB_KIND_CIRCLE_FILL, 6, 10),
                (self.BOMB_KIND_CIRCLE_OUTLINE, 6, 8),
                (self.BOMB_KIND_CROSS, 3, 2),
                (self.BOMB_KIND_SPARKLE_OUTLINE, 3, 2),
            ])
            rng.shuffle(outer_specs)
            for idx in range(self.BOMB_PARTICLE_COUNT_OUTER):
                px, py, pz = self.random_point_on_sphere(rng.uniform(36.0, 40.0) * power_scale, rng)
                kind, size = outer_specs[idx]
                particles.append(BombSpark3D(px, py, pz, size, kind, rng.uniform(0.0, math.tau), 0))

        if self.BOMB_ENABLE_INNER_LAYER:
            inner_specs = self.build_particle_spec_pool([
                (self.BOMB_KIND_CIRCLE_FILL, 4, 4),
                (self.BOMB_KIND_CIRCLE_OUTLINE, 4, 4),
                (self.BOMB_KIND_CIRCLE_FILL, 6, 2),
                (self.BOMB_KIND_CIRCLE_OUTLINE, 6, 2),
                (self.BOMB_KIND_CROSS, 3, 4),
                (self.BOMB_KIND_CROSS, 5, 2),
                (self.BOMB_KIND_SPARKLE_FILL, 3, 2),
                (self.BOMB_KIND_SPARKLE_OUTLINE, 3, 2),
                (self.BOMB_KIND_SPARKLE_FILL, 5, 1),
                (self.BOMB_KIND_SPARKLE_OUTLINE, 5, 1),
            ])
            rng.shuffle(inner_specs)
            for idx in range(self.BOMB_PARTICLE_COUNT_INNER):
                px, py, pz = self.random_point_on_sphere(rng.uniform(24.0, 31.0) * power_scale, rng)
                kind, size = inner_specs[idx]
                particles.append(BombSpark3D(px, py, pz, size, kind, rng.uniform(0.0, math.tau), 1))

        if self.BOMB_ENABLE_TWINKLE_LAYER:
            twinkle_specs = self.build_particle_spec_pool([
                (self.BOMB_KIND_SPARKLE_FILL, 3, 4),
                (self.BOMB_KIND_SPARKLE_OUTLINE, 3, 4),
                (self.BOMB_KIND_SPARKLE_FILL, 5, 3),
                (self.BOMB_KIND_SPARKLE_OUTLINE, 5, 3),
                (self.BOMB_KIND_SPARKLE_FILL, 7, 1),
                (self.BOMB_KIND_SPARKLE_OUTLINE, 7, 1),
                (self.BOMB_KIND_CROSS, 3, 1),
                (self.BOMB_KIND_CROSS, 5, 1),
            ])
            rng.shuffle(twinkle_specs)
            for idx in range(self.BOMB_PARTICLE_COUNT_TWINKLE):
                px, py, pz = self.random_point_on_sphere(rng.uniform(26.0, 36.0) * power_scale, rng)
                kind, size = twinkle_specs[idx]
                particles.append(BombSpark3D(px, py, pz, size, kind, rng.uniform(0.0, math.tau), 2))

        if self.BOMB_ENABLE_FLOW_LAYER:
            flow_specs = self.build_particle_spec_pool([
                (self.BOMB_KIND_SQUARE_FILL, 1, 12),
                (self.BOMB_KIND_SQUARE_FILL, 2, 10),
            ])
            rng.shuffle(flow_specs)
            for idx in range(self.BOMB_PARTICLE_COUNT_FLOW):
                angle = rng.uniform(0.0, math.tau)
                target_radius = rng.uniform(56.0, 118.0) * power_scale
                kind, size = flow_specs[idx]
                flow_particles.append(
                    BombSpark3D(
                        local_x=math.cos(angle) * target_radius,
                        local_y=math.sin(angle) * target_radius,
                        local_z=rng.uniform(0.52, 0.78),
                        size=size,
                        kind=kind,
                        phase=rng.uniform(0.02, 0.18),
                        layer=3,
                    )
                )

        if self.BOMB_ENABLE_RED_SPARKLE_LAYER:
            red_specs = self.build_particle_spec_pool([
                (self.BOMB_KIND_SPARKLE_FILL, 3, 15),
                (self.BOMB_KIND_SPARKLE_OUTLINE, 3, 13),
                (self.BOMB_KIND_SPARKLE_FILL, 5, 8),
                (self.BOMB_KIND_SPARKLE_OUTLINE, 5, 6),
            ])
            rng.shuffle(red_specs)
            for idx in range(self.BOMB_PARTICLE_COUNT_RED_SPARKLE):
                angle = rng.uniform(0.0, math.tau)
                target_radius = rng.uniform(72.0, 126.0) * power_scale
                kind, size = red_specs[idx]
                flow_particles.append(
                    BombSpark3D(
                        local_x=math.cos(angle) * target_radius,
                        local_y=math.sin(angle) * target_radius,
                        local_z=rng.uniform(0.68, 0.96),
                        size=size,
                        kind=kind,
                        phase=rng.uniform(0.00, 0.10),
                        layer=4,
                    )
                )

        layer_params = {
            0: {
                "axis": self.random_unit_vector_rng(rng),
                "speed": rng.uniform(0.10, 0.22) * rng.choice((-1.0, 1.0)),
                "pulse_amp": rng.uniform(0.18, 0.30),
                "pulse_phase": rng.uniform(0.0, math.tau),
            },
            1: {
                "axis": self.random_unit_vector_rng(rng),
                "speed": rng.uniform(0.18, 0.34) * rng.choice((-1.0, 1.0)),
                "pulse_amp": rng.uniform(0.10, 0.22),
                "pulse_phase": rng.uniform(0.0, math.tau),
            },
            2: {
                "axis": self.random_unit_vector_rng(rng),
                "speed": rng.uniform(0.08, 0.28) * rng.choice((-1.0, 1.0)),
                "pulse_amp": rng.uniform(0.06, 0.16),
                "pulse_phase": rng.uniform(0.0, math.tau),
            },
        }

        frames: list[PrecomputedBombFrame] = []
        frame_span = max(1, self.BOMB_PATTERN_FRAMES - 1)
        for frame_idx in range(self.BOMB_PATTERN_FRAMES):
            sample_time = (frame_idx / frame_span) * self.BOMB_VISUAL_PLAYBACK_FRAMES
            frame_particles: list[PrecomputedParticleFrame] = []
            frame_flow_particles: list[PrecomputedParticleFrame] = []
            progress01 = sample_time / max(1, self.BOMB_VISUAL_PLAYBACK_FRAMES)

            for spark in particles:
                params = layer_params[spark.layer]
                angle = params["speed"] * sample_time
                quat = quaternion_from_axis_angle(params["axis"], angle)
                rx, ry, rz = rotate_vector_by_quaternion(
                    (spark.local_x, spark.local_y, spark.local_z),
                    quat,
                )
                pulse = 1.0 + params["pulse_amp"] * math.sin(params["pulse_phase"] + sample_time * 0.19 + spark.phase)
                dx, dy, depth = self.project_point(rx * pulse, ry * pulse, rz)
                twinkle = 0.5 + 0.5 * math.sin(spark.phase + sample_time * 0.32)
                color, size = self.particle_color_and_size(depth, spark.size, spark.kind, twinkle)
                frame_particles.append(
                    PrecomputedParticleFrame(
                        dx=dx,
                        dy=dy,
                        color=color,
                        size=size,
                        kind=spark.kind,
                    )
                )

            for spark in flow_particles:
                local_progress = (progress01 - spark.phase) / max(0.16, spark.local_z)
                if local_progress <= 0.0 or local_progress >= 1.0:
                    continue
                if spark.layer == 3:
                    eased = 1.0 - ((1.0 - local_progress) ** 2)
                    dx = int(spark.local_x * eased)
                    dy = int(spark.local_y * eased)
                    fade = 1.0 - local_progress
                    trail_steps = 3 if spark.size >= 2 else 2
                    trail_len = 8 if spark.size >= 2 else 5
                    for step in range(trail_steps, -1, -1):
                        trail_progress = max(0.0, eased - (step / max(1, trail_steps)) * (trail_len / max(1.0, math.hypot(spark.local_x, spark.local_y))))
                        trail_dx = int(spark.local_x * trail_progress)
                        trail_dy = int(spark.local_y * trail_progress)
                        trail_fade = fade * (0.45 + 0.55 * (step / max(1, trail_steps)))
                        if trail_fade > 0.72:
                            color = 15
                        elif trail_fade > 0.40:
                            color = 10
                        else:
                            color = 6
                        frame_flow_particles.append(
                            PrecomputedParticleFrame(
                                dx=trail_dx,
                                dy=trail_dy,
                                color=color,
                                size=spark.size,
                                kind=self.BOMB_KIND_SQUARE_FILL,
                            )
                        )
                    continue

                ring_progress = 1.0 - ((1.0 - local_progress) ** 3)
                bomb_outer_radius = (
                    (self.BOMB_BASE_RADIUS + self.BOMB_EXPANSION_RADIUS * (1.0 - ((1.0 - progress01) ** 3))) * power_scale
                ) * 0.92
                base_radius = 44.0 * power_scale
                target_radius = math.hypot(spark.local_x, spark.local_y)
                radial = base_radius + (target_radius - base_radius) * ring_progress
                radial = min(radial, max(base_radius + 4.0, bomb_outer_radius - 10.0))
                angle = math.atan2(spark.local_y, spark.local_x)
                dx = int(math.cos(angle) * radial)
                dy = int(math.sin(angle) * radial)
                twinkle = 0.5 + 0.5 * math.sin(spark.phase * 11.0 + sample_time * 0.24)
                if twinkle > 0.78:
                    color = 15
                elif twinkle > 0.46:
                    color = 8
                else:
                    color = 2
                frame_flow_particles.append(
                    PrecomputedParticleFrame(
                        dx=dx,
                        dy=dy,
                        color=color,
                        size=spark.size,
                        kind=spark.kind,
                    )
                )

            frames.append(PrecomputedBombFrame(frame_particles, frame_flow_particles))
        pattern = PrecomputedBombPattern(frames=frames, total_frames=len(frames))
        self._build_bomb_pattern_sheet(pattern)
        return pattern

    def _next_bomb_pattern_seed(self) -> int:
        seed = 1000 + self.start_weapon_index * 97 + self.boss_spawn_count * 17 + self.bomb_pattern_seed_cursor * 137
        self.bomb_pattern_seed_cursor += 1
        return seed

    def maybe_build_bomb_pattern_in_reward(self) -> None:
        if self.phase != GamePhase.REWARD_SELECT:
            return
        if self.pending_bomb_pattern_build <= 0:
            return
        if len(self.bomb_patterns) >= self._bomb_pattern_target_count():
            self.pending_bomb_pattern_build = 0
            return
        self.bomb_patterns.append(self.build_bomb_pattern(self._next_bomb_pattern_seed()))
        self.pending_bomb_pattern_build -= 1

    def spawn_bomb_visual(self, x: float, y: float, scale: float) -> None:
        if not self.bomb_patterns:
            return
        pattern_id = self.next_bomb_pattern_cursor % len(self.bomb_patterns)
        self.next_bomb_pattern_cursor = (self.next_bomb_pattern_cursor + 1) % max(1, len(self.bomb_patterns))
        self.active_bomb_visuals.append(
            ActiveBombVisual(x=x, y=y, pattern_id=pattern_id, frame_index=0, age=0, scale=scale, alive=True)
        )

    def update_bomb_visuals(self) -> None:
        next_visuals: list[ActiveBombVisual] = []
        for visual in self.active_bomb_visuals:
            if not visual.alive:
                continue
            if visual.pattern_id < 0 or visual.pattern_id >= len(self.bomb_patterns):
                continue
            pattern = self.bomb_patterns[visual.pattern_id]
            visual.age += 1
            loop_age = visual.age % max(1, self.BOMB_VISUAL_PLAYBACK_FRAMES)
            visual.frame_index = min(
                pattern.total_frames - 1,
                int((loop_age / max(1, self.BOMB_VISUAL_PLAYBACK_FRAMES)) * pattern.total_frames),
            )
            if visual.age >= self.BOMB_VISUAL_DURATION_FRAMES:
                continue
            next_visuals.append(visual)
        self.active_bomb_visuals = next_visuals

    def _point_in_circle(self, px: float, py: float, cx: float, cy: float, r: float) -> bool:
        dx = px - cx
        dy = py - cy
        return dx * dx + dy * dy <= r * r

    def _point_in_rect(self, px: float, py: float, x: float, y: float, w: float, h: float) -> bool:
        return x <= px <= x + w and y <= py <= y + h

    def _mobile_controls_enabled(self) -> bool:
        return sys.platform == "emscripten" or self.DESKTOP_DEBUG_MOBILE_CONTROLS

    def _is_touch_in_mobile_control_area(self) -> bool:
        if not self._mobile_controls_enabled():
            return False
        if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            return False
        return self._point_in_rect(
            float(pyxel.mouse_x),
            float(pyxel.mouse_y),
            float(self.MOBILE_PANEL_X),
            float(self.MOBILE_PANEL_Y),
            float(self.MOBILE_PANEL_W),
            float(self.MOBILE_PANEL_H),
        )

    def _mobile_polar(self, px: float, py: float) -> tuple[float, float]:
        dx = px - float(self.MOBILE_CTRL_CX)
        dy = float(self.MOBILE_CTRL_CY) - py
        distance = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(dy, dx))
        return distance, angle

    def _point_in_mobile_arc(
        self,
        px: float,
        py: float,
        angle_start: float,
        angle_end: float,
        inner_radius: float,
        outer_radius: float,
    ) -> bool:
        distance, angle = self._mobile_polar(px, py)
        return (
            inner_radius <= distance <= outer_radius
            and angle_start <= angle <= angle_end
        )

    def _mobile_arc_point(self, radius: float, angle_deg: float) -> tuple[int, int]:
        rad = math.radians(angle_deg)
        x = self.MOBILE_CTRL_CX + math.cos(rad) * radius
        y = self.MOBILE_CTRL_CY - math.sin(rad) * radius
        return int(round(x)), int(round(y))

    def _mobile_arc_midpoint(self, angle_start: float, angle_end: float, radius: float) -> tuple[int, int]:
        return self._mobile_arc_point(radius, (angle_start + angle_end) * 0.5)

    def _is_mobile_laser_pressed(self) -> bool:
        if not self._mobile_controls_enabled():
            return False
        if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            return False
        x, y, w, h = self._mobile_laser_button_rect()
        return self._point_in_rect(float(pyxel.mouse_x), float(pyxel.mouse_y), float(x), float(y), float(w), float(h))

    def _is_mobile_bomb_pressed(self) -> bool:
        if not self._mobile_controls_enabled():
            return False
        if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            return False
        x, y, w, h = self._mobile_bomb_button_rect()
        return self._point_in_rect(float(pyxel.mouse_x), float(pyxel.mouse_y), float(x), float(y), float(w), float(h))

    def _update_mobile_action_buttons(self) -> None:
        if not self._mobile_controls_enabled():
            self.prev_mobile_laser_pressed = False
            self.prev_mobile_bomb_pressed = False
            return

        laser_pressed = self._is_mobile_laser_pressed()
        bomb_pressed = self._is_mobile_bomb_pressed()

        if laser_pressed and not self.prev_mobile_laser_pressed:
            self._try_activate_homing_laser()

        if bomb_pressed and not self.prev_mobile_bomb_pressed:
            self._try_activate_bomb()

        self.prev_mobile_laser_pressed = laser_pressed
        self.prev_mobile_bomb_pressed = bomb_pressed

    def _update_touch_mode(self) -> None:
        touch_down = self._active_touch_count() > 0 or pyxel.btn(pyxel.MOUSE_BUTTON_LEFT)
        self.touch_active = touch_down

        if touch_down and not self.prev_touch_down:
            started_in_control = self._is_touch_in_mobile_control_area()
            self.touch_drag_active = not started_in_control
        elif not touch_down:
            self.touch_drag_active = False

        self.prev_touch_down = touch_down

    def _active_touch_count(self) -> int:
        touches_fn = getattr(pyxel, "touches", None)
        if callable(touches_fn):
            try:
                return len(touches_fn())
            except Exception:
                return 0
        touch_count_attr = getattr(pyxel, "touch_count", None)
        if callable(touch_count_attr):
            try:
                return int(touch_count_attr())
            except Exception:
                return 0
        if isinstance(touch_count_attr, int):
            return touch_count_attr
        return 0

    def _is_shoot_enabled(self) -> bool:
        if self.phase != GamePhase.PLAYING:
            return False

        touch_count = self._active_touch_count()
        left_pressed = pyxel.btn(pyxel.MOUSE_BUTTON_LEFT)
        right_pressed = pyxel.btn(pyxel.MOUSE_BUTTON_RIGHT)

        if touch_count >= 2:
            self.shoot_suppressed = True
            return False
        if touch_count == 1:
            enabled = self.touch_drag_active
            self.shoot_suppressed = not enabled
            return enabled

        if left_pressed and right_pressed:
            self.shoot_suppressed = True
            return False
        if left_pressed and self.touch_drag_active:
            self.shoot_suppressed = False
            return True

        self.shoot_suppressed = False
        return False

    def _weapon_name(self, family: str | None = None) -> str:
        family = family or self.current_weapon_family
        return self.WEAPON_FAMILY_DATA.get(family, self.WEAPON_FAMILY_DATA[self.WEAPON_FAMILY_FAN])["name"]

    def _weapon_hud_name(self, family: str | None) -> str:
        if family is None:
            return "-----"
        return self._weapon_name(family)

    def _weapon_accent(self, family: str | None = None) -> int:
        family = family or self.current_weapon_family
        return self.WEAPON_FAMILY_DATA.get(family, self.WEAPON_FAMILY_DATA[self.WEAPON_FAMILY_FAN])["accent"]

    def _weapon_colors(self, family: str | None = None) -> tuple[int, int]:
        family = family or self.current_weapon_family
        data = self.WEAPON_FAMILY_DATA.get(family, self.WEAPON_FAMILY_DATA[self.WEAPON_FAMILY_FAN])
        return data["core"], data["outer"]

    def _current_weapon_level(self) -> int:
        return self._weapon_level(self.current_weapon_family)

    def _set_weapon_level(self, family: str, level: int) -> None:
        self.weapon_levels[family] = max(self.SHOT_LEVEL_SINGLE, min(level, self.SHOT_LEVEL_MAX))

    def _weapon_damage_bonus(self, family: str | None = None) -> int:
        family = family or self.current_weapon_family
        return max(0, min(self.WEAPON_OVERDRIVE_CAP, self.weapon_overdrive_bonus.get(family, 0)))

    def _weapon_level(self, family: str) -> int:
        level = max(self.SHOT_LEVEL_SINGLE, self.weapon_levels.get(family, self.SHOT_LEVEL_SINGLE))
        if self._fever_active() and family in self._active_fire_families():
            return self.SHOT_LEVEL_MAX
        return level

    def _dual_shot_ready(self) -> bool:
        return len(self.unlocked_weapon_families) >= 2 and any(
            self.weapon_levels.get(family, -1) >= self.SHOT_LEVEL_MAX
            for family in self.unlocked_weapon_families
        )

    def _available_dual_pairs(self) -> list[tuple[str, str]]:
        unlocked = list(self.unlocked_weapon_families)
        return [
            (unlocked[i], unlocked[j])
            for i in range(len(unlocked))
            for j in range(i + 1, len(unlocked))
        ]

    def _sync_active_weapon_slots(self) -> None:
        cleaned: list[str] = []
        for family in getattr(self, "active_weapon_slots", []):
            if self._is_weapon_unlocked(family) and family not in cleaned:
                cleaned.append(family)

        if self.current_weapon_family not in cleaned and self._is_weapon_unlocked(self.current_weapon_family):
            cleaned.append(self.current_weapon_family)

        for family in self.unlocked_weapon_families:
            if family not in cleaned:
                cleaned.append(family)

        self.active_weapon_slots = cleaned[:2]
        if self.current_weapon_family not in self.active_weapon_slots and self.active_weapon_slots:
            self.current_weapon_family = self.active_weapon_slots[-1]

    def _set_active_weapon_pair(self, pair: tuple[str, str]) -> None:
        self.active_weapon_slots = [pair[0], pair[1]]
        self._sync_active_weapon_slots()

    def _active_fire_families(self) -> list[str]:
        self._sync_active_weapon_slots()
        return self.active_weapon_slots[:2] if self._dual_shot_ready() else [self.current_weapon_family]

    def _has_power_weapon_active(self) -> bool:
        for family in self._active_fire_families():
            if self._weapon_level(family) >= self.SHOT_LEVEL_POWER_SINGLE:
                return True
        return False

    def _current_spawn_interval_sec(self) -> float:
        if self._fever_active():
            return max(0.18, self.spawn_interval_sec * self.FEVER_SPAWN_INTERVAL_MULT)
        return self.spawn_interval_sec

    def _is_weapon_unlocked(self, family: str) -> bool:
        return family in self.unlocked_weapon_families

    def _locked_weapon_families(self) -> list[str]:
        return [family for family in self.WEAPON_FAMILY_ORDER if family not in self.unlocked_weapon_families]

    def _unlock_weapon_family(self, family: str, equip_now: bool = True) -> None:
        previous_family = self.current_weapon_family
        was_unlocked = family in self.unlocked_weapon_families
        if family not in self.unlocked_weapon_families:
            self.unlocked_weapon_families.append(family)
        if self.weapon_levels.get(family, -1) < self.SHOT_LEVEL_SINGLE:
            self.weapon_levels[family] = self.SHOT_LEVEL_SINGLE
        if equip_now:
            self.current_weapon_family = family
        if not was_unlocked and equip_now and previous_family != family and self._is_weapon_unlocked(previous_family):
            self.active_weapon_slots = [previous_family, family]
        self._sync_active_weapon_slots()

    def _next_unlocked_weapon_family(self, family: str) -> str:
        if family not in self.unlocked_weapon_families or len(self.unlocked_weapon_families) <= 1:
            return family
        idx = self.unlocked_weapon_families.index(family)
        return self.unlocked_weapon_families[(idx + 1) % len(self.unlocked_weapon_families)]

    def _shot_level_name(self, level: int | None = None) -> str:
        level = self._current_weapon_level() if level is None else level
        mapping = {
            self.SHOT_LEVEL_SINGLE: "1WAY",
            self.SHOT_LEVEL_DOUBLE: "2WAY",
            self.SHOT_LEVEL_TRIPLE: "3WAY",
            self.SHOT_LEVEL_POWER_SINGLE: "P-1WAY",
            self.SHOT_LEVEL_POWER_DOUBLE: "P-2WAY",
            self.SHOT_LEVEL_POWER_TRIPLE: "P-3WAY",
        }
        return mapping.get(level, "1WAY")

    def _current_shot_cooldown_frames(self) -> int:
        cooldown = max(2, self.shoot_interval_frames - self._rapid_cooldown_reduction())
        for family in self._active_fire_families():
            if family != self.WEAPON_FAMILY_BEAM:
                if family == self.WEAPON_FAMILY_ECHO:
                    cooldown = max(cooldown, max(3, self.ECHO_COOLDOWN - self._rapid_cooldown_reduction()))
                elif family == self.WEAPON_FAMILY_FAN:
                    cooldown = max(cooldown, max(3, self.shoot_interval_frames + 1 - self._rapid_cooldown_reduction()))
                continue
            level = self._weapon_level(family)
            beam_cooldown = max(
                3,
                self.shoot_interval_frames + (8 if level <= self.SHOT_LEVEL_TRIPLE else 10) - self._rapid_cooldown_reduction(),
            )
            cooldown = max(cooldown, beam_cooldown)
        return cooldown

    def _weapon_notice_kind(self, family: str) -> str:
        return f"weapon_{family}"

    def _notice_palette(self) -> tuple[int, int, int, int]:
        if self.reward_notice_kind == self._weapon_notice_kind(self.WEAPON_FAMILY_FAN):
            return 11, 3, 1, 0
        if self.reward_notice_kind == self._weapon_notice_kind(self.WEAPON_FAMILY_LANCE):
            return 8, 13, 1, 0
        if self.reward_notice_kind == self._weapon_notice_kind(self.WEAPON_FAMILY_RAIN):
            return 12, 5, 1, 0
        if self.reward_notice_kind == self._weapon_notice_kind(self.WEAPON_FAMILY_BEAM):
            return 14, 6, 1, 0
        if self.reward_notice_kind == self._weapon_notice_kind(self.WEAPON_FAMILY_ECHO):
            return 15, 12, 1, 0
        if self.reward_notice_kind.startswith("boss_buff_"):
            return 7, 15, 13, 0
        if self.reward_notice_kind == "overload":
            return 10, 9, 1, 0
        return 10, 9, 1, 0

    def _boss_pattern_active(self) -> bool:
        return self.boss_pattern_id is not None and (
            self.boss_event_started
            or self._is_boss_active()
            or self.boss_defeat_timer > 0
        )

    def _clear_boss_pattern_state(self) -> None:
        self.boss_pattern_id = None
        self.boss_pattern_transition_timer = 0
        self.boss_pattern_label_timer = 0
        self.boss_pattern_confetti_timer = 0
        self.boss_pattern_name = ""
        self.boss_pattern_buff = ""
        self.boss_pattern_accent = 10
        self.boss_damage_taken_multiplier = 1.0
        self.boss_move_speed_multiplier = 1.0
        self.boss_shippo_enabled = False
        self.boss_slow_inflict_enabled = False
        self.player_slow_timer = 0
        self.player_slow_factor = 1.0

    def _select_boss_pattern(self) -> None:
        forced_pattern = self.debug_forced_boss_pattern
        if forced_pattern in self.BOSS_PATTERN_DATA:
            pattern_id = forced_pattern
        else:
            pattern_id = random.choice(tuple(self.BOSS_PATTERN_DATA.keys()))
        data = self.BOSS_PATTERN_DATA[pattern_id]
        self.boss_pattern_id = pattern_id
        self.boss_pattern_name = data["name"]
        self.boss_pattern_buff = data["buff"]
        self.boss_pattern_accent = data["accent"]
        self.boss_pattern_transition_timer = self.BOSS_PATTERN_INTRO_FRAMES
        self.boss_pattern_label_timer = 0
        self.boss_pattern_confetti_timer = self.BOSS_PATTERN_CONFETTI_FRAMES
        self.boss_damage_taken_multiplier = self.SEIGAIHA_DAMAGE_TAKEN_MULT if pattern_id == "seigaiha" else 1.0
        self.boss_move_speed_multiplier = self.YAGASURI_MOVE_SPEED_MULT if pattern_id == "yagasuri" else 1.0
        self.boss_shippo_enabled = pattern_id == "shippo"
        self.boss_slow_inflict_enabled = pattern_id == "karakusa"

    def _show_notice(
        self,
        *,
        label: str,
        title: str,
        description: str,
        accent: int,
        kind: str = "reward",
    ) -> None:
        self.reward_notice_label = label
        self.reward_notice_text = title
        self.reward_notice_desc = description
        self.reward_notice_accent = accent
        self.reward_notice_kind = kind
        self.reward_notice_timer = self.REWARD_NOTICE_FRAMES

    def _play_weapon_cutin_se(self) -> None:
        self.audio.play_se("weapon_cutin")

    def _upgrade_weapon_family(self, family: str, switch_if_needed: bool = True) -> None:
        self.audio.play_se("item_tea_get")

        if not self._is_weapon_unlocked(family):
            self._unlock_weapon_family(family, equip_now=True)
            self._play_weapon_cutin_se()
            self._show_notice(
                label="WEAPON GET",
                title=f"{self._weapon_name(family)} UNLOCK",
                description=f"Now using {self._weapon_name(family)}",
                accent=self._weapon_accent(family),
                kind=self._weapon_notice_kind(family),
            )
            self.shot_pick_flash_timer = self.TEA_FLASH_FRAMES
            return

        previous_family = self.current_weapon_family
        if switch_if_needed and family != self.current_weapon_family:
            if self._dual_shot_ready():
                self._sync_active_weapon_slots()
                if family in self.active_weapon_slots:
                    keep = [slot for slot in self.active_weapon_slots if slot != family]
                    self.active_weapon_slots = keep + [family]
                elif len(self.unlocked_weapon_families) >= 3 and len(self.active_weapon_slots) >= 2:
                    self.active_weapon_slots = [self.active_weapon_slots[-1], family]
                else:
                    self.active_weapon_slots = [self.active_weapon_slots[0], family]
            self.current_weapon_family = family
            self._sync_active_weapon_slots()
            self._play_weapon_cutin_se()
            self._show_notice(
                label="WEAPON CHANGE",
                title=f"{self._weapon_name(family)} READY",
                description=f"Switched from {self._weapon_name(previous_family)}",
                accent=self._weapon_accent(family),
                kind=self._weapon_notice_kind(family),
            )
            self.shot_pick_flash_timer = self.TEA_FLASH_FRAMES
            return

        if self.weapon_levels.get(family, self.SHOT_LEVEL_SINGLE) >= self.SHOT_LEVEL_MAX:
            next_bonus = min(self._weapon_damage_bonus(family) + 1, self.WEAPON_OVERDRIVE_CAP)
            current_bonus = self._weapon_damage_bonus(family)
            if next_bonus > current_bonus:
                self.weapon_overdrive_bonus[family] = next_bonus
                self.shot_pick_flash_timer = self.TEA_FLASH_FRAMES
                self.audio.play_se("weapon_level_up")
                self._play_weapon_cutin_se()
                self._show_notice(
                    label="MAX POWER",
                    title=f"{self._weapon_name(family)} DRIVE",
                    description=f"ATK +{next_bonus}",
                    accent=self._weapon_accent(family),
                    kind=self._weapon_notice_kind(family),
                )
            return

        next_level = min(self.weapon_levels.get(family, self.SHOT_LEVEL_SINGLE) + 1, self.SHOT_LEVEL_MAX)
        self._set_weapon_level(family, next_level)
        self._sync_active_weapon_slots()
        self.shot_pick_flash_timer = self.TEA_FLASH_FRAMES
        self.audio.play_se("weapon_level_up")
        self._play_weapon_cutin_se()
        self._show_notice(
            label="SHOT UP",
            title=f"{self._weapon_name(family)} BOOST",
            description=f"Now {self._shot_level_name(next_level)}",
            accent=self._weapon_accent(family),
            kind=self._weapon_notice_kind(family),
        )

    def _tea_drop_rate(self) -> float:
        return min(0.70, self.TEA_DROP_CHANCE + self.tea_drop_bonus)

    def _next_shot_level_name(self, family: str | None = None) -> str:
        family = family or self.current_weapon_family
        current_level = max(self.SHOT_LEVEL_SINGLE, self.weapon_levels.get(family, self.SHOT_LEVEL_SINGLE))
        next_level = min(current_level + 1, self.SHOT_LEVEL_MAX)
        mapping = {
            self.SHOT_LEVEL_SINGLE: "1WAY",
            self.SHOT_LEVEL_DOUBLE: "2WAY",
            self.SHOT_LEVEL_TRIPLE: "3WAY",
            self.SHOT_LEVEL_POWER_SINGLE: "P-1WAY",
            self.SHOT_LEVEL_POWER_DOUBLE: "P-2WAY",
            self.SHOT_LEVEL_POWER_TRIPLE: "P-3WAY",
        }
        return mapping.get(next_level, "1WAY")

    def _reward_category(self, reward_id: str) -> str:
        if reward_id.startswith("unlock_") or reward_id.startswith("boost_") or reward_id.startswith("overdrive_"):
            return "WEAPON"
        if reward_id in {"max_hp", "repair", "bomb_cap", "bomb_fill", "bomb_power"}:
            return "SURVIVE"
        return "UTILITY"

    def _reward_choice(self, reward_id: str) -> RewardChoice:
        if reward_id.startswith("boost_"):
            family = reward_id.split("_", 1)[1]
            return RewardChoice(
                reward_id=reward_id,
                title=f"{self._weapon_name(family)} BOOST",
                description=f"Level up to {self._next_shot_level_name(family)}",
                accent_color=self._weapon_accent(family),
                tag="WEAPON",
            )
        if reward_id.startswith("overdrive_"):
            family = reward_id.split("_", 1)[1]
            next_bonus = min(self._weapon_damage_bonus(family) + 1, self.WEAPON_OVERDRIVE_CAP)
            return RewardChoice(
                reward_id=reward_id,
                title=f"{self._weapon_name(family)} DRIVE",
                description=f"ATK up to +{next_bonus}",
                accent_color=self._weapon_accent(family),
                tag="WEAPON",
            )
        if reward_id.startswith("unlock_"):
            family = reward_id.split("_", 1)[1]
            return RewardChoice(
                reward_id=reward_id,
                title=f"UNLOCK {self._weapon_name(family)}",
                description=f"Unlock and switch to {self._weapon_name(family)}",
                accent_color=self._weapon_accent(family),
                tag="WEAPON",
            )
        if reward_id == "max_hp":
            return RewardChoice(
                reward_id=reward_id,
                title="MAX HP UP",
                description="Max HP +1 and heal fully",
                accent_color=10,
                tag="SURVIVE",
            )
        if reward_id == "repair":
            heal_amount = min(2, self.player.max_hp - self.player.hp)
            return RewardChoice(
                reward_id=reward_id,
                title="REPAIR",
                description=f"Recover {heal_amount} HP",
                accent_color=8,
                tag="SURVIVE",
            )
        if reward_id == "bomb_cap":
            next_cap = self._bomb_capacity() + 1
            return RewardChoice(
                reward_id=reward_id,
                title="BOMB CAP UP",
                description=f"Carry up to {next_cap} bombs",
                accent_color=9,
                tag="SURVIVE",
            )
        if reward_id == "bomb_fill":
            return RewardChoice(
                reward_id=reward_id,
                title="BOMB REFILL",
                description=f"Refill to {self._bomb_capacity()} bombs",
                accent_color=10,
                tag="SURVIVE",
            )
        if reward_id == "bomb_power":
            next_level = min(self.BOMB_POWER_MAX_LEVEL, self.bomb_power_level + 1) + 1
            return RewardChoice(
                reward_id=reward_id,
                title="BOMB POWER UP",
                description=f"Blast size up to LV {next_level}",
                accent_color=8,
                tag="SURVIVE",
            )
        if reward_id == "move_up":
            next_speed = min(self.PLAYER_SPEED_CAP, self.player.speed_x + 1)
            return RewardChoice(
                reward_id=reward_id,
                title="MOVE UP",
                description=f"Move faster: speed {next_speed}",
                accent_color=12,
                tag="UTILITY",
            )
        if reward_id == "laser_count_up":
            next_count = min(self.LASER_SHOT_COUNT_MAX, self.laser_shot_count + 1)
            return RewardChoice(
                reward_id=reward_id,
                title="LASER COUNT UP",
                description=f"Fire {next_count} lasers at once",
                accent_color=14,
                tag="UTILITY",
            )
        if reward_id == "laser_tune":
            next_wait = max(
                self.LASER_COOLDOWN_MIN,
                self.laser_cooldown_frames - self.LASER_COOLDOWN_REWARD_STEP,
            )
            return RewardChoice(
                reward_id=reward_id,
                title="LASER TUNE",
                description=f"Laser reload: {next_wait} frames",
                accent_color=14,
                tag="UTILITY",
            )
        if reward_id == "item_rate":
            next_rate = int(round(min(0.70, self._tea_drop_rate() + self.TEA_DROP_BONUS_STEP) * 100))
            return RewardChoice(
                reward_id=reward_id,
                title="ITEM RATE UP",
                description=f"Weapon item rate: {next_rate}%",
                accent_color=3,
                tag="UTILITY",
            )
        return RewardChoice(
            reward_id="max_hp",
            title="MAX HP UP",
            description="Max HP +1 and heal fully",
            accent_color=10,
            tag="SURVIVE",
        )

    def _eligible_reward_ids(self) -> list[str]:
        reward_ids = ["bomb_cap", "item_rate"]

        if self.player.max_hp < self.PLAYER_HP_CAP:
            reward_ids.append("max_hp")

        if self.player.hp < self.player.max_hp:
            reward_ids.append("repair")
        if self.bomb_stock < self._bomb_capacity():
            reward_ids.append("bomb_fill")
        if self.bomb_power_level < self.BOMB_POWER_MAX_LEVEL:
            reward_ids.append("bomb_power")

        for family in self.unlocked_weapon_families:
            if self.weapon_levels.get(family, self.SHOT_LEVEL_SINGLE) < self.SHOT_LEVEL_MAX:
                reward_ids.append(f"boost_{family}")
            elif self._weapon_damage_bonus(family) < self.WEAPON_OVERDRIVE_CAP:
                reward_ids.append(f"overdrive_{family}")
        for family in self._locked_weapon_families():
            reward_ids.append(f"unlock_{family}")
        if self.player.speed_x < self.PLAYER_SPEED_CAP or self.player.speed_y < self.PLAYER_SPEED_CAP:
            reward_ids.append("move_up")
        if self.laser_shot_count < self.LASER_SHOT_COUNT_MAX:
            reward_ids.append("laser_count_up")
        if self.laser_cooldown_frames > self.LASER_COOLDOWN_MIN:
            reward_ids.append("laser_tune")

        return reward_ids

    def _reward_weight(self, reward_id: str) -> float:
        loop_depth = max(0, self.boss_spawn_count)

        if reward_id.startswith("boost_"):
            family = reward_id.split("_", 1)[1]
            missing_levels = self.SHOT_LEVEL_MAX - max(self.SHOT_LEVEL_SINGLE, self.weapon_levels.get(family, self.SHOT_LEVEL_SINGLE))
            current_bias = 1.0 if family == self.current_weapon_family else 0.25
            return 2.4 + missing_levels * 1.10 + current_bias + max(0.0, 1.0 - loop_depth * 0.16)
        if reward_id.startswith("overdrive_"):
            family = reward_id.split("_", 1)[1]
            current_bias = 0.9 if family == self.current_weapon_family else 0.2
            return 1.6 + current_bias + loop_depth * 0.14
        if reward_id.startswith("unlock_"):
            family = reward_id.split("_", 1)[1]
            family_bias = {
                self.WEAPON_FAMILY_LANCE: 2.4,
                self.WEAPON_FAMILY_RAIN: 2.0,
                self.WEAPON_FAMILY_BEAM: 1.8,
                self.WEAPON_FAMILY_ECHO: 1.7,
            }
            return family_bias.get(family, 1.6) + max(0.0, 1.4 - loop_depth * 0.18)

        if reward_id == "max_hp":
            missing_hp = self.player.max_hp - self.player.hp
            low_hp_bonus = 3.2 if self.player.hp <= 1 else 0.0
            early_survival_bonus = max(0.0, (self.PLAYER_HP_CAP - self.player.max_hp) * 0.75)
            return 1.8 + missing_hp * 2.1 + low_hp_bonus + early_survival_bonus

        if reward_id == "repair":
            missing_hp = self.player.max_hp - self.player.hp
            return 1.1 + missing_hp * 1.7 + (2.0 if self.player.hp <= 1 else 0.0)

        if reward_id == "bomb_cap":
            return max(0.9, 2.7 - self.bomb_bonus_cap * 0.55 + loop_depth * 0.16)

        if reward_id == "bomb_fill":
            missing_bombs = self._bomb_capacity() - self.bomb_stock
            return 0.9 + missing_bombs * 1.3

        if reward_id == "bomb_power":
            levels_left = self.BOMB_POWER_MAX_LEVEL - self.bomb_power_level
            return 2.6 + levels_left * 1.35 + loop_depth * 0.10

        if reward_id == "move_up":
            speed_gap = self.PLAYER_SPEED_CAP - max(self.player.speed_x, self.player.speed_y)
            return max(0.8, 1.5 + speed_gap * 0.72 - loop_depth * 0.08)

        if reward_id == "laser_count_up":
            shot_gap = self.LASER_SHOT_COUNT_MAX - self.laser_shot_count
            return max(0.9, 2.1 + shot_gap * 1.1 + loop_depth * 0.14)

        if reward_id == "laser_tune":
            cooldown_gap = self.laser_cooldown_frames - self.LASER_COOLDOWN_MIN
            tune_steps_left = cooldown_gap / max(1, self.LASER_COOLDOWN_REWARD_STEP)
            return max(0.8, 1.4 + tune_steps_left * 0.8 + loop_depth * 0.18)

        if reward_id == "item_rate":
            item_steps = self.tea_drop_bonus / max(0.001, self.TEA_DROP_BONUS_STEP)
            return max(0.7, 2.4 - item_steps * 0.45 + loop_depth * 0.12)

        return 1.0

    def _pick_weighted_reward_ids(self, reward_ids: list[str], count: int) -> list[str]:
        available = list(reward_ids)
        picks: list[str] = []

        while available and len(picks) < count:
            weighted = [(reward_id, max(0.05, self._reward_weight(reward_id))) for reward_id in available]
            total_weight = sum(weight for _reward_id, weight in weighted)

            if total_weight <= 0.0:
                picks.append(available.pop(0))
                continue

            roll = random.uniform(0.0, total_weight)
            cursor = 0.0
            selected_id = available[-1]

            for reward_id, weight in weighted:
                cursor += weight
                if roll <= cursor:
                    selected_id = reward_id
                    break

            picks.append(selected_id)
            available.remove(selected_id)

        return picks

    def _guaranteed_reward_id(self, reward_ids: list[str]) -> str | None:
        if "max_hp" in reward_ids and self.player.hp <= 1:
            return "max_hp"
        if "repair" in reward_ids and self.player.hp <= 1:
            return "repair"

        if len(self.unlocked_weapon_families) == 1:
            for family in (
                self.WEAPON_FAMILY_LANCE,
                self.WEAPON_FAMILY_RAIN,
                self.WEAPON_FAMILY_BEAM,
                self.WEAPON_FAMILY_ECHO,
            ):
                reward_id = f"unlock_{family}"
                if reward_id in reward_ids:
                    return reward_id

        current_boost_id = f"boost_{self.current_weapon_family}"
        if current_boost_id in reward_ids and self._current_weapon_level() <= self.SHOT_LEVEL_TRIPLE and self.boss_spawn_count <= 1:
            return current_boost_id

        return None

    def _build_reward_choices(self) -> list[RewardChoice]:
        pool = self._eligible_reward_ids()
        picks: list[str] = []

        guaranteed_id = self._guaranteed_reward_id(pool)
        if guaranteed_id is not None:
            picks.append(guaranteed_id)
            pool.remove(guaranteed_id)

        for category in ("WEAPON", "SURVIVE", "UTILITY"):
            if len(picks) >= self.REWARD_OPTION_COUNT:
                break
            category_ids = [reward_id for reward_id in pool if self._reward_category(reward_id) == category]
            if not category_ids:
                continue
            selected = self._pick_weighted_reward_ids(category_ids, 1)
            if not selected:
                continue
            picks.extend(selected)
            for reward_id in selected:
                if reward_id in pool:
                    pool.remove(reward_id)

        remaining = self.REWARD_OPTION_COUNT - len(picks)
        if remaining > 0:
            picks.extend(self._pick_weighted_reward_ids(pool, remaining))

        return [self._reward_choice(reward_id) for reward_id in picks[: self.REWARD_OPTION_COUNT]]

    def _sync_reward_pair_preview(self) -> None:
        pairs = self._available_dual_pairs()
        if not pairs:
            self.reward_pair_preview_index = 0
            return

        self._sync_active_weapon_slots()
        active = tuple(self.active_weapon_slots[:2])
        if active in pairs:
            self.reward_pair_preview_index = pairs.index(active)
            return

        if len(active) == 2:
            active_set = set(active)
            for idx, pair in enumerate(pairs):
                if set(pair) == active_set:
                    self.reward_pair_preview_index = idx
                    return

        self.reward_pair_preview_index = min(self.reward_pair_preview_index, len(pairs) - 1)
        self._set_active_weapon_pair(pairs[self.reward_pair_preview_index])

    def _cycle_reward_pair_preview(self, delta: int) -> None:
        pairs = self._available_dual_pairs()
        if not pairs:
            return
        self.reward_pair_preview_index = (self.reward_pair_preview_index + delta) % len(pairs)
        self._set_active_weapon_pair(pairs[self.reward_pair_preview_index])

    def _dual_button_rect(self, index: int) -> tuple[int, int, int, int]:
        button_w = 52
        button_h = 24
        gap = 4
        total_w = button_w * len(self.WEAPON_FAMILY_ORDER) + gap * (len(self.WEAPON_FAMILY_ORDER) - 1)
        start_x = (self.WIDTH - total_w) // 2
        y = self.HEIGHT - 84
        return start_x + index * (button_w + gap), y, button_w, button_h

    def _select_dual_weapon_button(self, family: str) -> None:
        if not self._is_weapon_unlocked(family):
            return

        if not self._dual_shot_ready():
            self.current_weapon_family = family
            self.active_weapon_slots = [family]
            return

        self._sync_active_weapon_slots()
        slots = [slot for slot in self.active_weapon_slots if self._is_weapon_unlocked(slot)]

        if family in slots:
            if len(slots) >= 2:
                slots = list(reversed(slots[:2]))
        else:
            slots.append(family)
            slots = slots[-2:]

        self.active_weapon_slots = slots
        self.current_weapon_family = slots[0] if slots else family
        self._sync_reward_pair_preview()

    def _start_reward_selection(self) -> None:
        self.enemies.clear()
        self.retreat_shadows.clear()
        self.enemy_bullets.clear()
        self.bullets.clear()
        self.echo_shots.clear()
        self.bombs.clear()
        self.active_bomb_visuals.clear()
        self.homing_lasers.clear()
        self.weapon_items.clear()
        self.heal_items.clear()
        self.bit_items.clear()
        self.wasabi_items.clear()
        self.boss_defeat_sushis.clear()
        self.boss_defeat_cheers.clear()
        self.fever_arrival_effect = FeverArrivalEffect()
        self.fever_arrival_pending = False
        self._clear_boss_pattern_state()
        self.reward_choices = self._build_reward_choices()
        self.reward_selection_index = 0
        self.reward_intro_timer = self.REWARD_DISSOLVE_FRAMES
        self._sync_reward_pair_preview()
        self.audio.play_bgm("bgm_reward")
        self.phase = GamePhase.REWARD_SELECT

    def _apply_reward_choice(self, choice: RewardChoice) -> None:
        if choice.reward_id.startswith("boost_"):
            family = choice.reward_id.split("_", 1)[1]
            self._upgrade_weapon_family(family, switch_if_needed=False)
        elif choice.reward_id.startswith("overdrive_"):
            family = choice.reward_id.split("_", 1)[1]
            next_bonus = min(self._weapon_damage_bonus(family) + 1, self.WEAPON_OVERDRIVE_CAP)
            self.weapon_overdrive_bonus[family] = next_bonus
            self._show_notice(
                label="MAX POWER",
                title=f"{self._weapon_name(family)} DRIVE",
                description=f"ATK +{next_bonus}",
                accent=self._weapon_accent(family),
                kind=self._weapon_notice_kind(family),
            )
        elif choice.reward_id.startswith("unlock_"):
            family = choice.reward_id.split("_", 1)[1]
            self._unlock_weapon_family(family, equip_now=True)
            self._show_notice(
                label="WEAPON GET",
                title=f"{self._weapon_name(family)} UNLOCK",
                description=f"Now using {self._weapon_name(family)}",
                accent=self._weapon_accent(family),
                kind=self._weapon_notice_kind(family),
            )
        elif choice.reward_id == "max_hp":
            self.player.max_hp = min(self.PLAYER_HP_CAP, self.player.max_hp + 1)
            self.player.hp = self.player.max_hp
        elif choice.reward_id == "repair":
            self.player.hp = min(self.player.max_hp, self.player.hp + 2)
        elif choice.reward_id == "bomb_cap":
            self.bomb_bonus_cap += 1
            self._on_bomb_capacity_changed()
            self._restock_bombs_full()
        elif choice.reward_id == "bomb_fill":
            self._restock_bombs_full()
        elif choice.reward_id == "bomb_power":
            self.bomb_power_level = min(self.BOMB_POWER_MAX_LEVEL, self.bomb_power_level + 1)
            self._on_bomb_power_changed()
        elif choice.reward_id == "move_up":
            self.player.speed_x = min(self.PLAYER_SPEED_CAP, self.player.speed_x + 1)
            self.player.speed_y = min(self.PLAYER_SPEED_CAP, self.player.speed_y + 1)
        elif choice.reward_id == "laser_count_up":
            self.laser_shot_count = min(self.LASER_SHOT_COUNT_MAX, self.laser_shot_count + 1)
        elif choice.reward_id == "laser_tune":
            self.laser_cooldown_frames = max(
                self.LASER_COOLDOWN_MIN,
                self.laser_cooldown_frames - self.LASER_COOLDOWN_REWARD_STEP,
            )
            self.laser_cooldown = min(self.laser_cooldown, self.laser_cooldown_frames)
        elif choice.reward_id == "item_rate":
            self.tea_drop_bonus += self.TEA_DROP_BONUS_STEP

        if (
            not choice.reward_id.startswith("unlock_")
            and not choice.reward_id.startswith("boost_")
            and not choice.reward_id.startswith("overdrive_")
        ):
            self._show_notice(
                label="REWARD GET",
                title=choice.title,
                description=choice.description,
                accent=choice.accent_color,
                kind="reward",
            )
        self._sync_active_weapon_slots()
        self.reward_choices.clear()
        self.reward_selection_index = 0
        self.touch_active = False
        self.touch_drag_active = False
        self.prev_touch_down = pyxel.btn(pyxel.MOUSE_BUTTON_LEFT)
        self.boss_defeated = False
        self.spawn_timer = max(self.spawn_timer, 24)
        self._begin_enemy_loop(after_boss=True)
        self.audio.play_bgm("bgm_stage")
        self.phase = GamePhase.PLAYING

    def _spawn_player_bullet(
        self,
        *,
        x: float,
        y: float,
        vx: float,
        vy: float,
        damage: int,
        radius: int,
        color_core: int,
        color_outer: int,
        style: str,
        max_life: int = 9999,
        radius_growth: float = 0.0,
        max_radius: float = 0.0,
        trail: list[tuple[float, float]] | None = None,
        piercing: bool = False,
        ignores_cancel: bool = False,
    ) -> None:
        vx += self._drift_x_bias(self.DRIFT_PLAYER_BULLET_VX)
        self.bullets.append(
            Bullet(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                damage=damage,
                radius=radius,
                color_core=color_core,
                color_outer=color_outer,
                style=style,
                max_life=max_life,
                radius_growth=radius_growth,
                max_radius=max_radius,
                trail=[] if trail is None else list(trail),
                piercing=piercing,
                ignores_cancel=ignores_cancel,
            )
        )

    def _fire_fan_shot(self, origin_x: float, origin_y: float, level: int) -> None:
        core_main, outer_main = self._weapon_colors(self.WEAPON_FAMILY_FAN)
        bonus = self._weapon_damage_bonus(self.WEAPON_FAMILY_FAN)
        wide = self._wide_scale()

        if level == self.SHOT_LEVEL_SINGLE:
            self._spawn_player_bullet(
                x=origin_x,
                y=origin_y,
                vx=0.0,
                vy=float(self.bullet_speed),
                damage=self._scaled_player_damage(3 + bonus),
                radius=3,
                color_core=core_main,
                color_outer=outer_main,
                style="normal",
            )
            return

        if level == self.SHOT_LEVEL_DOUBLE:
            for vx, xoff in ((-0.90, -4.0), (0.90, 4.0)):
                self._spawn_player_bullet(
                    x=origin_x + xoff * wide,
                    y=origin_y,
                    vx=vx * wide,
                    vy=float(self.bullet_speed),
                    damage=self._scaled_player_damage(3 + bonus),
                    radius=2,
                    color_core=11,
                    color_outer=3,
                    style="normal",
                )
            return

        if level == self.SHOT_LEVEL_TRIPLE:
            for vx, xoff, core, outer in ((-1.10, -6.0, 9, 4), (0.0, 0.0, core_main, outer_main), (1.10, 6.0, 9, 4)):
                self._spawn_player_bullet(
                    x=origin_x + xoff * wide,
                    y=origin_y,
                    vx=vx * wide,
                    vy=float(self.bullet_speed),
                    damage=self._scaled_player_damage(3 + bonus),
                    radius=2,
                    color_core=core,
                    color_outer=outer,
                    style="normal",
                )
            return

        if level == self.SHOT_LEVEL_POWER_SINGLE:
            self._spawn_player_bullet(
                x=origin_x,
                y=origin_y,
                vx=0.0,
                vy=float(self.bullet_speed),
                damage=self._scaled_player_damage(4 + bonus),
                radius=4,
                color_core=7,
                color_outer=11,
                style="power_single",
            )
            return

        if level == self.SHOT_LEVEL_POWER_DOUBLE:
            for vx, xoff, radius in ((-0.82, -5.0, 4), (0.82, 5.0, 4)):
                self._spawn_player_bullet(
                    x=origin_x + xoff * wide,
                    y=origin_y,
                    vx=vx * wide,
                    vy=float(self.bullet_speed),
                    damage=self._scaled_player_damage(5 + bonus),
                    radius=radius,
                    color_core=7,
                    color_outer=11,
                    style="power_double",
                )
            return

        for vx, xoff, radius, damage, style in (
            (-1.00, -7.0, 3, self._scaled_player_damage(5 + bonus), "power_triple"),
            (0.0, 0.0, 5, self._scaled_player_damage(7 + bonus), "power_single"),
            (1.00, 7.0, 3, self._scaled_player_damage(5 + bonus), "power_triple"),
        ):
            self._spawn_player_bullet(
                x=origin_x + xoff * wide,
                y=origin_y,
                vx=vx * wide,
                vy=float(self.bullet_speed),
                damage=damage,
                radius=radius,
                color_core=7,
                color_outer=11,
                style=style,
            )

    def _fire_lance_shot(self, origin_x: float, origin_y: float, level: int) -> None:
        core, outer = self._weapon_colors(self.WEAPON_FAMILY_LANCE)
        bonus = self._weapon_damage_bonus(self.WEAPON_FAMILY_LANCE)
        speed = float(self.bullet_speed + 2.2)
        wide = 1.0 + 0.12 * self.buff_scale("wide")

        patterns = {
            self.SHOT_LEVEL_SINGLE: ((0.0, 0.0, 3, 4, "lance"),),
            self.SHOT_LEVEL_DOUBLE: ((-0.18, -2.0, 3, 4, "lance"), (0.18, 2.0, 3, 4, "lance")),
            self.SHOT_LEVEL_TRIPLE: ((-0.22, -3.0, 3, 4, "lance"), (0.0, 0.0, 4, 5, "lance_power"), (0.22, 3.0, 3, 4, "lance")),
            self.SHOT_LEVEL_POWER_SINGLE: ((0.0, 0.0, 5, 6, "lance_power"),),
            self.SHOT_LEVEL_POWER_DOUBLE: ((-0.24, -4.0, 5, 6, "lance_power"), (0.24, 4.0, 5, 6, "lance_power")),
            self.SHOT_LEVEL_POWER_TRIPLE: ((-0.30, -6.0, 5, 6, "lance_power"), (0.0, 0.0, 7, 7, "beam_core"), (0.30, 6.0, 5, 6, "lance_power")),
        }

        for vx, xoff, damage, radius, style in patterns[level]:
            self._spawn_player_bullet(
                x=origin_x + xoff * wide,
                y=origin_y,
                vx=vx * wide,
                vy=speed,
                damage=self._scaled_player_damage(damage + bonus),
                radius=radius,
                color_core=core,
                color_outer=outer,
                style=style,
            )

    def _fire_rain_shot(self, origin_x: float, origin_y: float, level: int) -> None:
        core, outer = self._weapon_colors(self.WEAPON_FAMILY_RAIN)
        bonus = self._weapon_damage_bonus(self.WEAPON_FAMILY_RAIN)
        speed = float(self.bullet_speed - 2.2)
        wide = self._wide_scale()
        patterns = {
            self.SHOT_LEVEL_SINGLE: (-16.0, 0.0, 16.0),
            self.SHOT_LEVEL_DOUBLE: (-24.0, -8.0, 8.0, 24.0),
            self.SHOT_LEVEL_TRIPLE: (-30.0, -15.0, 0.0, 15.0, 30.0),
            self.SHOT_LEVEL_POWER_SINGLE: (-24.0, -8.0, 8.0, 24.0),
            self.SHOT_LEVEL_POWER_DOUBLE: (-32.0, -16.0, 0.0, 16.0, 32.0),
            self.SHOT_LEVEL_POWER_TRIPLE: (-40.0, -24.0, -8.0, 8.0, 24.0, 40.0),
        }
        damage = self._scaled_player_damage(1 + max(0, bonus - 1))
        radius = 2 if level <= self.SHOT_LEVEL_TRIPLE else 3
        style = "rain" if level <= self.SHOT_LEVEL_TRIPLE else "rain_power"
        growth = 0.12 if level <= self.SHOT_LEVEL_TRIPLE else 0.17
        max_radius = {
            self.SHOT_LEVEL_SINGLE: 3.8,
            self.SHOT_LEVEL_DOUBLE: 4.3,
            self.SHOT_LEVEL_TRIPLE: 4.9,
            self.SHOT_LEVEL_POWER_SINGLE: 5.6,
            self.SHOT_LEVEL_POWER_DOUBLE: 6.4,
            self.SHOT_LEVEL_POWER_TRIPLE: 7.1,
        }[level]
        max_life = {
            self.SHOT_LEVEL_SINGLE: 28,
            self.SHOT_LEVEL_DOUBLE: 29,
            self.SHOT_LEVEL_TRIPLE: 31,
            self.SHOT_LEVEL_POWER_SINGLE: 33,
            self.SHOT_LEVEL_POWER_DOUBLE: 35,
            self.SHOT_LEVEL_POWER_TRIPLE: 37,
        }[level]

        for idx, xoff in enumerate(patterns[level]):
            vx = -0.85 if idx % 2 == 0 else 0.85
            self._spawn_player_bullet(
                x=origin_x + xoff * wide,
                y=origin_y - abs(xoff * wide) * 0.30,
                vx=vx * wide,
                vy=speed,
                damage=damage,
                radius=radius,
                color_core=core,
                color_outer=outer,
                style=style,
                max_life=max_life,
                radius_growth=growth,
                max_radius=max_radius,
            )

    def _fire_beam_shot(self, origin_x: float, origin_y: float, level: int) -> None:
        core, outer = self._weapon_colors(self.WEAPON_FAMILY_BEAM)
        bonus = self._weapon_damage_bonus(self.WEAPON_FAMILY_BEAM)
        speed = float(self.bullet_speed + 2.8)
        wide = 1.0 + 0.18 * self.buff_scale("wide")
        patterns = {
            self.SHOT_LEVEL_SINGLE: ((0.0, 0.0),),
            self.SHOT_LEVEL_DOUBLE: ((-0.78, -9.0), (0.78, 9.0)),
            self.SHOT_LEVEL_TRIPLE: ((-1.18, -18.0), (-0.38, -6.0), (0.38, 6.0), (1.18, 18.0)),
            self.SHOT_LEVEL_POWER_SINGLE: ((0.0, 0.0),),
            self.SHOT_LEVEL_POWER_DOUBLE: ((-0.84, -10.0), (0.84, 10.0)),
            self.SHOT_LEVEL_POWER_TRIPLE: ((-1.24, -20.0), (-0.42, -7.0), (0.42, 7.0), (1.24, 20.0)),
        }
        damage = self._scaled_player_damage((3 if level <= self.SHOT_LEVEL_TRIPLE else 4) + bonus)
        radius = (2 if level <= self.SHOT_LEVEL_TRIPLE else 3) + int(self.buff_scale("wide") > 0)
        style = "beam_arc" if level <= self.SHOT_LEVEL_TRIPLE else "beam_arc_power"
        life = 78 if level <= self.SHOT_LEVEL_TRIPLE else 88

        for vx, xoff in patterns[level]:
            spread_scale = random.uniform(0.94, 1.10)
            vx_jitter = random.uniform(-0.05, 0.05)
            xoff_jitter = random.uniform(-1.5, 1.5)
            self._spawn_player_bullet(
                x=origin_x + xoff * wide + xoff_jitter,
                y=origin_y,
                vx=vx * spread_scale * wide + vx_jitter,
                vy=speed,
                damage=damage,
                radius=radius,
                color_core=core,
                color_outer=outer,
                style=style,
                max_life=life,
                trail=[(origin_x + xoff, origin_y)],
                piercing=True,
            )

    def _echo_pattern(self, level: int) -> tuple[tuple[float, float], ...]:
        patterns = {
            self.SHOT_LEVEL_SINGLE: ((0.0, 0.0),),
            self.SHOT_LEVEL_DOUBLE: ((-0.42, -5.0), (0.42, 5.0)),
            self.SHOT_LEVEL_TRIPLE: ((-0.72, -9.0), (0.0, 0.0), (0.72, 9.0), (-0.22, -3.0)),
            self.SHOT_LEVEL_POWER_SINGLE: ((0.0, 0.0),),
            self.SHOT_LEVEL_POWER_DOUBLE: ((-0.54, -6.0), (0.54, 6.0)),
            self.SHOT_LEVEL_POWER_TRIPLE: ((-0.92, -12.0), (-0.30, -4.0), (0.30, 4.0), (0.92, 12.0)),
        }
        return patterns[level]

    def _fire_echo_shot(self, origin_x: float, origin_y: float, level: int) -> None:
        if self.echo_cooldown > 0:
            return
        wide = self._wide_scale()
        damage = self._scaled_player_damage(self.ECHO_DAMAGE + self._weapon_damage_bonus(self.WEAPON_FAMILY_ECHO))
        patterns = self._echo_pattern(level)
        split_generations = 1 if level <= self.SHOT_LEVEL_TRIPLE else 2
        split_angle_deg = 45.0 if level <= self.SHOT_LEVEL_TRIPLE else 40.0
        power_variant = level >= self.SHOT_LEVEL_POWER_SINGLE
        for dx, xoff in patterns:
            self.echo_shots.append(
                EchoShot(
                    x=origin_x + xoff * wide,
                    y=origin_y,
                    dx=dx * wide,
                    dy=-self.ECHO_SPEED,
                    damage=damage,
                    bounce_left=split_generations,
                    lifetime=self.ECHO_LIFETIME,
                    length=self.ECHO_LENGTH + int(2 * self.buff_scale("wide")),
                    split_angle_deg=split_angle_deg,
                    generation=0,
                    power_variant=power_variant,
                )
            )
        self.echo_cooldown = max(3, self.ECHO_COOLDOWN - self._rapid_cooldown_reduction())

    def _echo_split_damage(self, parent: EchoShot) -> int:
        if parent.generation <= 0:
            scale = 0.45
        else:
            scale = 0.32
        if parent.power_variant:
            scale += 0.05
        return max(1, int(round(parent.damage * scale)))

    def _spawn_echo_split(self, x: float, y: float, parent: EchoShot) -> None:
        if parent.bounce_left <= 0:
            return
        spread = math.radians(parent.split_angle_deg)
        base_angle = -math.pi / 2
        split_damage = self._echo_split_damage(parent)
        split_length = max(6, self.ECHO_SPLIT_LENGTH + int(2 * self.buff_scale("wide")))
        for direction in (-1, 1):
            angle = base_angle + spread * direction
            self.echo_shots.append(
                EchoShot(
                    x=x,
                    y=y,
                    dx=math.cos(angle) * self.ECHO_SPLIT_SPEED,
                    dy=math.sin(angle) * self.ECHO_SPLIT_SPEED,
                    damage=split_damage,
                    bounce_left=parent.bounce_left - 1,
                    lifetime=self.ECHO_SPLIT_LIFETIME,
                    length=split_length,
                    split_angle_deg=parent.split_angle_deg,
                    generation=parent.generation + 1,
                    power_variant=parent.power_variant,
                    active=True,
                )
            )

    def _fire_current_shot(self) -> None:
        origin_x = float(self.player.x)
        origin_y = float(self.player.y - self.PLAYER_HALF_H - 6)
        families = self._active_fire_families()
        dual_offsets = (0.0,) if len(families) == 1 else (-7.0, 7.0)

        for idx, family in enumerate(families):
            level = self._weapon_level(family)
            shot_x = origin_x + dual_offsets[idx]

            if family == self.WEAPON_FAMILY_LANCE:
                self._fire_lance_shot(shot_x, origin_y, level)
                continue
            if family == self.WEAPON_FAMILY_RAIN:
                self._fire_rain_shot(shot_x, origin_y, level)
                continue
            if family == self.WEAPON_FAMILY_BEAM:
                self._fire_beam_shot(shot_x, origin_y, level)
                continue
            if family == self.WEAPON_FAMILY_ECHO:
                self._fire_echo_shot(shot_x, origin_y, level)
                continue

            self._fire_fan_shot(shot_x, origin_y, level)

    def _maybe_spawn_weapon_item(self, x: float, y: float, extra_drop_rate: float = 0.0) -> None:
        drop_rate = min(0.85, self._tea_drop_rate() + max(0.0, extra_drop_rate))
        if random.random() > drop_rate:
            return

        family = random.choice(self.unlocked_weapon_families)
        self.weapon_items.append(
            WeaponItem(
                x=x,
                y=y,
                vx=random.uniform(-0.25, 0.25),
                vy=self.TEA_FALL_SPEED + random.uniform(-0.15, 0.18),
                family=family,
                bob_phase=random.uniform(0.0, math.tau),
            )
        )

    def _maybe_spawn_heal_item(self, x: float, y: float) -> None:
        if random.random() > self.HEAL_DROP_CANCEL_CHANCE:
            return

        self.heal_items.append(
            HealItem(
                x=x,
                y=y,
                vx=random.uniform(-0.18, 0.18),
                vy=self.TEA_FALL_SPEED + random.uniform(-0.10, 0.12),
                bob_phase=random.uniform(0.0, math.tau),
            )
        )

    def _maybe_spawn_bit_item(self, x: float, y: float) -> None:
        if random.random() > self.BIT_ITEM_DROP_CHANCE_ON_RARE:
            return

        self.bit_items.append(
            BitItem(
                x=x,
                y=y,
                vx=random.uniform(-0.20, 0.20),
                vy=self.TEA_FALL_SPEED + random.uniform(-0.10, 0.12),
                variant=random.randrange(0, 2),
                bob_phase=random.uniform(0.0, math.tau),
            )
        )

    def _maybe_spawn_wasabi_item(self, x: float, y: float, enemy: Enemy) -> None:
        if enemy.enemy_type == "rare":
            drop_rate = self.WASABI_ITEM_DROP_CHANCE_ON_RARE
        elif enemy.enemy_category == "fish_source":
            drop_rate = self.WASABI_ITEM_DROP_CHANCE_ON_FISH
        else:
            drop_rate = self.WASABI_ITEM_DROP_CHANCE

        if random.random() > drop_rate:
            return

        self.wasabi_items.append(
            WasabiItem(
                x=x,
                y=y,
                vx=random.uniform(-0.18, 0.18),
                vy=self.TEA_FALL_SPEED + random.uniform(-0.10, 0.12),
                bob_phase=random.uniform(0.0, math.tau),
            )
        )

    def _update_weapon_items(self) -> None:
        next_items: list[WeaponItem] = []

        for item in self.weapon_items:
            if not item.active:
                continue

            if item.switch_lock_timer > 0:
                item.switch_lock_timer -= 1
            item.bob_phase += self.TEA_BOB_SPEED
            item.x += item.vx + math.sin(item.bob_phase) * 0.45
            item.y += item.vy

            if item.y > self.HEIGHT + 20:
                item.active = False
                continue

            dx = item.x - self.player.x
            dy = item.y - self.player.y
            limit = item.radius + self.TEA_PICKUP_RADIUS
            if dx * dx + dy * dy <= limit * limit:
                item.active = False
                self._upgrade_weapon_family(item.family)
                continue

            next_items.append(item)

        self.weapon_items = next_items

    def _update_heal_items(self) -> None:
        next_items: list[HealItem] = []

        for item in self.heal_items:
            if not item.active:
                continue

            item.bob_phase += self.TEA_BOB_SPEED
            item.x += item.vx + math.sin(item.bob_phase) * 0.38
            item.y += item.vy

            if item.y > self.HEIGHT + 20:
                item.active = False
                continue

            dx = item.x - self.player.x
            dy = item.y - self.player.y
            limit = item.radius + self.TEA_PICKUP_RADIUS
            if dx * dx + dy * dy <= limit * limit:
                item.active = False
                if self.player.hp < self.player.max_hp:
                    self.player.hp = min(self.player.max_hp, self.player.hp + 1)
                    self._show_notice(
                        label="HP GET",
                        title="HEART RECOVER",
                        description=f"HP {self.player.hp}/{self.player.max_hp}",
                        accent=8,
                        kind="shot_up",
                    )
                continue

            next_items.append(item)

        self.heal_items = next_items

    def _update_bit_items(self) -> None:
        next_items: list[BitItem] = []

        for item in self.bit_items:
            if not item.active:
                continue

            item.bob_phase += self.TEA_BOB_SPEED
            item.x += item.vx + math.sin(item.bob_phase) * 0.42
            item.y += item.vy

            if item.y > self.HEIGHT + 20:
                item.active = False
                continue

            dx = item.x - self.player.x
            dy = item.y - self.player.y
            limit = item.radius + self.TEA_PICKUP_RADIUS
            if dx * dx + dy * dy <= limit * limit:
                item.active = False
                upgraded_slot = self._upgrade_player_bits()
                if upgraded_slot < 0:
                    continue
                self._show_notice(
                    label="BIT GET",
                    title="SOY BIT BOOST",
                    description=f"BIT {upgraded_slot + 1} LV {self.player_bit_levels[upgraded_slot]}",
                    accent=10,
                    kind="reward",
                )
                continue

            next_items.append(item)

        self.bit_items = next_items

    def _update_wasabi_items(self) -> None:
        next_items: list[WasabiItem] = []

        for item in self.wasabi_items:
            if not item.active:
                continue

            item.bob_phase += self.TEA_BOB_SPEED
            item.x += item.vx + math.sin(item.bob_phase) * 0.40
            item.y += item.vy

            if item.y > self.HEIGHT + 20:
                item.active = False
                continue

            dx = item.x - self.player.x
            dy = item.y - self.player.y
            limit = item.radius + self.TEA_PICKUP_RADIUS
            if dx * dx + dy * dy <= limit * limit:
                item.active = False
                self.wasabi_pickup_count += 1
                self._add_wasabi_orbit_entry()
                self._show_notice(
                    label="WASABI GET",
                    title="WASABI STOCK",
                    description="EXPAND NEXT SETTLE",
                    accent=11,
                    kind="reward",
                )
                continue

            next_items.append(item)

        self.wasabi_items = next_items

    def _upgrade_player_bits(self) -> int:
        for idx in range(self.BIT_SLOT_COUNT_MAX):
            if self.player_bit_levels[idx] == 0:
                self.player_bit_levels[idx] = 1
                return idx

        for level in range(1, self.BIT_POWER_LEVEL_MAX):
            for idx in range(self.BIT_SLOT_COUNT_MAX):
                if self.player_bit_levels[idx] == level:
                    self.player_bit_levels[idx] = level + 1
                    return idx

        return -1

    def _calc_enemy_bullet_max_life(self, vx: float, vy: float) -> int:
        speed = max(0.01, math.hypot(vx, vy))
        travel_w = self.WIDTH + (self.ENEMY_BULLET_MARGIN * 2)
        travel_h = (self.HEIGHT - self.PLAY_TOP) + (self.ENEMY_BULLET_MARGIN * 2)
        travel_distance = math.hypot(travel_w, travel_h)
        life = int(travel_distance / speed) + 12
        return max(self.ENEMY_BULLET_MIN_LIFE, min(self.ENEMY_BULLET_MAX_LIFE, life))

    def _is_enemy_bullet_in_bounds(self, bullet: EnemyBullet) -> bool:
        return (
            -self.ENEMY_BULLET_MARGIN <= bullet.x <= self.WIDTH + self.ENEMY_BULLET_MARGIN
            and self.PLAY_TOP - self.ENEMY_BULLET_MARGIN <= bullet.y <= self.HEIGHT + self.ENEMY_BULLET_MARGIN
        )

    def _append_enemy_bullet(
        self,
        *,
        x: float,
        y: float,
        vx: float,
        vy: float,
        radius: int,
        color: int,
        damage: int,
        display_scale: float,
        slow_inflict: bool = False,
    ) -> bool:
        if len(self.enemy_bullets) >= self.ENEMY_BULLET_MAX_COUNT:
            return False
        vx += self._drift_x_bias(self.DRIFT_ENEMY_BULLET_VX)

        self.enemy_bullets.append(
            EnemyBullet(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                radius=radius,
                color=color,
                damage=damage,
                display_scale=display_scale,
                slow_inflict=slow_inflict,
                age=0,
                max_life=self._calc_enemy_bullet_max_life(vx, vy),
            )
        )
        return True

    def _trim_enemy_bullets_to_cap(self) -> None:
        if len(self.enemy_bullets) <= self.ENEMY_BULLET_MAX_COUNT:
            return

        def keep_priority(bullet: EnemyBullet) -> tuple[int, float, int]:
            inside_visible = 0 <= bullet.x <= self.WIDTH and self.PLAY_TOP <= bullet.y <= self.HEIGHT
            distance_to_player = abs(bullet.x - self.player.x) + abs(bullet.y - self.player.y)
            return (1 if inside_visible else 0, -distance_to_player, -bullet.age)

        self.enemy_bullets.sort(key=keep_priority, reverse=True)

        for bullet in self.enemy_bullets[self.ENEMY_BULLET_MAX_COUNT :]:
            bullet.active = False

        self.enemy_bullets = self.enemy_bullets[: self.ENEMY_BULLET_MAX_COUNT]

    def _enemy_burst_scale_from_enemy(self, enemy: Enemy) -> float:
        return max(1.0, 0.75 + enemy.display_scale * 1.15)

    def _boss_burst_scale(self, boss: Boss | None = None) -> float:
        target = boss if boss is not None else self.boss
        if target is None:
            return 3.0
        return max(3.0, 1.20 + target.display_scale * 1.55)

    def _spawn_enemy_burst(self, x: float, y: float, scale: float = 1.0) -> None:
        self.effects.spawn_enemy_burst(x=x, y=y, scale=scale, layer=10)

    def _spawn_hit_spark(self, x: float, y: float, scale: float = 1.0) -> None:
        self.effects.spawn_hit_spark(x=x, y=y, scale=scale, layer=11)

    def _spawn_bullet_cancel_sprite(self, x: float, y: float, scale: float = 1.0) -> None:
        self.effects.spawn_bullet_cancel_sprite(x=x, y=y, scale=scale, layer=11)

    def _spawn_laser_impact(self, x: float, y: float, vx: float, vy: float, scale: float = 1.0) -> None:
        self.effects.spawn_laser_impact(x=x, y=y, vx=vx, vy=vy, scale=scale, layer=12)

    def _spawn_bomb_launch_flash(self, x: float, y: float, scale: float = 1.0) -> None:
        self.effects.spawn_bomb_launch_flash(x=x, y=y, scale=scale, layer=9)

    def _is_boss_active(self) -> bool:
        return self.boss is not None and self.boss.active

    def _boss_phase(self) -> int:
        return boss_phase(self.boss)

    def _should_trigger_boss(self) -> bool:
        if self.boss_event_started or self._is_boss_active() or self.boss_intro_timer > 0:
            return False

        return (
            self.enemy_kill_count >= self.next_boss_kill_threshold
            or self.combat_progress_score >= self.next_boss_score_threshold
        )

    def _start_boss_intro(self) -> None:
        self.boss_event_started = True
        retreating_enemies = bool(self.enemies)
        self.boss_retreat_timer = self.BOSS_RETREAT_FRAMES if retreating_enemies else 0
        self.boss_intro_timer = self.BOSS_WARNING_TIME + self.boss_retreat_timer
        self._select_boss_pattern()
        self.audio.play_se("boss_warning")
        self.audio.play_bgm("bgm_boss")

        self.enemy_bullets.clear()
        self.bullets.clear()
        self.echo_shots.clear()
        self.bombs.clear()
        self.homing_lasers.clear()
        if retreating_enemies:
            self._start_enemy_retreat_for_boss()
        else:
            self.enemies.clear()
            self.retreat_shadows.clear()

    def _spawn_boss(self) -> None:
        self.boss = spawn_boss(
            width=self.WIDTH,
            entry_target_y=float(self.BOSS_ENTRY_TARGET_Y),
            max_hp=self.BOSS_MAX_HP,
            spawn_count=self.boss_spawn_count,
        )
        self.assign_buff_to_current_boss()
        self.audio.play_se("boss_entry")
        if self.boss_pattern_id == "asanoha":
            boosted_hp = int(round(self.boss.max_hp * self.ASANOHA_HP_MULT))
            self.boss.max_hp = boosted_hp
            self.boss.hp = boosted_hp
        self.boss_pattern_label_timer = self.BOSS_PATTERN_LABEL_FRAMES
        self.boss_hp_display = float(self.boss.max_hp)
        self.boss_hp_trail = float(self.boss.max_hp)
        self.boss_hp_shake_timer = 0
        self.boss_hp_flash_timer = 0

    def _advance_boss_progression(self) -> None:
        self.boss_spawn_count += 1
        extra_kills = self.FEVER_EXTRA_KILL_TARGET if self._fever_active() else 0
        extra_score = self.FEVER_EXTRA_SCORE_TARGET if self._fever_active() else 0
        self.next_boss_kill_threshold += self.BOSS_TRIGGER_KILLS + extra_kills
        self.next_boss_score_threshold += (self.boss_spawn_count + 1) * 1000 + extra_score
        self.spawn_interval_sec = max(0.28, self.spawn_interval_sec - 0.04)

    def _update_boss_intro(self) -> None:
        if self.boss_intro_timer <= 0:
            return
        self.boss_intro_timer -= 1
        if self.boss_retreat_timer > 0:
            self.boss_retreat_timer -= 1
        if self.boss_intro_timer > 0 and self.boss_intro_timer % 28 == 0:
            self.audio.play_se("boss_warning")
        if self.boss_intro_timer <= 0 and self.boss is None:
            self.enemies.clear()
            self.retreat_shadows.clear()
            self._spawn_boss()

    def _update_boss_hp_bar_fx(self) -> None:
        if self.boss_damage_cooldown > 0:
            self.boss_damage_cooldown -= 1
        if self.boss_hp_shake_timer > 0:
            self.boss_hp_shake_timer -= 1
        if self.boss_hp_flash_timer > 0:
            self.boss_hp_flash_timer -= 1

        target_hp = float(self.boss.hp) if self.boss is not None else 0.0
        self.boss_hp_display = target_hp

        if self.boss_hp_trail > target_hp:
            diff = self.boss_hp_trail - target_hp
            self.boss_hp_trail -= max(0.8, diff * 0.10)
            if self.boss_hp_trail < target_hp:
                self.boss_hp_trail = target_hp
        else:
            self.boss_hp_trail = target_hp

    def _trigger_boss_hp_bar_hit_fx(self) -> None:
        self.boss_hp_shake_timer = max(self.boss_hp_shake_timer, 6)
        self.boss_hp_flash_timer = max(self.boss_hp_flash_timer, 5)

    def _boss_hp_bar_shake_offset(self) -> int:
        if self.boss_hp_shake_timer <= 0:
            return 0
        pattern = (-2, 2, -1, 1, -1, 1)
        idx = min(len(pattern) - 1, 6 - self.boss_hp_shake_timer)
        return pattern[idx]

    def _update_boss(self) -> None:
        if self.boss is None or not self.boss.active:
            return

        prev_laser_telegraph = getattr(self.boss, "laser_telegraph_timer", 0)
        prev_special_beam_telegraph = getattr(self.boss, "special_beam_telegraph_timer", 0)
        prev_dash_telegraph = getattr(self.boss, "dash_telegraph_timer", 0)
        prev_summon_flash = getattr(self.boss, "summon_flash_timer", 0)

        def append_boss_bullet(
            *,
            x: float,
            y: float,
            vx: float,
            vy: float,
            radius: int,
            color: int,
            damage: int,
            display_scale: float,
        ) -> bool:
            scaled_radius = radius
            scaled_display = display_scale

            if self.boss_shippo_enabled:
                size_scale = random.choice(self.SHIPPO_SIZE_SCALES)
                scaled_radius = max(2, int(round(radius * size_scale)))
                scaled_display = display_scale * (0.92 + (size_scale - 1.0) * 0.55)

            return self._append_enemy_bullet(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                radius=scaled_radius,
                color=color,
                damage=damage,
                display_scale=scaled_display,
                slow_inflict=self.boss_slow_inflict_enabled,
            )

        update_boss(
            boss=self.boss,
            frame_count=self.frame_count,
            width=self.WIDTH,
            height=self.HEIGHT,
            side_margin=self.SIDE_MARGIN,
            boss_sprite_w=self.BOSS_SPRITE_W,
            player_x=float(self.player.x),
            player_y=float(self.player.y),
            append_enemy_bullet=append_boss_bullet,
            move_speed_multiplier=self.boss_move_speed_multiplier,
            spawn_count=self.boss_spawn_count,
            mercy_rage=not self._has_power_weapon_active(),
            enemies=self.enemies,
            create_enemy=self._create_enemy,
        )

        if prev_laser_telegraph <= 0 and getattr(self.boss, "laser_telegraph_timer", 0) > 0:
            self.audio.play_se("boss_laser_telegraph")
        if prev_special_beam_telegraph <= 0 and getattr(self.boss, "special_beam_telegraph_timer", 0) > 0:
            self.audio.play_se("boss_laser_telegraph")
        if prev_dash_telegraph <= 0 and getattr(self.boss, "dash_telegraph_timer", 0) > 0:
            self.audio.play_se("boss_dash_telegraph")
        if prev_summon_flash <= 0 and getattr(self.boss, "summon_flash_timer", 0) > 0:
            self.audio.play_se("boss_summon")

    def _update_boss_defeat_sequence(self) -> None:
        if self.boss_defeat_timer <= 0 and self.boss_defeat_confetti_timer <= 0:
            return

        self._update_boss_defeat_sushis()
        self._update_boss_defeat_cheers()

        if self.boss_defeat_confetti_timer > 0:
            self.boss_defeat_confetti_timer -= 1

        if self.boss_defeat_timer > 0:
            self.boss_defeat_timer -= 1
            elapsed = self.BOSS_DEFEAT_SEQUENCE_FRAMES - self.boss_defeat_timer

            if elapsed % 6 == 0:
                self.audio.play_se("boss_burst_pop")
                jitter_x = random.uniform(-22.0, 22.0)
                jitter_y = random.uniform(-16.0, 18.0)
                self._spawn_enemy_burst(
                    self.boss_defeat_x + jitter_x,
                    self.boss_defeat_y + jitter_y,
                    scale=max(1.4, self.boss_defeat_scale * (0.85 + elapsed * 0.015)),
                )
            if elapsed % 4 == 0:
                self.audio.play_se("boss_burst_low")
                self._spawn_enemy_burst(
                    self.boss_defeat_x + random.uniform(-30.0, 30.0),
                    self.boss_defeat_y + random.uniform(-24.0, 24.0),
                    scale=max(0.7, self.boss_defeat_scale * 0.45),
                )
            if elapsed % 5 == 0:
                self._spawn_hit_spark(
                    self.boss_defeat_x + random.uniform(-34.0, 34.0),
                    self.boss_defeat_y + random.uniform(-28.0, 22.0),
                    scale=max(0.9, self.boss_defeat_scale * 0.55),
                )
            if elapsed >= self.BOSS_DEFEAT_SEQUENCE_FRAMES // 2 and elapsed % 7 == 0:
                self._spawn_hit_spark(
                    self.boss_defeat_x + random.uniform(-42.0, 42.0),
                    self.boss_defeat_y + random.uniform(-32.0, 26.0),
                    scale=max(0.7, self.boss_defeat_scale * 0.42),
                )

        if self.boss_defeat_timer <= 0 and self.boss_defeat_confetti_timer <= 0:
            self.boss_event_started = False
            self.boss_defeated = True
            self.boss_defeat_sushis.clear()
            self.boss_defeat_cheers.clear()
            self._advance_boss_progression()
            if self.fever_arrival_pending:
                self._start_fever_arrival_effect()
            else:
                self._start_reward_selection()

    def _on_boss_defeated(self) -> None:
        if self.boss is None:
            return

        boss = self.boss
        self.absorb_current_boss_buff()
        self.score += self.BOSS_SCORE_VALUE
        self.combat_progress_score += self.BOSS_SCORE_VALUE
        self.boss_defeat_count += 1
        self.audio.play_se("boss_defeat")
        self.audio.play_bgm("bgm_stage")
        self.player.hp = self.player.max_hp
        self.enemy_bullets.clear()
        self.bomb_stock = min(self._bomb_capacity(), self.bomb_stock + 1)

        burst_scale = self._boss_burst_scale(boss)
        self._spawn_enemy_burst(boss.x, boss.y, scale=burst_scale)
        self._spawn_enemy_burst(boss.x - 18, boss.y + 6, scale=burst_scale * 0.74)
        self._spawn_enemy_burst(boss.x + 20, boss.y - 8, scale=burst_scale * 0.68)

        self.enemies.clear()
        self.bullets.clear()
        self.echo_shots.clear()
        self.bombs.clear()
        self.active_bomb_visuals.clear()
        self.homing_lasers.clear()
        self.weapon_items.clear()
        self.heal_items.clear()
        self.bit_items.clear()
        self.wasabi_items.clear()
        self.boss_defeat_timer = self.BOSS_DEFEAT_SEQUENCE_FRAMES
        self.boss_defeat_confetti_timer = self.BOSS_DEFEAT_CONFETTI_FRAMES
        self.boss_defeat_x = boss.x
        self.boss_defeat_y = boss.y
        self.boss_defeat_scale = boss.display_scale
        self._spawn_boss_defeat_sushi_burst(boss.x, boss.y, boss.display_scale)
        self._spawn_boss_defeat_cheers(boss.x, boss.y, boss.display_scale)
        if self.drift_state in {self.DRIFT_STATE_ENTERING, self.DRIFT_STATE_ACTIVE}:
            self.drift_exit_pending = True
        self.boss = None
        self.boss_defeated = False

    def _start_fever_arrival_effect(self) -> None:
        rng = random.Random(self.frame_count * 131 + self.enemy_kill_count * 17)
        center_x = self.WIDTH * 0.5
        center_y = self.PLAY_TOP + 226
        self.reward_notice_timer = 0
        self.audio.play_bgm("bgm_fever_arrival")
        self.bullets.clear()
        self.echo_shots.clear()
        self.bombs.clear()
        self.active_bomb_visuals.clear()
        self.homing_lasers.clear()
        self.enemy_bullets.clear()
        sushis: list[FeverArrivalSushi] = []
        cols = 7
        row_gap = 24
        col_gap = 24
        aligned_count = min(self.FEVER_ARRIVAL_ALIGNED_COUNT, self.FEVER_ARRIVAL_SUSHI_COUNT)
        for idx in range(self.FEVER_ARRIVAL_SUSHI_COUNT):
            if idx < aligned_count:
                row = idx // cols
                col = idx % cols
                target_x = center_x + (col - (cols - 1) / 2) * col_gap + rng.uniform(-4.0, 4.0)
                target_y = center_y + (row - 1.5) * row_gap + rng.uniform(-3.0, 3.0)
            else:
                extra_idx = idx - aligned_count
                extra_count = max(1, self.FEVER_ARRIVAL_SUSHI_COUNT - aligned_count)
                angle = (extra_idx / extra_count) * math.tau + rng.uniform(-0.22, 0.22)
                radius_x = 104.0 + rng.uniform(-18.0, 18.0)
                radius_y = 62.0 + rng.uniform(-14.0, 14.0)
                target_x = center_x + math.cos(angle) * radius_x
                target_y = center_y + math.sin(angle) * radius_y + rng.uniform(-6.0, 6.0) + 8.0
            side = -1 if idx % 2 == 0 else 1
            start_x = -26.0 - rng.uniform(0.0, 34.0) if side < 0 else self.WIDTH + 26.0 + rng.uniform(0.0, 34.0)
            start_y = center_y + rng.uniform(-72.0, 72.0)
            sushis.append(
                FeverArrivalSushi(
                    start_x=start_x,
                    start_y=start_y,
                    target_x=target_x,
                    target_y=target_y,
                    current_x=start_x,
                    current_y=start_y,
                    enemy_type=rng.choice(self.ORBIT_SPRITE_TYPES),
                    anim_offset=rng.randrange(0, self.ENEMY_SPRITE_FRAMES),
                    anim_dir=rng.choice((-1, 1)),
                    display_scale=rng.uniform(0.84, 1.16),
                    side=side,
                    delay=(idx % 18) * 4 + rng.randrange(0, 5),
                    bounce_height=rng.uniform(4.0, 11.0),
                    bounce_phase=rng.uniform(0.0, math.tau),
                )
            )
        self.fever_arrival_effect = FeverArrivalEffect(
            active=True,
            timer=0,
            center_x=center_x,
            center_y=center_y,
            sushis=sushis,
        )
        self.audio.play_se("weapon_level_up")

    def _update_fever_arrival_effect(self) -> None:
        effect = self.fever_arrival_effect
        if not effect.active:
            return
        effect.timer += 1

        gather_frames = self.FEVER_ARRIVAL_GATHER_FRAMES
        hop_frames = self.FEVER_ARRIVAL_HOP_FRAMES
        for sushi in effect.sushis:
            local_timer = max(0, effect.timer - sushi.delay)
            if local_timer < gather_frames:
                t = min(1.0, local_timer / max(1, gather_frames))
                u = 1.0 - (1.0 - t) * (1.0 - t)
                sushi.current_x = sushi.start_x + (sushi.target_x - sushi.start_x) * u
                sushi.current_y = sushi.start_y + (sushi.target_y - sushi.start_y) * u
            else:
                hop_elapsed = local_timer - gather_frames
                hop_u = min(1.0, hop_elapsed / max(1, hop_frames))
                hop_wave = abs(math.sin(hop_u * math.tau * 4.0 + sushi.bounce_phase))
                hover = math.sin(hop_u * math.tau * 0.8 + sushi.bounce_phase) * 1.5
                sushi.current_x = sushi.target_x
                sushi.current_y = sushi.target_y - hop_wave * sushi.bounce_height + hover

        if effect.timer >= self.FEVER_ARRIVAL_FRAMES:
            effect.active = False
            self.fever_arrival_pending = False
            self.audio.play_bgm("bgm_reward")
            self._start_reward_selection()

    def _spawn_boss_defeat_sushi_burst(self, x: float, y: float, boss_scale: float) -> None:
        rng = random.Random(self.frame_count * 97 + int(x * 3) + int(y * 5))
        burst: list[BossDefeatSushi] = []
        size_pool = (
            [0.82] * 34
            + [0.98] * 34
            + [1.14] * 22
            + [1.34] * 12
        )
        rng.shuffle(size_pool)
        delay_pool = [((idx % 14) * 3) + rng.randrange(0, 3) for idx in range(self.BOSS_DEFEAT_SUSHI_COUNT)]
        rng.shuffle(delay_pool)

        for idx in range(self.BOSS_DEFEAT_SUSHI_COUNT):
            angle = (math.tau / self.BOSS_DEFEAT_SUSHI_COUNT) * idx + rng.uniform(-0.045, 0.045)
            speed_band = rng.choice((0.62, 0.82, 1.04, 1.34, 1.58))
            speed = rng.uniform(3.8, 9.4) * speed_band * max(1.0, boss_scale * 0.74)
            spawn_r = rng.uniform(0.0, 10.0)
            depth = rng.uniform(-0.38, 0.42)
            scale = size_pool[idx % len(size_pool)] * (1.0 + depth * 0.16)
            if speed_band >= 1.34:
                scale *= rng.uniform(0.84, 0.92)
            elif speed_band <= 0.82:
                scale *= rng.uniform(1.08, 1.18)
            wave_delay = delay_pool[idx]
            if scale >= 1.28:
                wave_delay += rng.randrange(4, 10)
                speed *= rng.uniform(0.82, 0.90)
            elif scale >= 1.10:
                wave_delay += rng.randrange(1, 4)
                speed *= rng.uniform(0.92, 0.98)
            burst.append(
                BossDefeatSushi(
                    x=x + math.cos(angle) * spawn_r,
                    y=y + math.sin(angle) * spawn_r * 0.82,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed * rng.uniform(0.88, 1.04),
                    enemy_type=rng.choice(self.ORBIT_SPRITE_TYPES),
                    anim_offset=rng.randrange(0, self.ENEMY_SPRITE_FRAMES),
                    anim_dir=rng.choice((-1, 1)),
                    scale=max(0.78, min(1.72, scale)),
                    depth=depth,
                    delay=wave_delay + rng.randrange(0, 5),
                )
            )
        self.boss_defeat_sushis = burst

    def _spawn_boss_defeat_cheers(self, x: float, y: float, boss_scale: float) -> None:
        rng = random.Random(self.frame_count * 131 + int(x * 7) + int(y * 11))
        cheers: list[BossDefeatCheer] = []
        angle_step = math.tau / self.BOSS_DEFEAT_CHEER_COUNT
        delay_pool = [idx * 5 + rng.randrange(0, 4) for idx in range(self.BOSS_DEFEAT_CHEER_COUNT)]
        rng.shuffle(delay_pool)
        color_pool = (15, 10, 11, 14)
        for idx in range(self.BOSS_DEFEAT_CHEER_COUNT):
            angle = angle_step * idx + rng.uniform(-0.09, 0.09)
            speed = rng.uniform(2.4, 4.6) * max(1.0, boss_scale * 0.74)
            spawn_r = rng.uniform(2.0, 12.0)
            text = self.BOSS_DEFEAT_CHEER_TEXTS[idx % len(self.BOSS_DEFEAT_CHEER_TEXTS)]
            roll = rng.random()
            if roll < 0.52:
                scale = 0
            elif roll < 0.90:
                scale = 1
            else:
                scale = 2
            cheers.append(
                BossDefeatCheer(
                    x=x + math.cos(angle) * spawn_r,
                    y=y + math.sin(angle) * spawn_r * 0.82,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed * rng.uniform(0.86, 1.02),
                    text=text,
                    color=color_pool[idx % len(color_pool)],
                    shadow_color=1,
                    scale=scale,
                    delay=delay_pool[idx],
                )
            )
        self.boss_defeat_cheers = cheers

    def _update_boss_defeat_sushis(self) -> None:
        if not self.boss_defeat_sushis:
            return

        updated: list[BossDefeatSushi] = []
        for sushi in self.boss_defeat_sushis:
            if not sushi.active:
                continue
            if sushi.delay > 0:
                sushi.delay -= 1
                updated.append(sushi)
                continue

            sushi.life += 1
            sushi.x += sushi.vx
            sushi.y += sushi.vy
            sushi.vx *= 0.996
            sushi.vy *= 0.996
            if sushi.life > 4:
                sushi.vy += 0.015

            margin = 42
            if (
                sushi.x < -margin
                or sushi.x > self.WIDTH + margin
                or sushi.y < self.PLAY_TOP - margin
                or sushi.y > self.HEIGHT + margin
            ):
                continue
            updated.append(sushi)

        self.boss_defeat_sushis = updated

    def _update_boss_defeat_cheers(self) -> None:
        if not self.boss_defeat_cheers:
            return

        updated: list[BossDefeatCheer] = []
        for cheer in self.boss_defeat_cheers:
            if not cheer.active:
                continue
            if cheer.delay > 0:
                cheer.delay -= 1
                updated.append(cheer)
                continue

            cheer.life += 1
            cheer.x += cheer.vx
            cheer.y += cheer.vy
            cheer.vx *= 0.995
            cheer.vy *= 0.995
            if cheer.life > 5:
                cheer.vy += 0.012

            if (
                cheer.x < -96
                or cheer.x > self.WIDTH + 96
                or cheer.y < self.PLAY_TOP - 48
                or cheer.y > self.HEIGHT + 48
            ):
                continue
            updated.append(cheer)

        self.boss_defeat_cheers = updated

    def _laser_origin(self, boss: Boss) -> tuple[float, float]:
        return boss.x, boss.y + 4.0

    def _laser_dir(self, boss: Boss) -> tuple[float, float]:
        angle = getattr(boss, "laser_angle", math.pi / 2)
        return math.cos(angle), math.sin(angle)

    def _boss_special_beam_segments(self, boss: Boss) -> list[tuple[float, float, float, float]]:
        kind = getattr(boss, "special_beam_kind", "none")
        if kind == "dual_straight":
            oy = boss.y + 8.0
            length = max(self.WIDTH, self.HEIGHT) * 1.7
            return [
                (boss.x - 18.0, oy, boss.x - 18.0, oy + length),
                (boss.x + 18.0, oy, boss.x + 18.0, oy + length),
            ]
        if kind == "dual_cross":
            ox = boss.x
            oy = boss.y + 4.0
            length = max(self.WIDTH, self.HEIGHT) * 1.6
            segments: list[tuple[float, float, float, float]] = []
            for angle in (math.radians(62), math.radians(118)):
                dx = math.cos(angle) * length
                dy = math.sin(angle) * length
                segments.append((ox, oy, ox + dx, oy + dy))
            return segments
        return []

    def _boss_special_saber_state(self, boss: Boss) -> tuple[float, float, float] | None:
        if getattr(boss, "special_beam_kind", "none") != "saber_sweep":
            return None
        total = max(1, getattr(boss, "special_beam_total_active_timer", 1))
        active = max(0, getattr(boss, "special_beam_active_timer", 0))
        progress = 1.0 - (active / total)
        sweep_from = math.radians(30)
        sweep_to = math.radians(150)
        if getattr(boss, "special_beam_sweep_dir", 1) < 0:
            sweep_from, sweep_to = sweep_to, sweep_from
        current_angle = sweep_from + (sweep_to - sweep_from) * progress
        return (boss.x, boss.y + 10.0, current_angle)

    def _point_segment_distance_sq(
        self,
        px: float,
        py: float,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ) -> float:
        dx = x1 - x0
        dy = y1 - y0
        if dx == 0.0 and dy == 0.0:
            ox = px - x0
            oy = py - y0
            return ox * ox + oy * oy

        t = ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        cx = x0 + dx * t
        cy = y0 + dy * t
        ox = px - cx
        oy = py - cy
        return ox * ox + oy * oy

    def _boss_laser_hits_player(self) -> bool:
        if self.boss is None:
            return False
        if getattr(self.boss, "laser_active_timer", 0) <= 0:
            return False

        ox, oy = self._laser_origin(self.boss)
        dx, dy = self._laser_dir(self.boss)
        length = max(self.WIDTH, self.HEIGHT) * 1.7
        ex = ox + dx * length
        ey = oy + dy * length

        hit_r = 10.0
        px = float(self.player.x)
        py = float(self.player.y)
        limit_sq = hit_r * hit_r
        return self._point_segment_distance_sq(px, py, ox, oy, ex, ey) <= limit_sq

    def _boss_special_beam_hits_player(self) -> bool:
        if self.boss is None:
            return False
        if getattr(self.boss, "special_beam_active_timer", 0) <= 0:
            return False

        px = float(self.player.x)
        py = float(self.player.y)
        kind = getattr(self.boss, "special_beam_kind", "none")

        if kind == "saber_sweep":
            saber_state = self._boss_special_saber_state(self.boss)
            if saber_state is None:
                return False
            cx, cy, current_angle = saber_state
            dx = px - cx
            dy = py - cy
            radius = 96.0
            thickness = 13.0
            blade_arc = math.radians(34)
            distance = math.hypot(dx, dy)
            if abs(distance - radius) > thickness:
                return False
            point_angle = math.atan2(dy, dx)
            delta = math.atan2(math.sin(point_angle - current_angle), math.cos(point_angle - current_angle))
            return abs(delta) <= blade_arc

        hit_r = 11.0
        limit_sq = hit_r * hit_r
        for x0, y0, x1, y1 in self._boss_special_beam_segments(self.boss):
            if self._point_segment_distance_sq(px, py, x0, y0, x1, y1) <= limit_sq:
                return True
        return False

    def update(self) -> None:
        self.frame_count += 1
        self.audio.update(self.frame_count)

        self._update_stars()
        self._update_background_fireworks()
        self.effects.update()
        self._update_boss_hp_bar_fx()
        self._update_ui_timers()
        self.update_overload()
        self._update_drift_shift()
        self._update_retreat_shadows()

        if self.phase == GamePhase.START:
            self._update_start_input()
            return

        if self.phase == GamePhase.GAME_OVER:
            self._update_retry_input()
            return

        if self.phase == GamePhase.RESULT:
            self._update_result_input()
            return

        if self.phase == GamePhase.REWARD_SELECT:
            self.maybe_build_bomb_pattern_in_reward()
            self.maybe_build_orbit_pattern_in_nonbattle()
            self._update_reward_select_input()
            return

        if self.boss_defeat_timer > 0 or self.boss_defeat_confetti_timer > 0:
            self._update_boss_defeat_sequence()
            return

        if self.fever_arrival_effect.active:
            self._update_fever_arrival_effect()
            return

        self._update_player_state()
        self._update_touch_mode()
        self._update_player_input()
        self._update_shooting()
        self._update_special_input()
        self.update_orbit_sushi()
        self.update_sushi_settle_effect()

        if self.boss_intro_timer > 0:
            self._update_boss_intro()
            self._update_enemies()
        else:
            if self._is_boss_active():
                self._update_boss()
            else:
                self._update_spawning()
                self._update_enemies()

        self._update_bullets()
        self._update_echo_shots()
        self._update_enemy_bullets()
        self.update_bomb_visuals()
        self._update_bombs()
        self._update_homing_lasers()
        self._update_weapon_items()
        self._update_heal_items()
        self._update_bit_items()
        self._update_wasabi_items()

        self._handle_projectile_cancellations()
        self._handle_bullet_weapon_item_collisions()

        self._remove_offscreen_bullets()
        self._remove_offscreen_enemy_bullets()
        self._remove_offscreen_enemies()

        self._handle_bullet_enemy_collisions()
        self._handle_bullet_boss_collisions()
        self._handle_bomb_enemy_collisions()
        self._handle_bomb_boss_collisions()
        self._handle_homing_laser_enemy_collisions()
        self._handle_homing_laser_boss_collisions()
        self._handle_echo_enemy_collisions()
        self._handle_echo_boss_collisions()

        self._handle_player_enemy_collisions()
        self._handle_player_boss_collisions()
        self._handle_player_enemy_bullet_collisions()
        self.try_start_sushi_settlement()

        if self._boss_laser_hits_player():
            self._apply_player_damage(1, inflict_slow=self.boss_slow_inflict_enabled)
        elif self._boss_special_beam_hits_player():
            self._apply_player_damage(1, inflict_slow=False)

        if self.player.hp <= 0:
            self.audio.play_bgm("bgm_game_over")
            self.game_over_timer = self.GAME_OVER_FRAMES
            self.phase = GamePhase.GAME_OVER
            return

        if self._should_trigger_boss():
            self._start_boss_intro()

    def _update_start_input(self) -> None:
        if pyxel.btnp(pyxel.KEY_UP):
            self.start_menu_focus = max(0, self.start_menu_focus - 1)
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.start_menu_focus = min(self._start_menu_max_focus(), self.start_menu_focus + 1)

        if pyxel.btnp(pyxel.KEY_LEFT):
            if self.start_menu_focus == 0:
                self._move_theme_selection(-1)
            elif self.start_menu_focus == 1:
                self._move_start_weapon_selection(-1)
            elif self._start_sub_weapon_focus_index() == self.start_menu_focus:
                self._move_start_sub_weapon_selection(-1)
            elif self._start_bomb_power_focus_index() == self.start_menu_focus:
                self._move_start_bomb_power_selection(-1)
            elif self._start_laser_count_focus_index() == self.start_menu_focus:
                self._move_start_laser_count_selection(-1)
            elif self._start_fever_focus_index() == self.start_menu_focus:
                self._toggle_start_fever()
            elif self._start_prefever_focus_index() == self.start_menu_focus:
                self._toggle_start_prefever()
            elif self._start_boss_pattern_focus_index() == self.start_menu_focus:
                self._move_start_boss_pattern_selection(-1)
        elif pyxel.btnp(pyxel.KEY_RIGHT):
            if self.start_menu_focus == 0:
                self._move_theme_selection(1)
            elif self.start_menu_focus == 1:
                self._move_start_weapon_selection(1)
            elif self._start_sub_weapon_focus_index() == self.start_menu_focus:
                self._move_start_sub_weapon_selection(1)
            elif self._start_bomb_power_focus_index() == self.start_menu_focus:
                self._move_start_bomb_power_selection(1)
            elif self._start_laser_count_focus_index() == self.start_menu_focus:
                self._move_start_laser_count_selection(1)
            elif self._start_fever_focus_index() == self.start_menu_focus:
                self._toggle_start_fever()
            elif self._start_prefever_focus_index() == self.start_menu_focus:
                self._toggle_start_prefever()
            elif self._start_boss_pattern_focus_index() == self.start_menu_focus:
                self._move_start_boss_pattern_selection(1)

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            mx = float(pyxel.mouse_x)
            my = float(pyxel.mouse_y)

            extra_rows = self._start_debug_extra_rows()
            box_h = 300 + extra_rows * 64
            box_y = (self.HEIGHT - box_h) // 2
            selector_x = 46
            selector_y = box_y + 100
            selector_w = 268
            selector_h = 54
            weapon_selector_y = selector_y + 64
            sub_weapon_selector_y = weapon_selector_y + (64 if self._start_sub_weapon_menu_enabled() else 0)
            bomb_power_selector_y = sub_weapon_selector_y + 64
            laser_count_selector_y = bomb_power_selector_y + (64 if self.START_DEBUG_BOMB_POWER_MENU else 0)
            fever_selector_y = laser_count_selector_y + (64 if self.START_DEBUG_LASER_COUNT_MENU else 0)
            prefever_selector_y = fever_selector_y + (64 if self.START_DEBUG_FEVER_MENU else 0)
            debug_selector_y = prefever_selector_y + (64 if self.START_DEBUG_PREFEVER_MENU else 0)

            start_box_w = 280
            start_box_h = 34
            start_box_x = (self.WIDTH - start_box_w) // 2
            start_box_y = box_y + (238 + extra_rows * 64)

            if self._point_in_rect(mx, my, selector_x, selector_y, selector_w * 0.5, selector_h):
                self.start_menu_focus = 0
                self._move_theme_selection(-1)
                return
            if self._point_in_rect(mx, my, selector_x + selector_w * 0.5, selector_y, selector_w * 0.5, selector_h):
                self.start_menu_focus = 0
                self._move_theme_selection(1)
                return
            if self._point_in_rect(mx, my, selector_x, weapon_selector_y, selector_w * 0.5, selector_h):
                self.start_menu_focus = 1
                self._move_start_weapon_selection(-1)
                return
            if self._point_in_rect(mx, my, selector_x + selector_w * 0.5, weapon_selector_y, selector_w * 0.5, selector_h):
                self.start_menu_focus = 1
                self._move_start_weapon_selection(1)
                return
            if self._start_sub_weapon_menu_enabled():
                if self._point_in_rect(mx, my, selector_x, sub_weapon_selector_y, selector_w * 0.5, selector_h):
                    self.start_menu_focus = self._start_sub_weapon_focus_index() or 2
                    self._move_start_sub_weapon_selection(-1)
                    return
                if self._point_in_rect(mx, my, selector_x + selector_w * 0.5, sub_weapon_selector_y, selector_w * 0.5, selector_h):
                    self.start_menu_focus = self._start_sub_weapon_focus_index() or 2
                    self._move_start_sub_weapon_selection(1)
                    return
            if self.START_DEBUG_BOMB_POWER_MENU:
                if self._point_in_rect(mx, my, selector_x, bomb_power_selector_y, selector_w * 0.5, selector_h):
                    self.start_menu_focus = self._start_bomb_power_focus_index() or 2
                    self._move_start_bomb_power_selection(-1)
                    return
                if self._point_in_rect(mx, my, selector_x + selector_w * 0.5, bomb_power_selector_y, selector_w * 0.5, selector_h):
                    self.start_menu_focus = self._start_bomb_power_focus_index() or 2
                    self._move_start_bomb_power_selection(1)
                    return
            if self.START_DEBUG_LASER_COUNT_MENU:
                if self._point_in_rect(mx, my, selector_x, laser_count_selector_y, selector_w * 0.5, selector_h):
                    self.start_menu_focus = self._start_laser_count_focus_index() or 2
                    self._move_start_laser_count_selection(-1)
                    return
                if self._point_in_rect(mx, my, selector_x + selector_w * 0.5, laser_count_selector_y, selector_w * 0.5, selector_h):
                    self.start_menu_focus = self._start_laser_count_focus_index() or 2
                    self._move_start_laser_count_selection(1)
                    return
            if self.START_DEBUG_FEVER_MENU:
                if self._point_in_rect(mx, my, selector_x, fever_selector_y, selector_w, selector_h):
                    self.start_menu_focus = self._start_fever_focus_index() or 2
                    self._toggle_start_fever()
                    return
            if self.START_DEBUG_PREFEVER_MENU:
                if self._point_in_rect(mx, my, selector_x, prefever_selector_y, selector_w, selector_h):
                    self.start_menu_focus = self._start_prefever_focus_index() or 2
                    self._toggle_start_prefever()
                    return
            if self.START_DEBUG_BOSS_PATTERN_MENU:
                if self._point_in_rect(mx, my, selector_x, debug_selector_y, selector_w * 0.5, selector_h):
                    self.start_menu_focus = self._start_boss_pattern_focus_index() or 2
                    self._move_start_boss_pattern_selection(-1)
                    return
                if self._point_in_rect(mx, my, selector_x + selector_w * 0.5, debug_selector_y, selector_w * 0.5, selector_h):
                    self.start_menu_focus = self._start_boss_pattern_focus_index() or 2
                    self._move_start_boss_pattern_selection(1)
                    return
            if self._point_in_rect(mx, my, start_box_x, start_box_y, start_box_w, start_box_h):
                self.audio.play_se("ui_confirm")
                self._reset_play_state()
                self._begin_enemy_loop(after_boss=False)
                self.audio.play_bgm("bgm_stage")
                self.phase = GamePhase.PLAYING
                return

        wants_start = pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE)
        if wants_start:
            self.audio.play_se("ui_confirm")
            self._reset_play_state()
            self._begin_enemy_loop(after_boss=False)
            self.audio.play_bgm("bgm_stage")
            self.phase = GamePhase.PLAYING

    def _update_retry_input(self) -> None:
        if self.game_over_timer > 0:
            self.game_over_timer -= 1
            if self.game_over_timer <= 0:
                self._enter_result_state()
            return

    def _enter_result_state(self) -> None:
        self.enemies.clear()
        self.retreat_shadows.clear()
        self.enemy_bullets.clear()
        self.bullets.clear()
        self.echo_shots.clear()
        self.homing_lasers.clear()
        self.bombs.clear()
        self.active_bomb_visuals.clear()
        self.audio.play_bgm("bgm_result")
        self.phase = GamePhase.RESULT

    def _update_result_input(self) -> None:
        wants_retry = (
            pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.KEY_SPACE)
            or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
        )
        if wants_retry:
            self.audio.play_se("ui_confirm")
            self._save_weapon_progress_for_restart()
            self._sync_start_menu_from_carryover()
            self.start_sub_weapon_menu_unlocked = True
            self._reset_play_state()
            self.audio.play_bgm("bgm_start")
            self.phase = GamePhase.START

    def _result_enemy_rows(self) -> list[tuple[str, int]]:
        rows: list[tuple[str, int]] = []
        for enemy_type in self.RESULT_ENEMY_TYPE_ORDER:
            if enemy_type == "boss":
                count = self.boss_defeat_count
            else:
                count = self.kill_counts_by_type.get(enemy_type, 0)
            rows.append((enemy_type, count))
        return rows

    def _result_combo_rows(self) -> list[tuple[str, int]]:
        rows: list[tuple[str, int]] = []
        for combo_id, display_name in self.SUSHI_COMBO_DEFINITIONS:
            count = self.combo_counts.get(combo_id, 0)
            rows.append((display_name, count))
        return rows

    def _result_param_rows(self) -> list[tuple[str, str]]:
        return [
            ("WASABI", str(self.wasabi_pickup_count)),
            ("MAX HP", str(self.player.max_hp)),
            ("BOMB CAP", str(self._bomb_capacity())),
            ("BOMB PWR", f"LV{self.bomb_power_level + 1}"),
            ("LASER CNT", str(self.laser_shot_count)),
            ("LASER RLD", str(self.laser_cooldown_frames)),
            ("ITEM RATE", f"{int(round(self._tea_drop_rate() * 100))}%"),
            ("BITS", f"{self.player_bit_levels[0]}-{self.player_bit_levels[1]}"),
        ]

    def _result_weapon_rows(self) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        for family in self.WEAPON_FAMILY_ORDER:
            level = self.weapon_levels.get(family, -1)
            if level < 0:
                level_text = "-----"
            else:
                level_text = self._shot_level_name(level)
            rows.append((self._weapon_name(family), level_text))
        return rows

    def _update_reward_select_input(self) -> None:
        if not self.reward_choices:
            self._begin_enemy_loop(after_boss=True)
            self.audio.play_bgm("bgm_stage")
            self.phase = GamePhase.PLAYING
            return

        if self.reward_intro_timer > 0:
            self.reward_intro_timer -= 1

        if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_UP):
            self.reward_selection_index = (self.reward_selection_index - 1) % len(self.reward_choices)
            self.audio.play_se("ui_move")
        elif pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_DOWN):
            self.reward_selection_index = (self.reward_selection_index + 1) % len(self.reward_choices)
            self.audio.play_se("ui_move")

        if self.reward_intro_timer > 6:
            return

        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
            self.audio.play_se("ui_confirm")
            self._apply_reward_choice(self.reward_choices[self.reward_selection_index])
            return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            mx = float(pyxel.mouse_x)
            my = float(pyxel.mouse_y)
            if self._dual_shot_ready():
                for idx, family in enumerate(self.WEAPON_FAMILY_ORDER):
                    bx, by, bw, bh = self._dual_button_rect(idx)
                    if self._point_in_rect(mx, my, bx, by, bw, bh):
                        if not self._is_weapon_unlocked(family):
                            self.audio.play_se("ui_invalid")
                            return
                        self.audio.play_se("ui_move")
                        self._select_dual_weapon_button(family)
                        return
            for idx, _choice in enumerate(self.reward_choices):
                box_y = self.REWARD_BOX_START_Y + idx * (self.REWARD_BOX_H + self.REWARD_BOX_GAP)
                if self._point_in_rect(mx, my, self.REWARD_BOX_X, box_y, self.REWARD_BOX_W, self.REWARD_BOX_H):
                    self.reward_selection_index = idx
                    self.audio.play_se("ui_confirm")
                    self._apply_reward_choice(self.reward_choices[idx])
                    return

    def _update_player_state(self) -> None:
        if self.player.shoot_cooldown > 0:
            self.player.shoot_cooldown -= 1

        if self.player.invincible_timer > 0:
            self.player.invincible_timer -= 1
            self.player.is_hit = True
        else:
            self.player.is_hit = False

        if self.laser_cooldown > 0:
            self.laser_cooldown -= 1
        if self.echo_cooldown > 0:
            self.echo_cooldown -= 1
        if self.player_slow_timer > 0:
            self.player_slow_timer -= 1
        else:
            self.player_slow_factor = 1.0

    def _update_stars(self) -> None:
        drift_x = self._drift_x_bias(1.15)
        for star in self.stars:
            star[0] += drift_x * (0.55 + star[2] * 0.18)
            star[1] += star[2]
            if star[0] < 0:
                star[0] += self.WIDTH
            elif star[0] >= self.WIDTH:
                star[0] -= self.WIDTH
            if star[1] >= self.HEIGHT:
                star[0] = pyxel.rndi(0, self.WIDTH - 1)
                star[1] = -1
                star[2] = pyxel.rndi(1, 3)
                star[3] = self._random_star_color()

    def _update_background_fireworks(self) -> None:
        if not self.SHOW_BACKGROUND_FIREWORKS:
            self.fireworks.clear()
            return

        self.firework_spawn_timer -= 1
        if self.firework_spawn_timer <= 0 and len(self.fireworks) < self.max_fireworks:
            launch_x = pyxel.rndi(48, self.WIDTH - 48)
            launch_y = pyxel.rndi(self.HEIGHT // 2, self.HEIGHT - 110)
            self.fireworks.append(BackgroundFirework(launch_x, launch_y))
            self.firework_spawn_timer = random.randrange(65, 130)

        for firework in self.fireworks:
            firework.update()

        self.fireworks = [fw for fw in self.fireworks if not fw.is_dead()]

    def _update_player_input(self) -> None:
        left_bound = -self.PLAYER_EDGE_OVERHANG_X
        right_bound = self.WIDTH + self.PLAYER_EDGE_OVERHANG_X
        top_bound = self.PLAYER_MIN_Y
        bottom_bound = self.PLAYER_MAX_Y
        move_factor = self.player_slow_factor if self.player_slow_timer > 0 else 1.0
        speed_bonus = self._player_move_bonus()
        speed_x = max(1.0, (self.player.speed_x + speed_bonus) * move_factor)
        speed_y = max(1.0, (self.player.speed_y + speed_bonus) * move_factor)

        if pyxel.btn(pyxel.KEY_LEFT):
            self.player.x -= speed_x
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.player.x += speed_x
        if pyxel.btn(pyxel.KEY_UP):
            self.player.y -= speed_y
        if pyxel.btn(pyxel.KEY_DOWN):
            self.player.y += speed_y

        if self.touch_drag_active:
            drag_factor = 0.16 + 0.36 * move_factor
            self.player.x += (float(pyxel.mouse_x) - self.player.x) * drag_factor
            self.player.y += (float(pyxel.mouse_y) - self.player.y) * drag_factor

        self.player.x = min(max(self.player.x, left_bound), right_bound)
        self.player.y = min(max(self.player.y, top_bound), bottom_bound)

    def _update_shooting(self) -> None:
        wants_fire = pyxel.btn(pyxel.KEY_RETURN) or self._is_shoot_enabled()

        if wants_fire and self.player.shoot_cooldown <= 0:
            self._fire_current_shot()
            self.player.shoot_cooldown = self._current_shot_cooldown_frames()

    def _update_special_input(self) -> None:
        if pyxel.btnp(pyxel.KEY_X):
            self._try_activate_homing_laser()
        if pyxel.btnp(pyxel.KEY_C):
            self._try_activate_bomb()

        self._update_mobile_action_buttons()

    def _try_activate_bomb(self) -> None:
        if self.bomb_stock <= 0:
            return
        if len(self.bombs) >= self.bomb_active_limit:
            return

        bomb_scale = self._bomb_power_scale()
        launch_x = self.player.x
        launch_y = self.player.y - self.PLAYER_HALF_H - 8
        target_y = max(self.PLAYER_MIN_Y + 48, self.player.y - 190)

        self._spawn_bomb_launch_flash(launch_x, launch_y, scale=1.0)

        self.bombs.append(
            BombField(
                x=launch_x,
                y=launch_y,
                vx=0.0,
                vy=-7.2,
                target_y=target_y,
                phase="launch",
                life=100,
                max_life=100,
                radius=self.BOMB_BASE_RADIUS * bomb_scale,
                expansion=self.BOMB_EXPANSION_RADIUS * bomb_scale,
                rotation=0.0,
                rotation_speed=0.07,
                damage_interval=4,
                damage_timer=0,
                power_level=self.bomb_power_level,
            )
        )
        self.audio.play_se("bomb_fire")
        self.bomb_stock -= 1

    def _try_activate_homing_laser(self) -> None:
        if self.laser_cooldown > 0:
            return
        bit_shot_count = sum(1 for level in self.player_bit_levels if level > 0)
        if len(self.homing_lasers) + self.laser_shot_count + bit_shot_count > self.laser_active_limit:
            return

        laser_speed = 9.3
        laser_y = float(self.player.y - self.PLAYER_HALF_H - 10)
        count = max(self.LASER_SHOT_COUNT_MIN, min(self.LASER_SHOT_COUNT_MAX, self.laser_shot_count))
        if count == 1:
            offsets = [(0.0, 0.0)]
            speed_bonuses = [0.0]
        elif count == 2:
            offsets = [(-12.0, -45.0), (12.0, 45.0)]
            speed_bonuses = [1.0, 2.0]
        else:
            offsets = [(-14.0, -55.0), (0.0, 0.0), (14.0, 55.0)]
            speed_bonuses = [2.0, 3.0, 5.0]

        if len(speed_bonuses) > 1:
            speed_bonuses = random.sample(speed_bonuses, len(speed_bonuses))

        for (xoff, angle_from_up_deg), speed_bonus in zip(offsets, speed_bonuses):
            laser_x = float(self.player.x + xoff)
            shot_speed = laser_speed + speed_bonus
            shot_angle = (-math.pi / 2.0) + math.radians(angle_from_up_deg)
            self.homing_lasers.append(
                HomingLaser(
                    x=laser_x,
                    y=laser_y,
                    vx=math.cos(shot_angle) * shot_speed,
                    vy=math.sin(shot_angle) * shot_speed,
                    speed=shot_speed,
                    turn_rate=0.052,
                    life=180,
                    max_life=180,
                    radius=7,
                    band_width=5,
                    damage=2,
                    trail=[(laser_x, laser_y)],
                )
            )

        if self._player_bits_active():
            bit_states = self._player_bit_states()
            for side_idx, (bit_x, bit_y, bit_variant, bit_level) in enumerate(bit_states):
                side_sign = -1.0 if side_idx == 0 else 1.0
                origin_x = float(bit_x + side_sign * self.PLAYER_BIT_LASER_SIDE_OFFSET_X)
                origin_y = float(bit_y - 3.0)
                shot_speed = laser_speed + 0.8 + side_idx * 0.4
                shot_angle = 0.0 if side_sign > 0 else math.pi
                self.homing_lasers.append(
                    HomingLaser(
                        x=origin_x,
                        y=origin_y,
                        vx=math.cos(shot_angle) * shot_speed,
                        vy=math.sin(shot_angle) * shot_speed,
                        speed=shot_speed + bit_level * 0.25,
                        turn_rate=0.052,
                        life=168,
                        max_life=168,
                        radius=5,
                        band_width=bit_level,
                        damage=bit_level,
                        trail=[(origin_x, origin_y)],
                        steer_delay=self.PLAYER_BIT_LASER_STEER_DELAY,
                    )
                )
        self.audio.play_se("laser_fire")
        self.laser_cooldown = self.laser_cooldown_frames

    def _create_enemy(self, spawn_x: float, enemy_type: str) -> Enemy:
        return create_enemy(
            spawn_x=spawn_x,
            enemy_type=enemy_type,
            enemy_half_h=float(self.ENEMY_HALF_H),
            enemy_half_w=float(self.ENEMY_HALF_W),
            loop_depth=self.boss_spawn_count,
        )

    def _update_spawning(self) -> None:
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            drift_spawn = self._drift_x_bias(self.DRIFT_SPAWN_X_SHIFT)
            spawn_x = float(pyxel.rndi(self.SIDE_MARGIN, self.WIDTH - self.SIDE_MARGIN)) - drift_spawn
            spawn_x = min(max(spawn_x, self.SIDE_MARGIN), self.WIDTH - self.SIDE_MARGIN)
            enemy_type = pick_enemy_type(self.score, self.boss_spawn_count)
            self.enemies.append(self._create_enemy(spawn_x, enemy_type))
            self.spawn_timer = int(60 * self._current_spawn_interval_sec())

    def _update_enemies(self) -> None:
        update_enemies(
            enemies=self.enemies,
            frame_count=self.frame_count,
            side_margin=self.SIDE_MARGIN,
            width=self.WIDTH,
            enemy_half_w=float(self.ENEMY_HALF_W),
            player_x=float(self.player.x),
            player_y=float(self.player.y),
            enemy_bullet_max_count=self.ENEMY_BULLET_MAX_COUNT,
            current_enemy_bullet_count=len(self.enemy_bullets),
            append_enemy_bullet=self._append_enemy_bullet,
            drift_x_bias=self._drift_x_bias(0.36),
        )

    def _update_bullets(self) -> None:
        next_bullets: list[Bullet] = []
        for bullet in self.bullets:
            if not bullet.active:
                continue
            if bullet.hit_cooldowns:
                bullet.hit_cooldowns = {
                    target_id: timer - 1
                    for target_id, timer in bullet.hit_cooldowns.items()
                    if timer > 1
                }
            bullet.age += 1
            bullet.x += bullet.vx
            bullet.y -= bullet.vy
            if bullet.style.startswith("beam_arc"):
                bullet.vx *= 0.996
            if bullet.radius_growth > 0.0:
                bullet.radius += bullet.radius_growth
                if bullet.max_radius > 0.0:
                    bullet.radius = min(bullet.radius, bullet.max_radius)
            if bullet.style.startswith("beam_arc"):
                bullet.trail.append((bullet.x, bullet.y))
                trail_limit = 10 if bullet.style == "beam_arc" else 13
                if len(bullet.trail) > trail_limit:
                    bullet.trail = bullet.trail[-trail_limit:]
            if bullet.age >= bullet.max_life:
                bullet.active = False
                continue
            offscreen_margin = 96 if bullet.style.startswith("beam_arc") else 16
            if bullet.y < -offscreen_margin or bullet.x < -offscreen_margin or bullet.x > self.WIDTH + offscreen_margin:
                bullet.active = False
                continue
            next_bullets.append(bullet)
        self.bullets = next_bullets

    def _update_enemy_bullets(self) -> None:
        next_enemy_bullets: list[EnemyBullet] = []
        for bullet in self.enemy_bullets:
            if not bullet.active:
                continue

            bullet.x += bullet.vx
            bullet.y += bullet.vy
            bullet.age += 1

            if bullet.age >= bullet.max_life:
                bullet.active = False
                continue
            if not self._is_enemy_bullet_in_bounds(bullet):
                bullet.active = False
                continue

            next_enemy_bullets.append(bullet)

        self.enemy_bullets = next_enemy_bullets
        self._trim_enemy_bullets_to_cap()

    def _bomb_current_radius(self, bomb: BombField) -> float:
        if bomb.phase != "burst":
            return 0.0
        progress = 1.0 - (bomb.life / bomb.max_life)
        eased = 1.0 - ((1.0 - progress) ** 3)
        return bomb.radius + bomb.expansion * eased

    def _update_bombs(self) -> None:
        for bomb in self.bombs:
            if not bomb.active:
                continue

            if bomb.phase == "launch":
                bomb.x += bomb.vx
                bomb.y += bomb.vy
                bomb.rotation += bomb.rotation_speed * 0.35

                if bomb.y <= bomb.target_y:
                    bomb.y = bomb.target_y
                    bomb.phase = "burst"
                    bomb.damage_timer = 0
                    bomb.rotation = 0.0
                    self.audio.play_se("bomb_burst")
                    self.spawn_bomb_visual(bomb.x, bomb.y, self._bomb_power_scale(bomb.power_level))

                continue

            if bomb.life <= 0:
                bomb.active = False
                continue

            progress = 1.0 - (bomb.life / bomb.max_life)
            current_radius = self._bomb_current_radius(bomb)

            bomb.rotation += bomb.rotation_speed

            if bomb.damage_timer <= 0:
                bomb.damage_timer = bomb.damage_interval
            else:
                bomb.damage_timer -= 1

            bomb.life -= 1
            if bomb.life <= 0:
                bomb.active = False

        self.bombs = [bomb for bomb in self.bombs if bomb.active]

    def _wrap_angle(self, angle: float) -> float:
        while angle > math.pi:
            angle -= math.tau
        while angle < -math.pi:
            angle += math.tau
        return angle

    def _clamp_laser_angle(self, angle: float) -> float:
        min_angle = -5 * math.pi / 6
        max_angle = -math.pi / 6
        return min(max(angle, min_angle), max_angle)

    def _rotate_homing_velocity_quaternion(
        self,
        vx: float,
        vy: float,
        desired_angle: float,
        turn_rate: float,
        speed: float,
    ) -> tuple[float, float]:
        current_angle = math.atan2(vy, vx)
        diff = self._wrap_angle(desired_angle - current_angle)
        if abs(diff) <= turn_rate * 1.15:
            snapped_angle = self._clamp_laser_angle(desired_angle)
            return math.cos(snapped_angle) * speed, math.sin(snapped_angle) * speed
        step = max(-turn_rate, min(turn_rate, diff))
        rotation = quaternion_from_axis_angle((0.0, 0.0, 1.0), step)
        rotated_x, rotated_y, _ = rotate_vector_by_quaternion((vx, vy, 0.0), rotation)

        rotated_angle = self._clamp_laser_angle(math.atan2(rotated_y, rotated_x))
        return math.cos(rotated_angle) * speed, math.sin(rotated_angle) * speed

    def _find_enemy_by_id(self, enemy_id: int | None) -> Enemy | None:
        if enemy_id is None:
            return None
        for enemy in self.enemies:
            if id(enemy) == enemy_id:
                return enemy
        return None

    def _find_enemy_bullet_by_id(self, bullet_id: int | None) -> EnemyBullet | None:
        if bullet_id is None:
            return None
        for bullet in self.enemy_bullets:
            if id(bullet) == bullet_id:
                return bullet
        return None

    def _is_homing_target_in_front(self, laser: HomingLaser, target_x: float, target_y: float) -> bool:
        _ = target_x
        # Treat "front" as screen-up for this vertical shooter, not the laser's current heading.
        return target_y < laser.y - 2.0

    def _find_homing_target(self, laser: HomingLaser) -> Enemy | Boss | EnemyBullet | None:
        if laser.target_id is not None and laser.reacquire_timer > 0:
            if self._is_boss_active() and id(self.boss) == laser.target_id:
                return self.boss

            existing = self._find_enemy_by_id(laser.target_id)
            if (
                existing is not None
                and existing.y <= laser.y + 24
                and self._is_homing_target_in_front(laser, existing.x, existing.y)
            ):
                return existing

            existing_bullet = self._find_enemy_bullet_by_id(laser.target_id)
            if (
                existing_bullet is not None
                and existing_bullet.y <= laser.y + 28
                and self._is_homing_target_in_front(laser, existing_bullet.x, existing_bullet.y)
            ):
                return existing_bullet

        best_target: Enemy | Boss | EnemyBullet | None = None
        best_score = float("inf")

        if self._is_boss_active():
            boss = self.boss
            if (
                boss is not None
                and boss.y <= laser.y + 36
                and self._is_homing_target_in_front(laser, boss.x, boss.y)
            ):
                dx = boss.x - laser.x
                dy = boss.y - laser.y
                dist2 = dx * dx + dy * dy
                best_score = dist2
                best_target = boss

        for enemy in self.enemies:
            if enemy.y > laser.y + 24:
                continue
            if not self._is_homing_target_in_front(laser, enemy.x, enemy.y):
                continue
            dx = enemy.x - laser.x
            dy = enemy.y - laser.y
            dist2 = dx * dx + dy * dy
            if dist2 < best_score:
                best_score = dist2
                best_target = enemy

        for bullet in self.enemy_bullets:
            if bullet.y > laser.y + 28:
                continue
            if not self._is_homing_target_in_front(laser, bullet.x, bullet.y):
                continue
            dx = bullet.x - laser.x
            dy = bullet.y - laser.y
            dist2 = dx * dx + dy * dy
            if dist2 < best_score:
                best_score = dist2
                best_target = bullet

        if best_target is not None:
            laser.target_id = id(best_target)
            laser.reacquire_timer = 18

        return best_target

    def _find_homing_redirect_point(self, laser: HomingLaser) -> tuple[float, float] | None:
        best_score = float("inf")
        best_point: tuple[float, float] | None = None

        target = self._find_homing_target(laser)
        if target is not None:
            dx = target.x - laser.x
            dy = target.y - laser.y
            best_score = dx * dx + dy * dy
            best_point = (target.x, target.y)

        for bullet in self.enemy_bullets:
            if bullet.y > laser.y + 28:
                continue
            if not self._is_homing_target_in_front(laser, bullet.x, bullet.y):
                continue
            dx = bullet.x - laser.x
            dy = bullet.y - laser.y
            dist2 = dx * dx + dy * dy
            if dist2 < best_score:
                best_score = dist2
                best_point = (bullet.x, bullet.y)

        return best_point

    def _force_homing_laser_redirect(self, laser: HomingLaser) -> None:
        laser.target_id = None
        laser.reacquire_timer = 0
        redirect_point = self._find_homing_redirect_point(laser)
        if redirect_point is None:
            return
        target_x, target_y = redirect_point
        desired_angle = self._clamp_laser_angle(math.atan2(target_y - laser.y, target_x - laser.x))
        laser.vx = math.cos(desired_angle) * laser.speed
        laser.vy = math.sin(desired_angle) * laser.speed

    def _update_homing_lasers(self) -> None:
        margin = 24

        for laser in self.homing_lasers:
            if not laser.active:
                continue

            expired_keys = [key for key, value in laser.hit_cooldowns.items() if value <= 1]
            for key in expired_keys:
                del laser.hit_cooldowns[key]
            for key in list(laser.hit_cooldowns.keys()):
                laser.hit_cooldowns[key] -= 1

            if laser.reacquire_timer > 0:
                laser.reacquire_timer -= 1

            if laser.steer_delay > 0:
                laser.steer_delay -= 1
            else:
                target = self._find_homing_target(laser)
                if target is not None:
                    dx = target.x - laser.x
                    dy = target.y - laser.y
                    desired_angle = math.atan2(dy, dx)
                    desired_angle = self._clamp_laser_angle(desired_angle)
                    laser.vx, laser.vy = self._rotate_homing_velocity_quaternion(
                        laser.vx,
                        laser.vy,
                        desired_angle,
                        laser.turn_rate,
                        laser.speed,
                    )
                else:
                    current_angle = self._clamp_laser_angle(math.atan2(laser.vy, laser.vx))
                    laser.vx = math.cos(current_angle) * laser.speed
                    laser.vy = math.sin(current_angle) * laser.speed

            laser.x += laser.vx
            laser.y += laser.vy
            laser.trail.append((laser.x, laser.y))
            if len(laser.trail) > 28:
                laser.trail = laser.trail[-28:]

            laser.life -= 1
            if (
                laser.life <= 0
                or laser.x < -margin
                or laser.x > self.WIDTH + margin
                or laser.y < -margin
                or laser.y > self.HEIGHT + margin
            ):
                laser.active = False

        self.homing_lasers = [laser for laser in self.homing_lasers if laser.active]

    def _update_echo_shots(self) -> None:
        next_shots: list[EchoShot] = []
        for shot in self.echo_shots:
            if not shot.active:
                continue

            shot.x += shot.dx
            shot.y += shot.dy

            shot.lifetime -= 1
            if shot.lifetime <= 0:
                continue
            if (
                shot.x < self.SIDE_MARGIN - 12
                or shot.x > self.WIDTH - self.SIDE_MARGIN + 12
                or shot.y < self.PLAY_TOP - 12
                or shot.y > self.HEIGHT + 12
            ):
                continue
            next_shots.append(shot)

        self.echo_shots = next_shots

    def _remove_offscreen_bullets(self) -> None:
        self.bullets = [b for b in self.bullets if b.active]

    def _remove_offscreen_enemy_bullets(self) -> None:
        self.enemy_bullets = [
            b
            for b in self.enemy_bullets
            if b.active and b.age < b.max_life and self._is_enemy_bullet_in_bounds(b)
        ]
        self._trim_enemy_bullets_to_cap()

    def _remove_offscreen_enemies(self) -> None:
        self.enemies = [
            e for e in self.enemies
            if (
                e.y <= self.HEIGHT + (self.ENEMY_HALF_H * e.display_scale)
                and (e.state != "retreating" or e.y >= self.PLAY_TOP - 40)
                and e.x >= -40
                and e.x <= self.WIDTH + 40
                and e.active
            )
        ]

    def _echo_segment(self, shot: EchoShot) -> tuple[float, float, float, float]:
        length = math.hypot(shot.dx, shot.dy)
        if length <= 0.001:
            return shot.x, shot.y, shot.x, shot.y - shot.length
        ux = shot.dx / length
        uy = shot.dy / length
        return (
            shot.x,
            shot.y,
            shot.x - ux * shot.length,
            shot.y - uy * shot.length,
        )

    def _circles_overlap(self, x1: float, y1: float, r1: float, x2: float, y2: float, r2: float) -> bool:
        dx = x1 - x2
        dy = y1 - y2
        limit = r1 + r2
        return dx * dx + dy * dy <= limit * limit

    def _laser_hits_enemy_bullet(self, laser: HomingLaser, bullet: EnemyBullet) -> bool:
        if len(laser.trail) < 2:
            return False

        hit_r = laser.band_width + bullet.radius
        limit_sq = hit_r * hit_r
        trail = laser.trail[-8:]

        for idx in range(1, len(trail)):
            x0, y0 = trail[idx - 1]
            x1, y1 = trail[idx]
            if self._point_segment_distance_sq(bullet.x, bullet.y, x0, y0, x1, y1) <= limit_sq:
                return True
        return False

    def _cancel_enemy_bullets_by_circle(self, x: float, y: float, radius: float) -> int:
        removed = 0
        remaining: list[EnemyBullet] = []

        for enemy_bullet in self.enemy_bullets:
            if self._circles_overlap(x, y, radius, enemy_bullet.x, enemy_bullet.y, enemy_bullet.radius):
                self._maybe_spawn_heal_item(enemy_bullet.x, enemy_bullet.y)
                self._spawn_bullet_cancel_sprite(
                    enemy_bullet.x,
                    enemy_bullet.y,
                    scale=max(0.85, enemy_bullet.display_scale * 1.05),
                )
                removed += 1
                continue
            remaining.append(enemy_bullet)

        if removed > 0:
            self.enemy_bullets = remaining
        return removed

    def _play_boss_cancel_chain_se(self, canceled_count: int) -> None:
        if not self._is_boss_active() or canceled_count <= 0:
            return
        if self.boss_cancel_chain_timer > 0:
            self.boss_cancel_chain_step = (self.boss_cancel_chain_step + 1) % 3
        else:
            self.boss_cancel_chain_step = 0
        self.boss_cancel_chain_timer = 8
        se_name = (
            "boss_cancel_1",
            "boss_cancel_2",
            "boss_cancel_3",
        )[self.boss_cancel_chain_step]
        self.audio.play_se(se_name)

    def _play_boss_cancel_chain_se_for_laser(self, laser: HomingLaser, canceled_count: int) -> None:
        if not self._is_boss_active() or canceled_count <= 0:
            return
        if laser.cancel_chain_timer > 0:
            laser.cancel_chain_step = (laser.cancel_chain_step + 1) % 3
        else:
            laser.cancel_chain_step = 0
        laser.cancel_chain_timer = 8
        se_name = (
            "boss_cancel_1",
            "boss_cancel_2",
            "boss_cancel_3",
        )[laser.cancel_chain_step]
        self.audio.play_se(se_name)

    def _cancel_radius_for_bullet(self, bullet: Bullet) -> float:
        radius = bullet.radius
        if bullet.style == "beam_arc":
            return radius + 2.0
        if bullet.style == "beam_arc_power":
            return radius + 3.0
        return radius

    def _handle_projectile_cancellations(self) -> None:
        cancel_events = 0
        for bullet in self.bullets[:]:
            if bullet.ignores_cancel:
                continue
            removed = self._cancel_enemy_bullets_by_circle(
                bullet.x,
                bullet.y,
                self._cancel_radius_for_bullet(bullet),
            )
            if removed <= 0:
                continue
            cancel_events += removed
            if bullet.piercing and bullet.style.startswith("beam_arc"):
                continue
            if bullet in self.bullets:
                self.bullets.remove(bullet)

        for bomb in self.bombs:
            cancel_r = 8.0 if bomb.phase == "launch" else self._bomb_current_radius(bomb) * 0.92
            if cancel_r <= 0:
                continue
            cancel_events += self._cancel_enemy_bullets_by_circle(bomb.x, bomb.y, cancel_r)

        laser_cancel_events = 0
        for laser in self.homing_lasers:
            laser_canceled = 0
            for enemy_bullet in self.enemy_bullets[:]:
                if self._laser_hits_enemy_bullet(laser, enemy_bullet):
                    self._maybe_spawn_heal_item(enemy_bullet.x, enemy_bullet.y)
                    self._spawn_bullet_cancel_sprite(
                        enemy_bullet.x,
                        enemy_bullet.y,
                        scale=max(0.9, enemy_bullet.display_scale * 1.1),
                    )
                    if enemy_bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(enemy_bullet)
                    laser_canceled += 1
                    self._force_homing_laser_redirect(laser)
                    break
            if laser_canceled > 0:
                laser_cancel_events += laser_canceled
                self._play_boss_cancel_chain_se_for_laser(laser, laser_canceled)
            elif laser.cancel_chain_timer > 0:
                laser.cancel_chain_timer -= 1
                if laser.cancel_chain_timer <= 0:
                    laser.cancel_chain_step = 0

        cancel_events += self._handle_echo_enemy_bullet_cancellations()
        if cancel_events > 0:
            self._play_boss_cancel_chain_se(cancel_events)
        elif self.boss_cancel_chain_timer > 0:
            self.boss_cancel_chain_timer -= 1
            if self.boss_cancel_chain_timer <= 0:
                self.boss_cancel_chain_step = 0

    def _handle_bullet_weapon_item_collisions(self) -> None:
        if len(self.unlocked_weapon_families) <= 1:
            return

        for bullet in self.bullets[:]:
            for item in self.weapon_items:
                if not item.active:
                    continue
                if item.switch_lock_timer > 0:
                    continue
                if bullet.piercing and id(item) in bullet.hit_cooldowns:
                    continue
                if not self._circles_overlap(
                    bullet.x,
                    bullet.y,
                    bullet.radius,
                    item.x,
                    item.y,
                    item.radius,
                ):
                    continue

                item.family = self._next_unlocked_weapon_family(item.family)
                item.bob_phase += math.pi / 2
                item.vx += bullet.vx * 0.55
                item.vy = max(-1.2, item.vy - 0.28)
                item.switch_lock_timer = self.WEAPON_ITEM_SWITCH_LOCK_FRAMES
                if bullet.piercing:
                    bullet.hit_cooldowns[id(item)] = 8
                    break
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                break

    def _is_bullet_hitting_enemy(self, bullet: Bullet, enemy: Enemy) -> bool:
        if bullet.style.startswith("beam_arc"):
            hit_r = max(1, int(round(bullet.radius)))
            for px, py in bullet.trail[-8:]:
                if self._point_hits_enemy(px, py, hit_r, enemy):
                    return True
            return self._point_hits_enemy(bullet.x, bullet.y, hit_r, enemy)
        hit_r = bullet.radius + 1
        return (
            bullet.x - hit_r < enemy.x + enemy.hit_half_w
            and bullet.x + hit_r > enemy.x - enemy.hit_half_w
            and bullet.y - hit_r < enemy.y + enemy.hit_half_h
            and bullet.y + hit_r > enemy.y - enemy.hit_half_h
        )

    def _is_bullet_hitting_boss(self, bullet: Bullet, boss: Boss) -> bool:
        if bullet.style.startswith("beam_arc"):
            hit_r = max(1, int(round(bullet.radius)))
            for px, py in bullet.trail[-10:]:
                if self._point_hits_boss(px, py, hit_r, boss):
                    return True
            return self._point_hits_boss(bullet.x, bullet.y, hit_r, boss)
        hit_r = bullet.radius + 1
        boss_cx, boss_cy = self._boss_hit_center(boss)
        hit_half_w = boss.hit_half_w + self.BOSS_HITBOX_EXTRA_W
        return (
            bullet.x - hit_r < boss_cx + hit_half_w
            and bullet.x + hit_r > boss_cx - hit_half_w
            and bullet.y - hit_r < boss_cy + boss.hit_half_h
            and bullet.y + hit_r > boss_cy - boss.hit_half_h
        )

    def _point_hits_enemy(self, x: float, y: float, radius: int, enemy: Enemy) -> bool:
        if enemy.state == "retreating":
            return False
        if enemy.invincible_timer > 0:
            return False
        return (
            x - radius < enemy.x + enemy.hit_half_w
            and x + radius > enemy.x - enemy.hit_half_w
            and y - radius < enemy.y + enemy.hit_half_h
            and y + radius > enemy.y - enemy.hit_half_h
        )

    def _point_hits_boss(self, x: float, y: float, radius: int, boss: Boss) -> bool:
        boss_cx, boss_cy = self._boss_hit_center(boss)
        hit_half_w = boss.hit_half_w + self.BOSS_HITBOX_EXTRA_W
        return (
            x - radius < boss_cx + hit_half_w
            and x + radius > boss_cx - hit_half_w
            and y - radius < boss_cy + boss.hit_half_h
            and y + radius > boss_cy - boss.hit_half_h
        )

    def _boss_hit_center(self, boss: Boss) -> tuple[float, float]:
        return (
            boss.x + self.BOSS_HITBOX_CENTER_X_OFFSET,
            boss.y + self.BOSS_HITBOX_CENTER_Y_OFFSET,
        )

    def _is_laser_hitting_enemy(self, laser: HomingLaser, enemy: Enemy) -> bool:
        sampled_points = laser.trail[-10::2]
        return any(self._point_hits_enemy(px, py, laser.band_width, enemy) for px, py in sampled_points)

    def _is_laser_hitting_boss(self, laser: HomingLaser, boss: Boss) -> bool:
        sampled_points = laser.trail[-10::2]
        return any(self._point_hits_boss(px, py, laser.band_width, boss) for px, py in sampled_points)

    def _is_echo_hitting_enemy(self, shot: EchoShot, enemy: Enemy) -> bool:
        x0, y0, x1, y1 = self._echo_segment(shot)
        hit_r = 5.0 + self.buff_scale("wide") * 1.5
        center_dist_sq = self._point_segment_distance_sq(enemy.x, enemy.y, x0, y0, x1, y1)
        limit = max(enemy.hit_half_w, enemy.hit_half_h) + hit_r
        return center_dist_sq <= limit * limit

    def _is_echo_hitting_boss(self, shot: EchoShot, boss: Boss) -> bool:
        x0, y0, x1, y1 = self._echo_segment(shot)
        hit_r = 6.0 + self.buff_scale("wide") * 1.5
        boss_cx, boss_cy = self._boss_hit_center(boss)
        center_dist_sq = self._point_segment_distance_sq(boss_cx, boss_cy, x0, y0, x1, y1)
        limit = max(boss.hit_half_w + self.BOSS_HITBOX_EXTRA_W, boss.hit_half_h) + hit_r
        return center_dist_sq <= limit * limit

    def _handle_echo_enemy_bullet_cancellations(self) -> int:
        if not self.echo_shots or not self.enemy_bullets:
            return 0
        remaining: list[EnemyBullet] = []
        canceled_count = 0
        for enemy_bullet in self.enemy_bullets:
            canceled = False
            for shot in self.echo_shots:
                x0, y0, x1, y1 = self._echo_segment(shot)
                hit_r = enemy_bullet.radius + 4.5
                if self._point_segment_distance_sq(enemy_bullet.x, enemy_bullet.y, x0, y0, x1, y1) <= hit_r * hit_r:
                    self._maybe_spawn_heal_item(enemy_bullet.x, enemy_bullet.y)
                    self._spawn_bullet_cancel_sprite(
                        enemy_bullet.x,
                        enemy_bullet.y,
                        scale=max(0.9, enemy_bullet.display_scale * 1.08),
                    )
                    canceled = True
                    canceled_count += 1
                    break
            if not canceled:
                remaining.append(enemy_bullet)
        self.enemy_bullets = remaining
        return canceled_count

    def _is_enemy_hitting_player(self, enemy: Enemy) -> bool:
        return (
            self.player.x - self.PLAYER_HALF_W < enemy.x + enemy.hit_half_w
            and self.player.x + self.PLAYER_HALF_W > enemy.x - enemy.hit_half_w
            and self.player.y - self.PLAYER_HALF_H < enemy.y + enemy.hit_half_h
            and self.player.y + self.PLAYER_HALF_H > enemy.y - enemy.hit_half_h
        )

    def _is_boss_hitting_player(self, boss: Boss) -> bool:
        boss_cx, boss_cy = self._boss_hit_center(boss)
        hit_half_w = boss.hit_half_w + self.BOSS_HITBOX_EXTRA_W
        return (
            self.player.x - self.PLAYER_HALF_W < boss_cx + hit_half_w
            and self.player.x + self.PLAYER_HALF_W > boss_cx - hit_half_w
            and self.player.y - self.PLAYER_HALF_H < boss_cy + boss.hit_half_h
            and self.player.y + self.PLAYER_HALF_H > boss_cy - boss.hit_half_h
        )

    def _is_enemy_bullet_hitting_player(self, bullet: EnemyBullet) -> bool:
        return (
            bullet.x - bullet.radius < self.player.x + self.PLAYER_HALF_W
            and bullet.x + bullet.radius > self.player.x - self.PLAYER_HALF_W
            and bullet.y - bullet.radius < self.player.y + self.PLAYER_HALF_H
            and bullet.y + bullet.radius > self.player.y - self.PLAYER_HALF_H
        )

    def _enemy_destroy_sound_name(self, enemy_type: str) -> str:
        if enemy_type == "rare":
            return "enemy_destroy_rare"
        if enemy_type.endswith("_fish"):
            return "enemy_destroy_heavy"
        if enemy_type in {"basic", "zigzag", "sprint"}:
            return "enemy_destroy_light"
        if enemy_type in {"shooter", "aimer"}:
            return "enemy_destroy_sharp"
        if enemy_type in {"tank"}:
            return "enemy_destroy_heavy"
        if enemy_type in {"spreader"}:
            return "enemy_destroy_swirl"
        return "enemy_destroy"

    def _record_enemy_defeat(self, enemy: Enemy) -> None:
        self.enemy_kill_count += 1
        self.kill_counts_by_type[enemy.enemy_type] = self.kill_counts_by_type.get(enemy.enemy_type, 0) + 1

    def _spawn_split_sushi_from_source(self, enemy: Enemy) -> None:
        if not enemy.split_spawn_enemy_type:
            return

        spawn_count = random.randint(max(1, enemy.split_spawn_min), max(enemy.split_spawn_min, enemy.split_spawn_max))
        if spawn_count <= 0:
            return

        base_angle = random.uniform(-math.pi, math.pi)
        spread_angles = [
            base_angle + (math.tau / spawn_count) * idx
            for idx in range(spawn_count)
        ]

        for idx in range(spawn_count):
            split_enemy = self._create_enemy(enemy.x + (idx - (spawn_count - 1) / 2) * 10.0, enemy.split_spawn_enemy_type)
            angle = spread_angles[idx]
            speed = random.uniform(2.2, 3.4)
            split_enemy.display_scale *= 0.82
            split_enemy.hit_half_w *= 0.82
            split_enemy.hit_half_h *= 0.82
            split_enemy.x = enemy.x + math.cos(angle) * 9.0
            split_enemy.y = enemy.y + math.sin(angle) * 9.0
            split_enemy.vx = math.cos(angle) * speed
            split_enemy.vy = math.sin(angle) * speed
            split_enemy.shoot_cooldown = max(18, split_enemy.shoot_cooldown)
            split_enemy.invincible_timer = 18
            self.enemies.append(split_enemy)

    def _damage_enemy(
        self,
        enemy: Enemy,
        amount: int,
        source: str = "shot",
        hit_vx: float = 0.0,
        hit_vy: float = -1.0,
    ) -> None:
        if enemy.state == "retreating":
            return
        if enemy.invincible_timer > 0:
            return
        enemy.hp -= amount
        enemy.was_hit = True
        enemy.hit_flash_timer = max(enemy.hit_flash_timer, 4)

        if enemy.hp <= 0:
            self.score += enemy.score_value
            self.combat_progress_score += enemy.score_value
            self._record_enemy_defeat(enemy)
            self.audio.play_se(self._enemy_destroy_sound_name(enemy.enemy_type))
            self._spawn_enemy_burst(enemy.x, enemy.y, scale=self._enemy_burst_scale_from_enemy(enemy))
            self._maybe_spawn_wasabi_item(enemy.x, enemy.y, enemy)
            if enemy.enemy_category == "fish_source":
                self._spawn_split_sushi_from_source(enemy)
            elif enemy.enemy_type == "rare":
                self.add_orbit_sushi(enemy)
                self._show_notice(
                    label="RARE HIT",
                    title="BONUS TARGET",
                    description=f"SCORE +{enemy.score_value}",
                    accent=10,
                    kind="reward",
                )
                self.weapon_items.append(
                    WeaponItem(
                        x=enemy.x,
                        y=enemy.y,
                        vx=random.uniform(-0.18, 0.18),
                        vy=self.TEA_FALL_SPEED,
                        family=random.choice(self.unlocked_weapon_families),
                        bob_phase=random.uniform(0.0, math.tau),
                    )
                )
                self._maybe_spawn_bit_item(enemy.x, enemy.y)
            else:
                self.add_orbit_sushi(enemy)
                bonus_drop = self.HOMING_LASER_DROP_BONUS if source == "homing_laser" else 0.0
                self._maybe_spawn_weapon_item(enemy.x, enemy.y, extra_drop_rate=bonus_drop)
            if enemy in self.enemies:
                self.enemies.remove(enemy)
            return

        hit_len = math.hypot(hit_vx, hit_vy)
        if hit_len <= 0.001:
            kb_dx, kb_dy = 0.0, -1.0
        else:
            kb_dx, kb_dy = hit_vx / hit_len, hit_vy / hit_len
        knockback_power = 1.15
        if source == "bomb":
            knockback_power = 0.85
        elif source == "homing_laser":
            knockback_power = 1.3
        elif source == "laser":
            knockback_power = 1.2
        if enemy.enemy_category == "fish_source":
            knockback_power *= 0.82
        enemy.knockback_vx += kb_dx * knockback_power
        enemy.knockback_vy += kb_dy * knockback_power

        if source == "shot":
            self._spawn_hit_spark(enemy.x, enemy.y, scale=max(0.7, enemy.display_scale * 0.55))
        elif source == "laser":
            self._spawn_laser_impact(
                enemy.x, enemy.y, vx=hit_vx, vy=hit_vy,
                scale=max(0.8, enemy.display_scale * 0.60),
            )
        elif source == "body":
            self._spawn_hit_spark(enemy.x, enemy.y, scale=max(0.8, enemy.display_scale * 0.60))

    def _damage_boss(
        self,
        amount: int,
        source: str = "shot",
        hit_vx: float = 0.0,
        hit_vy: float = -1.0,
    ) -> None:
        if self.boss is None:
            return

        boss = self.boss

        if getattr(boss, "entry_invulnerable", False):
            return
        if getattr(boss, "shield_timer", 0) > 0:
            return

        actual_amount = amount
        if actual_amount > 0 and self.boss_damage_taken_multiplier < 1.0:
            actual_amount = max(1, int(actual_amount * self.boss_damage_taken_multiplier))

        if actual_amount > 0 and self.boss_damage_cooldown > 0 and source != "bomb":
            return

        if actual_amount > 0:
            self.audio.play_se("boss_hit")
            self._trigger_boss_hp_bar_hit_fx()
            if source != "bomb":
                self.boss_damage_cooldown = self.BOSS_DAMAGE_COOLDOWN_FRAMES

        boss.hp -= actual_amount
        boss.was_hit = True
        boss.hit_flash_timer = max(boss.hit_flash_timer, 4)

        if boss.hp <= 0:
            self._on_boss_defeated()
            return

        if source == "shot":
            self._spawn_hit_spark(boss.x, boss.y, scale=1.4)
        elif source == "laser":
            self._spawn_laser_impact(boss.x, boss.y, vx=hit_vx, vy=hit_vy, scale=1.5)
        elif source == "body":
            self._spawn_hit_spark(boss.x, boss.y, scale=1.5)

    def _handle_bullet_enemy_collisions(self) -> None:
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if not self._is_bullet_hitting_enemy(bullet, enemy):
                    continue
                if bullet.piercing and id(enemy) in bullet.hit_cooldowns:
                    continue
                self._damage_enemy(enemy, bullet.damage, source="shot")
                if bullet.piercing:
                    bullet.hit_cooldowns[id(enemy)] = 7
                    continue
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                break

    def _handle_bullet_boss_collisions(self) -> None:
        if self.boss is None:
            return

        for bullet in self.bullets[:]:
            if not self._is_bullet_hitting_boss(bullet, self.boss):
                continue
            if bullet.piercing and id(self.boss) in bullet.hit_cooldowns:
                continue
            self._damage_boss(bullet.damage, source="shot")
            if bullet.piercing:
                bullet.hit_cooldowns[id(self.boss)] = 5
                if self.boss is None:
                    break
                continue
            if bullet in self.bullets:
                self.bullets.remove(bullet)
            if self.boss is None:
                break

    def _handle_bomb_enemy_collisions(self) -> None:
        for bomb in self.bombs:
            if bomb.phase != "burst":
                continue
            if bomb.damage_timer != bomb.damage_interval:
                continue

            current_radius = self._bomb_current_radius(bomb)
            for enemy in self.enemies[:]:
                dx = enemy.x - bomb.x
                dy = enemy.y - bomb.y
                enemy_extent = max(enemy.hit_half_w, enemy.hit_half_h)
                limit = current_radius + enemy_extent
                if dx * dx + dy * dy <= limit * limit:
                    self._damage_enemy(enemy, 2, source="bomb")

    def _handle_bomb_boss_collisions(self) -> None:
        if self.boss is None:
            return

        for bomb in self.bombs:
            if bomb.phase != "burst":
                continue
            if bomb.damage_timer != bomb.damage_interval:
                continue

            current_radius = self._bomb_current_radius(bomb)
            boss_cx, boss_cy = self._boss_hit_center(self.boss)
            dx = boss_cx - bomb.x
            dy = boss_cy - bomb.y
            boss_extent = max(self.boss.hit_half_w + self.BOSS_HITBOX_EXTRA_W, self.boss.hit_half_h)
            limit = current_radius + boss_extent

            if dx * dx + dy * dy <= limit * limit:
                self._damage_boss(2, source="bomb")
                if self.boss is None:
                    break

    def _handle_homing_laser_enemy_collisions(self) -> None:
        for laser in self.homing_lasers:
            for enemy in self.enemies[:]:
                enemy_key = id(enemy)
                if laser.hit_cooldowns.get(enemy_key, 0) > 0:
                    continue
                if not self._is_laser_hitting_enemy(laser, enemy):
                    continue

                self._damage_enemy(enemy, laser.damage, source="homing_laser", hit_vx=laser.vx, hit_vy=laser.vy)
                laser.hit_cooldowns[enemy_key] = 8
                self._force_homing_laser_redirect(laser)
                break

    def _handle_homing_laser_boss_collisions(self) -> None:
        if self.boss is None:
            return

        boss_key = id(self.boss)
        for laser in self.homing_lasers:
            if laser.hit_cooldowns.get(boss_key, 0) > 0:
                continue
            if not self._is_laser_hitting_boss(laser, self.boss):
                continue

            self._damage_boss(laser.damage, source="laser", hit_vx=laser.vx, hit_vy=laser.vy)
            laser.hit_cooldowns[boss_key] = 8
            if self.boss is not None:
                self._force_homing_laser_redirect(laser)

            if self.boss is None:
                break

    def _handle_echo_enemy_collisions(self) -> None:
        for shot in self.echo_shots[:]:
            for enemy in self.enemies[:]:
                if not self._is_echo_hitting_enemy(shot, enemy):
                    continue
                hit_x = enemy.x
                hit_y = enemy.y
                self._damage_enemy(enemy, shot.damage, source="laser", hit_vx=shot.dx, hit_vy=shot.dy)
                self._spawn_echo_split(hit_x, hit_y, shot)
                shot.active = False
                break
        self.echo_shots = [shot for shot in self.echo_shots if shot.active]

    def _handle_echo_boss_collisions(self) -> None:
        if self.boss is None:
            return
        for shot in self.echo_shots[:]:
            if not self._is_echo_hitting_boss(shot, self.boss):
                continue
            hit_x = self.boss.x
            hit_y = self.boss.y
            self._damage_boss(shot.damage, source="laser", hit_vx=shot.dx, hit_vy=shot.dy)
            shot.active = False
            if self.boss is None:
                break
            self._spawn_echo_split(hit_x, hit_y, shot)
        self.echo_shots = [shot for shot in self.echo_shots if shot.active]

    def _apply_player_damage(self, damage: int, inflict_slow: bool = False) -> None:
        if self.player.invincible_timer > 0:
            return
        if self.consume_barrier_if_possible():
            return
        if self._fever_active() and self.boss_buff_state.fever_barrier_hits > 0:
            self.boss_buff_state.fever_barrier_hits -= 1
            self.player.invincible_timer = max(self.player.invincible_timer, 18)
            self._spawn_hit_spark(self.player.x, self.player.y - 2, scale=1.1)
            self.audio.play_se("weapon_level_up")
            return
        guard_ratio = self._guard_damage_ratio()
        if damage <= 1 and guard_ratio > 0.0 and random.random() < guard_ratio:
            reduced = 0
        else:
            reduced = max(1, int(math.ceil(damage * (1.0 - guard_ratio))))
        if reduced <= 0:
            self.player.invincible_timer = max(self.player.invincible_timer, 12)
            return
        self.player.hp -= reduced
        self.player.invincible_timer = self.PLAYER_INVINCIBLE_FRAMES
        self.player.is_hit = True
        self.audio.play_se("player_hit")
        if inflict_slow:
            self.player_slow_timer = max(self.player_slow_timer, self.KARAKUSA_SLOW_FRAMES)
            self.player_slow_factor = self.KARAKUSA_SLOW_FACTOR

    def _handle_player_enemy_collisions(self) -> None:
        for enemy in self.enemies[:]:
            if enemy.state == "retreating":
                continue
            if not self._is_enemy_hitting_player(enemy):
                continue
            self._apply_player_damage(1)
            self._spawn_enemy_burst(enemy.x, enemy.y, scale=self._enemy_burst_scale_from_enemy(enemy))
            if enemy in self.enemies:
                self.enemies.remove(enemy)
            break

    def _handle_player_boss_collisions(self) -> None:
        if self.boss is None:
            return
        if not self._is_boss_hitting_player(self.boss):
            return

        self._apply_player_damage(1)
        self._damage_boss(0, source="body")

    def _handle_player_enemy_bullet_collisions(self) -> None:
        for bullet in self.enemy_bullets[:]:
            if not self._is_enemy_bullet_hitting_player(bullet):
                continue
            self._apply_player_damage(bullet.damage, inflict_slow=bullet.slow_inflict)
            if bullet in self.enemy_bullets:
                self.enemy_bullets.remove(bullet)
            break

    def draw(self) -> None:
        pyxel.cls(self.play_bg_color)

        self._draw_background()
        self._draw_background_fireworks()
        self._draw_fever_side_decor()
        self._draw_frame()
        self._draw_boss_dash_telegraph()
        self._draw_boss_laser()
        self._draw_boss_special_beam()
        self._draw_bombs()
        self._draw_bomb_visuals()
        self._draw_enemies()
        self._draw_boss()
        self._draw_boss_defeat_sequence()
        self._draw_enemy_bullets()
        self._draw_weapon_items()
        self._draw_heal_items()
        self._draw_bit_items()
        self._draw_wasabi_items()
        self._draw_bullets()
        self._draw_echo_shots()
        self._draw_homing_lasers()
        self._draw_boss_hp_bar()
        self._draw_effects()
        self._draw_fever_arrival_waves(self.fever_arrival_effect)
        self._draw_player_orbit_layer()
        self._draw_sushi_settle_message()
        self._draw_fever_arrival_effect()
        self._draw_boss_pattern_label()
        self._draw_hud()
        self._draw_reward_notice()
        self._draw_mobile_controls()

        if self.boss_intro_timer > 0:
            self._draw_boss_warning()

        if self.phase == GamePhase.START:
            self._draw_start_screen()
        elif self.phase == GamePhase.REWARD_SELECT:
            self._draw_reward_select()
        elif self.phase == GamePhase.GAME_OVER:
            self._draw_game_over()
        elif self.phase == GamePhase.RESULT:
            self._draw_result_screen()

    def _draw_background(self) -> None:
        if self._boss_pattern_active():
            self._draw_boss_pattern_background()

        for x, y, _, color in self.stars:
            pyxel.pset(x, y, color)

        if self._boss_pattern_active():
            self._draw_boss_pattern_transition_overlay()

    def _draw_fever_side_decor(self) -> None:
        if not self._fever_active():
            return
        if self.fever_arrival_effect.active:
            return
        if self.phase != GamePhase.PLAYING:
            return
        if self.fever_decor_sheet_image is None or self.fever_decor_frame_w <= 0 or self.fever_decor_frame_h <= 0:
            return

        frame_idx = self.frame_count % self.FEVER_DECOR_LOOP_FRAMES
        cols = max(1, self.fever_decor_sheet_cols)
        cell_x = (frame_idx % cols) * self.fever_decor_frame_w
        cell_y = (frame_idx // cols) * self.fever_decor_frame_h
        side_w = self.FEVER_DECOR_SIDE_W
        visible_w = self.FEVER_DECOR_VISIBLE_W
        overflow_w = self.FEVER_DECOR_OVERFLOW_W
        draw_w = visible_w + overflow_w

        pyxel.blt(
            -overflow_w,
            self.PLAY_TOP,
            self.fever_decor_sheet_image,
            cell_x,
            cell_y,
            draw_w,
            self.fever_decor_frame_h,
            0,
        )
        pyxel.blt(
            self.WIDTH - visible_w,
            self.PLAY_TOP,
            self.fever_decor_sheet_image,
            cell_x + (side_w - draw_w),
            cell_y,
            draw_w,
            self.fever_decor_frame_h,
            0,
        )

    def _draw_boss_pattern_background(self) -> None:
        if self.boss_pattern_id is None:
            return

        data = self.BOSS_PATTERN_DATA[self.boss_pattern_id]
        top = self.PLAY_TOP
        area_h = self.HEIGHT - top
        pyxel.rect(0, top, self.WIDTH, area_h, data["bg"])
        self._draw_boss_pattern_tilemap(self.boss_pattern_id, top)

    def _draw_boss_pattern_tilemap(self, pattern_id: str, top: int) -> None:
        data = self.BOSS_PATTERN_DATA[pattern_id]
        tile_info = data.get("tile")
        tile_w = tile_info[3] if tile_info is not None else 32
        tile_h = tile_info[4] if tile_info is not None else 32
        for ty in range(top, self.HEIGHT, tile_h):
            for tx in range(0, self.WIDTH, tile_w):
                if tile_info is not None:
                    img, u, v, src_w, src_h = tile_info
                    pyxel.blt(tx, ty, img, u, v, src_w, src_h)
                elif pattern_id == "seigaiha":
                    self._draw_tile_seigaiha(tx, ty, data["bg"], data["line"], data["sub"])
                elif pattern_id == "karakusa":
                    self._draw_tile_karakusa(tx, ty, data["bg"], data["line"], data["sub"])
                elif pattern_id == "shippo":
                    self._draw_tile_shippo(tx, ty, data["bg"], data["line"], data["sub"])
                elif pattern_id == "asanoha":
                    self._draw_tile_asanoha(tx, ty, data["bg"], data["line"], data["sub"])
                elif pattern_id == "yagasuri":
                    self._draw_tile_yagasuri(tx, ty, data["bg"], data["line"], data["sub"])

    def _draw_tile_seigaiha(self, ox: int, oy: int, bg: int, line: int, sub: int) -> None:
        pyxel.rect(ox, oy, 32, 32, bg)
        for row_idx, cy in enumerate((oy + 8, oy + 16, oy + 24, oy + 32)):
            offset = 0 if row_idx % 2 == 0 else 16
            for cx in (ox - 16 + offset, ox + 16 + offset):
                pyxel.circb(cx, cy + 8, 14, line)
                pyxel.circb(cx, cy + 8, 10, line)
                pyxel.circb(cx, cy + 8, 6, sub)

    def _draw_spiral(self, cx: float, cy: float, radius: float, color: int, clockwise: bool = True) -> None:
        prev_x = cx
        prev_y = cy
        direction = -1.0 if clockwise else 1.0
        for step in range(1, 28):
            ratio = step / 27.0
            angle = ratio * math.tau * 1.85 * direction
            r = radius * (1.0 - ratio * 0.82)
            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r
            pyxel.line(int(prev_x), int(prev_y), int(px), int(py), color)
            prev_x = px
            prev_y = py

    def _draw_tile_karakusa(self, ox: int, oy: int, bg: int, line: int, sub: int) -> None:
        pyxel.rect(ox, oy, 32, 32, bg)
        pyxel.line(ox - 4, oy + 11, ox + 36, oy + 11, sub)
        pyxel.line(ox - 4, oy + 23, ox + 36, oy + 23, sub)
        self._draw_spiral(ox + 7, oy + 9, 8, line, clockwise=True)
        self._draw_spiral(ox + 24, oy + 8, 9, line, clockwise=False)
        self._draw_spiral(ox + 12, oy + 24, 9, line, clockwise=False)
        self._draw_spiral(ox + 29, oy + 23, 7, line, clockwise=True)
        pyxel.circb(ox + 18, oy + 15, 3, line)
        pyxel.circb(ox + 3, oy + 22, 2, line)

    def _draw_tile_shippo(self, ox: int, oy: int, bg: int, line: int, sub: int) -> None:
        pyxel.rect(ox, oy, 32, 32, bg)
        centers = (
            (ox, oy),
            (ox + 16, oy),
            (ox + 32, oy),
            (ox, oy + 16),
            (ox + 16, oy + 16),
            (ox + 32, oy + 16),
            (ox, oy + 32),
            (ox + 16, oy + 32),
            (ox + 32, oy + 32),
        )
        for idx, (cx, cy) in enumerate(centers):
            color = line if idx % 2 == 0 else sub
            pyxel.circb(cx, cy, 11, color)
            pyxel.circb(cx, cy, 10, color)

    def _draw_tile_asanoha(self, ox: int, oy: int, bg: int, line: int, sub: int) -> None:
        pyxel.rect(ox, oy, 32, 32, bg)
        for cx, cy in ((8, 8), (24, 8), (8, 24), (24, 24)):
            px = ox + cx
            py = oy + cy
            pyxel.line(px, py, px, py - 8, line)
            pyxel.line(px, py, px - 7, py - 4, line)
            pyxel.line(px, py, px + 7, py - 4, line)
            pyxel.line(px, py, px - 7, py + 4, sub)
            pyxel.line(px, py, px + 7, py + 4, sub)
            pyxel.line(px, py, px, py + 8, sub)
        pyxel.line(ox + 8, oy + 8, ox + 24, oy + 8, line)
        pyxel.line(ox + 8, oy + 24, ox + 24, oy + 24, sub)
        pyxel.line(ox + 8, oy + 8, ox + 8, oy + 24, line)
        pyxel.line(ox + 24, oy + 8, ox + 24, oy + 24, sub)

    def _draw_tile_yagasuri(self, ox: int, oy: int, bg: int, line: int, sub: int) -> None:
        pyxel.rect(ox, oy, 32, 32, bg)
        for col_x in (8, 24):
            px = ox + col_x
            for base_y in (-8, 8, 24):
                cy = oy + base_y
                pyxel.tri(px, cy, px - 6, cy + 8, px + 6, cy + 8, line)
                pyxel.rect(px - 3, cy + 8, 6, 8, line)
                pyxel.tri(px, cy + 24, px - 6, cy + 16, px + 6, cy + 16, line)
                pyxel.line(px - 6, cy + 8, px - 3, cy + 8, sub)
                pyxel.line(px + 3, cy + 8, px + 6, cy + 8, sub)

    def _draw_boss_pattern_transition_overlay(self) -> None:
        if self.boss_pattern_transition_timer <= 0 and self.boss_pattern_confetti_timer <= 0:
            return

        top = self.PLAY_TOP
        area_h = self.HEIGHT - top
        if self.boss_pattern_transition_timer > 0:
            ratio = self.boss_pattern_transition_timer / self.BOSS_PATTERN_INTRO_FRAMES
            reveal = 1.0 - ratio
            reveal = reveal * reveal * (3.0 - 2.0 * reveal)
            center = self.WIDTH // 2
            half_gap = int((self.WIDTH * 0.58) * reveal)
            left_cover = max(0, center - half_gap)
            right_start = min(self.WIDTH, center + half_gap)

            if left_cover > 0:
                pyxel.rect(0, top, left_cover, area_h, 0)
            if right_start < self.WIDTH:
                pyxel.rect(right_start, top, self.WIDTH - right_start, area_h, 0)

            edge_color = self.boss_pattern_accent if (self.frame_count // 3) % 2 == 0 else 7
            pyxel.line(left_cover, top, left_cover, self.HEIGHT - 1, edge_color)
            pyxel.line(right_start, top, right_start, self.HEIGHT - 1, edge_color)

        confetti_ratio = self.boss_pattern_confetti_timer / self.BOSS_PATTERN_CONFETTI_FRAMES if self.BOSS_PATTERN_CONFETTI_FRAMES > 0 else 0.0
        confetti_strength = min(1.0, confetti_ratio * 1.25)
        confetti_colors = (7, self.boss_pattern_accent, 10, 11, 14)
        confetti_count = 34
        fall_range = int(area_h * (1.10 - confetti_ratio * 0.18))

        for idx in range(confetti_count):
            phase = (self.frame_count * (2 + idx % 3)) + idx * 29
            base_x = phase % (self.WIDTH + 42)
            swing = math.sin((self.frame_count * 0.06) + idx * 1.37) * (7 + (idx % 5) * 2)
            cx = int(base_x - 21 + swing)
            cy = top + ((idx * 23 + self.frame_count * (3 + idx % 2)) % max(24, fall_range + 36)) - 24

            if cx < -10 or cx > self.WIDTH + 10 or cy < top + 2 or cy > self.HEIGHT - 8:
                continue

            color = confetti_colors[idx % len(confetti_colors)]
            edge = 7 if idx % 4 != 0 else 1
            large_piece = idx % 3 == 0
            if large_piece:
                width = 6 if idx % 2 == 0 else 5
                height = 4 if idx % 2 == 0 else 5
                pyxel.rect(cx - width // 2, cy - height // 2, width, height, color)
                pyxel.rectb(cx - width // 2, cy - height // 2, width, height, edge)
                pyxel.line(cx - width // 2 + 1, cy - height // 2 + 1, cx + width // 2 - 2, cy + height // 2 - 1, edge)
            elif idx % 3 == 1:
                pyxel.line(cx - 3, cy - 2, cx + 2, cy + 3, color)
                pyxel.line(cx - 2, cy - 2, cx + 3, cy + 3, edge)
                pyxel.line(cx - 1, cy - 3, cx + 1, cy - 1, color)
            else:
                pyxel.line(cx + 3, cy - 2, cx - 2, cy + 3, color)
                pyxel.line(cx + 2, cy - 2, cx - 3, cy + 3, edge)
                pyxel.line(cx + 1, cy - 3, cx - 1, cy - 1, color)

            if confetti_strength > 0.15 and idx % 5 == 0:
                pyxel.pset(cx + 2, cy + 2, edge)

    def _split_label_words_balanced(self, text: str) -> tuple[str, str]:
        words = text.split()
        if len(words) <= 1:
            return text, ""

        best_left = text
        best_right = ""
        best_gap = 9999

        for split_idx in range(1, len(words)):
            left = " ".join(words[:split_idx])
            right = " ".join(words[split_idx:])
            gap = abs(len(left) - len(right))
            if gap < best_gap:
                best_gap = gap
                best_left = left
                best_right = right

        return best_left, best_right

    def _draw_boss_pattern_label(self) -> None:
        if self.boss_pattern_label_timer <= 0 or self.boss_pattern_id is None:
            return

        timer_ratio = self.boss_pattern_label_timer / self.BOSS_PATTERN_LABEL_FRAMES
        visibility = min(1.0, (1.0 - timer_ratio) * 2.4, timer_ratio * 2.0)
        rise = int((1.0 - visibility) * 16)
        box_w = 286
        box_h = 62
        box_x = (self.WIDTH - box_w) // 2
        box_y = self.PLAY_TOP + 72 + rise
        accent = self.boss_pattern_accent
        pulse = 7 if (self.frame_count // 4) % 2 == 0 else accent

        pyxel.rect(box_x, box_y, box_w, box_h, 0)
        pyxel.rectb(box_x - 1, box_y - 1, box_w + 2, box_h + 2, accent)
        pyxel.rectb(box_x + 3, box_y + 3, box_w - 6, box_h - 6, 7)
        pyxel.rect(box_x + 8, box_y + 8, 54, box_h - 16, accent)
        pyxel.text(box_x + 20, box_y + 28, "BOSS", 1)

        name_x = box_x + 74
        buff_x = box_x + 80
        pattern_name_text = f"PATTERN: {self.boss_pattern_name}"
        draw_big_text(name_x, box_y + 12, pattern_name_text, 2, pulse, shadow_color=1)
        buff_line_1, buff_line_2 = self._split_label_words_balanced(self.boss_pattern_buff)
        draw_big_text(buff_x, box_y + 34, buff_line_1, 1, 7, shadow_color=1)
        if buff_line_2:
            draw_big_text(buff_x, box_y + 46, buff_line_2, 1, 7, shadow_color=1)

        marker_x = box_x + box_w - 28
        marker_y = box_y + box_h - 18
        pyxel.circb(marker_x, marker_y, 10, accent)
        pyxel.circb(marker_x, marker_y, 6, 7)
        pyxel.pset(marker_x, marker_y, 7)

    def _draw_background_fireworks(self) -> None:
        if not self.SHOW_BACKGROUND_FIREWORKS:
            return
        for firework in self.fireworks:
            firework.draw(self.frame_count)

    def _draw_frame(self) -> None:
        pyxel.rectb(0, 0, self.WIDTH, self.HEIGHT, self.frame_color)
        pyxel.line(0, self.HUD_H, self.WIDTH - 1, self.HUD_H, self.divider_color)

    def _draw_boss_dash_telegraph(self) -> None:
        if self.boss is None:
            return
        if getattr(self.boss, "dash_telegraph_timer", 0) <= 0:
            return

        bx = int(self.boss.x)
        by = int(self.boss.y)
        tx = int(getattr(self.boss, "dash_target_x", self.boss.x))
        ty = int(getattr(self.boss, "dash_target_y", self.boss.y))

        if (self.frame_count // 3) % 2 == 0:
            pyxel.line(bx, by, tx, ty, 8)
            pyxel.line(bx - 1, by, tx - 1, ty, 10)
            pyxel.line(bx + 1, by, tx + 1, ty, 10)
            pyxel.circb(tx, ty, 8, 7)
            pyxel.circb(tx, ty, 12, 8)

    def _draw_boss_laser(self) -> None:
        if self.boss is None:
            return

        telegraph = getattr(self.boss, "laser_telegraph_timer", 0)
        active = getattr(self.boss, "laser_active_timer", 0)
        if telegraph <= 0 and active <= 0:
            return
        if getattr(self.boss, "entry_invulnerable", False):
            return

        ox, oy = self._laser_origin(self.boss)
        dx, dy = self._laser_dir(self.boss)
        length = max(self.WIDTH, self.HEIGHT) * 1.7
        ex = ox + dx * length
        ey = oy + dy * length

        if telegraph > 0:
            if (self.frame_count // 3) % 2 == 0:
                pyxel.line(int(ox), int(oy), int(ex), int(ey), 8)
                pyxel.line(int(ox - 1), int(oy), int(ex - 1), int(ey), 14)
                pyxel.line(int(ox + 1), int(oy), int(ex + 1), int(ey), 14)
            return

        if active > 0:
            for offset, color in (
                (-4, 8),
                (-3, 10),
                (-2, 7),
                (-1, 7),
                (0, 15),
                (1, 7),
                (2, 7),
                (3, 10),
                (4, 8),
            ):
                perp_x = -dy * offset
                perp_y = dx * offset
                pyxel.line(
                    int(ox + perp_x),
                    int(oy + perp_y),
                    int(ex + perp_x),
                    int(ey + perp_y),
                    color,
                )

    def _draw_boss_special_beam(self) -> None:
        if self.boss is None:
            return

        telegraph = getattr(self.boss, "special_beam_telegraph_timer", 0)
        active = getattr(self.boss, "special_beam_active_timer", 0)
        if telegraph <= 0 and active <= 0:
            return
        if getattr(self.boss, "entry_invulnerable", False):
            return

        kind = getattr(self.boss, "special_beam_kind", "none")
        if kind == "saber_sweep":
            saber_state = self._boss_special_saber_state(self.boss)
            if saber_state is None:
                return
            cx, cy, current_angle = saber_state
            radius = 96.0
            arc_span = math.radians(34)
            if telegraph > 0:
                self._draw_arc_beam(cx, cy, radius, math.radians(30), math.radians(150), 8, 1)
                self._draw_arc_beam(cx, cy, radius, current_angle - arc_span, current_angle + arc_span, 14, 1)
                return

            self._draw_arc_beam(cx, cy, radius - 2.0, current_angle - arc_span, current_angle + arc_span, 8, 2)
            self._draw_arc_beam(cx, cy, radius, current_angle - arc_span, current_angle + arc_span, 15, 2)
            self._draw_arc_beam(cx, cy, radius + 2.0, current_angle - arc_span, current_angle + arc_span, 10, 2)
            return

        segments = self._boss_special_beam_segments(self.boss)
        if telegraph > 0:
            for x0, y0, x1, y1 in segments:
                pyxel.line(int(x0), int(y0), int(x1), int(y1), 8)
                pyxel.line(int(x0 - 1), int(y0), int(x1 - 1), int(y1), 14)
                pyxel.line(int(x0 + 1), int(y0), int(x1 + 1), int(y1), 14)
            return

        for x0, y0, x1, y1 in segments:
            for offset, color in (
                (-4, 8),
                (-3, 10),
                (-2, 7),
                (-1, 7),
                (0, 15),
                (1, 7),
                (2, 7),
                (3, 10),
                (4, 8),
            ):
                dx = x1 - x0
                dy = y1 - y0
                length = max(0.001, math.hypot(dx, dy))
                perp_x = -dy / length * offset
                perp_y = dx / length * offset
                pyxel.line(
                    int(x0 + perp_x),
                    int(y0 + perp_y),
                    int(x1 + perp_x),
                    int(y1 + perp_y),
                    color,
                )

    def _draw_arc_beam(
        self,
        cx: float,
        cy: float,
        radius: float,
        angle_start: float,
        angle_end: float,
        color: int,
        step_deg: int,
    ) -> None:
        if angle_end < angle_start:
            angle_start, angle_end = angle_end, angle_start
        prev_x = cx + math.cos(angle_start) * radius
        prev_y = cy + math.sin(angle_start) * radius
        for deg in range(int(math.degrees(angle_start)) + step_deg, int(math.degrees(angle_end)) + step_deg, step_deg):
            angle = min(angle_end, math.radians(deg))
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            pyxel.line(int(prev_x), int(prev_y), int(x), int(y), color)
            prev_x, prev_y = x, y

    def _draw_mobile_controls(self) -> None:
        if not self._mobile_controls_enabled():
            return
        if self.phase != GamePhase.PLAYING:
            return

        panel_fill = 1
        panel_border = 5
        if self._is_touch_in_mobile_control_area() and (self.frame_count // 3) % 2 == 0:
            panel_fill = 2
            panel_border = 7

        pyxel.rect(self.MOBILE_PANEL_X, self.MOBILE_PANEL_Y, self.MOBILE_PANEL_W, self.MOBILE_PANEL_H, panel_fill)
        pyxel.rectb(self.MOBILE_PANEL_X, self.MOBILE_PANEL_Y, self.MOBILE_PANEL_W, self.MOBILE_PANEL_H, panel_border)
        self._draw_mobile_laser_button()
        self._draw_mobile_bomb_button()

    def _mobile_laser_button_rect(self) -> tuple[int, int, int, int]:
        return (
            self.MOBILE_PANEL_X + 6,
            self.MOBILE_PANEL_Y + 5,
            self.MOBILE_BUTTON_W,
            self.MOBILE_BUTTON_H,
        )

    def _mobile_bomb_button_rect(self) -> tuple[int, int, int, int]:
        return (
            self.MOBILE_PANEL_X + 6 + self.MOBILE_BUTTON_W + self.MOBILE_BUTTON_GAP,
            self.MOBILE_PANEL_Y + 5,
            self.MOBILE_BUTTON_W,
            self.MOBILE_BUTTON_H,
        )

    def _draw_mobile_rect_button(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        *,
        fill: int,
        border: int,
        title: str,
        pressed: bool,
        text: int,
    ) -> None:
        pyxel.rect(x, y, w, h, fill)
        pyxel.rectb(x, y, w, h, border)
        if pressed:
            pyxel.rectb(x - 1, y - 1, w + 2, h + 2, 7)
        title_w = big_text_width(title, 2)
        title_x = x + (w - title_w) // 2
        title_y = y + (h - 14) // 2
        draw_big_text(title_x, title_y, title, 2, 1 if pressed else text, shadow_color=1)

    def _draw_mobile_arc_outline(self, radius: float, angle_start: float, angle_end: float, color: int) -> None:
        prev_x, prev_y = self._mobile_arc_point(radius, angle_start)
        for angle in range(int(angle_start) + 2, int(angle_end) + 3, 2):
            x, y = self._mobile_arc_point(radius, min(angle, angle_end))
            pyxel.line(prev_x, prev_y, x, y, color)
            prev_x, prev_y = x, y

    def _draw_mobile_sector_fill(self, radius: float, angle_start: float, angle_end: float, color: int) -> None:
        prev_x, prev_y = self._mobile_arc_point(radius, angle_start)
        for angle in range(int(angle_start) + 2, int(angle_end) + 3, 2):
            x, y = self._mobile_arc_point(radius, min(angle, angle_end))
            pyxel.tri(
                self.MOBILE_CTRL_CX,
                self.MOBILE_CTRL_CY,
                prev_x,
                prev_y,
                x,
                y,
                color,
            )
            prev_x, prev_y = x, y

    def _draw_mobile_arc_button(
        self,
        *,
        angle_start: float,
        angle_end: float,
        fill: int,
        border: int,
        title: str,
        pressed: bool,
        text: int,
    ) -> None:
        inner = self.MOBILE_RING_INNER_RADIUS
        outer = self.MOBILE_RING_OUTER_RADIUS - 4

        self._draw_mobile_sector_fill(outer, angle_start, angle_end, fill)

        self._draw_mobile_arc_outline(inner, angle_start, angle_end, 1)
        self._draw_mobile_arc_outline(outer, angle_start, angle_end, border)

        sx0, sy0 = self._mobile_arc_point(inner, angle_start)
        sx1, sy1 = self._mobile_arc_point(outer, angle_start)
        ex0, ey0 = self._mobile_arc_point(inner, angle_end)
        ex1, ey1 = self._mobile_arc_point(outer, angle_end)
        pyxel.line(sx0, sy0, sx1, sy1, border)
        pyxel.line(ex0, ey0, ex1, ey1, border)

        if pressed:
            self._draw_mobile_arc_outline(outer + 2, angle_start, angle_end, 7)
            self._draw_mobile_arc_outline(inner + 2, angle_start, angle_end, 7)

        label_x, label_y = self._mobile_arc_midpoint(angle_start, angle_end, inner + (outer - inner) * 0.62)
        title_w = big_text_width(title, 2)
        title_x = label_x - title_w // 2
        draw_big_text(title_x, label_y - 10, title, 2, 1 if pressed else text, shadow_color=1)

    def _draw_mobile_laser_button(self) -> None:
        ready = self.laser_cooldown <= 0 and len(self.homing_lasers) + self.laser_shot_count <= self.laser_active_limit
        pressed = self._is_mobile_laser_pressed()
        x, y, w, h = self._mobile_laser_button_rect()

        if ready:
            fill = 12
            border = 7
            text = 7
        else:
            fill = 5
            border = 13
            text = 6

        if pressed and ready:
            fill = 7
            border = 12
            text = 1

        self._draw_mobile_rect_button(
            x,
            y,
            w,
            h,
            fill=fill,
            border=border,
            title="LASER",
            pressed=pressed,
            text=text,
        )

    def _draw_mobile_bomb_button(self) -> None:
        ready = self.bomb_stock > 0 and len(self.bombs) < self.bomb_active_limit
        pressed = self._is_mobile_bomb_pressed()
        x, y, w, h = self._mobile_bomb_button_rect()

        if ready:
            fill = 10
            border = 7
            text = 7
        else:
            fill = 2
            border = 5
            text = 6

        if pressed and ready:
            fill = 7
            border = 10
            text = 1

        self._draw_mobile_rect_button(
            x,
            y,
            w,
            h,
            fill=fill,
            border=border,
            title="BOMB",
            pressed=pressed,
            text=text,
        )

    def _draw_orbit_sushi(
        self,
        x: float,
        y: float,
        *,
        enemy_type: str,
        has_wasabi: bool,
        anim_offset: int,
        anim_dir: int,
        display_scale: float,
        sample_scale: float = 1.0,
        brightness_rank: int = 1,
        glow: bool = False,
        render_scale: float = 1.0,
    ) -> None:
        scale = min(1.125, max(0.82, 0.92 + (sample_scale - 0.9) * 0.40)) * render_scale

        if glow and (self.frame_count // 3) % 2 == 0:
            pyxel.circb(int(round(x)), int(round(y)), max(4, int(8 * scale)), 10)
        elif brightness_rank >= 2:
            pyxel.circb(int(round(x)), int(round(y)), max(3, int(7 * scale)), 7)
        elif brightness_rank <= 0:
            pyxel.circb(int(round(x)), int(round(y)), max(3, int(6 * scale)), 5)

        if has_wasabi:
            self._draw_wasabi_sprite(x, y, scale=scale)
        else:
            self._draw_orbit_enemy_sprite(
                x,
                y,
                enemy_type=enemy_type,
                anim_offset=anim_offset,
                anim_dir=anim_dir,
                scale=scale,
            )

    def _draw_settle_sparkle_layer(self, *, front: bool) -> None:
        effect = self.sushi_settle_effect
        if not effect.active or not effect.sushis:
            return
        if effect.phase >= self.SETTLE_PHASE_FINISH:
            return
        sheet = self.settle_sparkle_front_sheet_image if front else self.settle_sparkle_back_sheet_image
        if sheet is None:
            return
        elapsed = self._settle_total_elapsed_frames(effect)
        total_frames = (
            self.SETTLE_PREALIGN_FRAMES
            + self.SETTLE_ALIGN_FRAMES
            + self.SETTLE_GLOW_FRAMES
            + self.SETTLE_STOP_FRAMES
            + self.SETTLE_BOUNCE_FRAMES
            + self.SETTLE_SHAKE_FRAMES
            + self.SETTLE_EXPLODE_FRAMES
        )
        frame = min(max(0, elapsed), max(0, total_frames - 1))
        cell_x = (frame % self.settle_sparkle_sheet_cols) * self.settle_sparkle_frame_w
        cell_y = (frame // self.settle_sparkle_sheet_cols) * self.settle_sparkle_frame_h
        draw_x = int(round(effect.center_x - self.settle_sparkle_frame_w / 2))
        draw_y = int(round(effect.center_y - self.settle_sparkle_frame_h / 2))
        pyxel.blt(
            draw_x,
            draw_y,
            sheet,
            cell_x,
            cell_y,
            self.settle_sparkle_frame_w,
            self.settle_sparkle_frame_h,
            0,
        )

    def _collect_player_orbit_draw_items(self) -> list[DrawItem]:
        items: list[DrawItem] = []

        for sample, draw_x, draw_y, sparkle_idx in self._orbit_shell_sparkle_states():
            items.append(
                DrawItem(
                    layer_group=1,
                    depth=sample.depth,
                    kind="orbit_shell_sparkle",
                    x=draw_x,
                    y=draw_y,
                    payload=(sample, sparkle_idx),
                )
            )

        for entry, sample, draw_x, draw_y, _ring_kind in self._orbit_render_states(self.orbit_sushi_queue):
            items.append(
                DrawItem(
                    layer_group=1,
                    depth=sample.depth,
                    kind="orbit_sushi",
                    x=draw_x,
                    y=draw_y,
                    payload=(entry, sample),
                )
            )

        for bit_x, bit_y, bit_variant, _bit_level in self._player_bit_states():
            items.append(
                DrawItem(
                    layer_group=1,
                    depth=-0.02,
                    kind="player_bit",
                    x=bit_x,
                    y=bit_y,
                    payload=bit_variant,
                )
            )

        items.append(
            DrawItem(
                layer_group=1,
                depth=0.0,
                kind="player",
                x=self.player.x,
                y=self.player.y,
            )
        )

        if self.barrier_stock > 0 or (self._fever_active() and self.boss_buff_state.fever_barrier_hits > 0):
            items.append(
                DrawItem(
                    layer_group=1,
                    depth=0.05,
                    kind="barrier",
                    x=self.player.x,
                    y=self.player.y,
                )
            )

        effect = self.sushi_settle_effect
        if effect.active and effect.sushis:
            glow = effect.phase == self.SETTLE_PHASE_GLOW
            for sushi in effect.sushis:
                items.append(
                    DrawItem(
                        layer_group=1,
                        depth=0.18,
                        kind="settle_sushi",
                        x=sushi.current_x + sushi.offset_x,
                        y=sushi.current_y + sushi.offset_y,
                        payload=(sushi, glow),
                    )
                )

        items.sort(key=lambda item: (item.layer_group, item.depth))
        return items

    def _draw_player_orbit_layer(self) -> None:
        self._draw_settle_sparkle_layer(front=False)
        fever_orbit_shell = self._fever_active()
        for item in self._collect_player_orbit_draw_items():
            if item.kind == "orbit_shell_sparkle":
                if not fever_orbit_shell:
                    continue
                sample, sparkle_idx = item.payload
                self._draw_orbit_shell_sparkle(
                    item.x,
                    item.y,
                    brightness_rank=sample.brightness_rank,
                    sparkle_idx=sparkle_idx,
                )
            elif item.kind == "orbit_sushi":
                entry, sample = item.payload
                self._draw_orbit_sushi(
                    item.x,
                    item.y,
                    enemy_type=entry.enemy_type,
                    has_wasabi=entry.has_wasabi,
                    anim_offset=entry.anim_offset,
                    anim_dir=entry.anim_dir,
                    display_scale=entry.display_scale,
                    sample_scale=sample.scale,
                    brightness_rank=sample.brightness_rank,
                )
            elif item.kind == "player_bit":
                self._draw_player_bit(item.x, item.y, int(item.payload))
            elif item.kind == "settle_sushi":
                settling_sushi, glow = item.payload
                self._draw_orbit_sushi(
                    item.x,
                    item.y,
                    enemy_type=settling_sushi.enemy_type,
                    has_wasabi=settling_sushi.has_wasabi,
                    anim_offset=settling_sushi.anim_offset,
                    anim_dir=settling_sushi.anim_dir,
                    display_scale=settling_sushi.display_scale,
                    sample_scale=1.0,
                    brightness_rank=2,
                    glow=glow,
                    render_scale=1.125,
                )
            elif item.kind == "barrier":
                self._draw_player_barrier(int(round(item.x)), int(round(item.y)))
            elif item.kind == "player":
                self._draw_player(int(round(item.x)), int(round(item.y)))
        self._draw_settle_sparkle_layer(front=True)

    def _draw_orbit_shell_sparkle(self, x: float, y: float, *, brightness_rank: int, sparkle_idx: int) -> None:
        src = pyxel.image(self.SETTLE_SPARKLE_BANK)
        frame = ((self.frame_count // 2) + sparkle_idx) % self.SETTLE_SPARKLE_FRAMES
        src_u = self.SETTLE_SPARKLE_U
        src_v = self.SETTLE_SPARKLE_V + frame * self.SETTLE_SPARKLE_SIZE
        scale = self.ORBIT_SHELL_SPARKLE_SCALE
        vx = x - self.player.x
        vy = y - self.player.y
        length = math.sqrt(vx * vx + vy * vy)
        if length > 1e-6:
            x += (vx / length) * self.ORBIT_SHELL_SPARKLE_DRAW_OFFSET
            y += (vy / length) * self.ORBIT_SHELL_SPARKLE_DRAW_OFFSET
        x += self.ORBIT_SHELL_SPARKLE_DRAW_X_OFFSET
        y += self.ORBIT_SHELL_SPARKLE_DRAW_Y_OFFSET
        draw_w = self.SETTLE_SPARKLE_SIZE * scale
        draw_h = self.SETTLE_SPARKLE_SIZE * scale
        draw_x = int(round(x - draw_w / 2))
        draw_y = int(round(y - draw_h / 2))
        if brightness_rank >= 2:
            pyxel.pset(int(round(x)), int(round(y)), 7)
        elif brightness_rank <= 0:
            pyxel.pset(int(round(x)), int(round(y)), 5)
        pyxel.blt(
            draw_x,
            draw_y,
            src,
            src_u,
            src_v,
            self.SETTLE_SPARKLE_SIZE,
            self.SETTLE_SPARKLE_SIZE,
            self.SETTLE_SPARKLE_COLKEY,
            0.0,
            scale,
        )

    def _draw_sushi_settle_message(self) -> None:
        effect = self.sushi_settle_effect
        if not effect.active or not effect.sushis:
            return
        if effect.phase < self.SETTLE_PHASE_GLOW or effect.phase >= self.SETTLE_PHASE_FINISH:
            return

        cx = int(round(effect.center_x)) + 3
        cy = int(round(effect.center_y))
        main_text = "ARIGATO!!"
        sub_text = "BONUS SCORE" if self.barrier_stock >= self.BARRIER_STOCK_CAP else "BARRIER+1"

        main_scale = 1
        sub_scale = 1
        main_w = big_text_width(main_text, main_scale)
        sub_w = big_text_width(sub_text, sub_scale)
        main_x = cx - main_w // 2 - 3
        sub_x = cx - sub_w // 2 - 3
        if sub_text == "BONUS SCORE":
            sub_x -= 6

        main_color = 15 if (self.frame_count // 2) % 2 == 0 else 10
        sub_color = 7 if (self.frame_count // 3) % 2 == 0 else 12

        def draw_main_with_bold_exclaim(x: int, y: int, color: int) -> None:
            word_text = "ARIGATO"
            exclaim_text = "!!"
            word_x = x
            exclaim_x = x + len(word_text) * 6 * main_scale
            draw_big_text(word_x, y, word_text, main_scale, color, shadow_color=1)
            draw_big_text(exclaim_x, y, exclaim_text, main_scale, color, shadow_color=1)
            draw_big_text(exclaim_x + 1, y, exclaim_text, main_scale, color, shadow_color=1)

        if effect.phase in {self.SETTLE_PHASE_GLOW, self.SETTLE_PHASE_STOP, self.SETTLE_PHASE_BOUNCE}:
            draw_main_with_bold_exclaim(main_x, cy - 7, main_color)
            if (self.frame_count // 2) % 2 == 0:
                draw_big_text(sub_x, cy + 3, sub_text, sub_scale, sub_color, shadow_color=1)
        elif effect.phase in {self.SETTLE_PHASE_SHAKE, self.SETTLE_PHASE_EXPLODE}:
            if (self.frame_count // 2) % 2 == 0:
                draw_main_with_bold_exclaim(main_x, cy - 7, main_color)
            if (self.frame_count // 3) % 2 == 0:
                draw_big_text(sub_x, cy + 3, sub_text, sub_scale, sub_color, shadow_color=1)

    def _draw_player_barrier(self, x: int, y: int) -> None:
        if self.barrier_stock > 0:
            barrier_color = 11 if (self.frame_count // 6) % 2 == 0 else 7
            pyxel.circb(x, y - 1, 14, barrier_color)
            pyxel.circb(x, y - 1, 16, 5)
            for idx in range(min(3, self.barrier_stock)):
                pyxel.circ(x - 10 + idx * 10, y - 18, 2, 10)
        if self._fever_active() and self.boss_buff_state.fever_barrier_hits > 0:
            fever_color = 10 if (self.frame_count // 4) % 2 == 0 else 7
            pyxel.circb(x, y - 1, 18, fever_color)
            pyxel.circb(x, y - 1, 20, 13)

    def _player_bit_states(self) -> list[tuple[float, float, int, int]]:
        t = self.frame_count
        base_x = self.player.x
        base_y = self.player.y + self.PLAYER_BIT_Y_OFFSET
        drift_side = self._drift_x_bias(10.0)
        left_x = base_x - self.PLAYER_BIT_X_OFFSET + math.sin(t * 0.08) * 2.0 - drift_side
        left_y = base_y + math.cos(t * 0.11) * 2.0
        right_x = base_x + self.PLAYER_BIT_X_OFFSET + math.sin(t * 0.08 + 1.9) * 2.0 - drift_side
        right_y = base_y + math.cos(t * 0.11 + 2.4) * 2.0
        states: list[tuple[float, float, int, int]] = []
        if self.player_bit_levels[0] > 0:
            states.append((left_x, left_y, 0, self.player_bit_levels[0]))
        if self.player_bit_levels[1] > 0:
            states.append((right_x, right_y, 1, self.player_bit_levels[1]))
        return states

    def _player_bits_active(self) -> bool:
        return any(level > 0 for level in self.player_bit_levels)

    def _draw_player_bit(self, x: float, y: float, variant: int) -> None:
        frame = (self.frame_count // 2 + variant) % self.PLAYER_BIT_SPRITE_FRAMES
        src_u = self.PLAYER_BIT_SPRITE_U if variant == 0 else self.PLAYER_BIT_ALT_SPRITE_U
        src_v = self.PLAYER_BIT_SPRITE_V + frame * self.PLAYER_BIT_SPRITE_SIZE
        draw_x = int(round(x - self.PLAYER_BIT_SPRITE_SIZE / 2))
        draw_y = int(round(y - self.PLAYER_BIT_SPRITE_SIZE / 2))
        src_w = -self.PLAYER_BIT_SPRITE_SIZE if variant == 0 else self.PLAYER_BIT_SPRITE_SIZE
        src_x = src_u + self.PLAYER_BIT_SPRITE_SIZE if variant == 0 else src_u
        pyxel.blt(
            draw_x,
            draw_y,
            self.PLAYER_BIT_SPRITE_BANK,
            src_x,
            src_v,
            src_w,
            self.PLAYER_BIT_SPRITE_SIZE,
            self.PLAYER_BIT_SPRITE_COLKEY,
        )

    def _draw_player(self, x: int | None = None, y: int | None = None) -> None:
        blink = True if self.phase == GamePhase.START else (not self.player.is_hit or (self.frame_count // 3) % 2 == 0)
        if not blink:
            return

        x = int(self.player.x if x is None else x)
        y = int(self.player.y if y is None else y)
        engine_flicker = (self.frame_count // 2) % 3
        flame_len = 4 + (1 if engine_flicker == 0 else 0)
        wing_tip_color = 12 if engine_flicker == 1 else 6
        tilt = int(round(self._drift_x_bias(self.DRIFT_PLAYER_TILT_X)))

        pyxel.line(x + tilt, y - 12, x - 3, y - 6, 7)
        pyxel.line(x + tilt, y - 12, x + 3, y - 6, 7)
        pyxel.line(x - 3, y - 6, x + 3, y - 6, 12)

        pyxel.tri(x + tilt, y - 10, x - 7, y + 5, x + 7, y + 5, 5)
        pyxel.tri(x + tilt, y - 8, x - 5, y + 4, x + 5, y + 4, 12)
        pyxel.line(x - 1 + tilt // 2, y - 8, x - 1, y + 5, 7)
        pyxel.line(x + 1 + tilt // 2, y - 8, x + 1, y + 5, 7)

        pyxel.tri(x - 6, y + 1, x - 13, y + 6, x - 4, y + 5, wing_tip_color)
        pyxel.tri(x + 6, y + 1, x + 13, y + 6, x + 4, y + 5, wing_tip_color)
        pyxel.line(x - 12, y + 6, x - 3, y + 3, 7)
        pyxel.line(x + 12, y + 6, x + 3, y + 3, 7)
        pyxel.line(x - 9, y + 3, x - 13, y - 1, 1)
        pyxel.line(x + 9, y + 3, x + 13, y - 1, 1)

        pyxel.rect(x - 2, y - 3, 4, 5, 8)
        pyxel.rect(x - 1, y - 2, 2, 3, 7)
        pyxel.pset(x, y - 1, 12)

        pyxel.rect(x - 3, y + 5, 2, 3, 13)
        pyxel.rect(x + 1, y + 5, 2, 3, 13)
        pyxel.line(x - 2, y + 7, x - 2, y + 7 + flame_len, 10)
        pyxel.line(x + 2, y + 7, x + 2, y + 7 + flame_len, 10)
        pyxel.line(x - 2, y + 8, x - 2, y + 9 + flame_len, 7)
        pyxel.line(x + 2, y + 8, x + 2, y + 9 + flame_len, 7)

        pyxel.line(x - 1, y + 4, x - 4, y + 10, 1)
        pyxel.line(x + 1, y + 4, x + 4, y + 10, 1)

    def _draw_bullets(self) -> None:
        for bullet in self.bullets:
            bx = int(bullet.x)
            by = int(bullet.y)
            br = max(1, int(round(bullet.radius)))

            if bullet.style == "normal":
                pyxel.line(bx, by + 6, bx, by - 3, bullet.color_outer)
                pyxel.circ(bx, by, br, bullet.color_core)
            elif bullet.style == "power_single":
                pyxel.line(bx, by + 8, bx, by - 6, bullet.color_outer)
                pyxel.circ(bx, by, br, bullet.color_core)
                pyxel.circb(bx, by, br + 1, 15)
            elif bullet.style == "power_double":
                pyxel.line(bx, by + 8, bx, by - 5, bullet.color_outer)
                pyxel.circ(bx, by, br, bullet.color_core)
                pyxel.pset(bx, by, 15)
            elif bullet.style == "power_triple":
                pyxel.line(bx, by + 8, bx, by - 6, bullet.color_outer)
                pyxel.circ(bx, by, br, bullet.color_core)
                pyxel.circb(bx, by, br + 1, 7)
            elif bullet.style == "lance":
                pyxel.line(bx, by + 9, bx, by - 8, bullet.color_outer)
                pyxel.line(bx - 2, by + 4, bx - 2, by - 2, bullet.color_outer)
                pyxel.line(bx - 1, by + 6, bx - 1, by - 4, bullet.color_core)
                pyxel.line(bx + 1, by + 6, bx + 1, by - 4, bullet.color_core)
                pyxel.line(bx + 2, by + 4, bx + 2, by - 2, bullet.color_outer)
                pyxel.pset(bx, by - 9, 7)
            elif bullet.style == "lance_power":
                pyxel.line(bx, by + 10, bx, by - 10, bullet.color_outer)
                pyxel.line(bx - 2, by + 7, bx - 2, by - 5, bullet.color_outer)
                pyxel.line(bx - 1, by + 8, bx - 1, by - 6, bullet.color_core)
                pyxel.line(bx + 1, by + 8, bx + 1, by - 6, bullet.color_core)
                pyxel.line(bx + 2, by + 7, bx + 2, by - 5, bullet.color_outer)
                pyxel.circb(bx, by - 4, max(2, br - 2), 7)
            elif bullet.style == "rain":
                r = max(1, int(round(bullet.radius)))
                pyxel.circb(bx, by, r, bullet.color_outer)
                if r >= 2:
                    pyxel.circb(bx, by, max(1, r - 2), bullet.color_core)
                pyxel.pset(bx, by, 7)
            elif bullet.style == "rain_power":
                r = max(2, int(round(bullet.radius)))
                pyxel.circb(bx, by, r, bullet.color_outer)
                pyxel.circb(bx, by, max(1, r - 2), bullet.color_core)
                if r >= 5:
                    pyxel.circb(bx, by, max(1, r - 4), 7)
                pyxel.pset(bx, by, 15)
            elif bullet.style == "beam":
                pyxel.rect(bx - 1, by - 7, 3, 12, bullet.color_outer)
                pyxel.rect(bx, by - 6, 1, 10, bullet.color_core)
            elif bullet.style == "beam_core":
                pyxel.rect(bx - 2, by - 8, 5, 14, bullet.color_outer)
                pyxel.rect(bx - 1, by - 7, 3, 12, bullet.color_core)
                pyxel.line(bx, by - 9, bx, by + 6, 7)
            elif bullet.style == "beam_arc":
                trail = bullet.trail[-8:]
                for idx in range(1, len(trail)):
                    x0, y0 = trail[idx - 1]
                    x1, y1 = trail[idx]
                    shade = bullet.color_outer if idx < len(trail) - 2 else bullet.color_core
                    pyxel.line(int(x0), int(y0), int(x1), int(y1), shade)
                pyxel.line(bx, by + 2, bx, by - 6, bullet.color_core)
                pyxel.pset(bx, by - 7, 7)
            elif bullet.style == "beam_arc_power":
                trail = bullet.trail[-11:]
                for idx in range(1, len(trail)):
                    x0, y0 = trail[idx - 1]
                    x1, y1 = trail[idx]
                    shade = bullet.color_outer if idx < len(trail) - 3 else bullet.color_core
                    pyxel.line(int(x0), int(y0), int(x1), int(y1), shade)
                    pyxel.line(int(x0), int(y0) + 1, int(x1), int(y1) + 1, bullet.color_core)
                pyxel.line(bx - 1, by + 2, bx - 1, by - 7, bullet.color_outer)
                pyxel.line(bx, by + 3, bx, by - 8, bullet.color_core)
                pyxel.line(bx + 1, by + 2, bx + 1, by - 7, bullet.color_outer)
                pyxel.pset(bx, by - 8, 15)
            else:
                pyxel.line(bx, by + 6, bx, by - 3, bullet.color_outer)
                pyxel.circ(bx, by, br, bullet.color_core)

    def _draw_enemy_bullets(self) -> None:
        for bullet in self.enemy_bullets:
            bx = int(bullet.x)
            by = int(bullet.y)
            pyxel.circ(bx, by, bullet.radius, bullet.color)
            pyxel.pset(bx, by, 7)
            if bullet.radius >= 5:
                pyxel.circb(bx, by, bullet.radius, 7)

    def _draw_weapon_items(self) -> None:
        for item in self.weapon_items:
            ix = int(item.x)
            iy = int(item.y)
            accent = self._weapon_accent(item.family)
            ring_color = 7 if item.switch_lock_timer <= 0 or (self.frame_count // 6) % 2 == 0 else 13

            pyxel.circ(ix, iy, 7, accent)
            pyxel.circb(ix, iy, 7, ring_color)

            if item.family == self.WEAPON_FAMILY_FAN:
                pyxel.rect(ix - 3, iy - 2, 6, 5, 3)
                pyxel.line(ix + 6, iy - 1, ix + 9, iy + 1, 7)
                pyxel.line(ix + 9, iy + 1, ix + 8, iy + 4, 7)
                pyxel.pset(ix - 1, iy - 1, 11)
                pyxel.pset(ix, iy - 2, 11)
                pyxel.pset(ix + 1, iy - 1, 11)
            elif item.family == self.WEAPON_FAMILY_LANCE:
                pyxel.line(ix, iy + 5, ix, iy - 5, 7)
                pyxel.line(ix - 1, iy + 3, ix - 1, iy - 2, 8)
                pyxel.line(ix + 1, iy + 3, ix + 1, iy - 2, 8)
                pyxel.tri(ix, iy - 7, ix - 3, iy - 1, ix + 3, iy - 1, 15)
            elif item.family == self.WEAPON_FAMILY_RAIN:
                pyxel.line(ix, iy + 4, ix, iy - 3, 7)
                pyxel.pset(ix, iy - 5, 12)
                pyxel.pset(ix - 2, iy - 1, 15)
                pyxel.pset(ix + 2, iy + 1, 15)
            elif item.family == self.WEAPON_FAMILY_BEAM:
                pyxel.rect(ix - 2, iy - 5, 5, 10, 14)
                pyxel.rect(ix - 1, iy - 4, 3, 8, 7)
                pyxel.pset(ix, iy - 6, 15)
            elif item.family == self.WEAPON_FAMILY_ECHO:
                pyxel.line(ix - 4, iy + 4, ix + 4, iy - 4, 12)
                pyxel.line(ix - 3, iy + 5, ix + 5, iy - 3, 7)
                pyxel.pset(ix + 5, iy - 5, 15)

    def _draw_heal_items(self) -> None:
        for item in self.heal_items:
            frame = ((self.frame_count // 2) + int(item.bob_phase * 3.0)) % self.HEAL_SPRITE_FRAMES
            draw_x = int(round(item.x - self.HEAL_SPRITE_SIZE / 2))
            draw_y = int(round(item.y - self.HEAL_SPRITE_SIZE / 2))
            pyxel.blt(
                draw_x,
                draw_y,
                self.HEAL_SPRITE_BANK,
                self.HEAL_SPRITE_U,
                self.HEAL_SPRITE_V + frame * self.HEAL_SPRITE_SIZE,
                self.HEAL_SPRITE_SIZE,
                self.HEAL_SPRITE_SIZE,
                self.HEAL_SPRITE_COLKEY,
            )

    def _draw_bit_items(self) -> None:
        for item in self.bit_items:
            frame = ((self.frame_count // 2) + int(item.bob_phase * 3.0) + item.variant) % self.BIT_ITEM_SPRITE_FRAMES
            draw_x = int(round(item.x - self.BIT_ITEM_SPRITE_SIZE / 2))
            draw_y = int(round(item.y - self.BIT_ITEM_SPRITE_SIZE / 2))
            pyxel.blt(
                draw_x,
                draw_y,
                self.BIT_ITEM_SPRITE_BANK,
                self.BIT_ITEM_SPRITE_U + item.variant * self.BIT_ITEM_SPRITE_SIZE,
                self.BIT_ITEM_SPRITE_V + frame * self.BIT_ITEM_SPRITE_SIZE,
                self.BIT_ITEM_SPRITE_SIZE,
                self.BIT_ITEM_SPRITE_SIZE,
                self.BIT_ITEM_SPRITE_COLKEY,
            )

    def _draw_wasabi_items(self) -> None:
        for item in self.wasabi_items:
            frame = ((self.frame_count // 2) + int(item.bob_phase * 2.6)) % self.WASABI_SPRITE_FRAMES
            draw_x = int(round(item.x - self.WASABI_SPRITE_SIZE / 2))
            draw_y = int(round(item.y - self.WASABI_SPRITE_SIZE / 2))
            pyxel.blt(
                draw_x,
                draw_y,
                self.WASABI_SPRITE_BANK,
                self.WASABI_SPRITE_U,
                self.WASABI_SPRITE_V + frame * self.WASABI_SPRITE_SIZE,
                self.WASABI_SPRITE_SIZE,
                self.WASABI_SPRITE_SIZE,
                self.WASABI_SPRITE_COLKEY,
            )

    def _draw_bombs(self) -> None:
        for bomb in self.bombs:
            if bomb.phase == "launch":
                bx = int(bomb.x)
                by = int(bomb.y)
                pyxel.line(bx, by + 10, bx, by + 2, 7)
                pyxel.line(bx, by + 14, bx, by + 11, 10)
                pyxel.circ(bx, by, 4, 11)
                pyxel.circb(bx, by, 5, 7)
                continue

            current_radius = self._bomb_current_radius(bomb)
            center_x = int(bomb.x)
            center_y = int(bomb.y)
            progress = 1.0 - (bomb.life / bomb.max_life)
            trail_progress = max(0.0, progress - 0.12)
            trail_eased = 1.0 - ((1.0 - trail_progress) ** 3)

            if bomb.life > bomb.max_life * 0.66:
                outer_color = 11
                mid_color = 10
                inner_color = 7
            elif bomb.life > bomb.max_life * 0.33:
                outer_color = 12
                mid_color = 11
                inner_color = 7
            else:
                outer_color = 6
                mid_color = 12
                inner_color = 7

            outer_r = max(1, int(current_radius * 0.92))
            trail_r = max(1, int((bomb.radius + bomb.expansion * trail_eased) * 0.92))
            lead_r = outer_r + max(2, int(8 * ((1.0 - progress) ** 2)))

            if trail_r < outer_r - 1:
                pyxel.circb(center_x, center_y, trail_r, mid_color)
            pyxel.circb(center_x, center_y, outer_r, outer_color)
            pyxel.circb(center_x, center_y, lead_r, 7)

            streak_len = max(2, int(10 * ((1.0 - progress) ** 2)))
            if streak_len > 2:
                pyxel.line(center_x - lead_r - streak_len, center_y, center_x - lead_r + 1, center_y, mid_color)
                pyxel.line(center_x + lead_r - 1, center_y, center_x + lead_r + streak_len, center_y, mid_color)
                pyxel.line(center_x, center_y - lead_r - streak_len, center_x, center_y - lead_r + 1, mid_color)
                pyxel.line(center_x, center_y + lead_r - 1, center_x, center_y + lead_r + streak_len, mid_color)

            core_r = max(3, int(current_radius * 0.18))
            pyxel.circ(center_x, center_y, core_r, mid_color)
            pyxel.pset(center_x, center_y, inner_color)

    def _draw_bomb_visuals(self) -> None:
        for visual in self.active_bomb_visuals:
            if visual.pattern_id < 0 or visual.pattern_id >= len(self.bomb_patterns):
                continue
            pattern = self.bomb_patterns[visual.pattern_id]
            if visual.frame_index < 0 or visual.frame_index >= pattern.total_frames:
                continue
            frame = pattern.frames[visual.frame_index]
            flow_frame_index = min(
                pattern.total_frames - 1,
                int((visual.age / max(1, self.BOMB_VISUAL_DURATION_FRAMES)) * pattern.total_frames),
            )
            flow_frame = pattern.frames[flow_frame_index]
            if pattern.flow_sheet_image is not None and pattern.flow_frame_w > 0 and pattern.flow_frame_h > 0:
                flow_x = int(visual.x) - pattern.flow_origin_x
                flow_y = int(visual.y) - pattern.flow_origin_y
                if (
                    flow_x < self.WIDTH
                    and flow_x + pattern.flow_frame_w >= 0
                    and flow_y < self.HEIGHT
                    and flow_y + pattern.flow_frame_h >= self.PLAY_TOP
                ):
                    pyxel.blt(
                        flow_x,
                        flow_y,
                        pattern.flow_sheet_image,
                        flow_frame.flow_sheet_x,
                        flow_frame.flow_sheet_y,
                        pattern.flow_frame_w,
                        pattern.flow_frame_h,
                        0,
                    )
            if pattern.sheet_image is not None and pattern.frame_w > 0 and pattern.frame_h > 0:
                draw_x = int(visual.x) - pattern.origin_x
                draw_y = int(visual.y) - pattern.origin_y
                if (
                    draw_x < self.WIDTH
                    and draw_x + pattern.frame_w >= 0
                    and draw_y < self.HEIGHT
                    and draw_y + pattern.frame_h >= self.PLAY_TOP
                ):
                    pyxel.blt(
                        draw_x,
                        draw_y,
                        pattern.sheet_image,
                        frame.sheet_x,
                        frame.sheet_y,
                        pattern.frame_w,
                        pattern.frame_h,
                        0,
                    )
                continue
            for particle in frame.particles:
                x = int(visual.x) + particle.dx
                y = int(visual.y) + particle.dy
                if x < 0 or x >= self.WIDTH or y < self.PLAY_TOP or y >= self.HEIGHT:
                    continue
                if particle.kind == 1:
                    pyxel.circb(x, y, particle.size, particle.color)
                elif particle.kind == 2:
                    pyxel.pset(x, y, particle.color)
                    if particle.size >= 2:
                        pyxel.pset(x - 1, y, 7)
                        pyxel.pset(x + 1, y, 7)
                        pyxel.pset(x, y - 1, 7)
                        pyxel.pset(x, y + 1, 7)
                else:
                    pyxel.circ(x, y, particle.size - 1, particle.color)

    def _draw_thick_segment(self, x0: float, y0: float, x1: float, y1: float, half_width: int) -> None:
        dx = x1 - x0
        dy = y1 - y0
        length = math.hypot(dx, dy)
        if length <= 0.001:
            return

        perp_x = -dy / length
        perp_y = dx / length

        for offset in range(-half_width, half_width + 1):
            ox = perp_x * offset
            oy = perp_y * offset
            abs_offset = abs(offset)

            if abs_offset <= 1:
                color = 7
            elif abs_offset <= max(2, half_width // 2):
                color = 10
            else:
                color = 12

            pyxel.line(int(x0 + ox), int(y0 + oy), int(x1 + ox), int(y1 + oy), color)

    def _draw_homing_lasers(self) -> None:
        for laser in self.homing_lasers:
            if len(laser.trail) < 2:
                continue

            trail = laser.trail
            trail_len = len(trail)

            for idx in range(1, trail_len):
                x0, y0 = trail[idx - 1]
                x1, y1 = trail[idx]
                ratio = idx / trail_len
                if ratio < 0.35:
                    color = 13
                elif ratio < 0.70:
                    color = 12
                else:
                    color = 7
                pyxel.line(int(x0), int(y0), int(x1), int(y1), color)
                pyxel.line(int(x0), int(y0) + 1, int(x1), int(y1) + 1, color if ratio < 0.70 else 13)

            tip_x, tip_y = trail[-1]
            prev_x, prev_y = trail[-2]
            pyxel.line(int(prev_x), int(prev_y), int(tip_x), int(tip_y), 15)
            pyxel.line(int(prev_x), int(prev_y) + 1, int(tip_x), int(tip_y) + 1, 7)
            pyxel.pset(int(tip_x), int(tip_y), 15)
            pyxel.pset(int(tip_x), int(tip_y) + 1, 7)

    def _draw_echo_shots(self) -> None:
        for shot in self.echo_shots:
            x0, y0, x1, y1 = self._echo_segment(shot)
            if shot.power_variant:
                outer = 14 if shot.generation == 0 else 10
                core = 15 if shot.generation == 0 else 7
                half = 2 if shot.generation == 0 else 1
                self._draw_thick_segment(x0, y0, x1, y1, half)
                pyxel.pset(int(x0), int(y0), 15)
                pyxel.pset(int(x0) - 1, int(y0), outer)
                pyxel.pset(int(x0) + 1, int(y0), outer)
                pyxel.pset(int(x0), int(y0) - 1, core)
                pyxel.pset(int(x0), int(y0) + 1, core)
                pyxel.pset(int(x1), int(y1), core)
            else:
                self._draw_thick_segment(x0, y0, x1, y1, 1)
                pyxel.line(int(x0), int(y0), int((x0 + x1) * 0.5), int((y0 + y1) * 0.5), 15)
                pyxel.pset(int(x0), int(y0), 15)
                pyxel.pset(int(x1), int(y1), 7)

    def _draw_effects(self) -> None:
        self.effects.draw()

    def _get_enemy_sprite_uv(self, enemy: Enemy) -> tuple[int, int]:
        u, v, _bank = self._get_enemy_type_sprite_frame(
            enemy.enemy_type,
            enemy.anim_offset,
            enemy.anim_dir,
            enemy.sprite_variant,
        )
        return u, v

    def _get_enemy_type_sprite_frame(
        self,
        enemy_type: str,
        anim_offset: int,
        anim_dir: int,
        sprite_variant: int = 0,
        *,
        result_mode: bool = False,
    ) -> tuple[int, int, int]:
        if enemy_type == "rare":
            column = sprite_variant % 7
            if result_mode:
                frame = self._anim_frame_from_sequence(
                    self.RESULT_SOURCE_FISH_ANIM_SEQUENCE,
                    self.SOURCE_FISH_SPRITE_FRAMES,
                    anim_offset,
                    anim_dir,
                )
            else:
                frame = self._anim_frame_linear(6, self.SOURCE_FISH_SPRITE_FRAMES, anim_offset, anim_dir)
            u = self.SOURCE_FISH_SPRITE_U + column * self.ENEMY_SPRITE_SIZE
            v = self.SOURCE_FISH_SPRITE_V + frame * self.ENEMY_SPRITE_SIZE
            return u, v, self.ENEMY_SPRITE_BANK

        if enemy_type.endswith("_fish"):
            column = self.SOURCE_FISH_SPRITE_COLUMNS.get(enemy_type, 0)
            if result_mode:
                frame = self._anim_frame_from_sequence(
                    self.RESULT_SOURCE_FISH_ANIM_SEQUENCE,
                    self.SOURCE_FISH_SPRITE_FRAMES,
                    anim_offset,
                    anim_dir,
                )
            elif enemy_type in self.SOURCE_FISH_ANIM_LINEAR_TYPES:
                frame = self._anim_frame_linear(6, self.SOURCE_FISH_SPRITE_FRAMES, anim_offset, anim_dir)
            else:
                frame = self._anim_frame_from_sequence(
                    self.SOURCE_FISH_ANIM_SEQUENCE,
                    self.SOURCE_FISH_SPRITE_FRAMES,
                    anim_offset,
                    anim_dir,
                )
            u = self.SOURCE_FISH_SPRITE_U + column * self.ENEMY_SPRITE_SIZE
            v = self.SOURCE_FISH_SPRITE_V + frame * self.ENEMY_SPRITE_SIZE
            return u, v, self.ENEMY_SPRITE_BANK

        column = self.ENEMY_SPRITE_COLUMNS.get(enemy_type, 0)
        if result_mode:
            frame = self._anim_frame_from_sequence(
                self.RESULT_ENEMY_ANIM_SEQUENCE,
                self.ENEMY_SPRITE_FRAMES,
                anim_offset,
                anim_dir,
            )
        elif enemy_type in self.ENEMY_ANIM_LINEAR_TYPES:
            frame = self._anim_frame_linear(4, self.ENEMY_SPRITE_FRAMES, anim_offset, anim_dir)
        else:
            frame = self._anim_frame_from_sequence(
                self.ENEMY_ANIM_SEQUENCE,
                self.ENEMY_SPRITE_FRAMES,
                anim_offset,
                anim_dir,
            )
        u = column * self.ENEMY_SPRITE_SIZE
        v = frame * self.ENEMY_SPRITE_SIZE
        return u, v, self.ENEMY_SPRITE_BANK

    def _draw_enemy_type_sprite(
        self,
        x: float,
        y: float,
        *,
        enemy_type: str,
        scale: float,
        anim_offset: int = 0,
        anim_dir: int = 1,
        sprite_variant: int | None = None,
        result_mode: bool = False,
    ) -> None:
        if sprite_variant is None and enemy_type == "rare":
            sprite_variant = (self.frame_count // 12) % 7
        u, v, bank = self._get_enemy_type_sprite_frame(
            enemy_type,
            anim_offset,
            anim_dir,
            sprite_variant or 0,
            result_mode=result_mode,
        )
        draw_w = self.ENEMY_SPRITE_SIZE * scale
        draw_h = self.ENEMY_SPRITE_SIZE * scale
        pyxel.blt(
            int(x - draw_w / 2),
            int(y - draw_h / 2),
            bank,
            u,
            v,
            self.ENEMY_SPRITE_SIZE,
            self.ENEMY_SPRITE_SIZE,
            self.ENEMY_SPRITE_COLKEY,
            0.0,
            scale,
        )

    def _draw_enemy_sprite(self, enemy: Enemy) -> None:
        if enemy.was_hit and (self.frame_count // 2) % 2 == 0:
            return
        if enemy.invincible_timer > 0 and (self.frame_count // 2) % 2 == 0:
            return

        u, v = self._get_enemy_sprite_uv(enemy)
        draw_w = self.ENEMY_SPRITE_SIZE * enemy.display_scale
        draw_h = self.ENEMY_SPRITE_SIZE * enemy.display_scale
        x = int(enemy.x - draw_w / 2)
        y = int(enemy.y - draw_h / 2)

        if enemy.enemy_type == "rare":
            pulse = 8 if (self.frame_count // 4) % 2 == 0 else 10
            rare_cx = int(enemy.x) - 5
            rare_cy = int(enemy.y - max(1, round(2 * enemy.display_scale)))
            pyxel.circb(rare_cx, rare_cy, max(8, int(11 * enemy.display_scale)), pulse)
            pyxel.circb(rare_cx, rare_cy, max(10, int(14 * enemy.display_scale)), 7)

        pyxel.blt(
            x, y,
            self.ENEMY_SPRITE_BANK,
            u, v,
            self.ENEMY_SPRITE_SIZE, self.ENEMY_SPRITE_SIZE,
            self.ENEMY_SPRITE_COLKEY,
            0.0, enemy.display_scale,
        )

    def _draw_enemy_hp_bar(self, enemy: Enemy) -> None:
        if enemy.max_hp <= 1:
            return
        if enemy.state == "retreating":
            return

        sprite_half_h = self.ENEMY_HALF_H * enemy.display_scale
        bar_w = max(14, int(14 * enemy.display_scale))
        bar_h = 3
        ratio = max(0.0, enemy.hp / enemy.max_hp)
        fill_w = int(bar_w * ratio)

        ex = int(enemy.x - bar_w / 2)
        ey = int(enemy.y - sprite_half_h - 8)

        pyxel.rect(ex, ey, bar_w, bar_h, 1)
        pyxel.rectb(ex - 1, ey - 1, bar_w + 2, bar_h + 2, 5)
        if fill_w > 0:
            fill_color = 10 if enemy.enemy_type == "rare" else 11
            pyxel.rect(ex, ey, fill_w, bar_h, fill_color)

    def _draw_retreat_shadows(self) -> None:
        for shadow in self.retreat_shadows:
            self._draw_enemy_type_sprite(
                shadow.x,
                shadow.y,
                enemy_type=shadow.enemy_type,
                scale=shadow.display_scale,
                anim_offset=shadow.anim_offset,
                anim_dir=shadow.anim_dir,
                sprite_variant=shadow.sprite_variant,
            )
            cx = int(round(shadow.x))
            cy = int(round(shadow.y))
            pyxel.circb(cx, cy, max(8, int(10 * shadow.display_scale)), 5)

    def _draw_enemies(self) -> None:
        self._draw_retreat_shadows()
        for enemy in self.enemies:
            self._draw_enemy_sprite(enemy)
            self._draw_enemy_hp_bar(enemy)

    def _draw_boss(self) -> None:
        if self.boss is None:
            return

        boss = self.boss

        frame = self._anim_frame_from_sequence(
            self.BOSS_ANIM_SEQUENCE,
            self.BOSS_SPRITE_FRAMES,
            0,
            boss.anim_dir,
        )
        u = self.BOSS_SPRITE_U
        v = self.BOSS_SPRITE_V + frame * self.BOSS_SPRITE_H

        draw_w = self.BOSS_SPRITE_W * boss.display_scale
        draw_h = self.BOSS_SPRITE_H * boss.display_scale
        x = int(boss.x - draw_w / 2)
        y = int(boss.y - draw_h / 2)

        if not (boss.was_hit and (self.frame_count // 2) % 2 == 0):
            pyxel.blt(
                x, y,
                self.BOSS_SPRITE_BANK,
                u, v,
                self.BOSS_SPRITE_W, self.BOSS_SPRITE_H,
                self.BOSS_SPRITE_COLKEY,
                0.0, boss.display_scale,
            )

        aura_cx = int(round(boss.x + self.BOSS_AURA_CENTER_X_OFFSET))
        aura_cy = int(round(boss.y + self.BOSS_AURA_CENTER_Y_OFFSET))

        if getattr(boss, "entry_invulnerable", False):
            aura_r = int(max(draw_w, draw_h) * 0.78)
            aura_color = 12 if (self.frame_count // 3) % 2 == 0 else 7
            pyxel.circb(aura_cx, aura_cy, aura_r, aura_color)
            pyxel.circb(aura_cx, aura_cy, max(14, aura_r - 6), 6)
            pyxel.circb(aura_cx, aura_cy, max(10, aura_r - 12), 7)

        if getattr(boss, "shield_timer", 0) > 0:
            base_r = int(max(draw_w, draw_h) * 0.82)
            c1 = 12 if (self.frame_count // 3) % 2 == 0 else 7
            c2 = 6 if (self.frame_count // 5) % 2 == 0 else 13
            pyxel.circb(aura_cx, aura_cy, base_r, c1)
            pyxel.circb(aura_cx, aura_cy, base_r + 8, c2)
            pyxel.circb(aura_cx, aura_cy, max(16, base_r - 10), 7)

        if getattr(boss, "summon_flash_timer", 0) > 0:
            flash_r = int(max(draw_w, draw_h) * 0.70)
            pyxel.circb(int(boss.x), int(boss.y), flash_r, 10)
            if (self.frame_count // 2) % 2 == 0:
                pyxel.circb(int(boss.x), int(boss.y), flash_r + 3, 7)

    def _draw_boss_defeat_sequence(self) -> None:
        if self.boss_defeat_timer <= 0 and self.boss_defeat_confetti_timer <= 0:
            return

        progress = 1.0
        if self.boss_defeat_timer > 0:
            progress = 1.0 - (self.boss_defeat_timer / self.BOSS_DEFEAT_SEQUENCE_FRAMES)
        cx = int(self.boss_defeat_x)
        cy = int(self.boss_defeat_y)
        if self.boss_defeat_timer > 0:
            flash_r = int(12 + progress * 28 * self.boss_defeat_scale)
            ring_r = int(22 + progress * 50 * self.boss_defeat_scale)
            outer_r = int(34 + progress * 76 * self.boss_defeat_scale)
            pulse = 7 if (self.frame_count // 2) % 2 == 0 else 10

            pyxel.circ(cx, cy, flash_r, pulse)
            pyxel.circb(cx, cy, ring_r, 10)
            pyxel.circb(cx, cy, outer_r, 7)

            for spread, color in ((14, 10), (26, 7), (38, 15)):
                arm = int(spread + progress * 22)
                pyxel.line(cx - arm, cy, cx + arm, cy, color)
                pyxel.line(cx, cy - arm, cx, cy + arm, color)

            for idx in range(10):
                angle = progress * 2.4 + idx * (math.tau / 10)
                px = int(cx + math.cos(angle) * outer_r)
                py = int(cy + math.sin(angle) * outer_r * 0.78)
                pyxel.pset(px, py, 10 if idx % 2 == 0 else 7)

        self._draw_boss_defeat_sushis()
        self._draw_boss_defeat_cheers()

        confetti_ratio = 0.0
        if self.BOSS_DEFEAT_CONFETTI_FRAMES > 0:
            confetti_ratio = self.boss_defeat_confetti_timer / self.BOSS_DEFEAT_CONFETTI_FRAMES
        confetti_strength = min(1.0, confetti_ratio * 1.35)
        confetti_colors = (7, 10, 11, 14, 15)

        for idx in range(24):
            angle = idx * 0.51 + self.frame_count * 0.04
            radius = 22 + (idx % 5) * 10 + (1.0 - confetti_ratio) * 62
            drift_x = math.cos(angle * 1.18) * (10 + idx % 4 * 3)
            drift_y = math.sin(angle * 1.42) * (6 + idx % 3 * 4)
            fall = (self.frame_count * (1 + idx % 3) + idx * 19) % 68
            px = int(cx + math.cos(angle) * radius + drift_x)
            py = int(cy - 12 + math.sin(angle * 0.83) * 18 + fall - drift_y)
            if px < -8 or px > self.WIDTH + 8 or py < self.PLAY_TOP or py > self.HEIGHT - 4:
                continue

            color = confetti_colors[idx % len(confetti_colors)]
            edge = 1 if idx % 4 == 0 else 7
            if idx % 3 == 0:
                pyxel.rect(px - 3, py - 2, 6, 4, color)
                pyxel.rectb(px - 3, py - 2, 6, 4, edge)
            elif idx % 3 == 1:
                pyxel.line(px - 3, py - 2, px + 2, py + 3, color)
                pyxel.line(px - 2, py - 2, px + 3, py + 3, edge)
            else:
                pyxel.line(px + 3, py - 2, px - 2, py + 3, color)
                pyxel.line(px + 2, py - 2, px - 3, py + 3, edge)

            if confetti_strength > 0.20 and idx % 4 == 0:
                pyxel.pset(px, py - 3, 15)
                pyxel.pset(px - 1, py - 2, 7)
                pyxel.pset(px + 1, py - 2, 7)

        for idx in range(16):
            angle = idx * (math.tau / 16) + self.frame_count * 0.03
            sparkle_r = 28 + (1.0 - confetti_ratio) * 54 + (idx % 3) * 6
            px = int(cx + math.cos(angle) * sparkle_r)
            py = int(cy + math.sin(angle * 1.14) * sparkle_r * 0.56)
            if px < 4 or px >= self.WIDTH - 4 or py < self.PLAY_TOP + 4 or py >= self.HEIGHT - 4:
                continue
            color = 15 if idx % 2 == 0 else 10
            pyxel.pset(px, py, color)
            pyxel.pset(px - 1, py, 7)
            pyxel.pset(px + 1, py, 7)
            pyxel.pset(px, py - 1, 7)
            pyxel.pset(px, py + 1, 7)

    def _draw_boss_defeat_sushis(self) -> None:
        if not self.boss_defeat_sushis:
            return

        for sushi in sorted(self.boss_defeat_sushis, key=lambda item: (item.depth, item.scale)):
            if sushi.delay > 0:
                continue
            if sushi.depth <= -0.08:
                pyxel.circb(int(round(sushi.x)), int(round(sushi.y)), max(4, int(7 * sushi.scale)), 5)
            elif sushi.depth >= 0.20:
                pyxel.circb(int(round(sushi.x)), int(round(sushi.y)), max(4, int(8 * sushi.scale)), 7)
            self._draw_orbit_enemy_sprite(
                sushi.x,
                sushi.y,
                enemy_type=sushi.enemy_type,
                anim_offset=sushi.anim_offset,
                anim_dir=sushi.anim_dir,
                scale=sushi.scale,
            )

    def _draw_boss_defeat_cheers(self) -> None:
        if not self.boss_defeat_cheers:
            return

        for cheer in self.boss_defeat_cheers:
            if cheer.delay > 0:
                continue
            if cheer.scale <= 0:
                text_w = hud_value_text_width(cheer.text)
                text_h = 7
            else:
                text_w = big_text_width(cheer.text, cheer.scale)
                text_h = 7 * cheer.scale
            text_x = int(round(cheer.x)) - text_w // 2
            text_y = int(round(cheer.y)) - text_h // 2
            pulse_color = cheer.color if (self.frame_count // 2) % 2 == 0 else 15
            if cheer.scale <= 0:
                draw_hud_value_text(text_x, text_y, cheer.text, pulse_color, shadow_color=cheer.shadow_color)
            else:
                draw_big_text(
                    text_x,
                    text_y,
                    cheer.text,
                    cheer.scale,
                    pulse_color,
                    shadow_color=cheer.shadow_color,
                )

    def _draw_fever_arrival_effect(self) -> None:
        effect = self.fever_arrival_effect
        if not effect.active or not effect.sushis:
            return

        center_x = int(round(effect.center_x))
        center_y = int(round(effect.center_y))
        gather_done = effect.timer >= self.FEVER_ARRIVAL_GATHER_FRAMES
        pulse_color = 10 if (self.frame_count // 4) % 2 == 0 else 15
        sub_color = 7 if (self.frame_count // 6) % 2 == 0 else 12

        for sushi in sorted(effect.sushis, key=lambda item: item.current_y):
            self._draw_orbit_enemy_sprite(
                sushi.current_x,
                sushi.current_y,
                enemy_type=sushi.enemy_type,
                anim_offset=sushi.anim_offset,
                anim_dir=sushi.anim_dir,
                scale=sushi.display_scale,
            )
            if gather_done and (self.frame_count + sushi.delay) % 8 < 4:
                pyxel.pset(int(round(sushi.current_x)), int(round(sushi.current_y - 10)), 15)

        self._draw_fever_arrival_cheers(effect, center_x, center_y)

        if effect.timer >= self.FEVER_ARRIVAL_GATHER_FRAMES // 2:
            main_text = "ALL 5 BUFFS ABSORBED"
            sub_text = "FEVER TIME START!!"
            main_w = big_text_width(main_text, 2)
            sub_w = big_text_width(sub_text, 2)
            draw_big_text(center_x - main_w // 2, center_y - 108, main_text, 2, pulse_color, shadow_color=1)
            if (self.frame_count // 2) % 2 == 0:
                draw_big_text(center_x - sub_w // 2, center_y - 82, sub_text, 2, sub_color, shadow_color=1)

    def _draw_fever_arrival_waves(self, effect: FeverArrivalEffect) -> None:
        if not effect.active or not effect.sushis:
            return
        if (
            self.fever_arrival_wave_left_sheet is None
            or self.fever_arrival_wave_right_sheet is None
            or self.fever_arrival_wave_frame_w <= 0
            or self.fever_arrival_wave_frame_h <= 0
        ):
            return
        frame_idx = effect.timer % self.FEVER_ARRIVAL_WAVE_LOOP_FRAMES
        cols = max(1, self.fever_arrival_wave_sheet_cols)
        cell_x = (frame_idx % cols) * self.fever_arrival_wave_frame_w
        cell_y = (frame_idx // cols) * self.fever_arrival_wave_frame_h
        draw_y = self.HEIGHT - self.fever_arrival_wave_frame_h + self.FEVER_ARRIVAL_WAVE_Y_PAD
        right_x = self.WIDTH - self.fever_arrival_wave_frame_w + self.FEVER_ARRIVAL_WAVE_OVERFLOW_X

        pyxel.blt(
            self.FEVER_ARRIVAL_WAVE_LEFT_X,
            draw_y,
            self.fever_arrival_wave_left_sheet,
            cell_x,
            cell_y,
            self.fever_arrival_wave_frame_w,
            self.fever_arrival_wave_frame_h,
            0,
        )
        pyxel.blt(
            right_x,
            draw_y,
            self.fever_arrival_wave_right_sheet,
            cell_x,
            cell_y,
            self.fever_arrival_wave_frame_w,
            self.fever_arrival_wave_frame_h,
            0,
        )

    def _draw_fever_arrival_cheers(self, effect: FeverArrivalEffect, center_x: int, center_y: int) -> None:
        if effect.timer < self.FEVER_ARRIVAL_GATHER_FRAMES // 3:
            return

        for idx, (text, dx, dy, delay) in enumerate(self.FEVER_ARRIVAL_CHEER_TEXTS):
            if effect.timer < delay:
                continue
            local_timer = effect.timer - delay
            cycle = local_timer % 96
            if cycle >= 68:
                continue

            x = center_x + dx
            y = center_y + dy + int(math.sin((local_timer + idx * 3) * 0.12) * 2.0)
            color = 10 if (cycle // 4) % 2 == 0 else 15
            pyxel.text(x, y, text, color)
            pyxel.text(x + 1, y, text, 1)

    def _draw_boss_hp_bar(self) -> None:
        if self.boss is None and self.boss_hp_trail <= 0:
            return

        ratio = 0.0
        phase_text = ""
        if self.boss is not None and self.boss.max_hp > 0:
            ratio = max(0.0, self.boss.hp / self.boss.max_hp)
            phase_text = f"P{self._boss_phase()}"

        if ratio > 0.65:
            main_color = 8
            trail_color = 10
            inner_border = 7
        elif ratio > 0.30:
            main_color = 9
            trail_color = 10
            inner_border = 7
        else:
            main_color = 8
            trail_color = 9
            inner_border = 10

        if self.boss is not None and getattr(self.boss, "shield_timer", 0) > 0:
            main_color = 12
            trail_color = 6
            inner_border = 7

        flash = self.boss_hp_flash_timer > 0
        if flash:
            main_color = 7
            inner_border = 15

        shake_x = self._boss_hp_bar_shake_offset()

        bar_x = 44 + shake_x
        bar_y = self.HUD_H + 8
        bar_w = self.WIDTH - 62
        bar_h = 18

        current_hp = self.boss_hp_display
        max_hp = float(self.boss.max_hp) if self.boss is not None else float(self.BOSS_MAX_HP)

        fill_ratio = 0.0 if max_hp <= 0 else max(0.0, current_hp / max_hp)
        trail_ratio = 0.0 if max_hp <= 0 else max(0.0, self.boss_hp_trail / max_hp)

        fill_w = int((bar_w - 4) * fill_ratio)
        trail_w = int((bar_w - 4) * trail_ratio)

        pyxel.text(8 + shake_x, bar_y + 5, "BOSS", 8 if not flash else 7)

        pyxel.rect(bar_x, bar_y, bar_w, bar_h, 1)
        pyxel.rectb(bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4, 0)
        pyxel.rectb(bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2, 5)
        pyxel.rectb(bar_x, bar_y, bar_w, bar_h, inner_border)

        if trail_w > 0:
            pyxel.rect(bar_x + 2, bar_y + 2, trail_w, bar_h - 4, trail_color)
        if fill_w > 0:
            pyxel.rect(bar_x + 2, bar_y + 2, fill_w, bar_h - 4, main_color)
            pyxel.line(bar_x + 2, bar_y + 3, bar_x + 1 + fill_w, bar_y + 3, 15 if not flash else 7)

        hp_text = f"{int(max(0, round(current_hp))):03d}/{int(max_hp):03d}"
        pyxel.text(bar_x + bar_w - 48, bar_y + 6, hp_text, 7 if not flash else 15)
        if phase_text:
            pyxel.text(bar_x + bar_w - 82, bar_y - 8, phase_text, 10 if not flash else 7)

        if self.boss_pattern_id is not None and self.boss_pattern_buff:
            status_text = self.boss_pattern_buff
            status_scale = 1
            status_y = bar_y + bar_h + 6
            status_w = big_text_width(status_text, status_scale)
            status_x = 44 + (bar_w - status_w) // 2
            status_color = self.boss_pattern_accent if not flash else 7
            pyxel.rect(status_x - 6, status_y - 2, status_w + 12, 12, 1)
            pyxel.rectb(status_x - 7, status_y - 3, status_w + 14, 14, 5)
            draw_big_text(status_x, status_y, status_text, status_scale, status_color, shadow_color=1)
            draw_big_text(status_x + 1, status_y, status_text, status_scale, status_color, shadow_color=1)

    def _draw_boss_warning(self) -> None:
        if (self.frame_count // 20) % 2 != 0:
            return

        warning = "WARNING"
        sub = "BOSS APPROACH"

        warning_scale = 4
        sub_scale = 2

        warning_x = (self.WIDTH - big_text_width(warning, warning_scale)) // 2
        sub_x = (self.WIDTH - big_text_width(sub, sub_scale)) // 2
        center_y = self.HEIGHT // 2 - 40
        band_x = 24
        band_y = center_y - 8
        band_w = self.WIDTH - 48
        band_h = 72

        pyxel.rect(band_x, band_y, band_w, band_h, 10)
        pyxel.rectb(band_x - 2, band_y - 2, band_w + 4, band_h + 4, 0)
        pyxel.rectb(band_x - 1, band_y - 1, band_w + 2, band_h + 2, 7)
        pyxel.line(band_x, band_y + 12, band_x + band_w - 1, band_y + 12, 9)
        pyxel.line(band_x, band_y + band_h - 13, band_x + band_w - 1, band_y + band_h - 13, 9)

        draw_big_text(warning_x, center_y, warning, warning_scale, 0, shadow_color=9)
        draw_big_text(sub_x, center_y + 42, sub, sub_scale, 0, shadow_color=9)

    def _draw_hud(self) -> None:
        if self.phase == GamePhase.START:
            self._sync_start_preview_weapon_state()

        pyxel.rect(0, 0, self.WIDTH, self.HUD_H, self.hud_bg_color)

        left_x = 8
        right_x = 184
        top_label_y = 6
        top_value_y = 18
        info_row1_y = 40
        info_row2_y = 60
        status_row_y = 76
        bottom_row_y = 96
        left_value_x = 66
        right_value_x = 240

        draw_big_text(left_x, top_label_y, "SCORE", 1, 15, shadow_color=1)
        draw_big_text(left_x, top_value_y, f"{self.score:07d}", 2, 7, shadow_color=1)

        draw_big_text(146, top_label_y, "HP", 1, 15, shadow_color=1)
        self._draw_player_hp_meter(146, top_value_y + 4)

        kill_text = f"{self.enemy_kill_count:03d}"
        kill_label_x = self.WIDTH - 8 - big_text_width("FREED", 1)
        kill_value_x = self.WIDTH - 8 - big_text_width(kill_text, 2)
        draw_big_text(kill_label_x, top_label_y, "FREED", 1, 15, shadow_color=1)
        draw_big_text(kill_value_x, top_value_y, kill_text, 2, 12, shadow_color=1)

        draw_big_text(left_x, info_row1_y + 3, "MOVE", 1, 15, shadow_color=1)
        draw_hud_value_text(left_value_x, info_row1_y + 4, "ARROWS/DRAG", 7, shadow_color=1)

        draw_big_text(right_x, info_row1_y + 3, "SHOT", 1, 15, shadow_color=1)
        draw_hud_value_text(right_value_x, info_row1_y + 4, "ENTER/TOUCH", 7, shadow_color=1)

        bomb_label_color = 10 if self.bomb_restock_flash_timer <= 0 else 7
        bomb_value_color = 7 if self.bomb_restock_flash_timer <= 0 else 10
        laser_text_color = 7

        draw_big_text(left_x, info_row2_y + 3, "LASER", 1, 15, shadow_color=1)
        draw_hud_value_text(
            left_value_x,
            info_row2_y + 4,
            f"X {self.laser_shot_count}",
            laser_text_color,
            shadow_color=1,
        )
        draw_big_text(right_x, info_row2_y + 3, "BOMB", 1, bomb_label_color, shadow_color=1)
        draw_hud_value_text(
            right_value_x,
            info_row2_y + 4,
            f"C {self.bomb_stock}/{self._bomb_capacity()}",
            bomb_value_color,
            shadow_color=1,
        )

        if self.phase == GamePhase.START:
            main_family = self.current_weapon_family
            preview_slots = list(self.active_weapon_slots[:2])
            sub_family = preview_slots[1] if len(preview_slots) >= 2 else None
        else:
            self._sync_active_weapon_slots()
            main_family = self.current_weapon_family
            sub_family = next((slot for slot in self.active_weapon_slots if slot != main_family), None)

        self._draw_weapon_slot_inline(left_x, status_row_y, "MAIN", main_family, active=True)
        self._draw_weapon_slot_inline(right_x, status_row_y, "SUB", sub_family, active=sub_family is not None)

        self._draw_overload_ui(left_x, bottom_row_y)
        self._draw_boss_buff_ui(134, bottom_row_y)

    def _draw_player_hp_meter(self, x: int, y: int) -> None:
        block_w = 13
        block_h = 11
        gap = 4
        for idx in range(self.PLAYER_HP_CAP):
            bx = x + idx * (block_w + gap)
            if idx < self.player.hp:
                fill = 10
                border = 7
            elif idx < self.player.max_hp:
                fill = 5
                border = 13
            else:
                fill = 1
                border = 5
            pyxel.rect(bx, y, block_w, block_h, fill)
            pyxel.rectb(bx, y, block_w, block_h, border)

    def _draw_weapon_level_meter(self, x: int, y: int, family: str | None, *, active: bool) -> None:
        filled = 0 if family is None else self._weapon_level(family) + 1
        block_w = 11
        block_h = 10
        gap = 2
        accent = self._weapon_accent(family) if family is not None and (
            self.shot_pick_flash_timer <= 0 or (self.frame_count // 3) % 2 != 0
        ) else 15

        for idx in range(6):
            bx = x + idx * (block_w + gap)
            active = idx < filled
            if active:
                fill = accent if idx >= 3 else self._weapon_colors(family)[0]
                border = 7
            else:
                fill = 1
                border = 5

            pyxel.rect(bx, y, block_w, block_h, fill)
            pyxel.rectb(bx, y, block_w, block_h, border)

    def _draw_weapon_slot_inline(self, x: int, y: int, slot_label: str, family: str | None, *, active: bool) -> None:
        draw_big_text(x, y + 3, slot_label, 1, 15, shadow_color=1)
        label = self._weapon_hud_name(family)
        label_x = x + big_text_width(slot_label, 1) + 10
        box_x = label_x - 4
        box_y = y + 1
        box_w = big_text_width("LANCE", 1) + 8
        box_h = 14
        accent = self._weapon_accent(family) if family is not None and active else 5
        label_color = 7 if family is not None and active else 13
        pyxel.rect(box_x, box_y, box_w, box_h, 1)
        pyxel.rectb(box_x, box_y, box_w, box_h, accent)
        text_x = box_x + (box_w - big_text_width(label, 1)) // 2
        draw_big_text(text_x, y + 4, label, 1, label_color, shadow_color=1)
        meter_x = box_x + box_w + 8
        if self._fever_active() and active and family is not None:
            fever_text = "FEVER MAX!!"
            fever_color = 10 if (self.frame_count // 5) % 2 == 0 else 8
            draw_big_text(meter_x, y + 3, fever_text, 1, fever_color, shadow_color=1)
            return
        self._draw_weapon_level_meter(meter_x, y + 2, family, active=active)

    def _draw_boss_buff_ui(self, x: int, y: int) -> None:
        draw_big_text(x, y + 3, "BUFF", 1, 10, shadow_color=1)
        current_buff = self.boss_buff_state.current_boss_buff
        for idx, buff_id in enumerate(self.BUFF_IDS):
            bx = x + 56 + idx * 24
            acquired = buff_id in self.boss_buff_state.acquired_cycle_buffs or self.boss_buff_state.overload_active
            fill = 10 if acquired else 1
            border = 7 if acquired else 5
            pyxel.rect(bx, y + 2, 20, 11, fill)
            pyxel.rectb(bx, y + 2, 20, 11, border)
            text_color = 1 if acquired else 13
            draw_big_text(bx + 2, y + 4, self.BUFF_LABELS[buff_id], 1, text_color, shadow_color=None)
            if current_buff == buff_id:
                pyxel.line(bx + 2, y + 14, bx + 17, y + 14, 15)

    def _draw_overload_ui(self, x: int, y: int) -> None:
        if self.boss_buff_state.overload_active:
            color = 8 if (self.frame_count // 5) % 2 == 0 else 10
            draw_big_text(x, y, "FEVER x2", 2, color, shadow_color=1)
            return
        if self.barrier_stock > 0:
            draw_big_text(x, y + 3, "BARRIER", 1, 11, shadow_color=1)
            draw_big_text(x + 60, y, str(self.barrier_stock), 2, 7, shadow_color=1)

    def _draw_reward_notice(self) -> None:
        if self.reward_notice_timer <= 0 or self.phase != GamePhase.PLAYING:
            return

        elapsed = self.REWARD_NOTICE_FRAMES - self.reward_notice_timer
        intro = min(1.0, elapsed / self.REWARD_CUTIN_IN_FRAMES)
        outro = min(1.0, self.reward_notice_timer / self.REWARD_CUTIN_OUT_FRAMES)
        visibility = min(intro, outro)
        eased = 1.0 - (1.0 - visibility) ** 3

        centered_card = self.reward_notice_kind.startswith("boss_buff_")
        panel_w = 236 if centered_card else self.REWARD_CUTIN_W
        panel_h = 74 if centered_card else self.REWARD_CUTIN_H
        slant = 0 if centered_card else self.REWARD_CUTIN_SLANT
        if centered_card:
            target_x = (self.WIDTH - panel_w) // 2
            target_y = self.PLAY_TOP + ((self.HEIGHT - self.PLAY_TOP - panel_h) // 2)
            box_x = target_x
            box_y = int(target_y - (1.0 - eased) * 18)
        else:
            target_x = 8
            start_x = -panel_w - slant - 36
            box_x = int(start_x + (target_x - start_x) * eased)
            box_y = self.REWARD_CUTIN_Y
        accent = self.reward_notice_accent
        panel_main, panel_band, border_dark, title_dark = self._notice_palette()

        pulse = (self.frame_count // 3) % 2 == 0
        flash_x = box_x - 40 + ((elapsed * 11) % (panel_w + 96))

        if centered_card:
            pyxel.rect(box_x + 4, box_y + 4, panel_w, panel_h, 0)
            pyxel.rect(box_x, box_y, panel_w, panel_h, panel_main)
            pyxel.rectb(box_x, box_y, panel_w, panel_h, border_dark)
            pyxel.rectb(box_x + 2, box_y + 2, panel_w - 4, panel_h - 4, accent)
            pyxel.rect(box_x, box_y + panel_h - 14, panel_w, 14, panel_band)
        else:
            pyxel.rect(box_x + 4, box_y + 4, panel_w - slant + 10, panel_h, 0)
            pyxel.tri(
                box_x + panel_w - slant + 4,
                box_y + 4,
                box_x + panel_w + 8,
                box_y + 4,
                box_x + panel_w - slant + 4,
                box_y + panel_h + 4,
                0,
            )

            pyxel.rect(box_x, box_y, panel_w - slant, panel_h, panel_main)
            pyxel.tri(
                box_x + panel_w - slant,
                box_y,
                box_x + panel_w,
                box_y,
                box_x + panel_w - slant,
                box_y + panel_h,
                panel_main,
            )

            pyxel.rect(box_x, box_y + panel_h - 16, panel_w - slant, 16, panel_band)
            pyxel.tri(
                box_x + panel_w - slant,
                box_y + panel_h - 16,
                box_x + panel_w,
                box_y + panel_h - 16,
                box_x + panel_w - slant,
                box_y + panel_h,
                panel_band,
            )

            pyxel.line(box_x, box_y, box_x + panel_w - slant, box_y, 7)
            pyxel.line(box_x, box_y + panel_h - 1, box_x + panel_w - slant, box_y + panel_h - 1, border_dark)
            pyxel.line(box_x + panel_w - slant, box_y, box_x + panel_w, box_y, 7)
            pyxel.line(box_x + panel_w - slant, box_y + panel_h - 1, box_x + panel_w - slant, box_y + panel_h - 1, border_dark)
            pyxel.line(box_x, box_y, box_x, box_y + panel_h - 1, border_dark)
            pyxel.line(box_x + panel_w - slant, box_y, box_x + panel_w - slant, box_y + panel_h - 1, border_dark)
            pyxel.line(box_x + panel_w, box_y, box_x + panel_w - slant, box_y + panel_h - 1, border_dark)

        sparkle_points = (
            (82, 14, 7),
            (118, 22, accent),
            (154, 12, 15),
            (176, 44, 7),
            (208, 18, accent),
            (196, 52, 15),
        )
        sparkle_shift = (elapsed // 2) % 6
        for idx, (sx, sy, color) in enumerate(sparkle_points):
            if (idx + sparkle_shift) % 2 != 0:
                continue
            px = box_x + sx
            py = box_y + sy
            pyxel.pset(px, py, color)
            pyxel.pset(px - 1, py, 7)
            pyxel.pset(px + 1, py, 7)
            pyxel.pset(px, py - 1, 7)
            pyxel.pset(px, py + 1, 7)
            if idx % 3 == 0:
                pyxel.pset(px - 1, py - 1, 15)
                pyxel.pset(px + 1, py + 1, 15)

        pyxel.rect(box_x + 8, box_y + 8, 58, 14, 0)
        pyxel.text(box_x + 14, box_y + 12, self.reward_notice_label, accent)

        if self.reward_notice_kind.startswith("weapon_"):
            icon_x = box_x + 17
            icon_y = box_y + 31
            family = self.reward_notice_kind.split("_", 1)[1]
            if family == self.WEAPON_FAMILY_FAN:
                for idx, spread in enumerate((-7, 0, 7)):
                    pyxel.line(icon_x + 6, icon_y + 18, icon_x + 20 + spread, icon_y - 6, accent if idx == 1 else 7)
                pyxel.circ(icon_x + 6, icon_y + 20, 4, 0)
            elif family == self.WEAPON_FAMILY_LANCE:
                pyxel.line(icon_x + 8, icon_y + 20, icon_x + 8, icon_y - 8, 7)
                pyxel.line(icon_x + 12, icon_y + 20, icon_x + 12, icon_y - 12, accent)
                pyxel.line(icon_x + 16, icon_y + 20, icon_x + 16, icon_y - 8, 7)
                pyxel.tri(icon_x + 12, icon_y - 16, icon_x + 7, icon_y - 8, icon_x + 17, icon_y - 8, 15)
            elif family == self.WEAPON_FAMILY_RAIN:
                for drop_x, drop_y, rad in ((6, -4, 2), (14, 2, 3), (21, -6, 2), (24, 8, 3)):
                    pyxel.circb(icon_x + drop_x, icon_y + drop_y, rad, 7)
                    pyxel.pset(icon_x + drop_x, icon_y + drop_y + 1, accent)
            elif family == self.WEAPON_FAMILY_BEAM:
                pyxel.line(icon_x + 4, icon_y + 18, icon_x + 16, icon_y - 8, accent)
                pyxel.line(icon_x + 10, icon_y + 18, icon_x + 22, icon_y - 4, 7)
                pyxel.line(icon_x + 16, icon_y + 18, icon_x + 28, icon_y - 8, accent)
                pyxel.pset(icon_x + 16, icon_y - 10, 15)
            elif family == self.WEAPON_FAMILY_ECHO:
                pyxel.line(icon_x + 4, icon_y + 16, icon_x + 20, icon_y - 2, accent)
                pyxel.line(icon_x + 6, icon_y + 18, icon_x + 22, icon_y, 7)
                pyxel.line(icon_x + 20, icon_y - 2, icon_x + 28, icon_y - 8, accent)
                pyxel.pset(icon_x + 28, icon_y - 8, 15)
        elif self.reward_notice_kind.startswith("boss_buff_"):
            icon_x = box_x + 18
            icon_y = box_y + 33
            buff_id = self.reward_notice_kind.split("_", 2)[2]
            pyxel.circb(icon_x + 12, icon_y + 2, 12, accent)
            pyxel.circb(icon_x + 12, icon_y + 2, 9, 7)
            if buff_id == "power":
                pyxel.rect(icon_x + 9, icon_y - 8, 6, 20, accent)
                pyxel.tri(icon_x + 12, icon_y - 12, icon_x + 5, icon_y - 2, icon_x + 19, icon_y - 2, 15)
                pyxel.pset(icon_x + 12, icon_y + 14, 15)
            elif buff_id == "speed":
                pyxel.line(icon_x + 2, icon_y + 8, icon_x + 16, icon_y - 6, accent)
                pyxel.line(icon_x + 8, icon_y + 10, icon_x + 22, icon_y - 4, 7)
                pyxel.line(icon_x + 16, icon_y + 12, icon_x + 28, icon_y, 15)
            elif buff_id == "rapid":
                pyxel.line(icon_x + 2, icon_y - 2, icon_x + 22, icon_y - 2, accent)
                pyxel.line(icon_x + 2, icon_y + 4, icon_x + 22, icon_y + 4, 7)
                pyxel.line(icon_x + 2, icon_y + 10, icon_x + 22, icon_y + 10, accent)
                pyxel.pset(icon_x + 24, icon_y + 4, 15)
            elif buff_id == "wide":
                pyxel.line(icon_x + 12, icon_y + 2, icon_x - 2, icon_y - 8, accent)
                pyxel.line(icon_x + 12, icon_y + 2, icon_x + 26, icon_y - 8, accent)
                pyxel.line(icon_x + 12, icon_y + 2, icon_x - 6, icon_y + 10, 7)
                pyxel.line(icon_x + 12, icon_y + 2, icon_x + 30, icon_y + 10, 7)
                pyxel.pset(icon_x + 12, icon_y + 2, 15)
            elif buff_id == "guard":
                pyxel.tri(icon_x + 12, icon_y - 10, icon_x + 3, icon_y - 3, icon_x + 21, icon_y - 3, 7)
                pyxel.rect(icon_x + 4, icon_y - 2, 16, 12, accent)
                pyxel.rectb(icon_x + 4, icon_y - 2, 16, 12, 15)
                pyxel.line(icon_x + 12, icon_y - 2, icon_x + 12, icon_y + 10, 15)
                pyxel.line(icon_x + 6, icon_y + 4, icon_x + 18, icon_y + 4, 15)
        elif self.reward_notice_kind == "overload":
            icon_x = box_x + 16
            icon_y = box_y + 31
            pyxel.circb(icon_x + 14, icon_y + 2, 14, accent)
            pyxel.circb(icon_x + 14, icon_y + 2, 10, 15)
            for offset in (-12, -6, 0, 6, 12):
                pyxel.line(icon_x + 14, icon_y + 2, icon_x + 14 + offset, icon_y - 12, 7)
            pyxel.line(icon_x + 4, icon_y + 10, icon_x + 24, icon_y - 10, accent)
            pyxel.line(icon_x + 4, icon_y - 10, icon_x + 24, icon_y + 10, accent)
            pyxel.line(icon_x + 14, icon_y - 14, icon_x + 14, icon_y + 18, 15)
            pyxel.line(icon_x - 2, icon_y + 2, icon_x + 30, icon_y + 2, 15)
            pyxel.pset(icon_x + 14, icon_y + 2, 7)
        elif self.reward_notice_kind == "shot_up":
            arrow_x = box_x + 20
            arrow_y = box_y + 30
            pyxel.rect(arrow_x + 8, arrow_y + 8, 6, 18, accent)
            pyxel.rectb(arrow_x + 8, arrow_y + 8, 6, 18, 7)
            pyxel.tri(arrow_x + 11, arrow_y - 4, arrow_x + 2, arrow_y + 10, arrow_x + 20, arrow_y + 10, accent)
            pyxel.tri(arrow_x + 11, arrow_y - 8, arrow_x - 2, arrow_y + 12, arrow_x + 24, arrow_y + 12, 7)
            pyxel.pset(arrow_x + 11, arrow_y - 10, 15)
            pyxel.pset(arrow_x + 6, arrow_y + 18, 15)
            pyxel.pset(arrow_x + 16, arrow_y + 18, 15)
        else:
            chevron_y = box_y + 34
            for idx in range(3):
                cx = box_x + 14 + idx * 12
                pyxel.tri(cx, chevron_y, cx + 8, chevron_y + 6, cx, chevron_y + 12, 0)

        pyxel.rect(box_x + 44, box_y + 27, 4, 26, 0)
        pyxel.rect(box_x + 50, box_y + 27, 6, 26, accent)

        title_color = title_dark if pulse else 1
        draw_big_text(box_x + 64, box_y + 18, self.reward_notice_text, 2, title_color, shadow_color=7)
        draw_big_text(box_x + 64, box_y + 47, self.reward_notice_desc, 1, 0, shadow_color=7)

        if box_x <= flash_x <= box_x + panel_w:
            pyxel.line(flash_x, box_y + 4, flash_x + 20, box_y + panel_h - 6, 7)
            pyxel.line(flash_x + 1, box_y + 4, flash_x + 21, box_y + panel_h - 6, 15)

        pyxel.tri(
            box_x + panel_w - 18,
            box_y + 10,
            box_x + panel_w - 6,
            box_y + 20,
            box_x + panel_w - 22,
            box_y + 30,
            accent,
        )
        pyxel.tri(
            box_x + panel_w - 26,
            box_y + 30,
            box_x + panel_w - 10,
            box_y + 42,
            box_x + panel_w - 30,
            box_y + 54,
            0,
        )

    def _draw_reward_select(self) -> None:
        pyxel.rect(18, self.HUD_H + 18, self.WIDTH - 36, self.HEIGHT - self.HUD_H - 36, 1)
        pyxel.rectb(18, self.HUD_H + 18, self.WIDTH - 36, self.HEIGHT - self.HUD_H - 36, 10)
        pyxel.rectb(21, self.HUD_H + 21, self.WIDTH - 42, self.HEIGHT - self.HUD_H - 42, 7)

        title = "REWARD SELECT"
        sub = "CHOOSE ONE UPGRADE"
        info = "ARROWS OR TAP A CARD"

        title_x = (self.WIDTH - big_text_width(title, 3)) // 2
        sub_x = (self.WIDTH - big_text_width(sub, 2)) // 2
        info_x = (self.WIDTH - big_text_width(info, 1)) // 2

        draw_big_text(title_x, self.HUD_H + 34, title, 3, 10, shadow_color=1)
        draw_big_text(sub_x, self.HUD_H + 68, sub, 2, 7, shadow_color=1)
        draw_big_text(info_x, self.HUD_H + 90, info, 1, 12, shadow_color=1)

        for idx, choice in enumerate(self.reward_choices):
            box_x = self.REWARD_BOX_X
            box_y = self.REWARD_BOX_START_Y + idx * (self.REWARD_BOX_H + self.REWARD_BOX_GAP)
            selected = idx == self.reward_selection_index

            fill = 2 if not selected else 0
            border = choice.accent_color if not selected else 7
            inner = 5 if not selected else choice.accent_color

            pyxel.rect(box_x, box_y, self.REWARD_BOX_W, self.REWARD_BOX_H, fill)
            pyxel.rectb(box_x, box_y, self.REWARD_BOX_W, self.REWARD_BOX_H, border)
            pyxel.rectb(box_x + 3, box_y + 3, self.REWARD_BOX_W - 6, self.REWARD_BOX_H - 6, inner)

            if selected and (self.frame_count // 4) % 2 == 0:
                pyxel.rectb(box_x - 2, box_y - 2, self.REWARD_BOX_W + 4, self.REWARD_BOX_H + 4, 10)

            pyxel.rect(box_x + 10, box_y + 10, 18, self.REWARD_BOX_H - 20, choice.accent_color)
            pyxel.text(box_x + 14, box_y + 16, str(idx + 1), 1)

            title_color = 7 if selected else choice.accent_color
            desc_color = 12 if selected else 7
            tag_x = box_x + self.REWARD_BOX_W - 82

            draw_big_text(box_x + 40, box_y + 14, choice.title, 2, title_color, shadow_color=1)
            draw_big_text(box_x + 40, box_y + 42, choice.description, 1, desc_color, shadow_color=1)
            pyxel.rect(tag_x, box_y + 10, 68, 14, 1 if selected else 0)
            pyxel.rectb(tag_x, box_y + 10, 68, 14, choice.accent_color)
            pyxel.text(tag_x + 10, box_y + 14, choice.tag, 7 if selected else choice.accent_color)

        if self.reward_intro_timer > 0:
            reveal = 1.0 - (self.reward_intro_timer / self.REWARD_DISSOLVE_FRAMES)
            mask_x = 24
            mask_y = self.HUD_H + 24
            mask_w = self.WIDTH - 48
            mask_h = self.HEIGHT - self.HUD_H - 60
            cell = 12
            for gy in range(mask_y, mask_y + mask_h, cell):
                for gx in range(mask_x, mask_x + mask_w, cell):
                    grid_x = (gx - mask_x) // cell
                    grid_y = (gy - mask_y) // cell
                    threshold = ((grid_x * 17 + grid_y * 29 + grid_x * grid_y * 3) % 100) / 100.0
                    if threshold <= reveal:
                        continue
                    pyxel.rect(gx, gy, cell, cell, 1)

        if self._dual_shot_ready():
            title_words = ("CHOOSE", "DUAL", "WEAPON")
            title_char_gap = 7
            title_word_gap = 8
            title_widths = [
                scaled_text_width(word, 1, advance_x=title_char_gap)
                for word in title_words
            ]
            title_total_w = sum(title_widths) + title_word_gap * (len(title_words) - 1)
            title_x = (self.WIDTH - title_total_w) // 2 - 3
            title_y = self.HEIGHT - 107

            cursor_x = title_x
            for word, word_w in zip(title_words, title_widths):
                draw_scaled_text(
                    cursor_x,
                    title_y,
                    word,
                    1,
                    1,
                    10,
                    shadow_color=1,
                    advance_x=title_char_gap,
                )
                draw_scaled_text(
                    cursor_x + 1,
                    title_y,
                    word,
                    1,
                    1,
                    10,
                    advance_x=title_char_gap,
                )
                cursor_x += word_w + title_word_gap

            selected_slots = [
                slot
                for slot in self.active_weapon_slots[:2]
                if self._is_weapon_unlocked(slot)
            ]
            active = set(selected_slots)
            for idx, family in enumerate(self.WEAPON_FAMILY_ORDER):
                bx, by, bw, bh = self._dual_button_rect(idx)
                unlocked = self._is_weapon_unlocked(family)
                selected = family in active
                accent = self._weapon_accent(family)

                fill = 1
                border = 5
                inner = 0
                text = 13

                if unlocked:
                    fill = 0 if not selected else 1
                    border = accent if not selected else 7
                    inner = 5 if not selected else accent
                    text = 5 if not selected else 7

                if selected:
                    pyxel.rect(bx - 2, by - 2, bw + 4, bh + 4, accent)
                    pyxel.rectb(bx - 2, by - 2, bw + 4, bh + 4, 7)
                    slot_label = None
                    if selected_slots and family == selected_slots[0]:
                        slot_label = "MAIN"
                    elif len(selected_slots) >= 2 and family == selected_slots[1]:
                        slot_label = "SUB"
                    if slot_label is not None:
                        slot_label_x = bx + (bw - big_text_width(slot_label, 1)) // 2
                        draw_big_text(slot_label_x, by - 12, slot_label, 1, 7, shadow_color=1)

                pyxel.rect(bx, by, bw, bh, fill)
                pyxel.rectb(bx, by, bw, bh, border)
                pyxel.rectb(bx + 2, by + 2, bw - 4, bh - 4, inner)

                label = self._weapon_name(family) if unlocked else "LOCK"
                label_x = bx + (bw - big_text_width(label, 1)) // 2
                draw_big_text(label_x, by + 8, label, 1, text, shadow_color=1)

        footer = "ENTER / SPACE TO CONFIRM"
        footer_x = (self.WIDTH - big_text_width(footer, 1)) // 2
        footer_y = self.HEIGHT - 30 if not self._dual_shot_ready() else self.HEIGHT - 42
        draw_big_text(footer_x, footer_y, footer, 1, 10, shadow_color=1)

    def _draw_selector_arrow(self, x: int, y: int, direction: int, color: int) -> None:
        if direction < 0:
            pyxel.tri(x + 10, y, x, y + 6, x + 10, y + 12, color)
        else:
            pyxel.tri(x, y, x + 10, y + 6, x, y + 12, color)

    def _draw_start_screen(self) -> None:
        box_w = 320
        extra_rows = self._start_debug_extra_rows()
        box_h = 326 + extra_rows * 64
        box_x = (self.WIDTH - box_w) // 2
        box_y = (self.HEIGHT - box_h) // 2

        pyxel.rect(box_x, box_y, box_w, box_h, self.hud_bg_color)
        pyxel.rectb(box_x, box_y, box_w, box_h, 12)
        pyxel.rectb(box_x + 3, box_y + 3, box_w - 6, box_h - 6, self.hud_accent_color)

        title = "VERTICAL"
        subtitle = "SHOOTER"
        start_text = "TAP / ENTER TO START"

        title_scale = 4
        subtitle_scale = 4
        start_scale = 2

        title_x = (self.WIDTH - big_text_width(title, title_scale)) // 2
        subtitle_x = (self.WIDTH - big_text_width(subtitle, subtitle_scale)) // 2
        start_x = (self.WIDTH - big_text_width(start_text, start_scale)) // 2

        draw_big_text(title_x, box_y + 14, title, title_scale, 11, shadow_color=1)
        draw_big_text(subtitle_x, box_y + 48, subtitle, subtitle_scale, 10, shadow_color=1)

        selector_x = box_x + 26
        selector_y = box_y + 100
        selector_w = box_w - 52
        selector_h = 54
        weapon_selector_y = selector_y + 64
        sub_weapon_selector_y = weapon_selector_y + (64 if self._start_sub_weapon_menu_enabled() else 0)
        bomb_power_selector_y = sub_weapon_selector_y + 64
        laser_count_selector_y = bomb_power_selector_y + (64 if self.START_DEBUG_BOMB_POWER_MENU else 0)
        fever_selector_y = laser_count_selector_y + (64 if self.START_DEBUG_LASER_COUNT_MENU else 0)
        prefever_selector_y = fever_selector_y + (64 if self.START_DEBUG_FEVER_MENU else 0)
        debug_selector_y = prefever_selector_y + (64 if self.START_DEBUG_PREFEVER_MENU else 0)

        start_box_w = 280
        start_box_h = 34
        start_box_x = (self.WIDTH - start_box_w) // 2
        start_box_y = box_y + (238 + extra_rows * 64)

        theme_border = 10 if self.start_menu_focus == 0 else 6
        start_weapon = self._selected_start_weapon_family()
        weapon_border = self._weapon_accent(start_weapon) if self.start_menu_focus == 1 else 6
        sub_weapon_label = self._start_sub_weapon_label()
        sub_weapon_accent = self._start_sub_weapon_accent()
        sub_weapon_border = sub_weapon_accent if self.start_menu_focus == self._start_sub_weapon_focus_index() else 6
        bomb_power_label = self._start_bomb_power_label()
        bomb_power_accent = self._start_bomb_power_accent()
        bomb_power_border = bomb_power_accent if self.start_menu_focus == self._start_bomb_power_focus_index() else 6
        laser_count_label = self._start_laser_count_label()
        laser_count_accent = self._start_laser_count_accent()
        laser_count_border = laser_count_accent if self.start_menu_focus == self._start_laser_count_focus_index() else 6
        fever_label = "ON" if self.start_fever_enabled else "OFF"
        fever_accent = 10 if self.start_fever_enabled else 5
        fever_border = fever_accent if self.start_menu_focus == self._start_fever_focus_index() else 6
        prefever_label = "ON" if self.start_prefever_enabled else "OFF"
        prefever_accent = 11 if self.start_prefever_enabled else 5
        prefever_border = prefever_accent if self.start_menu_focus == self._start_prefever_focus_index() else 6
        debug_pattern = self._start_boss_pattern_label()
        debug_accent = self._start_boss_pattern_accent()
        debug_focus_index = self._start_boss_pattern_focus_index() or 2
        debug_border = debug_accent if self.start_menu_focus == debug_focus_index else 6

        pyxel.rect(selector_x, selector_y, selector_w, selector_h, 1)
        pyxel.rectb(selector_x, selector_y, selector_w, selector_h, theme_border)
        pyxel.rectb(selector_x + 2, selector_y + 2, selector_w - 4, selector_h - 4, 11)

        pyxel.text(selector_x + 10, selector_y + 8, "THEME SELECT", 12)
        pyxel.text(selector_x + 10, selector_y + 42, "TAP LEFT / RIGHT TO CHANGE", 7)

        arrow_y = selector_y + 20
        self._draw_selector_arrow(selector_x + 12, arrow_y, -1, 10)
        self._draw_selector_arrow(selector_x + selector_w - 22, arrow_y, 1, 10)

        theme_scale = 2
        theme_text = self.theme_display_name
        theme_x = (self.WIDTH - big_text_width(theme_text, theme_scale)) // 2
        draw_big_text(theme_x, selector_y + 18, theme_text, theme_scale, 7)

        pyxel.rect(selector_x, weapon_selector_y, selector_w, selector_h, 1)
        pyxel.rectb(selector_x, weapon_selector_y, selector_w, selector_h, weapon_border)
        pyxel.rectb(selector_x + 2, weapon_selector_y + 2, selector_w - 4, selector_h - 4, self._weapon_accent(start_weapon))

        pyxel.text(selector_x + 10, weapon_selector_y + 8, "START WEAPON", 12)
        pyxel.text(selector_x + 10, weapon_selector_y + 42, "UP / DOWN FOCUS, LEFT / RIGHT CHANGE", 7)

        arrow_y = weapon_selector_y + 20
        self._draw_selector_arrow(selector_x + 12, arrow_y, -1, self._weapon_accent(start_weapon))
        self._draw_selector_arrow(selector_x + selector_w - 22, arrow_y, 1, self._weapon_accent(start_weapon))

        weapon_text = self._weapon_name(start_weapon)
        weapon_x = (self.WIDTH - big_text_width(weapon_text, theme_scale)) // 2
        draw_big_text(weapon_x, weapon_selector_y + 18, weapon_text, theme_scale, self._weapon_accent(start_weapon), shadow_color=1)

        if self._start_sub_weapon_menu_enabled():
            pyxel.rect(selector_x, sub_weapon_selector_y, selector_w, selector_h, 1)
            pyxel.rectb(selector_x, sub_weapon_selector_y, selector_w, selector_h, sub_weapon_border)
            pyxel.rectb(selector_x + 2, sub_weapon_selector_y + 2, selector_w - 4, selector_h - 4, sub_weapon_accent)

            pyxel.text(selector_x + 10, sub_weapon_selector_y + 8, "SUB WEAPON", 12)
            pyxel.text(selector_x + 10, sub_weapon_selector_y + 42, "SET SECOND WEAPON SLOT", 7)

            arrow_y = sub_weapon_selector_y + 20
            self._draw_selector_arrow(selector_x + 12, arrow_y, -1, sub_weapon_accent)
            self._draw_selector_arrow(selector_x + selector_w - 22, arrow_y, 1, sub_weapon_accent)

            sub_weapon_x = (self.WIDTH - big_text_width(sub_weapon_label, theme_scale)) // 2
            draw_big_text(sub_weapon_x, sub_weapon_selector_y + 18, sub_weapon_label, theme_scale, sub_weapon_accent, shadow_color=1)

        if self.START_DEBUG_BOMB_POWER_MENU:
            pyxel.rect(selector_x, bomb_power_selector_y, selector_w, selector_h, 1)
            pyxel.rectb(selector_x, bomb_power_selector_y, selector_w, selector_h, bomb_power_border)
            pyxel.rectb(selector_x + 2, bomb_power_selector_y + 2, selector_w - 4, selector_h - 4, bomb_power_accent)

            pyxel.text(selector_x + 10, bomb_power_selector_y + 8, "DEBUG BOMB POWER", 12)
            pyxel.text(selector_x + 10, bomb_power_selector_y + 42, "SET START BOMB SIZE LEVEL", 7)

            arrow_y = bomb_power_selector_y + 20
            self._draw_selector_arrow(selector_x + 12, arrow_y, -1, bomb_power_accent)
            self._draw_selector_arrow(selector_x + selector_w - 22, arrow_y, 1, bomb_power_accent)

            bomb_power_x = (self.WIDTH - big_text_width(bomb_power_label, theme_scale)) // 2
            draw_big_text(bomb_power_x, bomb_power_selector_y + 18, bomb_power_label, theme_scale, bomb_power_accent, shadow_color=1)

        if self.START_DEBUG_LASER_COUNT_MENU:
            pyxel.rect(selector_x, laser_count_selector_y, selector_w, selector_h, 1)
            pyxel.rectb(selector_x, laser_count_selector_y, selector_w, selector_h, laser_count_border)
            pyxel.rectb(selector_x + 2, laser_count_selector_y + 2, selector_w - 4, selector_h - 4, laser_count_accent)

            pyxel.text(selector_x + 10, laser_count_selector_y + 8, "DEBUG LASER COUNT", 12)
            pyxel.text(selector_x + 10, laser_count_selector_y + 42, "SET START LASER SHOT COUNT", 7)

            arrow_y = laser_count_selector_y + 20
            self._draw_selector_arrow(selector_x + 12, arrow_y, -1, laser_count_accent)
            self._draw_selector_arrow(selector_x + selector_w - 22, arrow_y, 1, laser_count_accent)

            laser_count_x = (self.WIDTH - big_text_width(laser_count_label, theme_scale)) // 2
            draw_big_text(laser_count_x, laser_count_selector_y + 18, laser_count_label, theme_scale, laser_count_accent, shadow_color=1)

        if self.START_DEBUG_FEVER_MENU:
            pyxel.rect(selector_x, fever_selector_y, selector_w, selector_h, 1)
            pyxel.rectb(selector_x, fever_selector_y, selector_w, selector_h, fever_border)
            pyxel.rectb(selector_x + 2, fever_selector_y + 2, selector_w - 4, selector_h - 4, fever_accent)

            pyxel.text(selector_x + 10, fever_selector_y + 8, "DEBUG FEVER", 12)
            pyxel.text(selector_x + 10, fever_selector_y + 42, "START WITH FEVER TIME", 7)

            fever_x = (self.WIDTH - big_text_width(fever_label, theme_scale)) // 2
            draw_big_text(fever_x, fever_selector_y + 18, fever_label, theme_scale, fever_accent if self.start_fever_enabled else 13, shadow_color=1)

        if self.START_DEBUG_PREFEVER_MENU:
            pyxel.rect(selector_x, prefever_selector_y, selector_w, selector_h, 1)
            pyxel.rectb(selector_x, prefever_selector_y, selector_w, selector_h, prefever_border)
            pyxel.rectb(selector_x + 2, prefever_selector_y + 2, selector_w - 4, selector_h - 4, prefever_accent)

            pyxel.text(selector_x + 10, prefever_selector_y + 8, "DEBUG PRE-FEVER", 12)
            pyxel.text(selector_x + 10, prefever_selector_y + 42, "START AT LOOP 5 WITH 4 BUFFS", 7)

            prefever_x = (self.WIDTH - big_text_width(prefever_label, theme_scale)) // 2
            draw_big_text(prefever_x, prefever_selector_y + 18, prefever_label, theme_scale, prefever_accent if self.start_prefever_enabled else 13, shadow_color=1)

        if self.START_DEBUG_BOSS_PATTERN_MENU:
            pyxel.rect(selector_x, debug_selector_y, selector_w, selector_h, 1)
            pyxel.rectb(selector_x, debug_selector_y, selector_w, selector_h, debug_border)
            pyxel.rectb(selector_x + 2, debug_selector_y + 2, selector_w - 4, selector_h - 4, debug_accent)

            pyxel.text(selector_x + 10, debug_selector_y + 8, "DEBUG BOSS PATTERN", 12)
            pyxel.text(selector_x + 10, debug_selector_y + 42, "RANDOM OR FIX ONE PATTERN", 7)

            arrow_y = debug_selector_y + 20
            self._draw_selector_arrow(selector_x + 12, arrow_y, -1, debug_accent)
            self._draw_selector_arrow(selector_x + selector_w - 22, arrow_y, 1, debug_accent)

            debug_x = (self.WIDTH - big_text_width(debug_pattern, theme_scale)) // 2
            draw_big_text(debug_x, debug_selector_y + 18, debug_pattern, theme_scale, 7 if debug_pattern == "RANDOM" else debug_accent, shadow_color=1)

        pyxel.rect(start_box_x, start_box_y, start_box_w, start_box_h, 1)
        pyxel.rectb(start_box_x, start_box_y, start_box_w, start_box_h, 10)
        pyxel.rectb(start_box_x + 2, start_box_y + 2, start_box_w - 4, start_box_h - 4, 11)
        draw_big_text(start_x, start_box_y + 8, start_text, start_scale, 7, shadow_color=1)

        footer_y = box_y + (276 + extra_rows * 64)
        pyxel.text(box_x + 18, footer_y, "WEAPON ITEMS SWITCH OR BOOST SHOTS", 11)
        pyxel.text(box_x + 18, footer_y + 12, "BOMB / LASER AVAILABLE ON MOBILE", 10)
        if sys.platform != "emscripten":
            pyxel.text(box_x + 18, footer_y + 24, "PC: USE HALF-WIDTH INPUT", 9)

    def _draw_game_over(self) -> None:
        box_w = 248
        box_h = 128
        box_x = (self.WIDTH - box_w) // 2
        box_y = (self.HEIGHT - box_h) // 2

        pyxel.rect(box_x, box_y, box_w, box_h, self.hud_bg_color)
        pyxel.rectb(box_x, box_y, box_w, box_h, 8)
        pyxel.rectb(box_x + 3, box_y + 3, box_w - 6, box_h - 6, 13)

        title = "GAME OVER"
        retry = "TAP / CLICK"
        return_text = "BACK TO TITLE"
        score_text = f"FINAL SCORE {self.score}"

        title_scale = 4
        retry_scale = 2
        score_scale = 2
        return_scale = 2

        title_x = (self.WIDTH - big_text_width(title, title_scale)) // 2
        retry_x = (self.WIDTH - big_text_width(retry, retry_scale)) // 2
        score_x = (self.WIDTH - big_text_width(score_text, score_scale)) // 2
        return_x = (self.WIDTH - big_text_width(return_text, return_scale)) // 2

        draw_big_text(title_x, box_y + 18, title, title_scale, 8, shadow_color=2)
        draw_big_text(score_x, box_y + 68, score_text, score_scale, 7, shadow_color=1)
        draw_big_text(retry_x, box_y + 90, retry, retry_scale, 10, shadow_color=1)
        draw_big_text(return_x, box_y + 106, return_text, return_scale, 10, shadow_color=1)

    def _draw_result_enemy_row(self, enemy_type: str, count: int, x: int, y: int, col_w: int, row_index: int) -> None:
        if enemy_type == "boss":
            sprite_scale = 0.82
        else:
            sprite_scale = 1.0 if enemy_type.endswith("_fish") else 0.86

        icon_cx = x + 12
        icon_cy = y + 3 if enemy_type == "boss" else y + 9
        if enemy_type != "boss":
            pyxel.circ(icon_cx, icon_cy, 9, self.hud_bg_color)
            pyxel.circb(icon_cx, icon_cy, 9, 13)
        anim_offset = (row_index * 3) % max(2, self.ENEMY_SPRITE_FRAMES)
        anim_dir = -1 if row_index % 2 else 1

        if enemy_type == "boss":
            self._draw_result_boss_sprite(icon_cx, icon_cy, scale=sprite_scale, anim_offset=anim_offset)
        else:
            self._draw_enemy_type_sprite(
                icon_cx,
                icon_cy,
                enemy_type=enemy_type,
                scale=sprite_scale,
                anim_offset=anim_offset,
                anim_dir=anim_dir,
                result_mode=True,
            )

        label = self.RESULT_ENEMY_LABELS.get(enemy_type, enemy_type.upper())
        label_x = x + 34
        pyxel.text(label_x, y + 4, label, 1)
        count_text = f"x {count}"
        count_w = hud_value_text_width(count_text)
        count_x = x + col_w - count_w - 4
        draw_hud_value_text(count_x, y + 3, count_text, 10, shadow_color=7)

    def _draw_result_boss_sprite(self, x: float, y: float, *, scale: float, anim_offset: int = 0) -> None:
        frame = self._anim_frame_from_sequence(
            self.RESULT_BOSS_ANIM_SEQUENCE,
            self.BOSS_SPRITE_FRAMES,
            anim_offset,
            1,
        )
        draw_w = self.BOSS_SPRITE_W * scale
        draw_h = self.BOSS_SPRITE_H * scale
        pyxel.blt(
            int(x - draw_w / 2),
            int(y - draw_h / 2),
            self.BOSS_SPRITE_BANK,
            self.BOSS_SPRITE_U,
            self.BOSS_SPRITE_V + frame * self.BOSS_SPRITE_H,
            self.BOSS_SPRITE_W,
            self.BOSS_SPRITE_H,
            self.BOSS_SPRITE_COLKEY,
            0.0,
            scale,
        )

    def _draw_result_kv_row(self, label: str, value: str, x: int, y: int, width: int, *, value_color: int) -> None:
        pyxel.text(x, y + 4, label, 1)
        value_w = hud_value_text_width(value)
        draw_hud_value_text(x + width - value_w, y + 3, value, value_color, shadow_color=7)

    def _draw_result_screen(self) -> None:
        rows = self._result_enemy_rows()
        combo_rows = self._result_combo_rows()
        param_rows = self._result_param_rows()
        weapon_rows = self._result_weapon_rows()
        box_x = 16
        box_y = 28
        box_w = self.WIDTH - 32
        box_h = self.HEIGHT - 56

        paper = 7
        ink = 1
        accent = 10
        sub_ink = 5

        pyxel.rect(box_x, box_y, box_w, box_h, paper)
        pyxel.rectb(box_x, box_y, box_w, box_h, ink)
        for notch_x in range(box_x + 6, box_x + box_w - 6, 18):
            pyxel.pset(notch_x, box_y, 13)
            pyxel.pset(notch_x + 9, box_y + box_h - 1, 13)

        title = "RESULT"
        score_text = f"SCORE {self.score:07d}"
        kill_text = f"TOTAL FREED {self.enemy_kill_count}"
        title_x = (self.WIDTH - big_text_width(title, 3)) // 2
        score_x = (self.WIDTH - big_text_width(score_text, 1)) // 2
        kill_x = (self.WIDTH - big_text_width(kill_text, 1)) // 2
        draw_big_text(title_x, box_y + 14, title, 3, accent, shadow_color=paper)
        draw_big_text(score_x, box_y + 42, score_text, 1, ink, shadow_color=paper)
        draw_big_text(kill_x, box_y + 58, kill_text, 1, sub_ink, shadow_color=paper)

        pyxel.line(box_x + 12, box_y + 82, box_x + box_w - 12, box_y + 82, 13)

        list_x = box_x + 14
        list_y = box_y + 92
        col_gap = 18
        col_w = (box_w - 28 - col_gap) // 2
        rows_per_col = (len(rows) + 1) // 2
        row_gap = 22
        for idx, (enemy_type, count) in enumerate(rows):
            col = idx // rows_per_col
            row = idx % rows_per_col
            col_x = list_x + col * (col_w + col_gap)
            row_y = list_y + row * row_gap
            self._draw_result_enemy_row(enemy_type, count, col_x, row_y, col_w, idx)

        row_y = list_y + rows_per_col * row_gap + 4

        combo_title = "SUSHI COMBOS"
        combo_x = box_x + 18
        stats_x = box_x + box_w // 2 + 6
        stats_w = box_x + box_w - 18 - stats_x
        pyxel.line(box_x + 12, row_y + 2, box_x + box_w - 12, row_y + 2, 13)
        draw_big_text(combo_x, row_y + 8, combo_title, 1, accent, shadow_color=paper)
        draw_big_text(stats_x, row_y + 8, "RUN DATA", 1, accent, shadow_color=paper)
        combo_y = row_y + 24
        for label, count in combo_rows:
            pyxel.text(combo_x + 4, combo_y + 5, label, ink)
            count_text = f"x {count}"
            count_w = hud_value_text_width(count_text)
            draw_hud_value_text(box_x + box_w // 2 - count_w - 10, combo_y + 4, count_text, accent, shadow_color=paper)
            combo_y += 14

        stats_y = row_y + 24
        for label, value in param_rows:
            self._draw_result_kv_row(label, value, stats_x, stats_y, stats_w, value_color=accent)
            stats_y += 14

        section_bottom = max(combo_y, stats_y)
        pyxel.line(box_x + 12, section_bottom + 2, box_x + box_w - 12, section_bottom + 2, 13)
        weapon_title_y = section_bottom + 8
        draw_big_text(box_x + 18, weapon_title_y, "WEAPON BUILD", 1, accent, shadow_color=paper)
        weapon_start_y = weapon_title_y + 16
        weapon_col_gap = 18
        weapon_col_w = (box_w - 36 - weapon_col_gap) // 2
        weapon_rows_per_col = (len(weapon_rows) + 1) // 2
        for idx, (label, value) in enumerate(weapon_rows):
            col = idx // weapon_rows_per_col
            row = idx % weapon_rows_per_col
            wx = box_x + 18 + col * (weapon_col_w + weapon_col_gap)
            wy = weapon_start_y + row * 14
            self._draw_result_kv_row(label, value, wx, wy, weapon_col_w, value_color=sub_ink)

        continue_text = "TAP / CLICK TO CONTINUE"
        continue_x = (self.WIDTH - big_text_width(continue_text, 1)) // 2
        draw_big_text(continue_x, box_y + box_h - 22, continue_text, 1, accent, shadow_color=paper)


if __name__ == "__main__":
    ShootGame()
