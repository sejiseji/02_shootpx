from __future__ import annotations

import math
import random
from typing import Callable

from game_models import Boss, Enemy


AppendEnemyBullet = Callable[..., bool]
CreateEnemyCallback = Callable[[float, str], Enemy]


def boss_phase(boss: Boss | None) -> int:
    if boss is None or boss.max_hp <= 0:
        return 0

    ratio = boss.hp / boss.max_hp
    if ratio > 0.70:
        return 1
    if ratio > 0.30:
        return 2
    return 3


def _ensure_boss_runtime_fields(boss: Boss, spawn_count: int) -> None:
    if not hasattr(boss, "spawn_count"):
        boss.spawn_count = spawn_count
    if not hasattr(boss, "entry_invulnerable"):
        boss.entry_invulnerable = True
    if not hasattr(boss, "phase_bonus_level"):
        boss.phase_bonus_level = min(3, spawn_count)

    if not hasattr(boss, "laser_telegraph_timer"):
        boss.laser_telegraph_timer = 0
    if not hasattr(boss, "laser_active_timer"):
        boss.laser_active_timer = 0
    if not hasattr(boss, "laser_cooldown"):
        boss.laser_cooldown = 120
    if not hasattr(boss, "laser_angle"):
        boss.laser_angle = math.pi / 2
    if not hasattr(boss, "laser_kind"):
        boss.laser_kind = "vertical"
    if not hasattr(boss, "special_beam_telegraph_timer"):
        boss.special_beam_telegraph_timer = 0
    if not hasattr(boss, "special_beam_active_timer"):
        boss.special_beam_active_timer = 0
    if not hasattr(boss, "special_beam_total_active_timer"):
        boss.special_beam_total_active_timer = 0
    if not hasattr(boss, "special_beam_cooldown"):
        boss.special_beam_cooldown = 180
    if not hasattr(boss, "special_beam_kind"):
        boss.special_beam_kind = "none"
    if not hasattr(boss, "special_beam_sweep_dir"):
        boss.special_beam_sweep_dir = 1

    if not hasattr(boss, "shield_timer"):
        boss.shield_timer = 0
    if not hasattr(boss, "shield_cooldown"):
        boss.shield_cooldown = 180

    if not hasattr(boss, "summon_cooldown"):
        boss.summon_cooldown = 240
    if not hasattr(boss, "summon_flash_timer"):
        boss.summon_flash_timer = 0

    if not hasattr(boss, "dash_telegraph_timer"):
        boss.dash_telegraph_timer = 0
    if not hasattr(boss, "dash_active_timer"):
        boss.dash_active_timer = 0
    if not hasattr(boss, "dash_recover_timer"):
        boss.dash_recover_timer = 0
    if not hasattr(boss, "dash_cooldown"):
        boss.dash_cooldown = 260
    if not hasattr(boss, "dash_target_x"):
        boss.dash_target_x = boss.x
    if not hasattr(boss, "dash_target_y"):
        boss.dash_target_y = boss.y
    if not hasattr(boss, "dash_vx"):
        boss.dash_vx = 0.0
    if not hasattr(boss, "dash_vy"):
        boss.dash_vy = 0.0


def _scaled_boss_hp(base_hp: int, spawn_count: int) -> int:
    return int(base_hp + (spawn_count * 35) + (spawn_count * spawn_count * 5))


