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
    HomingLaser,
    Player,
    TeaItem,
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

    SHOT_FAMILY_TEA = "tea"
    SHOT_LEVEL_SINGLE = 0
    SHOT_LEVEL_DOUBLE = 1
    SHOT_LEVEL_TRIPLE = 2
    SHOT_LEVEL_POWER_SINGLE = 3
    SHOT_LEVEL_POWER_DOUBLE = 4
    SHOT_LEVEL_POWER_TRIPLE = 5
    SHOT_LEVEL_MAX = 5

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
        self.tea_items: list[TeaItem] = []
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

        self.shot_family = self.SHOT_FAMILY_TEA
        self.shot_level = self.SHOT_LEVEL_SINGLE
        self.shot_pick_flash_timer = 0

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

    def _is_mobile_laser_pressed(self) -> bool:
        if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            return False
        return self._point_in_circle(
            float(pyxel.mouse_x),
            float(pyxel.mouse_y),
            float(self.MOBILE_LASER_CX),
            float(self.MOBILE_LASER_CY),
            float(self.MOBILE_BTN_R),
        )

    def _is_mobile_bomb_pressed(self) -> bool:
        if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            return False
        return self._point_in_circle(
            float(pyxel.mouse_x),
            float(pyxel.mouse_y),
            float(self.MOBILE_BOMB_CX),
            float(self.MOBILE_BOMB_CY),
            float(self.MOBILE_BTN_R),
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

    def _shot_level_name(self) -> str:
        mapping = {
            self.SHOT_LEVEL_SINGLE: "SINGLE",
            self.SHOT_LEVEL_DOUBLE: "DOUBLE",
            self.SHOT_LEVEL_TRIPLE: "TRIPLE",
            self.SHOT_LEVEL_POWER_SINGLE: "P-SINGLE",
            self.SHOT_LEVEL_POWER_DOUBLE: "P-DOUBLE",
            self.SHOT_LEVEL_POWER_TRIPLE: "P-TRIPLE",
        }
        return mapping.get(self.shot_level, "SINGLE")

    def _advance_tea_shot(self) -> None:
        if self.shot_family != self.SHOT_FAMILY_TEA:
            self.shot_family = self.SHOT_FAMILY_TEA
            self.shot_level = self.SHOT_LEVEL_POWER_SINGLE
        else:
            self.shot_level = min(self.shot_level + 1, self.SHOT_LEVEL_MAX)

        self.shot_pick_flash_timer = self.TEA_FLASH_FRAMES

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
            )
        )

    def _fire_current_shot(self) -> None:
        origin_x = float(self.player.x)
        origin_y = float(self.player.y - self.PLAYER_HALF_H - 6)

        level = self.shot_level

        if level == self.SHOT_LEVEL_SINGLE:
            self._spawn_player_bullet(
                x=origin_x,
                y=origin_y,
                vx=0.0,
                vy=float(self.bullet_speed),
                damage=1,
                radius=3,
                color_core=10,
                color_outer=6,
                style="normal",
            )
            return

        if level == self.SHOT_LEVEL_DOUBLE:
            for vx in (-1.15, 1.15):
                self._spawn_player_bullet(
                    x=origin_x + (vx * 1.2),
                    y=origin_y,
                    vx=vx,
                    vy=float(self.bullet_speed),
                    damage=1,
                    radius=3,
                    color_core=11,
                    color_outer=3,
                    style="normal",
                )
            return

        if level == self.SHOT_LEVEL_TRIPLE:
            triples = (
                (-1.25, 0.0, 9, 4),
                (0.0, 0.0, 10, 6),
                (1.25, 0.0, 9, 4),
            )
            for vx, xoff, core, outer in triples:
                self._spawn_player_bullet(
                    x=origin_x + xoff,
                    y=origin_y,
                    vx=vx,
                    vy=float(self.bullet_speed),
                    damage=1,
                    radius=3,
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
                damage=2,
                radius=5,
                color_core=7,
                color_outer=11,
                style="power_single",
            )
            return

        if level == self.SHOT_LEVEL_POWER_DOUBLE:
            for vx, xoff in ((-1.0, -2.0), (1.0, 2.0)):
                self._spawn_player_bullet(
                    x=origin_x + xoff,
                    y=origin_y,
                    vx=vx,
                    vy=float(self.bullet_speed),
                    damage=2,
                    radius=5,
                    color_core=7,
                    color_outer=11,
                    style="power_double",
                )
            return

        if level == self.SHOT_LEVEL_POWER_TRIPLE:
            for vx, xoff in ((-1.05, -2.0), (0.0, 0.0), (1.05, 2.0)):
                self._spawn_player_bullet(
                    x=origin_x + xoff,
                    y=origin_y,
                    vx=vx,
                    vy=float(self.bullet_speed),
                    damage=2,
                    radius=5,
                    color_core=7,
                    color_outer=11,
                    style="power_triple",
                )

    def _maybe_spawn_tea_item(self, x: float, y: float) -> None:
        if random.random() > self.TEA_DROP_CHANCE:
            return

        self.tea_items.append(
            TeaItem(
                x=x,
                y=y,
                vx=random.uniform(-0.25, 0.25),
                vy=self.TEA_FALL_SPEED + random.uniform(-0.15, 0.18),
                bob_phase=random.uniform(0.0, math.tau),
            )
        )

    def _update_tea_items(self) -> None:
        next_items: list[TeaItem] = []

        for item in self.tea_items:
            if not item.active:
                continue

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
                self._advance_tea_shot()
                continue

            next_items.append(item)

        self.tea_items = next_items

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
        self.tea_items.clear()

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
        self._update_tea_items()

        self._handle_projectile_cancellations()

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
        move_left = pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_UP)
        move_right = pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_DOWN)

        if move_left:
            self._move_theme_selection(-1)
        elif move_right:
            self._move_theme_selection(1)

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            mx = float(pyxel.mouse_x)
            my = float(pyxel.mouse_y)

            selector_x = 46
            selector_y = (self.HEIGHT - 260) // 2 + 100
            selector_w = 268
            selector_h = 54

            start_box_w = 280
            start_box_h = 34
            start_box_x = (self.WIDTH - start_box_w) // 2
            start_box_y = (self.HEIGHT - 260) // 2 + 198

            if self._point_in_rect(mx, my, selector_x, selector_y, selector_w * 0.5, selector_h):
                self._move_theme_selection(-1)
                return
            if self._point_in_rect(mx, my, selector_x + selector_w * 0.5, selector_y, selector_w * 0.5, selector_h):
                self._move_theme_selection(1)
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
            self.player.shoot_cooldown = self.shoot_interval_frames

    def _update_special_input(self) -> None:
        if pyxel.btnp(pyxel.KEY_X):
            self._try_activate_bomb()
        if pyxel.btnp(pyxel.KEY_C):
            self._try_activate_homing_laser()

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
            bullet.x += bullet.vx
            bullet.y -= bullet.vy
            if bullet.y < -16 or bullet.x < -16 or bullet.x > self.WIDTH + 16:
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
            removed = False
            for enemy_bullet in self.enemy_bullets[:]:
                if self._circles_overlap(
                    bullet.x, bullet.y, bullet.radius,
                    enemy_bullet.x, enemy_bullet.y, enemy_bullet.radius,
                ):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    if enemy_bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(enemy_bullet)
                    removed = True
                    break
            if removed:
                continue

        for bomb in self.bombs:
            cancel_r = 8.0 if bomb.phase == "launch" else self._bomb_current_radius(bomb) * 0.92
            if cancel_r <= 0:
                continue

            for enemy_bullet in self.enemy_bullets[:]:
                if self._circles_overlap(
                    bomb.x, bomb.y, cancel_r,
                    enemy_bullet.x, enemy_bullet.y, enemy_bullet.radius,
                ):
                    if enemy_bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(enemy_bullet)

        for laser in self.homing_lasers:
            for enemy_bullet in self.enemy_bullets[:]:
                if self._laser_hits_enemy_bullet(laser, enemy_bullet):
                    if enemy_bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(enemy_bullet)

    def _is_bullet_hitting_enemy(self, bullet: Bullet, enemy: Enemy) -> bool:
        hit_r = bullet.radius + 1
        return (
            bullet.x - hit_r < enemy.x + enemy.hit_half_w
            and bullet.x + hit_r > enemy.x - enemy.hit_half_w
            and bullet.y - hit_r < enemy.y + enemy.hit_half_h
            and bullet.y + hit_r > enemy.y - enemy.hit_half_h
        )

    def _is_bullet_hitting_boss(self, bullet: Bullet, boss: Boss) -> bool:
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
            self._maybe_spawn_tea_item(enemy.x, enemy.y)
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
                self._damage_enemy(enemy, bullet.damage, source="shot")
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                break

    def _handle_bullet_boss_collisions(self) -> None:
        if self.boss is None:
            return

        for bullet in self.bullets[:]:
            if not self._is_bullet_hitting_boss(bullet, self.boss):
                continue
            self._damage_boss(bullet.damage, source="shot")
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
        self._draw_tea_items()
        self._draw_bullets()
        self._draw_homing_lasers()
        self._draw_effects()
        self._draw_player()
        self._draw_hud()
        self._draw_mobile_controls()

        if self.boss_intro_timer > 0:
            self._draw_boss_warning()

        if self.phase == GamePhase.START:
            self._draw_start_screen()
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

        fill_color = 8
        border_color = 10
        if self._is_touch_in_mobile_control_area() and (self.frame_count // 3) % 2 == 0:
            fill_color = 9
            border_color = 7

        pyxel.circ(self.MOBILE_CTRL_CX, self.MOBILE_CTRL_CY, self.MOBILE_CTRL_RADIUS, fill_color)
        pyxel.circb(self.MOBILE_CTRL_CX, self.MOBILE_CTRL_CY, self.MOBILE_CTRL_RADIUS, border_color)

        self._draw_mobile_laser_button()
        self._draw_mobile_bomb_button()

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

        cx = self.MOBILE_LASER_CX
        cy = self.MOBILE_LASER_CY
        r = self.MOBILE_BTN_R

        pyxel.circ(cx, cy, r, fill)
        pyxel.circb(cx, cy, r, border)
        pyxel.circb(cx, cy, r - 3, border)

        pyxel.text(cx - 14, cy - 8, "LASER", text)
        pyxel.text(cx - 10, cy + 4, "RDY" if self.laser_cooldown <= 0 else f"{self.laser_cooldown:02d}", text)

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

        cx = self.MOBILE_BOMB_CX
        cy = self.MOBILE_BOMB_CY
        r = self.MOBILE_BTN_R

        pyxel.circ(cx, cy, r, fill)
        pyxel.circb(cx, cy, r, border)
        pyxel.circb(cx, cy, r - 3, border)

        pyxel.text(cx - 12, cy - 8, "BOMB", text)
        pyxel.text(cx - 3, cy + 4, str(self.bomb_stock), text)

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

            if bullet.style == "normal":
                pyxel.line(bx, by + 6, bx, by - 3, bullet.color_outer)
                pyxel.circ(bx, by, bullet.radius, bullet.color_core)
            elif bullet.style == "power_single":
                pyxel.line(bx, by + 8, bx, by - 6, bullet.color_outer)
                pyxel.circ(bx, by, bullet.radius, bullet.color_core)
                pyxel.circb(bx, by, bullet.radius + 1, 15)
            elif bullet.style == "power_double":
                pyxel.line(bx, by + 8, bx, by - 5, bullet.color_outer)
                pyxel.circ(bx, by, bullet.radius, bullet.color_core)
                pyxel.pset(bx, by, 15)
            elif bullet.style == "power_triple":
                pyxel.line(bx, by + 8, bx, by - 6, bullet.color_outer)
                pyxel.circ(bx, by, bullet.radius, bullet.color_core)
                pyxel.circb(bx, by, bullet.radius + 1, 7)
            else:
                pyxel.line(bx, by + 6, bx, by - 3, bullet.color_outer)
                pyxel.circ(bx, by, bullet.radius, bullet.color_core)

    def _draw_enemy_bullets(self) -> None:
        for bullet in self.enemy_bullets:
            bx = int(bullet.x)
            by = int(bullet.y)
            pyxel.circ(bx, by, bullet.radius, bullet.color)
            pyxel.pset(bx, by, 7)
            if bullet.radius >= 5:
                pyxel.circb(bx, by, bullet.radius, 7)

    def _draw_tea_items(self) -> None:
        for item in self.tea_items:
            ix = int(item.x)
            iy = int(item.y)

            cup_color = 11 if (self.frame_count // 6) % 2 == 0 else 10
            leaf_color = 3

            pyxel.circ(ix, iy, 7, cup_color)
            pyxel.circb(ix, iy, 7, 7)
            pyxel.rect(ix - 3, iy - 2, 6, 5, 3)
            pyxel.line(ix + 6, iy - 1, ix + 9, iy + 1, 7)
            pyxel.line(ix + 9, iy + 1, ix + 8, iy + 4, 7)
            pyxel.pset(ix - 1, iy - 1, leaf_color)
            pyxel.pset(ix, iy - 2, leaf_color)
            pyxel.pset(ix + 1, iy - 1, leaf_color)

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

        if getattr(boss, "entry_invulnerable", False):
            aura_r = int(max(draw_w, draw_h) * 0.55)
            aura_color = 12 if (self.frame_count // 4) % 2 == 0 else 7
            pyxel.circb(int(boss.x), int(boss.y), aura_r, aura_color)
            pyxel.circb(int(boss.x), int(boss.y), max(8, aura_r - 4), 6)

        if getattr(boss, "shield_timer", 0) > 0:
            base_r = int(max(draw_w, draw_h) * 0.58)
            c1 = 12 if (self.frame_count // 3) % 2 == 0 else 7
            c2 = 6 if (self.frame_count // 5) % 2 == 0 else 13
            pyxel.circb(int(boss.x), int(boss.y), base_r, c1)
            pyxel.circb(int(boss.x), int(boss.y), base_r + 4, c2)
            pyxel.circb(int(boss.x), int(boss.y), max(10, base_r - 5), 7)

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
        draw_big_text(52, 74, f"X {self.bomb_stock}/{self._bomb_capacity()}", 1, bomb_value_color, shadow_color=1)

        laser_status = "READY" if self.laser_cooldown <= 0 else f"WAIT{self.laser_cooldown:02d}"
        draw_big_text(8, 92, "LASER", 1, 13, shadow_color=1)
        draw_big_text(
            60,
            92,
            f"C {laser_status} {len(self.homing_lasers)}/{self.laser_active_limit}",
            1,
            laser_text_color,
            shadow_color=1,
        )

    def _draw_selector_arrow(self, x: int, y: int, direction: int, color: int) -> None:
        if direction < 0:
            pyxel.tri(x + 10, y, x, y + 6, x + 10, y + 12, color)
        else:
            pyxel.tri(x, y, x + 10, y + 6, x, y + 12, color)

    def _draw_start_screen(self) -> None:
        box_w = 320
        box_h = 260
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

        start_box_w = 280
        start_box_h = 34
        start_box_x = (self.WIDTH - start_box_w) // 2
        start_box_y = box_y + 198

        pyxel.rect(selector_x, selector_y, selector_w, selector_h, 1)
        pyxel.rectb(selector_x, selector_y, selector_w, selector_h, 6)
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

        pyxel.rect(start_box_x, start_box_y, start_box_w, start_box_h, 1)
        pyxel.rectb(start_box_x, start_box_y, start_box_w, start_box_h, 10)
        pyxel.rectb(start_box_x + 2, start_box_y + 2, start_box_w - 4, start_box_h - 4, 11)
        draw_big_text(start_x, start_box_y + 8, start_text, start_scale, 7, shadow_color=1)

        pyxel.text(box_x + 18, box_y + 236, "GREEN TEA BOOSTS SHOT POWER", 11)
        pyxel.text(box_x + 18, box_y + 248, "BOMB / LASER AVAILABLE ON MOBILE", 10)

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