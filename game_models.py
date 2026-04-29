from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class GamePhase(Enum):
    START = auto()
    PLAYING = auto()
    REWARD_SELECT = auto()
    GAME_OVER = auto()
    RESULT = auto()


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
    slow_inflict: bool = False
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
    anim_offset: int = 0
    anim_dir: int = 1
    score_value: int = 10
    display_scale: float = 1.0
    hit_half_w: float = 8.0
    hit_half_h: float = 8.0
    sushi_type: str = "tuna"
    enemy_category: str = "sushi_enemy"
    split_spawn_enemy_type: str | None = None
    split_spawn_min: int = 0
    split_spawn_max: int = 0
    sprite_variant: int = 0
    invincible_timer: int = 0
    knockback_vx: float = 0.0
    knockback_vy: float = 0.0
    state: str = "normal"
    retreat_vx: float = 0.0
    retreat_vy: float = 0.0
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
    anim_dir: int = 1
    was_hit: bool = False
    hit_flash_timer: int = 0
    display_scale: float = 2.0
    hit_half_w: float = 26.0
    hit_half_h: float = 24.0
    buff_id: str | None = None
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
    power_level: int = 2
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
    steer_delay: int = 0
    cancel_chain_timer: int = 0
    cancel_chain_step: int = 0
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
class BitItem:
    x: float
    y: float
    vx: float
    vy: float
    radius: int = 8
    variant: int = 0
    bob_phase: float = 0.0
    active: bool = True


@dataclass
class WasabiItem:
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
    tag: str = "UTILITY"


@dataclass
class BossBuffState:
    current_boss_buff: str | None = None
    acquired_cycle_buffs: set[str] = field(default_factory=set)
    overload_active: bool = False
    overload_timer: int = 0
    fever_barrier_hits: int = 0


@dataclass
class EchoShot:
    x: float
    y: float
    dx: float
    dy: float
    damage: int
    bounce_left: int
    lifetime: int
    length: int
    split_angle_deg: float = 45.0
    generation: int = 0
    power_variant: bool = False
    active: bool = True


@dataclass
class BombSpark3D:
    local_x: float
    local_y: float
    local_z: float
    size: int
    kind: int
    phase: float
    layer: int


@dataclass
class PrecomputedParticleFrame:
    dx: int
    dy: int
    color: int
    size: int
    kind: int


@dataclass
class PrecomputedBombFrame:
    particles: list[PrecomputedParticleFrame] = field(default_factory=list)
    flow_particles: list[PrecomputedParticleFrame] = field(default_factory=list)
    sheet_x: int = 0
    sheet_y: int = 0
    flow_sheet_x: int = 0
    flow_sheet_y: int = 0


@dataclass
class PrecomputedBombPattern:
    frames: list[PrecomputedBombFrame] = field(default_factory=list)
    total_frames: int = 0
    sheet_image: Any | None = None
    frame_w: int = 0
    frame_h: int = 0
    origin_x: int = 0
    origin_y: int = 0
    flow_sheet_image: Any | None = None
    flow_frame_w: int = 0
    flow_frame_h: int = 0
    flow_origin_x: int = 0
    flow_origin_y: int = 0


@dataclass
class ActiveBombVisual:
    x: float
    y: float
    pattern_id: int
    scale: float = 1.0
    frame_index: int = 0
    age: int = 0
    alive: bool = True


@dataclass
class BossDefeatSushi:
    x: float
    y: float
    vx: float
    vy: float
    enemy_type: str
    anim_offset: int = 0
    anim_dir: int = 1
    scale: float = 1.0
    depth: float = 0.0
    delay: int = 0
    life: int = 0
    active: bool = True


@dataclass
class BossDefeatCheer:
    x: float
    y: float
    vx: float
    vy: float
    text: str
    color: int = 15
    shadow_color: int = 1
    scale: int = 1
    delay: int = 0
    life: int = 0
    active: bool = True


@dataclass
class RetreatShadow:
    x: float
    y: float
    vx: float
    vy: float
    enemy_type: str
    anim_offset: int = 0
    anim_dir: int = 1
    display_scale: float = 1.0
    sprite_variant: int = 0
    active: bool = True


@dataclass
class FeverArrivalSushi:
    start_x: float
    start_y: float
    target_x: float
    target_y: float
    current_x: float
    current_y: float
    enemy_type: str
    anim_offset: int = 0
    anim_dir: int = 1
    display_scale: float = 1.0
    side: int = 1
    delay: int = 0
    bounce_height: float = 0.0
    bounce_phase: float = 0.0


@dataclass
class FeverArrivalEffect:
    active: bool = False
    timer: int = 0
    center_x: float = 0.0
    center_y: float = 0.0
    sushis: list[FeverArrivalSushi] = field(default_factory=list)


@dataclass
class OrbitSushiEntry:
    sushi_type: str
    enemy_type: str
    acquire_order: int
    anim_offset: int = 0
    anim_dir: int = 1
    display_scale: float = 1.0
    has_wasabi: bool = False


@dataclass
class OrbitSample:
    dx: int
    dy: int
    depth: float
    scale: float
    brightness_rank: int


@dataclass
class OrbitPattern:
    samples: list[OrbitSample] = field(default_factory=list)
    rotation_frames: list[list[OrbitSample]] = field(default_factory=list)
    shell_rotation_frames: list[list[OrbitSample]] = field(default_factory=list)
    length: int = 0
    rotation_length: int = 0
    name: str = "orbit"


@dataclass
class SettlingSushi:
    sushi_type: str
    enemy_type: str
    has_wasabi: bool
    start_x: float
    start_y: float
    target_x: float
    target_y: float
    current_x: float
    current_y: float
    circle_angle: float
    anim_offset: int = 0
    anim_dir: int = 1
    display_scale: float = 1.0
    source_ring: str = "main"
    radius_group: str = "inner"
    jump_delay: int = 0
    jump_timer: int = 0
    shake_timer: int = 0
    offset_x: float = 0.0
    offset_y: float = 0.0
    explode_vx: float = 0.0
    explode_vy: float = 0.0
    done: bool = False


@dataclass
class SushiSettleEffect:
    active: bool = False
    phase: int = 0
    timer: int = 0
    sushis: list[SettlingSushi] | None = None
    gained_score: int = 0
    gained_barrier: int = 1
    center_x: float = 0.0
    center_y: float = 0.0
    score_applied: bool = False
    consumed_has_wasabi: bool = False
    combo_ids: list[str] = field(default_factory=list)
    expanded_settlement: bool = False


@dataclass
class DrawItem:
    layer_group: int
    depth: float
    kind: str
    x: float
    y: float
    payload: Any = None
