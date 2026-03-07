from __future__ import annotations

import math
from typing import Callable

from game_models import Boss


AppendEnemyBulletFn = Callable[..., bool]


def boss_phase(boss: Boss | None) -> int:
    if boss is None or boss.max_hp <= 0:
        return 0

    ratio = boss.hp / boss.max_hp
    if ratio > 0.70:
        return 1
    if ratio > 0.30:
        return 2
    return 3


def spawn_boss(
    *,
    width: int,
    entry_target_y: float,
    max_hp: int,
) -> Boss:
    display_scale = 2.0
    return Boss(
        x=width / 2,
        y=-48.0,
        vx=2.0,
        vy=1.8,
        hp=max_hp,
        max_hp=max_hp,
        target_y=float(entry_target_y),
        entry_done=False,
        shoot_cooldown=60,
        fire_interval=42,
        pattern_cycle=0,
        display_scale=display_scale,
        hit_half_w=13.0 * display_scale,
        hit_half_h=12.0 * display_scale,
    )


def _rotate_vector(vx: float, vy: float, angle: float) -> tuple[float, float]:
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (
        vx * cos_a - vy * sin_a,
        vx * sin_a + vy * cos_a,
    )


def _spawn_boss_aimed_fan(
    *,
    boss: Boss,
    player_x: float,
    player_y: float,
    ways: int,
    spread: float,
    speed: float,
    radius: int,
    color: int,
    append_enemy_bullet: AppendEnemyBulletFn,
) -> None:
    bx = boss.x
    by = boss.y + boss.hit_half_h - 4
    dx = player_x - bx
    dy = player_y - by
    length = math.hypot(dx, dy)

    if length <= 0.0001:
        base_vx = 0.0
        base_vy = speed
    else:
        base_vx = dx / length * speed
        base_vy = dy / length * speed

    if ways <= 1:
        angles = [0.0]
    else:
        angles = [
            -spread + (2.0 * spread) * (idx / (ways - 1))
            for idx in range(ways)
        ]

    for angle in angles:
        vx, vy = _rotate_vector(base_vx, base_vy, angle)
        append_enemy_bullet(
            x=bx,
            y=by,
            vx=vx,
            vy=vy,
            radius=radius,
            color=color,
            damage=1,
            display_scale=1.25,
        )


def _spawn_boss_ring(
    *,
    boss: Boss,
    count: int,
    speed: float,
    radius: int,
    color: int,
    angle_offset: float,
    append_enemy_bullet: AppendEnemyBulletFn,
) -> None:
    bx = boss.x
    by = boss.y + 6

    for idx in range(count):
        angle = (math.tau / count) * idx + angle_offset
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        append_enemy_bullet(
            x=bx,
            y=by,
            vx=vx,
            vy=vy,
            radius=radius,
            color=color,
            damage=1,
            display_scale=1.2,
        )


def _spawn_boss_down_fan(
    *,
    boss: Boss,
    vx_values: tuple[float, ...],
    vy: float,
    radius: int,
    color: int,
    append_enemy_bullet: AppendEnemyBulletFn,
) -> None:
    bx = boss.x
    by = boss.y + boss.hit_half_h - 2

    for vx in vx_values:
        append_enemy_bullet(
            x=bx,
            y=by,
            vx=vx,
            vy=vy,
            radius=radius,
            color=color,
            damage=1,
            display_scale=1.15,
        )


