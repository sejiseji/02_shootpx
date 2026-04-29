from __future__ import annotations

import math
import random
from typing import Callable

from game_models import Enemy


AppendEnemyBulletFn = Callable[..., bool]


ENEMY_SUSHI_TYPE = {
    "basic": "tuna",
    "zigzag": "salmon",
    "shooter": "egg",
    "tank": "shrimp",
    "sprint": "tuna",
    "spreader": "gunkan",
    "aimer": "salmon",
    "rare": "gunkan",
    "tuna_fish": "tuna",
    "salmon_fish": "salmon",
    "egg_fish": "egg",
    "shrimp_fish": "shrimp",
    "gunkan_fish": "gunkan",
    "sprint_fish": "tuna",
    "aimer_fish": "salmon",
}

SOURCE_FISH_TO_SUSHI_ENEMY = {
    "tuna_fish": "basic",
    "salmon_fish": "zigzag",
    "egg_fish": "shooter",
    "shrimp_fish": "tank",
    "sprint_fish": "sprint",
    "gunkan_fish": "spreader",
    "aimer_fish": "aimer",
}

SOURCE_FISH_TYPES = tuple(SOURCE_FISH_TO_SUSHI_ENEMY.keys())


def pick_enemy_type(score: int, loop_depth: int = 0) -> str:
    rare_chance = min(0.035, 0.008 + loop_depth * 0.004)
    if random.random() < rare_chance:
        return "rare"

    enemy_types = [
        "basic",
        "zigzag",
        "shooter",
        "tank",
        "sprint",
        "spreader",
        "aimer",
    ]

    if score < 80:
        weights = [42, 18, 14, 0, 26, 0, 0]
        source_weights = [0, 0, 0, 0, 0, 0, 0]
    elif score < 180:
        weights = [24, 14, 18, 10, 12, 12, 10]
        source_weights = [5, 4, 3, 2, 2, 2, 2]
    else:
        weights = [14, 10, 14, 16, 10, 18, 18]
        source_weights = [7, 6, 5, 4, 4, 4, 4]

    if loop_depth >= 3:
        source_weights = [weight + 1 for weight in source_weights]

    return random.choices(enemy_types + list(SOURCE_FISH_TYPES), weights=weights + source_weights, k=1)[0]


def pick_enemy_scale(enemy_type: str) -> float:
    ranges = {
        "basic": (1.45, 1.87),
        "zigzag": (1.36, 1.70),
        "shooter": (1.53, 1.91),
        "tank": (1.79, 2.38),
        "sprint": (1.28, 1.53),
        "spreader": (1.45, 1.87),
        "aimer": (1.53, 2.00),
        "rare": (1.34, 1.68),
        "tuna_fish": (2.10, 2.54),
        "salmon_fish": (2.04, 2.46),
        "egg_fish": (2.00, 2.40),
        "shrimp_fish": (2.18, 2.66),
        "sprint_fish": (1.92, 2.30),
        "gunkan_fish": (2.06, 2.52),
        "aimer_fish": (1.98, 2.38),
    }
    low, high = ranges.get(enemy_type, (1.45, 1.87))
    return random.uniform(low, high)


def scale_enemy_hp(base_hp: int, display_scale: float) -> int:
    factor = 0.70 + 0.35 * display_scale
    return max(1, math.ceil(base_hp * factor))


def scale_enemy_score(base_score: int, display_scale: float) -> int:
    factor = 0.75 + 0.55 * display_scale
    return max(base_score, int(round(base_score * factor)))


def scale_enemy_vx(base_vx: float, display_scale: float) -> float:
    if base_vx == 0:
        return 0.0
    factor = max(0.55, 1.15 - 0.16 * display_scale)
    return base_vx * factor


def scale_enemy_vy(base_vy: float, display_scale: float) -> float:
    factor = max(0.55, 1.18 - 0.18 * display_scale)
    return base_vy * factor


def build_enemy_hitbox(
    *,
    enemy_half_w: float,
    enemy_half_h: float,
    display_scale: float,
) -> tuple[float, float]:
    hit_half_w = max(6.5, enemy_half_w * display_scale * 0.76)
    hit_half_h = max(6.5, enemy_half_h * display_scale * 0.72)
    return hit_half_w, hit_half_h


def scale_enemy_bullet_radius(base_radius: int, display_scale: float) -> int:
    factor = max(1.0, 0.85 + 0.30 * display_scale)
    return max(2, int(round(base_radius * factor)))


