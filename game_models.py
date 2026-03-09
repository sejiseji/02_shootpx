from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class GamePhase(Enum):
    START = auto()
    PLAYING = auto()
    REWARD_SELECT = auto()
    GAME_OVER = auto()


@dataclass
class Bullet:
    x: float
    y: float
    vy: float
    vx: float = 0.0
    damage: int = 1
    radius: float = 3.0
    color_core: int = 10
    color_outer: int = 6
    style: str = "normal"
    age: int = 0
    max_life: int = 9999
    radius_growth: float = 0.0
    max_radius: float = 0.0
    trail: list[tuple[float, float]] = field(default_factory=list)
    hit_cooldowns: dict[int, int] = field(default_factory=dict)
    piercing: bool = False
    ignores_cancel: bool = False
    active: bool = True


@dataclass
class EnemyBullet:
    x: float
    y: float
    vx: float
    vy: float
    radius: int
    color: int
    damage: int
    display_scale: float
    active: bool = True
    age: int = 0
    max_life: int = 180


@dataclass
class Enemy:
    x: float
    y: float
    vx: float
    vy: float
    enemy_type: str
    hp: int
    max_hp: int
    anim_state: int = 0
    was_hit: bool = False
    hit_flash_timer: int = 0
    shoot_cooldown: int = 0
    fire_interval: int = 9999
    bullet_speed: float = 0.0
    move_phase: float = 0.0
    score_value: int = 10
    display_scale: float = 1.0
    hit_half_w: float = 8.0
    hit_half_h: float = 8.0
    active: bool = True


@dataclass
class Boss:
    x: float
    y: float
    vx: float
    vy: float
    hp: int
    max_hp: int
    target_y: float
    entry_done: bool = False
    shoot_cooldown: int = 60
    fire_interval: int = 42
    pattern_cycle: int = 0
    was_hit: bool = False
    hit_flash_timer: int = 0
    display_scale: float = 2.0
    hit_half_w: float = 26.0
    hit_half_h: float = 24.0
    active: bool = True


@dataclass
class Player:
    x: float
    y: float
    hp: int
    max_hp: int
    speed_x: int
    speed_y: int
    shoot_cooldown: int = 0
    is_hit: bool = False
    invincible_timer: int = 0


@dataclass
class BombField:
    x: float
    y: float
    vx: float
    vy: float
    target_y: float
    phase: str
    life: int
    max_life: int
    radius: float
    expansion: float
    rotation: float
    rotation_speed: float
    damage_interval: int
    damage_timer: int
    particle_points: list[complex] = field(default_factory=list)
    active: bool = True


@dataclass
class HomingLaser:
    x: float
    y: float
    vx: float
    vy: float
    speed: float
    turn_rate: float
    life: int
    max_life: int
    radius: int
    band_width: int
    damage: int
    trail: list[tuple[float, float]] = field(default_factory=list)
    hit_cooldowns: dict[int, int] = field(default_factory=dict)
    target_id: int | None = None
    reacquire_timer: int = 0
    active: bool = True


@dataclass
class WeaponItem:
    x: float
    y: float
    vx: float
    vy: float
    family: str
    radius: int = 8
    bob_phase: float = 0.0
    switch_lock_timer: int = 0
    active: bool = True


@dataclass
class HealItem:
    x: float
    y: float
    vx: float
    vy: float
    radius: int = 8
    bob_phase: float = 0.0
    active: bool = True


@dataclass
class RewardChoice:
    reward_id: str
    title: str
    description: str
    accent_color: int = 10
