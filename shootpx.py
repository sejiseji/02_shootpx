from __future__ import annotations

import math
import random

import pyxel

from bitmap_font import big_text_width, draw_big_text
from boss_system import boss_phase, spawn_boss, update_boss
from effects import EffectManager
from enemy_system import create_enemy, pick_enemy_type, update_enemies
from fireworks import (
    BackgroundFirework,
    radiating_sphere_projection_burst,
)
from game_models import (
    BombField,
    Boss,
    Bullet,
    Enemy,
    EnemyBullet,
    GamePhase,
    HealItem,
    HomingLaser,
    Player,
    RewardChoice,
    WeaponItem,
)


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

    ENEMY_W = 16
    ENEMY_H = 16
    ENEMY_HALF_W = ENEMY_W // 2
    ENEMY_HALF_H = ENEMY_H // 2

    BULLET_R = 3

    PLAYER_START_Y = HEIGHT - 84
    PLAYER_MIN_Y = PLAY_TOP + PLAYER_HALF_H + 10
    PLAYER_MAX_Y = HEIGHT - PLAYER_HALF_H - 18

    PLAYER_MAX_HP = 3
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

    BOSS_SPRITE_BANK = 1
    BOSS_SPRITE_U = 144
    BOSS_SPRITE_V = 0
    BOSS_SPRITE_W = 32
    BOSS_SPRITE_H = 32
    BOSS_SPRITE_FRAMES = 8
    BOSS_SPRITE_COLKEY = 15
    BOSS_AURA_CENTER_X_OFFSET = -12
    BOSS_AURA_CENTER_Y_OFFSET = -6

    BOSS_TRIGGER_SCORE = 1000
    BOSS_TRIGGER_KILLS = 40
    BOSS_WARNING_TIME = 90
    BOSS_ENTRY_TARGET_Y = PLAY_TOP + 88
    BOSS_MAX_HP = 140
    BOSS_SCORE_VALUE = 1000

    BOMB_RESTOCK_FLASH_FRAMES = 24

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

    TEA_DROP_CHANCE = 0.06
    TEA_FALL_SPEED = 1.35
    TEA_BOB_SPEED = 0.10
    TEA_PICKUP_RADIUS = 13
    TEA_FLASH_FRAMES = 22
    TEA_DROP_BONUS_STEP = 0.03
    WEAPON_ITEM_SWITCH_LOCK_FRAMES = 120
    HEAL_DROP_CANCEL_CHANCE = 0.0025
    WEAPON_OVERDRIVE_CAP = 2

    REWARD_OPTION_COUNT = 3
    REWARD_BOX_W = 292
    REWARD_BOX_H = 88
    REWARD_BOX_GAP = 14
    REWARD_BOX_X = (WIDTH - REWARD_BOX_W) // 2
    REWARD_BOX_START_Y = HUD_H + 106
    REWARD_NOTICE_FRAMES = 72
    REWARD_CUTIN_W = 236
    REWARD_CUTIN_H = 68
    REWARD_CUTIN_Y = HUD_H + 12
    REWARD_CUTIN_SLANT = 28
    REWARD_CUTIN_IN_FRAMES = 10
    REWARD_CUTIN_OUT_FRAMES = 12

    PLAYER_SPEED_CAP = 8
    LASER_COOLDOWN_REWARD_STEP = 3
    LASER_COOLDOWN_MIN = 8

    WEAPON_FAMILY_FAN = "fan"
    WEAPON_FAMILY_LANCE = "lance"
    WEAPON_FAMILY_RAIN = "rain"
    WEAPON_FAMILY_BEAM = "beam"
    WEAPON_FAMILY_ORDER = (
        WEAPON_FAMILY_FAN,
        WEAPON_FAMILY_LANCE,
        WEAPON_FAMILY_RAIN,
        WEAPON_FAMILY_BEAM,
    )
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
    }

    ENEMY_SPRITE_COLUMNS = {
        "basic": 0,
        "zigzag": 1,
        "shooter": 2,
        "tank": 3,
        "sprint": 4,
        "spreader": 5,
        "aimer": 6,
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

        self.start_theme_keys = list(self.THEMES.keys())
        self.start_theme_index = self.start_theme_keys.index("fresh_night")
        self.start_weapon_index = 0
        self.start_menu_focus = 0
        self.theme_name = self.start_theme_keys[self.start_theme_index]
        self._apply_theme(self.theme_name)

        self.stars = self._build_stars(84)
        self.fireworks: list[BackgroundFirework] = []
        self.firework_spawn_timer = random.randrange(50, 100)
        self.max_fireworks = 3

        self.effects = EffectManager(max_effects=96)

        self._reset_play_state()
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
        self.weapon_items: list[WeaponItem] = []
        self.heal_items: list[HealItem] = []
        self.boss: Boss | None = None

        self.effects.clear()

        self.score = 0
        self.enemy_kill_count = 0

        self.touch_active = False
        self.prev_touch_down = False
        self.touch_drag_active = False

        self.spawn_timer = 0
        self.spawn_interval_sec = 0.62
        self.shoot_interval_frames = 6
        self.bullet_speed = 10

        self.base_bomb_cap = 2
        self.bomb_bonus_cap = 0
        self.bomb_stock = self._bomb_capacity()
        self.bomb_active_limit = 1
        self.bomb_restock_flash_timer = 0

        self.laser_active_limit = 3
        self.laser_cooldown_frames = 24
        self.laser_cooldown = 0

        self.prev_mobile_bomb_pressed = False
        self.prev_mobile_laser_pressed = False

        self.boss_intro_timer = 0
        self.boss_event_started = False
        self.boss_defeated = False

        self.boss_hp_display = 0.0
        self.boss_hp_trail = 0.0
        self.boss_hp_shake_timer = 0
        self.boss_hp_flash_timer = 0

        self.boss_spawn_count = 0
        self.next_boss_kill_threshold = self.BOSS_TRIGGER_KILLS
        self.next_boss_score_threshold = self.BOSS_TRIGGER_SCORE

        start_family = self.WEAPON_FAMILY_ORDER[self.start_weapon_index]
        self.unlocked_weapon_families = [start_family]
        self.current_weapon_family = start_family
        self.weapon_levels = {
            family: (self.SHOT_LEVEL_SINGLE if family == start_family else -1)
            for family in self.WEAPON_FAMILY_ORDER
        }
        self.weapon_overdrive_bonus = {family: 0 for family in self.WEAPON_FAMILY_ORDER}
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

    def _set_start_weapon_by_index(self, index: int) -> None:
        self.start_weapon_index = index % len(self.WEAPON_FAMILY_ORDER)

    def _move_start_weapon_selection(self, delta: int) -> None:
        self._set_start_weapon_by_index(self.start_weapon_index + delta)

    def _recolor_stars(self) -> None:
        for star in self.stars:
            star[3] = self._random_star_color()

    def _bomb_capacity(self) -> int:
        return self.base_bomb_cap + self.bomb_bonus_cap

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

    def _point_in_circle(self, px: float, py: float, cx: float, cy: float, r: float) -> bool:
        dx = px - cx
        dy = py - cy
        return dx * dx + dy * dy <= r * r

    def _point_in_rect(self, px: float, py: float, x: float, y: float, w: float, h: float) -> bool:
        return x <= px <= x + w and y <= py <= y + h

    def _is_touch_in_mobile_control_area(self) -> bool:
        if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            return False

        mx = float(pyxel.mouse_x)
        my = float(pyxel.mouse_y)

        if mx < 0 or my > self.HEIGHT - 1:
            return False
        if mx > self.MOBILE_CTRL_RADIUS:
            return False
        if my < self.HEIGHT - 1 - self.MOBILE_CTRL_RADIUS:
            return False

        return self._point_in_circle(
            mx,
            my,
            float(self.MOBILE_CTRL_CX),
            float(self.MOBILE_CTRL_CY),
            float(self.MOBILE_CTRL_RADIUS),
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
        if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            return False
        return self._point_in_mobile_arc(
            float(pyxel.mouse_x),
            float(pyxel.mouse_y),
            float(self.MOBILE_LASER_ANGLE_START),
            float(self.MOBILE_LASER_ANGLE_END),
            float(self.MOBILE_RING_INNER_RADIUS),
            float(self.MOBILE_RING_OUTER_RADIUS),
        )

    def _is_mobile_bomb_pressed(self) -> bool:
        if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            return False
        return self._point_in_mobile_arc(
            float(pyxel.mouse_x),
            float(pyxel.mouse_y),
            float(self.MOBILE_BOMB_ANGLE_START),
            float(self.MOBILE_BOMB_ANGLE_END),
            float(self.MOBILE_RING_INNER_RADIUS),
            float(self.MOBILE_RING_OUTER_RADIUS),
        )

    def _update_mobile_action_buttons(self) -> None:
        laser_pressed = self._is_mobile_laser_pressed()
        bomb_pressed = self._is_mobile_bomb_pressed()

        if laser_pressed and not self.prev_mobile_laser_pressed:
            self._try_activate_homing_laser()

        if bomb_pressed and not self.prev_mobile_bomb_pressed:
            self._try_activate_bomb()

        self.prev_mobile_laser_pressed = laser_pressed
        self.prev_mobile_bomb_pressed = bomb_pressed

    def _update_touch_mode(self) -> None:
        touch_down = pyxel.btn(pyxel.MOUSE_BUTTON_LEFT)
        self.touch_active = touch_down

        if touch_down and not self.prev_touch_down:
            started_in_control = self._is_touch_in_mobile_control_area()
            self.touch_drag_active = not started_in_control
        elif not touch_down:
            self.touch_drag_active = False

        self.prev_touch_down = touch_down

    def _weapon_name(self, family: str | None = None) -> str:
        family = family or self.current_weapon_family
        return self.WEAPON_FAMILY_DATA.get(family, self.WEAPON_FAMILY_DATA[self.WEAPON_FAMILY_FAN])["name"]

    def _weapon_accent(self, family: str | None = None) -> int:
        family = family or self.current_weapon_family
        return self.WEAPON_FAMILY_DATA.get(family, self.WEAPON_FAMILY_DATA[self.WEAPON_FAMILY_FAN])["accent"]

    def _weapon_colors(self, family: str | None = None) -> tuple[int, int]:
        family = family or self.current_weapon_family
        data = self.WEAPON_FAMILY_DATA.get(family, self.WEAPON_FAMILY_DATA[self.WEAPON_FAMILY_FAN])
        return data["core"], data["outer"]

    def _current_weapon_level(self) -> int:
        return max(self.SHOT_LEVEL_SINGLE, self.weapon_levels.get(self.current_weapon_family, self.SHOT_LEVEL_SINGLE))

    def _set_weapon_level(self, family: str, level: int) -> None:
        self.weapon_levels[family] = max(self.SHOT_LEVEL_SINGLE, min(level, self.SHOT_LEVEL_MAX))

    def _weapon_damage_bonus(self, family: str | None = None) -> int:
        family = family or self.current_weapon_family
        return max(0, min(self.WEAPON_OVERDRIVE_CAP, self.weapon_overdrive_bonus.get(family, 0)))

    def _is_weapon_unlocked(self, family: str) -> bool:
        return family in self.unlocked_weapon_families

    def _locked_weapon_families(self) -> list[str]:
        return [family for family in self.WEAPON_FAMILY_ORDER if family not in self.unlocked_weapon_families]

    def _unlock_weapon_family(self, family: str, equip_now: bool = True) -> None:
        if family not in self.unlocked_weapon_families:
            self.unlocked_weapon_families.append(family)
        if self.weapon_levels.get(family, -1) < self.SHOT_LEVEL_SINGLE:
            self.weapon_levels[family] = self.SHOT_LEVEL_SINGLE
        if equip_now:
            self.current_weapon_family = family

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
        if self.current_weapon_family != self.WEAPON_FAMILY_BEAM:
            return self.shoot_interval_frames

        level = self._current_weapon_level()
        if level <= self.SHOT_LEVEL_TRIPLE:
            return self.shoot_interval_frames + 8
        return self.shoot_interval_frames + 10

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

    def _upgrade_weapon_family(self, family: str, switch_if_needed: bool = True) -> None:
        if not self._is_weapon_unlocked(family):
            self._unlock_weapon_family(family, equip_now=True)
            self._show_notice(
                label="WEAPON GET",
                title=f"{self._weapon_name(family)} UNLOCK",
                description=f"Now using {self._weapon_name(family)}",
                accent=self._weapon_accent(family),
                kind="shot_up",
            )
            self.shot_pick_flash_timer = self.TEA_FLASH_FRAMES
            return

        previous_family = self.current_weapon_family
        if switch_if_needed and family != self.current_weapon_family:
            self.current_weapon_family = family
            self._show_notice(
                label="WEAPON CHANGE",
                title=f"{self._weapon_name(family)} READY",
                description=f"Switched from {self._weapon_name(previous_family)}",
                accent=self._weapon_accent(family),
                kind="shot_up",
            )
            self.shot_pick_flash_timer = self.TEA_FLASH_FRAMES
            return

        if self.weapon_levels.get(family, self.SHOT_LEVEL_SINGLE) >= self.SHOT_LEVEL_MAX:
            next_bonus = min(self._weapon_damage_bonus(family) + 1, self.WEAPON_OVERDRIVE_CAP)
            current_bonus = self._weapon_damage_bonus(family)
            if next_bonus > current_bonus:
                self.weapon_overdrive_bonus[family] = next_bonus
                self.shot_pick_flash_timer = self.TEA_FLASH_FRAMES
                self._show_notice(
                    label="MAX POWER",
                    title=f"{self._weapon_name(family)} DRIVE",
                    description=f"ATK +{next_bonus}",
                    accent=self._weapon_accent(family),
                    kind="shot_up",
                )
            return

        next_level = min(self.weapon_levels.get(family, self.SHOT_LEVEL_SINGLE) + 1, self.SHOT_LEVEL_MAX)
        self._set_weapon_level(family, next_level)
        self.shot_pick_flash_timer = self.TEA_FLASH_FRAMES
        self._show_notice(
            label="SHOT UP",
            title=f"{self._weapon_name(family)} BOOST",
            description=f"Now {self._shot_level_name(next_level)}",
            accent=self._weapon_accent(family),
            kind="shot_up",
        )

    def _tea_drop_rate(self) -> float:
        return min(0.70, self.TEA_DROP_CHANCE + self.tea_drop_bonus)

    def _next_shot_level_name(self) -> str:
        next_level = min(self._current_weapon_level() + 1, self.SHOT_LEVEL_MAX)
        mapping = {
            self.SHOT_LEVEL_SINGLE: "1WAY",
            self.SHOT_LEVEL_DOUBLE: "2WAY",
            self.SHOT_LEVEL_TRIPLE: "3WAY",
            self.SHOT_LEVEL_POWER_SINGLE: "P-1WAY",
            self.SHOT_LEVEL_POWER_DOUBLE: "P-2WAY",
            self.SHOT_LEVEL_POWER_TRIPLE: "P-3WAY",
        }
        return mapping.get(next_level, "1WAY")

    def _reward_choice(self, reward_id: str) -> RewardChoice:
        if reward_id == "weapon_boost":
            return RewardChoice(
                reward_id=reward_id,
                title=f"{self._weapon_name()} BOOST",
                description=f"Shot level up to {self._next_shot_level_name()}",
                accent_color=self._weapon_accent(),
            )
        if reward_id.startswith("unlock_"):
            family = reward_id.split("_", 1)[1]
            return RewardChoice(
                reward_id=reward_id,
                title=f"UNLOCK {self._weapon_name(family)}",
                description=f"Unlock and switch to {self._weapon_name(family)}",
                accent_color=self._weapon_accent(family),
            )
        if reward_id == "max_hp":
            return RewardChoice(
                reward_id=reward_id,
                title="MAX HP UP",
                description="Max HP +1 and heal fully",
                accent_color=10,
            )
        if reward_id == "bomb_cap":
            next_cap = self._bomb_capacity() + 1
            return RewardChoice(
                reward_id=reward_id,
                title="BOMB CAP UP",
                description=f"Carry up to {next_cap} bombs",
                accent_color=9,
            )
        if reward_id == "move_up":
            next_speed = min(self.PLAYER_SPEED_CAP, self.player.speed_x + 1)
            return RewardChoice(
                reward_id=reward_id,
                title="MOVE UP",
                description=f"Move faster: speed {next_speed}",
                accent_color=12,
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
            )
        if reward_id == "item_rate":
            next_rate = int(round(min(0.70, self._tea_drop_rate() + self.TEA_DROP_BONUS_STEP) * 100))
            return RewardChoice(
                reward_id=reward_id,
                title="ITEM RATE UP",
                description=f"Weapon item rate: {next_rate}%",
                accent_color=3,
            )
        return RewardChoice(
            reward_id="max_hp",
            title="MAX HP UP",
            description="Max HP +1 and heal fully",
            accent_color=10,
        )

    def _eligible_reward_ids(self) -> list[str]:
        reward_ids = [
            "max_hp",
            "bomb_cap",
            "item_rate",
        ]

        if self._current_weapon_level() < self.SHOT_LEVEL_MAX:
            reward_ids.append("weapon_boost")
        for family in self._locked_weapon_families():
            reward_ids.append(f"unlock_{family}")
        if self.player.speed_x < self.PLAYER_SPEED_CAP or self.player.speed_y < self.PLAYER_SPEED_CAP:
            reward_ids.append("move_up")
        if self.laser_cooldown_frames > self.LASER_COOLDOWN_MIN:
            reward_ids.append("laser_tune")

        return reward_ids

    def _reward_weight(self, reward_id: str) -> float:
        loop_depth = max(0, self.boss_spawn_count)

        if reward_id == "weapon_boost":
            missing_levels = self.SHOT_LEVEL_MAX - self._current_weapon_level()
            return 2.8 + missing_levels * 1.25 + max(0.0, 1.2 - loop_depth * 0.18)
        if reward_id.startswith("unlock_"):
            family = reward_id.split("_", 1)[1]
            family_bias = {
                self.WEAPON_FAMILY_LANCE: 2.4,
                self.WEAPON_FAMILY_RAIN: 2.0,
                self.WEAPON_FAMILY_BEAM: 1.8,
            }
            return family_bias.get(family, 1.6) + max(0.0, 1.4 - loop_depth * 0.18)

        if reward_id == "max_hp":
            missing_hp = self.player.max_hp - self.player.hp
            low_hp_bonus = 3.2 if self.player.hp <= 1 else 0.0
            early_survival_bonus = max(0.0, (4 - self.player.max_hp) * 0.75)
            return 1.8 + missing_hp * 2.1 + low_hp_bonus + early_survival_bonus

        if reward_id == "bomb_cap":
            return max(0.9, 2.7 - self.bomb_bonus_cap * 0.55 + loop_depth * 0.16)

        if reward_id == "move_up":
            speed_gap = self.PLAYER_SPEED_CAP - max(self.player.speed_x, self.player.speed_y)
            return max(0.8, 1.5 + speed_gap * 0.72 - loop_depth * 0.08)

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

        if len(self.unlocked_weapon_families) == 1:
            for family in (self.WEAPON_FAMILY_LANCE, self.WEAPON_FAMILY_RAIN, self.WEAPON_FAMILY_BEAM):
                reward_id = f"unlock_{family}"
                if reward_id in reward_ids:
                    return reward_id

        if "weapon_boost" in reward_ids and self._current_weapon_level() <= self.SHOT_LEVEL_TRIPLE and self.boss_spawn_count <= 1:
            return "weapon_boost"

        return None

    def _build_reward_choices(self) -> list[RewardChoice]:
        pool = self._eligible_reward_ids()
        picks: list[str] = []

        guaranteed_id = self._guaranteed_reward_id(pool)
        if guaranteed_id is not None:
            picks.append(guaranteed_id)
            pool.remove(guaranteed_id)

        remaining = self.REWARD_OPTION_COUNT - len(picks)
        if remaining > 0:
            picks.extend(self._pick_weighted_reward_ids(pool, remaining))

        return [self._reward_choice(reward_id) for reward_id in picks[: self.REWARD_OPTION_COUNT]]

    def _start_reward_selection(self) -> None:
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.bullets.clear()
        self.bombs.clear()
        self.homing_lasers.clear()
        self.weapon_items.clear()
        self.heal_items.clear()
        self.reward_choices = self._build_reward_choices()
        self.reward_selection_index = 0
        self.phase = GamePhase.REWARD_SELECT

    def _apply_reward_choice(self, choice: RewardChoice) -> None:
        if choice.reward_id == "weapon_boost":
            self._upgrade_weapon_family(self.current_weapon_family, switch_if_needed=False)
        elif choice.reward_id.startswith("unlock_"):
            family = choice.reward_id.split("_", 1)[1]
            self._unlock_weapon_family(family, equip_now=True)
            self._show_notice(
                label="WEAPON GET",
                title=f"{self._weapon_name(family)} UNLOCK",
                description=f"Now using {self._weapon_name(family)}",
                accent=self._weapon_accent(family),
                kind="shot_up",
            )
        elif choice.reward_id == "max_hp":
            self.player.max_hp += 1
            self.player.hp = self.player.max_hp
        elif choice.reward_id == "bomb_cap":
            self.bomb_bonus_cap += 1
            self._restock_bombs_full()
        elif choice.reward_id == "move_up":
            self.player.speed_x = min(self.PLAYER_SPEED_CAP, self.player.speed_x + 1)
            self.player.speed_y = min(self.PLAYER_SPEED_CAP, self.player.speed_y + 1)
        elif choice.reward_id == "laser_tune":
            self.laser_cooldown_frames = max(
                self.LASER_COOLDOWN_MIN,
                self.laser_cooldown_frames - self.LASER_COOLDOWN_REWARD_STEP,
            )
            self.laser_cooldown = min(self.laser_cooldown, self.laser_cooldown_frames)
        elif choice.reward_id == "item_rate":
            self.tea_drop_bonus += self.TEA_DROP_BONUS_STEP

        if not choice.reward_id.startswith("unlock_") and choice.reward_id != "weapon_boost":
            self._show_notice(
                label="REWARD GET",
                title=choice.title,
                description=choice.description,
                accent=choice.accent_color,
                kind="reward",
            )
        self.reward_choices.clear()
        self.reward_selection_index = 0
        self.touch_active = False
        self.touch_drag_active = False
        self.prev_touch_down = pyxel.btn(pyxel.MOUSE_BUTTON_LEFT)
        self.boss_defeated = False
        self.spawn_timer = max(self.spawn_timer, 24)
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

        if level == self.SHOT_LEVEL_SINGLE:
            self._spawn_player_bullet(
                x=origin_x,
                y=origin_y,
                vx=0.0,
                vy=float(self.bullet_speed),
                damage=1 + bonus,
                radius=3,
                color_core=core_main,
                color_outer=outer_main,
                style="normal",
            )
            return

        if level == self.SHOT_LEVEL_DOUBLE:
            for vx, xoff in ((-0.90, -4.0), (0.90, 4.0)):
                self._spawn_player_bullet(
                    x=origin_x + xoff,
                    y=origin_y,
                    vx=vx,
                    vy=float(self.bullet_speed),
                    damage=1 + bonus,
                    radius=2,
                    color_core=11,
                    color_outer=3,
                    style="normal",
                )
            return

        if level == self.SHOT_LEVEL_TRIPLE:
            for vx, xoff, core, outer in ((-1.10, -6.0, 9, 4), (0.0, 0.0, core_main, outer_main), (1.10, 6.0, 9, 4)):
                self._spawn_player_bullet(
                    x=origin_x + xoff,
                    y=origin_y,
                    vx=vx,
                    vy=float(self.bullet_speed),
                    damage=1 + bonus,
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
                damage=2 + bonus,
                radius=4,
                color_core=7,
                color_outer=11,
                style="power_single",
            )
            return

        if level == self.SHOT_LEVEL_POWER_DOUBLE:
            for vx, xoff, radius in ((-0.82, -5.0, 4), (0.82, 5.0, 4)):
                self._spawn_player_bullet(
                    x=origin_x + xoff,
                    y=origin_y,
                    vx=vx,
                    vy=float(self.bullet_speed),
                    damage=3 + bonus,
                    radius=radius,
                    color_core=7,
                    color_outer=11,
                    style="power_double",
                )
            return

        for vx, xoff, radius, damage, style in (
            (-1.00, -7.0, 3, 3 + bonus, "power_triple"),
            (0.0, 0.0, 5, 5 + bonus, "power_single"),
            (1.00, 7.0, 3, 3 + bonus, "power_triple"),
        ):
            self._spawn_player_bullet(
                x=origin_x + xoff,
                y=origin_y,
                vx=vx,
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
                x=origin_x + xoff,
                y=origin_y,
                vx=vx,
                vy=speed,
                damage=damage + bonus,
                radius=radius,
                color_core=core,
                color_outer=outer,
                style=style,
            )

    def _fire_rain_shot(self, origin_x: float, origin_y: float, level: int) -> None:
        core, outer = self._weapon_colors(self.WEAPON_FAMILY_RAIN)
        bonus = self._weapon_damage_bonus(self.WEAPON_FAMILY_RAIN)
        speed = float(self.bullet_speed - 2.2)
        patterns = {
            self.SHOT_LEVEL_SINGLE: (-16.0, 0.0, 16.0),
            self.SHOT_LEVEL_DOUBLE: (-24.0, -8.0, 8.0, 24.0),
            self.SHOT_LEVEL_TRIPLE: (-30.0, -15.0, 0.0, 15.0, 30.0),
            self.SHOT_LEVEL_POWER_SINGLE: (-24.0, -8.0, 8.0, 24.0),
            self.SHOT_LEVEL_POWER_DOUBLE: (-32.0, -16.0, 0.0, 16.0, 32.0),
            self.SHOT_LEVEL_POWER_TRIPLE: (-40.0, -24.0, -8.0, 8.0, 24.0, 40.0),
        }
        damage = 1 + bonus
        radius = 2 if level <= self.SHOT_LEVEL_TRIPLE else 3
        style = "rain" if level <= self.SHOT_LEVEL_TRIPLE else "rain_power"
        growth = 0.13 if level <= self.SHOT_LEVEL_TRIPLE else 0.19
        max_radius = {
            self.SHOT_LEVEL_SINGLE: 4.0,
            self.SHOT_LEVEL_DOUBLE: 4.6,
            self.SHOT_LEVEL_TRIPLE: 5.3,
            self.SHOT_LEVEL_POWER_SINGLE: 6.1,
            self.SHOT_LEVEL_POWER_DOUBLE: 7.0,
            self.SHOT_LEVEL_POWER_TRIPLE: 7.8,
        }[level]
        max_life = {
            self.SHOT_LEVEL_SINGLE: 34,
            self.SHOT_LEVEL_DOUBLE: 34,
            self.SHOT_LEVEL_TRIPLE: 36,
            self.SHOT_LEVEL_POWER_SINGLE: 38,
            self.SHOT_LEVEL_POWER_DOUBLE: 40,
            self.SHOT_LEVEL_POWER_TRIPLE: 42,
        }[level]

        for idx, xoff in enumerate(patterns[level]):
            vx = -0.85 if idx % 2 == 0 else 0.85
            self._spawn_player_bullet(
                x=origin_x + xoff,
                y=origin_y - abs(xoff) * 0.30,
                vx=vx,
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
        patterns = {
            self.SHOT_LEVEL_SINGLE: ((0.0, 0.0),),
            self.SHOT_LEVEL_DOUBLE: ((-0.78, -9.0), (0.78, 9.0)),
            self.SHOT_LEVEL_TRIPLE: ((-1.18, -18.0), (-0.38, -6.0), (0.38, 6.0), (1.18, 18.0)),
            self.SHOT_LEVEL_POWER_SINGLE: ((0.0, 0.0),),
            self.SHOT_LEVEL_POWER_DOUBLE: ((-0.84, -10.0), (0.84, 10.0)),
            self.SHOT_LEVEL_POWER_TRIPLE: ((-1.24, -20.0), (-0.42, -7.0), (0.42, 7.0), (1.24, 20.0)),
        }
        damage = (2 if level <= self.SHOT_LEVEL_TRIPLE else 3) + bonus
        radius = 2 if level <= self.SHOT_LEVEL_TRIPLE else 3
        style = "beam_arc" if level <= self.SHOT_LEVEL_TRIPLE else "beam_arc_power"
        life = 78 if level <= self.SHOT_LEVEL_TRIPLE else 88

        for vx, xoff in patterns[level]:
            spread_scale = random.uniform(0.94, 1.10)
            vx_jitter = random.uniform(-0.05, 0.05)
            xoff_jitter = random.uniform(-1.5, 1.5)
            self._spawn_player_bullet(
                x=origin_x + xoff + xoff_jitter,
                y=origin_y,
                vx=vx * spread_scale + vx_jitter,
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

    def _fire_current_shot(self) -> None:
        origin_x = float(self.player.x)
        origin_y = float(self.player.y - self.PLAYER_HALF_H - 6)
        level = self._current_weapon_level()
        family = self.current_weapon_family

        if family == self.WEAPON_FAMILY_LANCE:
            self._fire_lance_shot(origin_x, origin_y, level)
            return
        if family == self.WEAPON_FAMILY_RAIN:
            self._fire_rain_shot(origin_x, origin_y, level)
            return
        if family == self.WEAPON_FAMILY_BEAM:
            self._fire_beam_shot(origin_x, origin_y, level)
            return

        self._fire_fan_shot(origin_x, origin_y, level)

    def _maybe_spawn_weapon_item(self, x: float, y: float) -> None:
        if random.random() > self._tea_drop_rate():
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
    ) -> bool:
        if len(self.enemy_bullets) >= self.ENEMY_BULLET_MAX_COUNT:
            return False

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
            or self.score >= self.next_boss_score_threshold
        )

    def _start_boss_intro(self) -> None:
        self.boss_event_started = True
        self.boss_intro_timer = self.BOSS_WARNING_TIME

        self.enemies.clear()
        self.enemy_bullets.clear()
        self.bullets.clear()
        self.bombs.clear()
        self.homing_lasers.clear()
        self.weapon_items.clear()
        self.heal_items.clear()

    def _spawn_boss(self) -> None:
        self.boss = spawn_boss(
            width=self.WIDTH,
            entry_target_y=float(self.BOSS_ENTRY_TARGET_Y),
            max_hp=self.BOSS_MAX_HP,
            spawn_count=self.boss_spawn_count,
        )
        self.boss_hp_display = float(self.boss.max_hp)
        self.boss_hp_trail = float(self.boss.max_hp)
        self.boss_hp_shake_timer = 0
        self.boss_hp_flash_timer = 0

    def _advance_boss_progression(self) -> None:
        self.boss_spawn_count += 1
        self.next_boss_kill_threshold += self.BOSS_TRIGGER_KILLS
        self.next_boss_score_threshold += (self.boss_spawn_count + 1) * 1000
        self.spawn_interval_sec = max(0.28, self.spawn_interval_sec - 0.04)

    def _update_boss_intro(self) -> None:
        if self.boss_intro_timer <= 0:
            return
        self.boss_intro_timer -= 1
        if self.boss_intro_timer <= 0 and self.boss is None:
            self._spawn_boss()

    def _update_boss_hp_bar_fx(self) -> None:
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

        update_boss(
            boss=self.boss,
            frame_count=self.frame_count,
            width=self.WIDTH,
            height=self.HEIGHT,
            side_margin=self.SIDE_MARGIN,
            boss_sprite_w=self.BOSS_SPRITE_W,
            player_x=float(self.player.x),
            player_y=float(self.player.y),
            append_enemy_bullet=self._append_enemy_bullet,
            spawn_count=self.boss_spawn_count,
            enemies=self.enemies,
            create_enemy=self._create_enemy,
        )

    def _on_boss_defeated(self) -> None:
        if self.boss is None:
            return

        boss = self.boss
        self.score += self.BOSS_SCORE_VALUE
        self.player.hp = self.player.max_hp
        self.enemy_bullets.clear()
        self._restock_bombs_full()

        burst_scale = self._boss_burst_scale(boss)
        self._spawn_enemy_burst(boss.x, boss.y, scale=burst_scale)
        self._spawn_enemy_burst(boss.x - 18, boss.y + 6, scale=burst_scale * 0.74)
        self._spawn_enemy_burst(boss.x + 20, boss.y - 8, scale=burst_scale * 0.68)

        self.boss = None
        self.boss_event_started = False
        self.boss_defeated = True
        self._advance_boss_progression()
        self._start_reward_selection()

    def _laser_origin(self, boss: Boss) -> tuple[float, float]:
        return boss.x, boss.y + 4.0

    def _laser_dir(self, boss: Boss) -> tuple[float, float]:
        angle = getattr(boss, "laser_angle", math.pi / 2)
        return math.cos(angle), math.sin(angle)

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

    def update(self) -> None:
        self.frame_count += 1

        self._update_stars()
        self._update_background_fireworks()
        self.effects.update()
        self._update_boss_hp_bar_fx()
        self._update_ui_timers()

        if self.phase == GamePhase.START:
            self._update_start_input()
            return

        if self.phase == GamePhase.GAME_OVER:
            self._update_retry_input()
            return

        if self.phase == GamePhase.REWARD_SELECT:
            self._update_reward_select_input()
            return

        self._update_player_state()
        self._update_touch_mode()
        self._update_player_input()
        self._update_shooting()
        self._update_special_input()

        if self.boss_intro_timer > 0:
            self._update_boss_intro()
        else:
            if self._is_boss_active():
                self._update_boss()
            else:
                self._update_spawning()
                self._update_enemies()

        self._update_bullets()
        self._update_enemy_bullets()
        self._update_bombs()
        self._update_homing_lasers()
        self._update_weapon_items()
        self._update_heal_items()

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

        self._handle_player_enemy_collisions()
        self._handle_player_boss_collisions()
        self._handle_player_enemy_bullet_collisions()

        if self._boss_laser_hits_player():
            self._apply_player_damage(1)

        if self.player.hp <= 0:
            self.phase = GamePhase.GAME_OVER
            return

        if self._should_trigger_boss():
            self._start_boss_intro()

    def _update_start_input(self) -> None:
        if pyxel.btnp(pyxel.KEY_UP):
            self.start_menu_focus = max(0, self.start_menu_focus - 1)
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.start_menu_focus = min(1, self.start_menu_focus + 1)

        if pyxel.btnp(pyxel.KEY_LEFT):
            if self.start_menu_focus == 0:
                self._move_theme_selection(-1)
            else:
                self._move_start_weapon_selection(-1)
        elif pyxel.btnp(pyxel.KEY_RIGHT):
            if self.start_menu_focus == 0:
                self._move_theme_selection(1)
            else:
                self._move_start_weapon_selection(1)

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            mx = float(pyxel.mouse_x)
            my = float(pyxel.mouse_y)

            selector_x = 46
            selector_y = (self.HEIGHT - 300) // 2 + 100
            selector_w = 268
            selector_h = 54
            weapon_selector_y = selector_y + 64

            start_box_w = 280
            start_box_h = 34
            start_box_x = (self.WIDTH - start_box_w) // 2
            start_box_y = (self.HEIGHT - 300) // 2 + 238

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
            if self._point_in_rect(mx, my, start_box_x, start_box_y, start_box_w, start_box_h):
                self._reset_play_state()
                self.phase = GamePhase.PLAYING
                return

        wants_start = pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE)
        if wants_start:
            self._reset_play_state()
            self.phase = GamePhase.PLAYING

    def _update_retry_input(self) -> None:
        wants_retry = (
            pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.KEY_SPACE)
            or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
        )
        if wants_retry:
            self._reset_play_state()
            self.phase = GamePhase.PLAYING

    def _update_reward_select_input(self) -> None:
        if not self.reward_choices:
            self.phase = GamePhase.PLAYING
            return

        if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_UP):
            self.reward_selection_index = (self.reward_selection_index - 1) % len(self.reward_choices)
        elif pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_DOWN):
            self.reward_selection_index = (self.reward_selection_index + 1) % len(self.reward_choices)

        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
            self._apply_reward_choice(self.reward_choices[self.reward_selection_index])
            return

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            mx = float(pyxel.mouse_x)
            my = float(pyxel.mouse_y)
            for idx, _choice in enumerate(self.reward_choices):
                box_y = self.REWARD_BOX_START_Y + idx * (self.REWARD_BOX_H + self.REWARD_BOX_GAP)
                if self._point_in_rect(mx, my, self.REWARD_BOX_X, box_y, self.REWARD_BOX_W, self.REWARD_BOX_H):
                    self.reward_selection_index = idx
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

    def _update_stars(self) -> None:
        for star in self.stars:
            star[1] += star[2]
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
        left_bound = self.SIDE_MARGIN
        right_bound = self.WIDTH - self.SIDE_MARGIN
        top_bound = self.PLAYER_MIN_Y
        bottom_bound = self.PLAYER_MAX_Y

        if pyxel.btn(pyxel.KEY_LEFT):
            self.player.x -= self.player.speed_x
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.player.x += self.player.speed_x
        if pyxel.btn(pyxel.KEY_UP):
            self.player.y -= self.player.speed_y
        if pyxel.btn(pyxel.KEY_DOWN):
            self.player.y += self.player.speed_y

        if self.touch_drag_active:
            self.player.x = float(pyxel.mouse_x)
            self.player.y = float(pyxel.mouse_y)

        self.player.x = min(max(self.player.x, left_bound), right_bound)
        self.player.y = min(max(self.player.y, top_bound), bottom_bound)

    def _update_shooting(self) -> None:
        wants_fire = pyxel.btn(pyxel.KEY_RETURN) or self.touch_drag_active

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
                life=110,
                max_life=110,
                radius=30.0,
                expansion=128.0,
                rotation=0.0,
                rotation_speed=0.07,
                damage_interval=4,
                damage_timer=0,
            )
        )
        self.bomb_stock -= 1

    def _try_activate_homing_laser(self) -> None:
        if self.laser_cooldown > 0:
            return
        if len(self.homing_lasers) >= self.laser_active_limit:
            return

        laser_speed = 5.2
        laser_x = float(self.player.x)
        laser_y = float(self.player.y - self.PLAYER_HALF_H - 10)

        self.homing_lasers.append(
            HomingLaser(
                x=laser_x,
                y=laser_y,
                vx=0.0,
                vy=-laser_speed,
                speed=laser_speed,
                turn_rate=0.022,
                life=180,
                max_life=180,
                radius=6,
                band_width=7,
                damage=2,
                trail=[(laser_x, laser_y)],
            )
        )
        self.laser_cooldown = self.laser_cooldown_frames

    def _create_enemy(self, spawn_x: float, enemy_type: str) -> Enemy:
        return create_enemy(
            spawn_x=spawn_x,
            enemy_type=enemy_type,
            enemy_half_h=float(self.ENEMY_HALF_H),
            enemy_half_w=float(self.ENEMY_HALF_W),
        )

    def _update_spawning(self) -> None:
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            spawn_x = float(pyxel.rndi(self.SIDE_MARGIN, self.WIDTH - self.SIDE_MARGIN))
            enemy_type = pick_enemy_type(self.score)
            self.enemies.append(self._create_enemy(spawn_x, enemy_type))
            self.spawn_timer = int(60 * self.spawn_interval_sec)

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
        return bomb.radius + bomb.expansion * progress

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

                continue

            if bomb.life <= 0:
                bomb.active = False
                continue

            progress = 1.0 - (bomb.life / bomb.max_life)
            current_radius = self._bomb_current_radius(bomb)

            bomb.rotation += bomb.rotation_speed
            bomb.particle_points = radiating_sphere_projection_burst(
                complex(bomb.x, bomb.y),
                r=current_radius * 0.36,
                num_particles=96,
                expansion_rate=current_radius * 0.64,
                life_ratio=progress,
                rotation_angle=bomb.rotation,
            )

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

    def _find_enemy_by_id(self, enemy_id: int | None) -> Enemy | None:
        if enemy_id is None:
            return None
        for enemy in self.enemies:
            if id(enemy) == enemy_id:
                return enemy
        return None

    def _find_homing_target(self, laser: HomingLaser) -> Enemy | Boss | None:
        if laser.target_id is not None and laser.reacquire_timer > 0:
            if self._is_boss_active() and id(self.boss) == laser.target_id:
                return self.boss

            existing = self._find_enemy_by_id(laser.target_id)
            if existing is not None and existing.y <= laser.y + 24:
                return existing

        best_target: Enemy | Boss | None = None
        best_score = float("inf")

        if self._is_boss_active():
            boss = self.boss
            if boss is not None and boss.y <= laser.y + 36:
                dx = boss.x - laser.x
                dy = boss.y - laser.y
                dist2 = dx * dx + dy * dy
                best_score = dist2
                best_target = boss

        for enemy in self.enemies:
            if enemy.y > laser.y + 24:
                continue
            dx = enemy.x - laser.x
            dy = enemy.y - laser.y
            dist2 = dx * dx + dy * dy
            if dist2 < best_score:
                best_score = dist2
                best_target = enemy

        if best_target is not None:
            laser.target_id = id(best_target)
            laser.reacquire_timer = 18

        return best_target

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

            target = self._find_homing_target(laser)
            current_angle = math.atan2(laser.vy, laser.vx)

            if target is not None:
                dx = target.x - laser.x
                dy = target.y - laser.y
                desired_angle = math.atan2(dy, dx)
                desired_angle = self._clamp_laser_angle(desired_angle)

                diff = self._wrap_angle(desired_angle - current_angle)
                diff = max(-laser.turn_rate, min(laser.turn_rate, diff))
                next_angle = self._clamp_laser_angle(current_angle + diff)
            else:
                next_angle = self._clamp_laser_angle(current_angle)

            laser.vx = math.cos(next_angle) * laser.speed
            laser.vy = math.sin(next_angle) * laser.speed

            laser.x += laser.vx
            laser.y += laser.vy
            laser.trail.append((laser.x, laser.y))
            if len(laser.trail) > 18:
                laser.trail = laser.trail[-18:]

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
            if e.y <= self.HEIGHT + (self.ENEMY_HALF_H * e.display_scale) and e.active
        ]

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

    def _handle_projectile_cancellations(self) -> None:
        for bullet in self.bullets[:]:
            if bullet.ignores_cancel:
                continue
            for enemy_bullet in self.enemy_bullets[:]:
                if self._circles_overlap(
                    bullet.x, bullet.y, bullet.radius,
                    enemy_bullet.x, enemy_bullet.y, enemy_bullet.radius,
                ):
                    self._maybe_spawn_heal_item(enemy_bullet.x, enemy_bullet.y)
                    if enemy_bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(enemy_bullet)
                    if bullet.piercing and bullet.style.startswith("beam_arc"):
                        continue
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

        for bomb in self.bombs:
            cancel_r = 8.0 if bomb.phase == "launch" else self._bomb_current_radius(bomb) * 0.92
            if cancel_r <= 0:
                continue

            for enemy_bullet in self.enemy_bullets[:]:
                if self._circles_overlap(
                    bomb.x, bomb.y, cancel_r,
                    enemy_bullet.x, enemy_bullet.y, enemy_bullet.radius,
                ):
                    self._maybe_spawn_heal_item(enemy_bullet.x, enemy_bullet.y)
                    if enemy_bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(enemy_bullet)

        for laser in self.homing_lasers:
            for enemy_bullet in self.enemy_bullets[:]:
                if self._laser_hits_enemy_bullet(laser, enemy_bullet):
                    self._maybe_spawn_heal_item(enemy_bullet.x, enemy_bullet.y)
                    if enemy_bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(enemy_bullet)

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
        return (
            bullet.x - hit_r < boss.x + boss.hit_half_w
            and bullet.x + hit_r > boss.x - boss.hit_half_w
            and bullet.y - hit_r < boss.y + boss.hit_half_h
            and bullet.y + hit_r > boss.y - boss.hit_half_h
        )

    def _point_hits_enemy(self, x: float, y: float, radius: int, enemy: Enemy) -> bool:
        return (
            x - radius < enemy.x + enemy.hit_half_w
            and x + radius > enemy.x - enemy.hit_half_w
            and y - radius < enemy.y + enemy.hit_half_h
            and y + radius > enemy.y - enemy.hit_half_h
        )

    def _point_hits_boss(self, x: float, y: float, radius: int, boss: Boss) -> bool:
        return (
            x - radius < boss.x + boss.hit_half_w
            and x + radius > boss.x - boss.hit_half_w
            and y - radius < boss.y + boss.hit_half_h
            and y + radius > boss.y - boss.hit_half_h
        )

    def _is_laser_hitting_enemy(self, laser: HomingLaser, enemy: Enemy) -> bool:
        sampled_points = laser.trail[-10::2]
        return any(self._point_hits_enemy(px, py, laser.band_width, enemy) for px, py in sampled_points)

    def _is_laser_hitting_boss(self, laser: HomingLaser, boss: Boss) -> bool:
        sampled_points = laser.trail[-10::2]
        return any(self._point_hits_boss(px, py, laser.band_width, boss) for px, py in sampled_points)

    def _is_enemy_hitting_player(self, enemy: Enemy) -> bool:
        return (
            self.player.x - self.PLAYER_HALF_W < enemy.x + enemy.hit_half_w
            and self.player.x + self.PLAYER_HALF_W > enemy.x - enemy.hit_half_w
            and self.player.y - self.PLAYER_HALF_H < enemy.y + enemy.hit_half_h
            and self.player.y + self.PLAYER_HALF_H > enemy.y - enemy.hit_half_h
        )

    def _is_boss_hitting_player(self, boss: Boss) -> bool:
        return (
            self.player.x - self.PLAYER_HALF_W < boss.x + boss.hit_half_w
            and self.player.x + self.PLAYER_HALF_W > boss.x - boss.hit_half_w
            and self.player.y - self.PLAYER_HALF_H < boss.y + boss.hit_half_h
            and self.player.y + self.PLAYER_HALF_H > boss.y - boss.hit_half_h
        )

    def _is_enemy_bullet_hitting_player(self, bullet: EnemyBullet) -> bool:
        return (
            bullet.x - bullet.radius < self.player.x + self.PLAYER_HALF_W
            and bullet.x + bullet.radius > self.player.x - self.PLAYER_HALF_W
            and bullet.y - bullet.radius < self.player.y + self.PLAYER_HALF_H
            and bullet.y + bullet.radius > self.player.y - self.PLAYER_HALF_H
        )

    def _damage_enemy(
        self,
        enemy: Enemy,
        amount: int,
        source: str = "shot",
        hit_vx: float = 0.0,
        hit_vy: float = -1.0,
    ) -> None:
        enemy.hp -= amount
        enemy.was_hit = True
        enemy.hit_flash_timer = max(enemy.hit_flash_timer, 4)

        if enemy.hp <= 0:
            self.score += enemy.score_value
            self.enemy_kill_count += 1
            self._spawn_enemy_burst(enemy.x, enemy.y, scale=self._enemy_burst_scale_from_enemy(enemy))
            self._maybe_spawn_weapon_item(enemy.x, enemy.y)
            if enemy in self.enemies:
                self.enemies.remove(enemy)
            return

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

        if amount > 0:
            self._trigger_boss_hp_bar_hit_fx()

        boss.hp -= amount
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
            dx = self.boss.x - bomb.x
            dy = self.boss.y - bomb.y
            boss_extent = max(self.boss.hit_half_w, self.boss.hit_half_h)
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

                self._damage_enemy(enemy, laser.damage, source="laser", hit_vx=laser.vx, hit_vy=laser.vy)
                laser.hit_cooldowns[enemy_key] = 8

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

            if self.boss is None:
                break

    def _apply_player_damage(self, damage: int) -> None:
        if self.player.invincible_timer > 0:
            return
        self.player.hp -= damage
        self.player.invincible_timer = self.PLAYER_INVINCIBLE_FRAMES
        self.player.is_hit = True

    def _handle_player_enemy_collisions(self) -> None:
        for enemy in self.enemies[:]:
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
            self._apply_player_damage(bullet.damage)
            if bullet in self.enemy_bullets:
                self.enemy_bullets.remove(bullet)
            break

    def draw(self) -> None:
        pyxel.cls(self.play_bg_color)

        self._draw_background()
        self._draw_background_fireworks()
        self._draw_frame()
        self._draw_boss_dash_telegraph()
        self._draw_boss_laser()
        self._draw_bombs()
        self._draw_enemies()
        self._draw_boss()
        self._draw_enemy_bullets()
        self._draw_weapon_items()
        self._draw_heal_items()
        self._draw_bullets()
        self._draw_homing_lasers()
        self._draw_effects()
        self._draw_player()
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

    def _draw_background(self) -> None:
        for x, y, _, color in self.stars:
            pyxel.pset(x, y, color)

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

    def _draw_mobile_controls(self) -> None:
        if self.phase != GamePhase.PLAYING:
            return

        fill_color = 1
        border_color = 5
        if self._is_touch_in_mobile_control_area() and (self.frame_count // 3) % 2 == 0:
            fill_color = 2
            border_color = 7

        pyxel.circ(self.MOBILE_CTRL_CX, self.MOBILE_CTRL_CY, self.MOBILE_RING_OUTER_RADIUS + 4, fill_color)
        pyxel.circb(self.MOBILE_CTRL_CX, self.MOBILE_CTRL_CY, self.MOBILE_RING_OUTER_RADIUS + 4, border_color)
        pyxel.circ(self.MOBILE_CTRL_CX, self.MOBILE_CTRL_CY, self.MOBILE_RING_OUTER_RADIUS, 8)
        pyxel.circb(self.MOBILE_CTRL_CX, self.MOBILE_CTRL_CY, self.MOBILE_RING_OUTER_RADIUS, 6)

        self._draw_mobile_laser_button()
        self._draw_mobile_bomb_button()
        pyxel.circ(self.MOBILE_CTRL_CX, self.MOBILE_CTRL_CY, self.MOBILE_RING_INNER_RADIUS, self.play_bg_color)
        pyxel.circb(self.MOBILE_CTRL_CX, self.MOBILE_CTRL_CY, self.MOBILE_RING_INNER_RADIUS, 5)

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
        subtitle: str,
        value: str,
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

        title_x = label_x - len(title) * 2
        subtitle_x = label_x - len(subtitle) * 2
        value_x = label_x - len(value) * 2
        pyxel.text(title_x, label_y - 12, title, text)
        pyxel.text(subtitle_x, label_y - 1, subtitle, text)
        pyxel.text(value_x, label_y + 10, value, 1 if pressed else 7)

    def _draw_mobile_laser_button(self) -> None:
        ready = self.laser_cooldown <= 0 and len(self.homing_lasers) < self.laser_active_limit
        pressed = self._is_mobile_laser_pressed()

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

        self._draw_mobile_arc_button(
            angle_start=self.MOBILE_LASER_ANGLE_START,
            angle_end=self.MOBILE_LASER_ANGLE_END,
            fill=fill,
            border=border,
            title="LASER",
            subtitle="SHOT",
            value="READY" if self.laser_cooldown <= 0 else f"WAIT {self.laser_cooldown:02d}",
            pressed=pressed,
            text=text,
        )

    def _draw_mobile_bomb_button(self) -> None:
        ready = self.bomb_stock > 0 and len(self.bombs) < self.bomb_active_limit
        pressed = self._is_mobile_bomb_pressed()

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

        self._draw_mobile_arc_button(
            angle_start=self.MOBILE_BOMB_ANGLE_START,
            angle_end=self.MOBILE_BOMB_ANGLE_END,
            fill=fill,
            border=border,
            title="BOMB",
            subtitle="",
            value=f"STOCK {self.bomb_stock}",
            pressed=pressed,
            text=text,
        )

    def _draw_player(self) -> None:
        blink = True if self.phase == GamePhase.START else (not self.player.is_hit or (self.frame_count // 3) % 2 == 0)
        if not blink:
            return

        x = int(self.player.x)
        y = int(self.player.y)

        pyxel.rect(x - 6, y - 5, 12, 10, 12)
        pyxel.line(x, y - 10, x - 4, y - 2, 7)
        pyxel.line(x, y - 10, x + 4, y - 2, 7)
        pyxel.line(x - 10, y + 3, x - 3, y + 1, 6)
        pyxel.line(x + 10, y + 3, x + 3, y + 1, 6)
        pyxel.rect(x - 1, y - 2, 2, 3, 10)

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

    def _draw_heal_items(self) -> None:
        for item in self.heal_items:
            ix = int(item.x)
            iy = int(item.y)

            pyxel.circ(ix, iy, 7, 13)
            pyxel.circb(ix, iy, 7, 7)
            pyxel.circ(ix - 2, iy - 1, 3, 8)
            pyxel.circ(ix + 2, iy - 1, 3, 8)
            pyxel.tri(ix - 6, iy, ix + 6, iy, ix, iy + 7, 8)
            pyxel.pset(ix, iy + 2, 7)

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
            mid_r = max(1, int(current_radius * 0.68))
            inner_r = max(1, int(current_radius * 0.42))

            pyxel.circb(center_x, center_y, outer_r, outer_color)
            pyxel.circb(center_x, center_y, mid_r, mid_color)
            pyxel.circb(center_x, center_y, inner_r, inner_color)

            points = bomb.particle_points
            for idx, pt in enumerate(points):
                x = int(pt.real)
                y = int(pt.imag)

                if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
                    pyxel.pset(x, y, outer_color)
                    if idx % 10 == 0 and x + 1 < self.WIDTH:
                        pyxel.pset(x + 1, y, mid_color)

            for idx in range(0, len(points) - 12, 12):
                p1 = points[idx]
                p2 = points[idx + 6]
                pyxel.line(int(p1.real), int(p1.imag), int(p2.real), int(p2.imag), mid_color)

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
                    width = max(2, laser.band_width - 3)
                elif ratio < 0.70:
                    width = max(3, laser.band_width - 1)
                else:
                    width = laser.band_width
                self._draw_thick_segment(x0, y0, x1, y1, width)

    def _draw_effects(self) -> None:
        self.effects.draw()

    def _get_enemy_sprite_uv(self, enemy: Enemy) -> tuple[int, int]:
        column = self.ENEMY_SPRITE_COLUMNS.get(enemy.enemy_type, 0)
        frame = (self.frame_count // 6) % self.ENEMY_SPRITE_FRAMES
        u = column * self.ENEMY_SPRITE_SIZE
        v = frame * self.ENEMY_SPRITE_SIZE
        return u, v

    def _draw_enemy_sprite(self, enemy: Enemy) -> None:
        if enemy.was_hit and (self.frame_count // 2) % 2 == 0:
            return

        u, v = self._get_enemy_sprite_uv(enemy)
        draw_w = self.ENEMY_SPRITE_SIZE * enemy.display_scale
        draw_h = self.ENEMY_SPRITE_SIZE * enemy.display_scale
        x = int(enemy.x - draw_w / 2)
        y = int(enemy.y - draw_h / 2)

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
            pyxel.rect(ex, ey, fill_w, bar_h, 11)

    def _draw_enemies(self) -> None:
        for enemy in self.enemies:
            self._draw_enemy_sprite(enemy)
            self._draw_enemy_hp_bar(enemy)

    def _draw_boss(self) -> None:
        if self.boss is None:
            return

        boss = self.boss

        frame = (self.frame_count // 6) % self.BOSS_SPRITE_FRAMES
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
            aura_color = 12 if (self.frame_count // 4) % 2 == 0 else 7
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

        self._draw_boss_hp_bar()

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

    def _draw_boss_warning(self) -> None:
        if (self.frame_count // 8) % 2 != 0:
            return

        warning = "WARNING"
        sub = "BOSS APPROACH"

        warning_scale = 4
        sub_scale = 2

        warning_x = (self.WIDTH - big_text_width(warning, warning_scale)) // 2
        sub_x = (self.WIDTH - big_text_width(sub, sub_scale)) // 2
        center_y = self.HEIGHT // 2 - 40

        draw_big_text(warning_x, center_y, warning, warning_scale, 8, shadow_color=1)
        draw_big_text(sub_x, center_y + 42, sub, sub_scale, 7, shadow_color=1)

    def _draw_hud(self) -> None:
        pyxel.rect(0, 0, self.WIDTH, self.HUD_H, self.hud_bg_color)

        pyxel.text(8, 6, "SCORE", 15)
        draw_big_text(8, 18, f"{self.score:07d}", 2, 7, shadow_color=1)

        pyxel.text(170, 6, "HP", 15)
        draw_big_text(170, 14, f"{self.player.hp}", 3, 10, shadow_color=1)

        pyxel.text(246, 6, "KILL", 15)
        draw_big_text(246, 14, f"{self.enemy_kill_count:03d}", 3, 12, shadow_color=1)

        draw_big_text(8, 52, "MOVE", 1, 13, shadow_color=1)
        draw_big_text(52, 52, "ARROWS/DRAG", 1, 7, shadow_color=1)

        draw_big_text(182, 52, "SHOT", 1, 13, shadow_color=1)
        draw_big_text(222, 52, "ENTER/TOUCH", 1, 7, shadow_color=1)

        bomb_label_color = 10 if self.bomb_restock_flash_timer <= 0 else 7
        bomb_value_color = 7 if self.bomb_restock_flash_timer <= 0 else 10
        laser_text_color = 7

        draw_big_text(8, 74, "BOMB", 1, bomb_label_color, shadow_color=1)
        draw_big_text(52, 74, f"C {self.bomb_stock}/{self._bomb_capacity()}", 1, bomb_value_color, shadow_color=1)

        laser_status = "READY" if self.laser_cooldown <= 0 else f"WAIT{self.laser_cooldown:02d}"
        draw_big_text(182, 74, "WEAPON", 1, 11 if self.shot_pick_flash_timer > 0 else 13, shadow_color=1)
        self._draw_weapon_meter(248, 76)

        draw_big_text(8, 92, "LASER", 1, 13, shadow_color=1)
        draw_big_text(
            60,
            92,
            f"X {laser_status} {len(self.homing_lasers)}/{self.laser_active_limit}",
            1,
            laser_text_color,
            shadow_color=1,
        )

    def _draw_weapon_meter(self, x: int, y: int) -> None:
        filled = self._current_weapon_level() + 1
        block_w = 12
        block_h = 10
        gap = 4
        accent = self._weapon_accent() if self.shot_pick_flash_timer <= 0 or (self.frame_count // 3) % 2 != 0 else 15

        for idx in range(6):
            bx = x + idx * (block_w + gap)
            active = idx < filled
            if active:
                fill = accent if idx >= 3 else self._weapon_colors()[0]
                border = 7
            else:
                fill = 1
                border = 5

            pyxel.rect(bx, y, block_w, block_h, fill)
            pyxel.rectb(bx, y, block_w, block_h, border)

        pyxel.text(x, y + 13, self._weapon_name(), self._weapon_accent())

    def _draw_reward_notice(self) -> None:
        if self.reward_notice_timer <= 0 or self.phase != GamePhase.PLAYING:
            return

        elapsed = self.REWARD_NOTICE_FRAMES - self.reward_notice_timer
        intro = min(1.0, elapsed / self.REWARD_CUTIN_IN_FRAMES)
        outro = min(1.0, self.reward_notice_timer / self.REWARD_CUTIN_OUT_FRAMES)
        visibility = min(intro, outro)
        eased = 1.0 - (1.0 - visibility) ** 3

        panel_w = self.REWARD_CUTIN_W
        panel_h = self.REWARD_CUTIN_H
        slant = self.REWARD_CUTIN_SLANT
        target_x = 8
        start_x = -panel_w - slant - 36
        box_x = int(start_x + (target_x - start_x) * eased)
        box_y = self.REWARD_CUTIN_Y
        accent = self.reward_notice_accent

        pulse = (self.frame_count // 3) % 2 == 0
        flash_x = box_x - 40 + ((elapsed * 11) % (panel_w + 96))

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

        pyxel.rect(box_x, box_y, panel_w - slant, panel_h, 10)
        pyxel.tri(
            box_x + panel_w - slant,
            box_y,
            box_x + panel_w,
            box_y,
            box_x + panel_w - slant,
            box_y + panel_h,
            10,
        )

        pyxel.rect(box_x, box_y + panel_h - 16, panel_w - slant, 16, 9)
        pyxel.tri(
            box_x + panel_w - slant,
            box_y + panel_h - 16,
            box_x + panel_w,
            box_y + panel_h - 16,
            box_x + panel_w - slant,
            box_y + panel_h,
            9,
        )

        pyxel.line(box_x, box_y, box_x + panel_w - slant, box_y, 7)
        pyxel.line(box_x, box_y + panel_h - 1, box_x + panel_w - slant, box_y + panel_h - 1, 1)
        pyxel.line(box_x + panel_w - slant, box_y, box_x + panel_w, box_y, 7)
        pyxel.line(box_x + panel_w - slant, box_y + panel_h - 1, box_x + panel_w - slant, box_y + panel_h - 1, 1)
        pyxel.line(box_x, box_y, box_x, box_y + panel_h - 1, 1)
        pyxel.line(box_x + panel_w - slant, box_y, box_x + panel_w - slant, box_y + panel_h - 1, 1)
        pyxel.line(box_x + panel_w, box_y, box_x + panel_w - slant, box_y + panel_h - 1, 1)

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
        pyxel.text(box_x + 14, box_y + 12, self.reward_notice_label, 10)

        if self.reward_notice_kind == "shot_up":
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

        title_color = 0 if pulse else 1
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

            draw_big_text(box_x + 40, box_y + 18, choice.title, 2, title_color, shadow_color=1)
            draw_big_text(box_x + 40, box_y + 52, choice.description, 1, desc_color, shadow_color=1)

        footer = "ENTER / SPACE TO CONFIRM"
        footer_x = (self.WIDTH - big_text_width(footer, 1)) // 2
        draw_big_text(footer_x, self.HEIGHT - 30, footer, 1, 10, shadow_color=1)

    def _draw_selector_arrow(self, x: int, y: int, direction: int, color: int) -> None:
        if direction < 0:
            pyxel.tri(x + 10, y, x, y + 6, x + 10, y + 12, color)
        else:
            pyxel.tri(x, y, x + 10, y + 6, x, y + 12, color)

    def _draw_start_screen(self) -> None:
        box_w = 320
        box_h = 300
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

        start_box_w = 280
        start_box_h = 34
        start_box_x = (self.WIDTH - start_box_w) // 2
        start_box_y = box_y + 238

        theme_border = 10 if self.start_menu_focus == 0 else 6
        start_weapon = self.WEAPON_FAMILY_ORDER[self.start_weapon_index]
        weapon_border = self._weapon_accent(start_weapon) if self.start_menu_focus == 1 else 6

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

        pyxel.rect(start_box_x, start_box_y, start_box_w, start_box_h, 1)
        pyxel.rectb(start_box_x, start_box_y, start_box_w, start_box_h, 10)
        pyxel.rectb(start_box_x + 2, start_box_y + 2, start_box_w - 4, start_box_h - 4, 11)
        draw_big_text(start_x, start_box_y + 8, start_text, start_scale, 7, shadow_color=1)

        pyxel.text(box_x + 18, box_y + 276, "WEAPON ITEMS SWITCH OR BOOST SHOTS", 11)
        pyxel.text(box_x + 18, box_y + 288, "BOMB / LASER AVAILABLE ON MOBILE", 10)

    def _draw_game_over(self) -> None:
        box_w = 248
        box_h = 128
        box_x = (self.WIDTH - box_w) // 2
        box_y = (self.HEIGHT - box_h) // 2

        pyxel.rect(box_x, box_y, box_w, box_h, self.hud_bg_color)
        pyxel.rectb(box_x, box_y, box_w, box_h, 8)
        pyxel.rectb(box_x + 3, box_y + 3, box_w - 6, box_h - 6, 13)

        title = "GAME OVER"
        retry = "TAP / CLICK TO RETRY"
        score_text = f"FINAL SCORE {self.score}"

        title_scale = 4
        retry_scale = 2
        score_scale = 2

        title_x = (self.WIDTH - big_text_width(title, title_scale)) // 2
        retry_x = (self.WIDTH - big_text_width(retry, retry_scale)) // 2
        score_x = (self.WIDTH - big_text_width(score_text, score_scale)) // 2

        draw_big_text(title_x, box_y + 18, title, title_scale, 8, shadow_color=2)
        draw_big_text(score_x, box_y + 68, score_text, score_scale, 7, shadow_color=1)
        draw_big_text(retry_x, box_y + 92, retry, retry_scale, 10, shadow_color=1)


if __name__ == "__main__":
    ShootGame()