def scale_enemy_bullet_speed_y(base_vy: float, display_scale: float) -> float:
    factor = max(0.72, 1.08 - 0.10 * display_scale)
    return base_vy * factor


def scale_enemy_bullet_speed_x(base_vx: float, display_scale: float) -> float:
    factor = max(0.72, 1.05 - 0.08 * display_scale)
    return base_vx * factor


def build_enemy_bullet_display_scale(display_scale: float) -> float:
    return max(1.0, 0.85 + 0.30 * display_scale)


def create_enemy(
    *,
    spawn_x: float,
    enemy_type: str,
    enemy_half_h: float,
    enemy_half_w: float,
    loop_depth: int = 0,
) -> Enemy:
    move_phase = random.uniform(0.0, math.tau)
    display_scale = pick_enemy_scale(enemy_type)

    if enemy_type == "zigzag":
        base_vx = random.uniform(1.2, 2.0)
        base_vy = random.uniform(1.6, 2.6)
        base_hp = 1
        base_score = 15
        shoot_cooldown = random.randrange(9999, 12000)
        fire_interval = 9999
        bullet_speed = 0.0

    elif enemy_type == "shooter":
        base_vx = random.choice([-0.6, 0.6])
        base_vy = random.uniform(1.1, 1.8)
        base_hp = 2
        base_score = 20
        shoot_cooldown = random.randrange(35, 70)
        fire_interval = random.randrange(55, 95)
        bullet_speed = scale_enemy_bullet_speed_y(
            random.uniform(2.4, 3.0),
            display_scale,
        )

    elif enemy_type == "tank":
        base_vx = random.choice([-0.4, 0.4])
        base_vy = random.uniform(0.9, 1.5)
        base_hp = 3
        base_score = 30
        shoot_cooldown = random.randrange(55, 95)
        fire_interval = random.randrange(70, 120)
        bullet_speed = scale_enemy_bullet_speed_y(
            random.uniform(2.0, 2.6),
            display_scale,
        )

    elif enemy_type == "sprint":
        base_vx = random.choice([-0.9, 0.9])
        base_vy = random.uniform(2.4, 4.2)
        base_hp = 1
        base_score = 18
        shoot_cooldown = random.randrange(9999, 12000)
        fire_interval = 9999
        bullet_speed = 0.0

    elif enemy_type == "spreader":
        base_vx = random.choice([-0.5, 0.5])
        base_vy = random.uniform(1.0, 1.6)
        base_hp = 2
        base_score = 24
        shoot_cooldown = random.randrange(45, 75)
        fire_interval = random.randrange(70, 110)
        bullet_speed = scale_enemy_bullet_speed_y(
            random.uniform(2.2, 2.8),
            display_scale,
        )

    elif enemy_type == "aimer":
        base_vx = random.choice([-0.35, 0.35])
        base_vy = random.uniform(0.9, 1.4)
        base_hp = 2
        base_score = 28
        shoot_cooldown = random.randrange(55, 95)
        fire_interval = random.randrange(90, 130)
        bullet_speed = scale_enemy_bullet_speed_y(
            random.uniform(2.6, 3.2),
            display_scale,
        )

    elif enemy_type == "rare":
        base_vx = random.choice([-1.1, 1.1])
        base_vy = random.uniform(1.9, 2.7)
        base_hp = 2
        base_score = 180
        shoot_cooldown = random.randrange(9999, 12000)
        fire_interval = 9999
        bullet_speed = 0.0

    elif enemy_type in SOURCE_FISH_TYPES:
        base_vx = random.choice([-0.45, 0.45])
        base_vy = random.uniform(1.0, 1.7)
        base_hp = 4
        base_score = 45
        shoot_cooldown = random.randrange(9999, 12000)
        fire_interval = 9999
        bullet_speed = 0.0

    else:
        base_vx = 0.0
        base_vy = random.uniform(1.8, 3.6)
        base_hp = 1
        base_score = 10
        shoot_cooldown = random.randrange(9999, 12000)
        fire_interval = 9999
        bullet_speed = 0.0

    scaled_vx = scale_enemy_vx(base_vx, display_scale)
    scaled_vy = scale_enemy_vy(base_vy, display_scale)
    scaled_hp = scale_enemy_hp(base_hp, display_scale)
    scaled_score = scale_enemy_score(base_score, display_scale)

    loop_hp_scale = 1.0 + min(0.70, loop_depth * 0.12)
    loop_move_scale = 1.0 + min(0.32, loop_depth * 0.05)
    loop_bullet_scale = 1.0 + min(0.34, loop_depth * 0.06)
    loop_fire_scale = max(0.68, 1.0 - loop_depth * 0.045)

    scaled_vx *= loop_move_scale
    scaled_vy *= loop_move_scale
    scaled_hp = max(1, int(math.ceil(scaled_hp * loop_hp_scale)))
    scaled_score = max(base_score, int(round(scaled_score * (1.0 + loop_depth * 0.10))))
    bullet_speed *= loop_bullet_scale
    if fire_interval < 9999:
        fire_interval = max(32, int(round(fire_interval * loop_fire_scale)))
        shoot_cooldown = max(18, int(round(shoot_cooldown * loop_fire_scale)))

    if enemy_type == "rare":
        scaled_vx *= 1.20
        scaled_vy *= 1.12
        scaled_score = max(scaled_score, 220 + loop_depth * 30)
    elif enemy_type in SOURCE_FISH_TYPES:
        scaled_hp = max(scaled_hp, int(math.ceil(scaled_hp * 1.7)))
        scaled_score = max(scaled_score, 55 + loop_depth * 8)

    hit_half_w, hit_half_h = build_enemy_hitbox(
        enemy_half_w=enemy_half_w,
        enemy_half_h=enemy_half_h,
        display_scale=display_scale,
    )

    return Enemy(
        x=spawn_x,
        y=float(-enemy_half_h * display_scale),
        vx=scaled_vx,
        vy=scaled_vy,
        enemy_type=enemy_type,
        hp=scaled_hp,
        max_hp=scaled_hp,
        shoot_cooldown=shoot_cooldown,
        fire_interval=fire_interval,
        bullet_speed=bullet_speed,
        move_phase=move_phase,
        anim_offset=random.randrange(0, 8),
        anim_dir=random.choice((-1, 1)),
        score_value=scaled_score,
        display_scale=display_scale,
        hit_half_w=hit_half_w,
        hit_half_h=hit_half_h,
        sushi_type=ENEMY_SUSHI_TYPE.get(enemy_type, "tuna"),
        enemy_category="fish_source" if enemy_type in SOURCE_FISH_TYPES else "sushi_enemy",
        split_spawn_enemy_type=SOURCE_FISH_TO_SUSHI_ENEMY.get(enemy_type),
        split_spawn_min=2 if enemy_type in SOURCE_FISH_TYPES else 0,
        split_spawn_max=3 if enemy_type in SOURCE_FISH_TYPES else 0,
        sprite_variant=random.randrange(0, 7) if enemy_type == "rare" else 0,
    )