def fire_boss_pattern(
    *,
    boss: Boss,
    frame_count: int,
    player_x: float,
    player_y: float,
    append_enemy_bullet: AppendEnemyBulletFn,
) -> None:
    phase = boss_phase(boss)
    pattern = boss.pattern_cycle % 3

    if phase == 1:
        if pattern == 0:
            _spawn_boss_aimed_fan(
                boss=boss,
                player_x=player_x,
                player_y=player_y,
                ways=5,
                spread=0.28,
                speed=3.2,
                radius=5,
                color=8,
                append_enemy_bullet=append_enemy_bullet,
            )
        elif pattern == 1:
            _spawn_boss_ring(
                boss=boss,
                count=10,
                speed=2.4,
                radius=4,
                color=14,
                angle_offset=frame_count * 0.02,
                append_enemy_bullet=append_enemy_bullet,
            )
        else:
            _spawn_boss_down_fan(
                boss=boss,
                vx_values=(-2.2, -1.4, -0.7, 0.0, 0.7, 1.4, 2.2),
                vy=2.6,
                radius=4,
                color=10,
                append_enemy_bullet=append_enemy_bullet,
            )

    elif phase == 2:
        if pattern == 0:
            _spawn_boss_aimed_fan(
                boss=boss,
                player_x=player_x,
                player_y=player_y,
                ways=7,
                spread=0.40,
                speed=3.5,
                radius=5,
                color=8,
                append_enemy_bullet=append_enemy_bullet,
            )
            _spawn_boss_aimed_fan(
                boss=boss,
                player_x=player_x,
                player_y=player_y,
                ways=3,
                spread=0.10,
                speed=4.0,
                radius=4,
                color=10,
                append_enemy_bullet=append_enemy_bullet,
            )
        elif pattern == 1:
            _spawn_boss_ring(
                boss=boss,
                count=14,
                speed=2.8,
                radius=4,
                color=14,
                angle_offset=frame_count * 0.03,
                append_enemy_bullet=append_enemy_bullet,
            )
        else:
            _spawn_boss_down_fan(
                boss=boss,
                vx_values=(-2.8, -2.1, -1.4, -0.7, 0.0, 0.7, 1.4, 2.1, 2.8),
                vy=2.9,
                radius=4,
                color=10,
                append_enemy_bullet=append_enemy_bullet,
            )
            _spawn_boss_aimed_fan(
                boss=boss,
                player_x=player_x,
                player_y=player_y,
                ways=3,
                spread=0.18,
                speed=3.6,
                radius=4,
                color=9,
                append_enemy_bullet=append_enemy_bullet,
            )

    else:
        if pattern == 0:
            _spawn_boss_aimed_fan(
                boss=boss,
                player_x=player_x,
                player_y=player_y,
                ways=9,
                spread=0.52,
                speed=3.9,
                radius=5,
                color=8,
                append_enemy_bullet=append_enemy_bullet,
            )
            _spawn_boss_aimed_fan(
                boss=boss,
                player_x=player_x,
                player_y=player_y,
                ways=5,
                spread=0.18,
                speed=4.4,
                radius=4,
                color=10,
                append_enemy_bullet=append_enemy_bullet,
            )
        elif pattern == 1:
            _spawn_boss_ring(
                boss=boss,
                count=18,
                speed=3.0,
                radius=4,
                color=14,
                angle_offset=frame_count * 0.04,
                append_enemy_bullet=append_enemy_bullet,
            )
            _spawn_boss_ring(
                boss=boss,
                count=9,
                speed=2.3,
                radius=4,
                color=10,
                angle_offset=(frame_count * 0.04) + 0.22,
                append_enemy_bullet=append_enemy_bullet,
            )
        else:
            _spawn_boss_down_fan(
                boss=boss,
                vx_values=(-3.2, -2.6, -2.0, -1.4, -0.8, 0.0, 0.8, 1.4, 2.0, 2.6, 3.2),
                vy=3.1,
                radius=4,
                color=10,
                append_enemy_bullet=append_enemy_bullet,
            )
            _spawn_boss_aimed_fan(
                boss=boss,
                player_x=player_x,
                player_y=player_y,
                ways=5,
                spread=0.24,
                speed=4.1,
                radius=4,
                color=8,
                append_enemy_bullet=append_enemy_bullet,
            )

    boss.pattern_cycle += 1


def update_boss(
    *,
    boss: Boss,
    frame_count: int,
    width: int,
    side_margin: int,
    boss_sprite_w: int,
    player_x: float,
    player_y: float,
    append_enemy_bullet: AppendEnemyBulletFn,
) -> None:
    if boss.hit_flash_timer > 0:
        boss.hit_flash_timer -= 1
        boss.was_hit = True
    else:
        boss.was_hit = False

    if not boss.entry_done:
        boss.y += boss.vy
        if boss.y >= boss.target_y:
            boss.y = boss.target_y
            boss.entry_done = True
            boss.vy = 0.0
            boss.shoot_cooldown = 45
        return

    phase = boss_phase(boss)
    target_speed = {1: 2.0, 2: 2.6, 3: 3.2}[phase]
    bob_amp = {1: 7.0, 2: 10.0, 3: 13.0}[phase]
    bob_speed = {1: 0.05, 2: 0.07, 3: 0.09}[phase]
    fire_interval = {1: 42, 2: 32, 3: 24}[phase]

    if boss.vx >= 0:
        boss.vx = abs(target_speed)
    else:
        boss.vx = -abs(target_speed)

    boss.fire_interval = fire_interval

    sprite_half_w = (boss_sprite_w * boss.display_scale) / 2.0
    side_min = side_margin + sprite_half_w
    side_max = width - side_margin - sprite_half_w

    boss.x += boss.vx
    if boss.x < side_min:
        boss.x = side_min
        boss.vx = abs(boss.vx)
    elif boss.x > side_max:
        boss.x = side_max
        boss.vx = -abs(boss.vx)

    boss.y = boss.target_y + math.sin(frame_count * bob_speed) * bob_amp

    if boss.shoot_cooldown > 0:
        boss.shoot_cooldown -= 1
    else:
        fire_boss_pattern(
            boss=boss,
            frame_count=frame_count,
            player_x=player_x,
            player_y=player_y,
            append_enemy_bullet=append_enemy_bullet,
        )
        boss.shoot_cooldown = boss.fire_interval