def spawn_boss(
    *,
    width: int,
    entry_target_y: float,
    max_hp: int,
    spawn_count: int = 0,
) -> Boss:
    display_scale = 2.0
    scaled_hp = _scaled_boss_hp(max_hp, spawn_count)

    boss = Boss(
        x=width / 2,
        y=-48.0,
        vx=2.0,
        vy=1.8,
        hp=scaled_hp,
        max_hp=scaled_hp,
        target_y=entry_target_y,
        entry_done=False,
        shoot_cooldown=60,
        fire_interval=42,
        pattern_cycle=0,
        anim_dir=-1 if random.random() < 0.5 else 1,
        display_scale=display_scale,
        hit_half_w=13.0 * display_scale,
        hit_half_h=12.0 * display_scale,
    )

    boss.spawn_count = spawn_count
    boss.entry_invulnerable = True
    boss.phase_bonus_level = min(3, spawn_count)

    boss.laser_telegraph_timer = 0
    boss.laser_active_timer = 0
    boss.laser_cooldown = 120
    boss.laser_angle = math.pi / 2
    boss.laser_kind = "vertical"
    boss.special_beam_telegraph_timer = 0
    boss.special_beam_active_timer = 0
    boss.special_beam_total_active_timer = 0
    boss.special_beam_cooldown = 180
    boss.special_beam_kind = "none"
    boss.special_beam_sweep_dir = 1

    boss.shield_timer = 0
    boss.shield_cooldown = 180

    boss.summon_cooldown = 240
    boss.summon_flash_timer = 0

    boss.dash_telegraph_timer = 0
    boss.dash_active_timer = 0
    boss.dash_recover_timer = 0
    boss.dash_cooldown = 260
    boss.dash_target_x = boss.x
    boss.dash_target_y = boss.y
    boss.dash_vx = 0.0
    boss.dash_vy = 0.0
    return boss


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
    append_enemy_bullet: AppendEnemyBullet,
    display_scale: float = 1.25,
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
            display_scale=display_scale,
        )


def _spawn_boss_ring(
    *,
    boss: Boss,
    count: int,
    speed: float,
    radius: int,
    color: int,
    angle_offset: float,
    append_enemy_bullet: AppendEnemyBullet,
    display_scale: float = 1.20,
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
            display_scale=display_scale,
        )


def _spawn_boss_down_fan(
    *,
    boss: Boss,
    vx_values: tuple[float, ...],
    vy: float,
    radius: int,
    color: int,
    append_enemy_bullet: AppendEnemyBullet,
    display_scale: float = 1.15,
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
            display_scale=display_scale,
        )


def _choose_laser_kind(boss: Boss, phase: int) -> None:
    spawn_count = getattr(boss, "spawn_count", 0)

    if spawn_count >= 4 and phase >= 3:
        if boss.pattern_cycle % 2 == 0:
            boss.laser_kind = "slash_left"
            boss.laser_angle = math.radians(108)
        else:
            boss.laser_kind = "slash_right"
            boss.laser_angle = math.radians(72)
    else:
        boss.laser_kind = "vertical"
        boss.laser_angle = math.pi / 2


def _try_start_laser_telegraph(boss: Boss, phase: int, spawn_count: int) -> None:
    if spawn_count < 2:
        return
    if boss.laser_active_timer > 0 or boss.laser_telegraph_timer > 0:
        return
    if boss.laser_cooldown > 0:
        return
    if boss.shield_timer > 0:
        return
    if boss.dash_telegraph_timer > 0 or boss.dash_active_timer > 0 or boss.dash_recover_timer > 0:
        return

    _choose_laser_kind(boss, phase)
    boss.laser_telegraph_timer = max(24, 34 - min(10, spawn_count * 2))
    boss.laser_active_timer = 0
    boss.laser_cooldown = 150 - min(50, spawn_count * 10)


def _update_laser_state(boss: Boss, phase: int, spawn_count: int) -> None:
    if spawn_count < 2:
        return

    if boss.laser_cooldown > 0:
        boss.laser_cooldown -= 1

    if boss.laser_telegraph_timer > 0:
        boss.laser_telegraph_timer -= 1
        if boss.laser_telegraph_timer <= 0:
            boss.laser_active_timer = 18 + min(8, spawn_count * 2)
        return

    if boss.laser_active_timer > 0:
        boss.laser_active_timer -= 1
        if boss.laser_active_timer <= 0:
            boss.laser_cooldown = max(70, 120 - min(40, spawn_count * 8))
        return

    _try_start_laser_telegraph(boss, phase, spawn_count)