def spawn_enemy_shot(
    *,
    enemy: Enemy,
    player_x: float,
    player_y: float,
    append_enemy_bullet: AppendEnemyBulletFn,
) -> None:
    base_x = enemy.x
    base_y = enemy.y + enemy.hit_half_h + 4
    bullet_scale = build_enemy_bullet_display_scale(enemy.display_scale)

    if enemy.enemy_type == "shooter":
        radius = scale_enemy_bullet_radius(3, enemy.display_scale)
        append_enemy_bullet(
            x=base_x,
            y=base_y,
            vx=0.0,
            vy=enemy.bullet_speed,
            radius=radius,
            color=8,
            damage=1,
            display_scale=bullet_scale,
        )
        return

    if enemy.enemy_type == "tank":
        radius = scale_enemy_bullet_radius(4, enemy.display_scale)
        for base_vx in (-0.8, 0.8):
            append_enemy_bullet(
                x=base_x,
                y=base_y,
                vx=scale_enemy_bullet_speed_x(base_vx, enemy.display_scale),
                vy=enemy.bullet_speed,
                radius=radius,
                color=14,
                damage=1,
                display_scale=bullet_scale,
            )
        return

    if enemy.enemy_type == "spreader":
        radius = scale_enemy_bullet_radius(3, enemy.display_scale)
        for base_vx in (-1.0, 0.0, 1.0):
            append_enemy_bullet(
                x=base_x,
                y=base_y,
                vx=scale_enemy_bullet_speed_x(base_vx, enemy.display_scale),
                vy=enemy.bullet_speed,
                radius=radius,
                color=9,
                damage=1,
                display_scale=bullet_scale,
            )
        return

    if enemy.enemy_type == "aimer":
        radius = scale_enemy_bullet_radius(4, enemy.display_scale)
        dx = player_x - base_x
        dy = player_y - base_y
        length = math.hypot(dx, dy)
        if length <= 0.0001:
            aim_vx = 0.0
            aim_vy = enemy.bullet_speed
        else:
            aim_vx = dx / length * enemy.bullet_speed
            aim_vy = dy / length * enemy.bullet_speed

        append_enemy_bullet(
            x=base_x,
            y=base_y,
            vx=aim_vx,
            vy=aim_vy,
            radius=radius,
            color=10,
            damage=1,
            display_scale=bullet_scale,
        )


