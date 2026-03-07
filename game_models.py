from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class GamePhase(Enum):
    START = auto()
    PLAYING = auto()
    GAME_OVER = auto()


@dataclass
class Bullet:
    x: float
    y: float
    vy: float
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
    display_scale: float = 1.0
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
    fire_interval: int = 0
    bullet_speed: float = 0.0
    move_phase: float = 0.0
    score_value: int = 0
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
    shoot_cooldown: int = 0
    fire_interval: int = 0
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
    speed_x: float
    speed_y: float
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
    radius: float
    band_width: float
    damage: int
    trail: list[tuple[float, float]] = field(default_factory=list)
    hit_cooldowns: dict[int, int] = field(default_factory=dict)
    target_id: int | None = None
    reacquire_timer: int = 0
    active: bool = True