def _choose_special_beam_kind(boss: Boss) -> None:
    pattern = boss.pattern_cycle % 3
    if pattern == 0:
        boss.special_beam_kind = "dual_straight"
    elif pattern == 1:
        boss.special_beam_kind = "dual_cross"
    else:
        boss.special_beam_kind = "saber_sweep"
        boss.special_beam_sweep_dir = -1 if (boss.pattern_cycle // 3) % 2 == 0 else 1


def _try_start_special_beam(boss: Boss, phase: int, spawn_count: int) -> None:
    if spawn_count < 4 or phase < 2:
        return
    if boss.special_beam_telegraph_timer > 0 or boss.special_beam_active_timer > 0:
        return
    if boss.special_beam_cooldown > 0:
        return
    if boss.shield_timer > 0:
        return
    if boss.laser_telegraph_timer > 0 or boss.laser_active_timer > 0:
        return
    if boss.dash_telegraph_timer > 0 or boss.dash_active_timer > 0 or boss.dash_recover_timer > 0:
        return

    _choose_special_beam_kind(boss)
    boss.special_beam_telegraph_timer = max(18, 26 - min(8, spawn_count))
    boss.special_beam_active_timer = 0
    boss.special_beam_total_active_timer = 0
    boss.special_beam_cooldown = max(110, 210 - min(70, spawn_count * 10))


def _update_special_beam_state(boss: Boss, phase: int, spawn_count: int) -> bool:
    if spawn_count < 4 or phase < 2:
        return False

    if boss.special_beam_cooldown > 0:
        boss.special_beam_cooldown -= 1

    if boss.special_beam_telegraph_timer > 0:
        boss.special_beam_telegraph_timer -= 1
        if boss.special_beam_telegraph_timer <= 0:
            if boss.special_beam_kind == "saber_sweep":
                boss.special_beam_total_active_timer = 34 + min(8, spawn_count)
            else:
                boss.special_beam_total_active_timer = 22 + min(6, spawn_count)
            boss.special_beam_active_timer = boss.special_beam_total_active_timer
        return True

    if boss.special_beam_active_timer > 0:
        boss.special_beam_active_timer -= 1
        if boss.special_beam_active_timer <= 0:
            boss.special_beam_total_active_timer = 0
            boss.special_beam_cooldown = max(90, 180 - min(60, spawn_count * 8))
        return True

    _try_start_special_beam(boss, phase, spawn_count)
    return boss.special_beam_telegraph_timer > 0


def _try_activate_shield(boss: Boss, phase: int, spawn_count: int) -> None:
    if spawn_count < 3:
        return
    if boss.shield_timer > 0:
        return
    if boss.shield_cooldown > 0:
        return
    if boss.laser_active_timer > 0 or boss.laser_telegraph_timer > 0:
        return
    if boss.dash_telegraph_timer > 0 or boss.dash_active_timer > 0 or boss.dash_recover_timer > 0:
        return

    base_duration = {1: 28, 2: 38, 3: 52}[phase]
    boss.shield_timer = base_duration + min(18, spawn_count * 3)
    boss.shield_cooldown = max(160, 320 - min(120, spawn_count * 20))


def _update_shield_state(boss: Boss, phase: int, spawn_count: int) -> None:
    if spawn_count < 3:
        return

    if boss.shield_cooldown > 0:
        boss.shield_cooldown -= 1

    if boss.shield_timer > 0:
        boss.shield_timer -= 1
        return

    _try_activate_shield(boss, phase, spawn_count)


def _summon_enemy_types(spawn_count: int) -> tuple[str, ...]:
    if spawn_count >= 5:
        return ("sprint", "shooter", "spreader")
    if spawn_count >= 4:
        return ("sprint", "shooter")
    return ("sprint",)


def _try_summon_helpers(
    boss: Boss,
    *,
    width: int,
    side_margin: int,
    current_enemy_count: int,
    enemies: list[Enemy],
    create_enemy: CreateEnemyCallback | None,
) -> None:
    spawn_count = getattr(boss, "spawn_count", 0)
    if spawn_count < 4:
        return
    if create_enemy is None:
        return
    if boss.summon_cooldown > 0:
        return
    if boss.shield_timer > 0:
        return
    if boss.dash_telegraph_timer > 0 or boss.dash_active_timer > 0 or boss.dash_recover_timer > 0:
        return
    if current_enemy_count >= 7:
        boss.summon_cooldown = 90
        return

    max_summon = 1 if spawn_count == 4 else 2
    summon_now = min(max_summon, max(0, 7 - current_enemy_count))
    if summon_now <= 0:
        boss.summon_cooldown = 90
        return

    types = _summon_enemy_types(spawn_count)
    offsets = (-64.0, 64.0)

    for idx in range(summon_now):
        summon_type = random.choice(types)
        spawn_x = boss.x + offsets[idx % len(offsets)]
        spawn_x = min(max(spawn_x, side_margin + 20.0), width - side_margin - 20.0)

        enemy = create_enemy(float(spawn_x), summon_type)
        enemy.y = boss.y + boss.hit_half_h + 10 + (idx * 8)
        enemy.shoot_cooldown = max(enemy.shoot_cooldown, 40)
        if summon_type == "sprint":
            enemy.vy *= 1.08
        elif summon_type == "shooter":
            enemy.fire_interval = max(36, int(enemy.fire_interval * 0.88))
        elif summon_type == "spreader":
            enemy.fire_interval = max(44, int(enemy.fire_interval * 0.90))

        enemies.append(enemy)

    boss.summon_flash_timer = 22
    boss.summon_cooldown = max(180, 340 - min(120, spawn_count * 18))


def _update_summon_state(
    boss: Boss,
    *,
    width: int,
    side_margin: int,
    current_enemy_count: int,
    enemies: list[Enemy],
    create_enemy: CreateEnemyCallback | None,
) -> None:
    spawn_count = getattr(boss, "spawn_count", 0)
    if spawn_count < 4:
        return

    if boss.summon_cooldown > 0:
        boss.summon_cooldown -= 1
    if boss.summon_flash_timer > 0:
        boss.summon_flash_timer -= 1

    _try_summon_helpers(
        boss,
        width=width,
        side_margin=side_margin,
        current_enemy_count=current_enemy_count,
        enemies=enemies,
        create_enemy=create_enemy,
    )


def _try_start_dash(
    boss: Boss,
    *,
    phase: int,
    spawn_count: int,
    move_speed_multiplier: float,
    width: int,
    height: int,
    side_margin: int,
    boss_sprite_w: int,
    player_x: float,
    player_y: float,
) -> None:
    if spawn_count < 5:
        return
    if phase < 2:
        return
    if boss.dash_cooldown > 0:
        return
    if boss.dash_telegraph_timer > 0 or boss.dash_active_timer > 0 or boss.dash_recover_timer > 0:
        return
    if boss.shield_timer > 0:
        return
    if boss.laser_telegraph_timer > 0 or boss.laser_active_timer > 0:
        return

    sprite_half_w = (boss_sprite_w * boss.display_scale) / 2.0
    side_min = side_margin + sprite_half_w
    side_max = width - side_margin - sprite_half_w

    target_x = min(max(player_x, side_min), side_max)
    target_y = min(
        max(player_y - 42.0, boss.target_y + 44.0),
        height * 0.72,
    )

    dx = target_x - boss.x
    dy = target_y - boss.y
    distance = max(1.0, math.hypot(dx, dy))
    speed = (8.8 + min(2.2, spawn_count * 0.22)) * move_speed_multiplier

    boss.dash_target_x = target_x
    boss.dash_target_y = target_y
    boss.dash_vx = dx / distance * speed
    boss.dash_vy = dy / distance * speed
    boss.dash_telegraph_timer = max(16, 26 - min(8, spawn_count))
    boss.dash_active_timer = 0
    boss.dash_recover_timer = 0
    boss.dash_cooldown = max(160, 320 - min(120, spawn_count * 16))


def _update_dash_state(
    boss: Boss,
    *,
    phase: int,
    spawn_count: int,
    move_speed_multiplier: float,
    width: int,
    height: int,
    side_margin: int,
    boss_sprite_w: int,
    player_x: float,
    player_y: float,
) -> bool:
    if spawn_count < 5:
        return False

    if boss.dash_cooldown > 0:
        boss.dash_cooldown -= 1

    if boss.dash_telegraph_timer > 0:
        boss.dash_telegraph_timer -= 1
        if boss.dash_telegraph_timer <= 0:
            dx = boss.dash_target_x - boss.x
            dy = boss.dash_target_y - boss.y
            distance = max(1.0, math.hypot(dx, dy))
            speed = max(1.0, math.hypot(boss.dash_vx, boss.dash_vy))
            boss.dash_active_timer = max(6, int(distance / speed))
        return True

    if boss.dash_active_timer > 0:
        boss.x += boss.dash_vx
        boss.y += boss.dash_vy
        boss.dash_active_timer -= 1

        reached_x = (boss.dash_vx >= 0 and boss.x >= boss.dash_target_x) or (boss.dash_vx < 0 and boss.x <= boss.dash_target_x)
        reached_y = (boss.dash_vy >= 0 and boss.y >= boss.dash_target_y) or (boss.dash_vy < 0 and boss.y <= boss.dash_target_y)

        if boss.dash_active_timer <= 0 or (reached_x and reached_y):
            boss.x = boss.dash_target_x
            boss.y = boss.dash_target_y
            boss.dash_active_timer = 0
            boss.dash_recover_timer = 18
            boss.shoot_cooldown = max(boss.shoot_cooldown, 18)
        return True

    if boss.dash_recover_timer > 0:
        boss.dash_recover_timer -= 1
        boss.y += (boss.target_y - boss.y) * 0.28
        return True

    _try_start_dash(
        boss,
        phase=phase,
        spawn_count=spawn_count,
        move_speed_multiplier=move_speed_multiplier,
        width=width,
        height=height,
        side_margin=side_margin,
        boss_sprite_w=boss_sprite_w,
        player_x=player_x,
        player_y=player_y,
    )
    return boss.dash_telegraph_timer > 0


def _boss_fire(
    *,
    boss: Boss,
    frame_count: int,
    player_x: float,
    player_y: float,
    append_enemy_bullet: AppendEnemyBullet,
    spawn_count: int,
    mercy_rage: bool = False,
) -> None:
    phase = boss_phase(boss)
    pattern = boss.pattern_cycle % 3
    bonus_level = min(3, spawn_count)
    soften_rage = phase == 3 and (spawn_count >= 4 or mercy_rage)

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
                ways=8 if soften_rage else 9,
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
                ways=4 if soften_rage else 5,
                spread=0.18,
                speed=4.4,
                radius=4,
                color=10,
                append_enemy_bullet=append_enemy_bullet,
            )
        elif pattern == 1:
            _spawn_boss_ring(
                boss=boss,
                count=16 if soften_rage else 18,
                speed=3.0,
                radius=4,
                color=14,
                angle_offset=frame_count * 0.04,
                append_enemy_bullet=append_enemy_bullet,
            )
            _spawn_boss_ring(
                boss=boss,
                count=8 if soften_rage else 9,
                speed=2.3,
                radius=4,
                color=10,
                angle_offset=(frame_count * 0.04) + 0.22,
                append_enemy_bullet=append_enemy_bullet,
            )
        else:
            _spawn_boss_down_fan(
                boss=boss,
                vx_values=(-2.8, -2.1, -1.4, -0.7, 0.0, 0.7, 1.4, 2.1, 2.8) if soften_rage else (-3.2, -2.6, -2.0, -1.4, -0.8, 0.0, 0.8, 1.4, 2.0, 2.6, 3.2),
                vy=3.1,
                radius=4,
                color=10,
                append_enemy_bullet=append_enemy_bullet,
            )
            _spawn_boss_aimed_fan(
                boss=boss,
                player_x=player_x,
                player_y=player_y,
                ways=4 if soften_rage else 5,
                spread=0.24,
                speed=4.1,
                radius=4,
                color=8,
                append_enemy_bullet=append_enemy_bullet,
            )

    if bonus_level >= 1:
        _spawn_boss_aimed_fan(
            boss=boss,
            player_x=player_x,
            player_y=player_y,
            ways=3,
            spread=0.08,
            speed=4.0 + (phase * 0.15),
            radius=4,
            color=11,
            append_enemy_bullet=append_enemy_bullet,
            display_scale=1.15,
        )

    if bonus_level >= 2 and pattern == 1:
        _spawn_boss_ring(
            boss=boss,
            count=(6 + (phase * 2)) if soften_rage else (8 + (phase * 2)),
            speed=2.0 + (phase * 0.2),
            radius=3,
            color=12,
            angle_offset=(frame_count * 0.025) + 0.14,
            append_enemy_bullet=append_enemy_bullet,
            display_scale=1.0,
        )

    if bonus_level >= 3 and pattern == 2:
        _spawn_boss_down_fan(
            boss=boss,
            vx_values=(-2.7, -1.8, -0.9, 0.0, 0.9, 1.8, 2.7) if soften_rage else (-3.6, -2.7, -1.8, -0.9, 0.0, 0.9, 1.8, 2.7, 3.6),
            vy=3.0 + (phase * 0.12),
            radius=3,
            color=7,
            append_enemy_bullet=append_enemy_bullet,
            display_scale=1.0,
        )

    if getattr(boss, "shield_timer", 0) > 0:
        _spawn_boss_ring(
            boss=boss,
            count=6 + phase * 2,
            speed=1.7 + phase * 0.15,
            radius=3,
            color=6,
            angle_offset=(frame_count * 0.05),
            append_enemy_bullet=append_enemy_bullet,
            display_scale=0.95,
        )

    boss.pattern_cycle += 1