def update_enemies(
    *,
    enemies: list[Enemy],
    frame_count: int,
    side_margin: int,
    width: int,
    enemy_half_w: float,
    player_x: float,
    player_y: float,
    enemy_bullet_max_count: int,
    current_enemy_bullet_count: int,
    append_enemy_bullet: AppendEnemyBulletFn,
    drift_x_bias: float = 0.0,
) -> None:
    for enemy in enemies:
        sprite_half_w = enemy_half_w * enemy.display_scale
        side_min = side_margin + sprite_half_w
        side_max = width - side_margin - sprite_half_w

        if enemy.state == "retreating":
            enemy.x += enemy.retreat_vx
            enemy.y += enemy.retreat_vy
            enemy.anim_state = (frame_count // 8) % 2
            enemy.was_hit = False
            if enemy.hit_flash_timer > 0:
                enemy.hit_flash_timer -= 1
            if enemy.invincible_timer > 0:
                enemy.invincible_timer -= 1
            enemy.shoot_cooldown = max(enemy.shoot_cooldown, 999)
            continue

        if enemy.enemy_type == "zigzag":
            enemy.x += math.sin((frame_count * 0.12) + enemy.move_phase) * enemy.vx
        elif enemy.enemy_type == "spreader":
            enemy.x += enemy.vx * 0.45 + math.sin((frame_count * 0.08) + enemy.move_phase) * enemy.vx
        elif enemy.enemy_type == "aimer":
            enemy.x += enemy.vx * 0.30 + math.cos((frame_count * 0.06) + enemy.move_phase) * enemy.vx
        elif enemy.enemy_type == "sprint":
            enemy.x += enemy.vx
            if frame_count % 32 == 0:
                enemy.vx *= -1.0
        elif enemy.enemy_type == "rare":
            enemy.x += math.sin((frame_count * 0.16) + enemy.move_phase) * enemy.vx * 0.95
        elif enemy.enemy_type in SOURCE_FISH_TYPES:
            enemy.x += math.sin((frame_count * 0.10) + enemy.move_phase) * enemy.vx * 0.65
        else:
            enemy.x += enemy.vx

        enemy.x += drift_x_bias
        enemy.y += enemy.vy
        enemy.x += enemy.knockback_vx
        enemy.y += enemy.knockback_vy
        enemy.knockback_vx *= 0.72
        enemy.knockback_vy *= 0.72
        if abs(enemy.knockback_vx) < 0.02:
            enemy.knockback_vx = 0.0
        if abs(enemy.knockback_vy) < 0.02:
            enemy.knockback_vy = 0.0
        enemy.anim_state = (frame_count // 10) % 2

        if enemy.x < side_min:
            enemy.x = side_min
            if enemy.enemy_type != "zigzag":
                enemy.vx = abs(enemy.vx)
        elif enemy.x > side_max:
            enemy.x = side_max
            if enemy.enemy_type != "zigzag":
                enemy.vx = -abs(enemy.vx)

        if enemy.hit_flash_timer > 0:
            enemy.hit_flash_timer -= 1
            enemy.was_hit = True
        else:
            enemy.was_hit = False

        if enemy.invincible_timer > 0:
            enemy.invincible_timer -= 1

        if enemy.shoot_cooldown > 0:
            enemy.shoot_cooldown -= 1
        elif enemy.enemy_type in {"shooter", "tank", "spreader", "aimer"}:
            if current_enemy_bullet_count < enemy_bullet_max_count:
                spawn_enemy_shot(
                    enemy=enemy,
                    player_x=player_x,
                    player_y=player_y,
                    append_enemy_bullet=append_enemy_bullet,
                )
                enemy.shoot_cooldown = enemy.fire_interval