def update_boss(
    *,
    boss: Boss,
    frame_count: int,
    width: int,
    height: int,
    side_margin: int,
    boss_sprite_w: int,
    player_x: float,
    player_y: float,
    append_enemy_bullet: AppendEnemyBullet,
    move_speed_multiplier: float = 1.0,
    spawn_count: int = 0,
    mercy_rage: bool = False,
    enemies: list[Enemy] | None = None,
    create_enemy: CreateEnemyCallback | None = None,
) -> None:
    if not boss.active:
        return

    _ensure_boss_runtime_fields(boss, spawn_count)

    if boss.hit_flash_timer > 0:
        boss.hit_flash_timer -= 1
        boss.was_hit = True
    else:
        boss.was_hit = False

    if not boss.entry_done:
        boss.y += boss.vy * move_speed_multiplier
        boss.entry_invulnerable = True

        if boss.y >= boss.target_y:
            boss.y = boss.target_y
            boss.entry_done = True
            boss.entry_invulnerable = False
            boss.vy = 0.0
            boss.shoot_cooldown = 45

        return

    phase = boss_phase(boss)

    dash_busy = _update_dash_state(
        boss,
        phase=phase,
        spawn_count=spawn_count,
        move_speed_multiplier=move_speed_multiplier,
        width=width,
        height=height,
        side_margin=side_margin,
        boss_sprite_w=boss_sprite_w,
        player_x=player_x,
        player_y=player_y,
    )

    if dash_busy:
        if boss.shoot_cooldown > 0:
            boss.shoot_cooldown -= 1
        return

    speed_bonus = min(0.75, spawn_count * 0.15)
    target_speed = ({1: 2.0, 2: 2.6, 3: 3.2}[phase] + speed_bonus) * move_speed_multiplier
    bob_amp = {1: 7.0, 2: 10.0, 3: 13.0}[phase] + min(5.0, spawn_count * 0.9)
    bob_speed = ({1: 0.05, 2: 0.07, 3: 0.09}[phase] + min(0.03, spawn_count * 0.004)) * move_speed_multiplier
    fire_interval = max(
        12,
        {1: 42, 2: 32, 3: 24}[phase] - min(10, spawn_count * 2),
    )

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

    _update_shield_state(boss, phase, spawn_count)
    _update_laser_state(boss, phase, spawn_count)

    if enemies is not None:
        _update_summon_state(
            boss,
            width=width,
            side_margin=side_margin,
            current_enemy_count=len(enemies),
            enemies=enemies,
            create_enemy=create_enemy,
        )

    special_beam_busy = _update_special_beam_state(boss, phase, spawn_count)
    if special_beam_busy:
        if boss.shoot_cooldown > 0:
            boss.shoot_cooldown -= 1
        return

    if boss.shoot_cooldown > 0:
        boss.shoot_cooldown -= 1
    else:
        _boss_fire(
            boss=boss,
            frame_count=frame_count,
            player_x=player_x,
            player_y=player_y,
            append_enemy_bullet=append_enemy_bullet,
            spawn_count=spawn_count,
            mercy_rage=mercy_rage,
        )
        boss.shoot_cooldown = boss.fire_interval
