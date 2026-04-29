from __future__ import annotations

import math
from dataclasses import dataclass

import pyxel

TRANSPARENT = -1

# 16x16 source frames
# "." = transparent
# "f" = 15
# "w" = 7
# "y" = 10
# "o" = 9
# "r" = 8
_ENEMY_BURST_SYMBOL_TO_COLOR = {
    ".": TRANSPARENT,
    "f": 15,
    "w": 7,
    "y": 10,
    "o": 9,
    "r": 8,
}

_ENEMY_BURST_FRAME_PATTERNS = [
    [
        "................",
        "................",
        "................",
        "................",
        "................",
        ".....royor......",
        ".....oywyo......",
        ".....ywfwy......",
        ".....oywyo......",
        ".....royor......",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    [
        "................",
        "................",
        "................",
        ".......o........",
        "....r.ooo.r.....",
        ".....oyyyo......",
        "....oyfwfyo.....",
        "...ooywfwyoo....",
        "....oyfwfyo.....",
        ".....oyyyo......",
        "....r.ooo.r.....",
        ".......o........",
        "................",
        "................",
        "................",
        "................",
    ],
    [
        "................",
        "................",
        "................",
        ".....o.y.o......",
        "....oroooro.....",
        "...oroyyyoro....",
        "....oywfwyo.....",
        "...yoyfffyoy....",
        "....oywfwyo.....",
        "...oroyyyoro....",
        "....oroooro.....",
        ".....o.y.o......",
        "................",
        "................",
        "................",
        "................",
    ],
    [
        "................",
        "................",
        ".....or.ro......",
        "...o...o...o....",
        "................",
        "..o..royor..o...",
        "..r..oywyo..r...",
        "...o.ywywy.o....",
        "..r..oywyo..r...",
        "..o..royor..o...",
        "................",
        "...o...o...o....",
        ".....or.ro......",
        "................",
        "................",
        "................",
    ],
    [
        ".......f........",
        "......r.r.......",
        ".....o...o......",
        "................",
        "....o..o..o.....",
        "..o.........o...",
        ".r....owo....r..",
        "f...o.wyw.o...f.",
        ".r....owo....r..",
        "..o.........o...",
        "....o..o..o.....",
        "................",
        ".....o...o......",
        "......r.r.......",
        ".......f........",
        "................",
    ],
    [
        ".....o.f.o......",
        "....r.....r.....",
        "......o.o.......",
        "................",
        ".r...........r..",
        "o....o.o.o....o.",
        "..o.........o...",
        "f....o...o....f.",
        "..o.........o...",
        "o....o.o.o....o.",
        ".r...........r..",
        "................",
        "......o.o.......",
        "....r.....r.....",
        ".....o.f.o......",
        "................",
    ],
    [
        "....f.....f.....",
        "......r.r.......",
        "................",
        ".......o........",
        "f.............f.",
        "................",
        ".r...........r..",
        "...o.......o....",
        ".r...........r..",
        "................",
        "f.............f.",
        ".......o........",
        "................",
        "......r.r.......",
        "....f.....f.....",
        "................",
    ],
]


def _decode_frame(pattern: list[str]) -> list[list[int]]:
    return [
        [_ENEMY_BURST_SYMBOL_TO_COLOR[ch] for ch in row]
        for row in pattern
    ]


ENEMY_BURST_FRAMES: list[list[list[int]]] = [
    _decode_frame(pattern)
    for pattern in _ENEMY_BURST_FRAME_PATTERNS
]


@dataclass
class BaseEffect:
    x: float
    y: float
    layer: int = 0
    active: bool = True

    def update(self) -> None:
        raise NotImplementedError

    def draw(self) -> None:
        raise NotImplementedError


class EnemyBurstEffect(BaseEffect):
    SOURCE_SIZE = 16
    FRAME_HOLD = 3

    def __init__(self, x: float, y: float, scale: float = 1.0, layer: int = 10):
        super().__init__(x=x, y=y, layer=layer, active=True)
        self.scale = max(0.6, scale)
        self.frame_index = 0
        self.frame_timer = 0

    def update(self) -> None:
        if not self.active:
            return

        self.frame_timer += 1
        if self.frame_timer < self.FRAME_HOLD:
            return

        self.frame_timer = 0
        self.frame_index += 1
        if self.frame_index >= len(ENEMY_BURST_FRAMES):
            self.active = False

    def draw(self) -> None:
        if not self.active:
            return

        if self.frame_index >= len(ENEMY_BURST_FRAMES):
            return

        frame = ENEMY_BURST_FRAMES[self.frame_index]
        scaled_size = self.SOURCE_SIZE * self.scale
        origin_x = self.x - (scaled_size / 2.0)
        origin_y = self.y - (scaled_size / 2.0)

        for sy, row in enumerate(frame):
            y0 = int(round(origin_y + (sy * self.scale)))
            y1 = int(round(origin_y + ((sy + 1) * self.scale))) - 1
            if y1 < y0:
                y1 = y0

            for sx, color in enumerate(row):
                if color == TRANSPARENT:
                    continue

                x0 = int(round(origin_x + (sx * self.scale)))
                x1 = int(round(origin_x + ((sx + 1) * self.scale))) - 1
                if x1 < x0:
                    x1 = x0

                pyxel.rect(
                    x0,
                    y0,
                    x1 - x0 + 1,
                    y1 - y0 + 1,
                    color,
                )


class HitSparkEffect(BaseEffect):
    MAX_LIFE = 8

    def __init__(self, x: float, y: float, scale: float = 1.0, layer: int = 11):
        super().__init__(x=x, y=y, layer=layer, active=True)
        self.scale = max(0.5, scale)
        self.life = self.MAX_LIFE
        self.max_life = self.MAX_LIFE

    def update(self) -> None:
        if not self.active:
            return

        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self) -> None:
        if not self.active:
            return

        progress = 1.0 - (self.life / self.max_life)
        arm = max(1, int(round((6.0 * self.scale) * (1.0 - 0.45 * progress))))
        diag = max(1, int(round((4.0 * self.scale) * (1.0 - 0.40 * progress))))

        cx = int(round(self.x))
        cy = int(round(self.y))

        pyxel.line(cx - arm, cy, cx + arm, cy, 10)
        pyxel.line(cx, cy - arm, cx, cy + arm, 10)

        pyxel.line(cx - diag, cy - diag, cx + diag, cy + diag, 7)
        pyxel.line(cx - diag, cy + diag, cx + diag, cy - diag, 7)

        pyxel.pset(cx - arm - 1, cy, 9)
        pyxel.pset(cx + arm + 1, cy, 9)
        pyxel.pset(cx, cy - arm - 1, 9)
        pyxel.pset(cx, cy + arm + 1, 9)

        pyxel.rect(cx - 1, cy - 1, 3, 3, 7)


class LaserImpactEffect(BaseEffect):
    MAX_LIFE = 7

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        scale: float = 1.0,
        layer: int = 12,
    ):
        super().__init__(x=x, y=y, layer=layer, active=True)
        self.scale = max(0.6, scale)
        self.life = self.MAX_LIFE
        self.max_life = self.MAX_LIFE

        length = math.hypot(vx, vy)
        if length <= 0.0001:
            self.dir_x = 0.0
            self.dir_y = -1.0
        else:
            self.dir_x = vx / length
            self.dir_y = vy / length

        self.perp_x = -self.dir_y
        self.perp_y = self.dir_x

    def update(self) -> None:
        if not self.active:
            return

        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self) -> None:
        if not self.active:
            return

        progress = 1.0 - (self.life / self.max_life)

        main_len = max(2, int(round((8.0 * self.scale) * (1.0 - 0.50 * progress))))
        side_len = max(1, int(round((4.0 * self.scale) * (1.0 - 0.55 * progress))))
        back_len = max(1, int(round((3.0 * self.scale) * (1.0 - 0.50 * progress))))

        cx = self.x
        cy = self.y

        fx = cx + self.dir_x * main_len
        fy = cy + self.dir_y * main_len
        bx = cx - self.dir_x * back_len
        by = cy - self.dir_y * back_len

        lx = cx + self.perp_x * side_len
        ly = cy + self.perp_y * side_len
        rx = cx - self.perp_x * side_len
        ry = cy - self.perp_y * side_len

        pyxel.line(int(round(bx)), int(round(by)), int(round(fx)), int(round(fy)), 7)
        pyxel.line(int(round(lx)), int(round(ly)), int(round(rx)), int(round(ry)), 12)

        pyxel.line(
            int(round(cx - self.perp_x * 2 - self.dir_x * 2)),
            int(round(cy - self.perp_y * 2 - self.dir_y * 2)),
            int(round(cx + self.perp_x * 2 + self.dir_x * 2)),
            int(round(cy + self.perp_y * 2 + self.dir_y * 2)),
            6,
        )
        pyxel.line(
            int(round(cx + self.perp_x * 2 - self.dir_x * 2)),
            int(round(cy + self.perp_y * 2 - self.dir_y * 2)),
            int(round(cx - self.perp_x * 2 + self.dir_x * 2)),
            int(round(cy - self.perp_y * 2 + self.dir_y * 2)),
            6,
        )

        pyxel.rect(int(round(cx)) - 1, int(round(cy)) - 1, 3, 3, 7)


class BombLaunchFlashEffect(BaseEffect):
    MAX_LIFE = 12

    def __init__(self, x: float, y: float, scale: float = 1.0, layer: int = 9):
        super().__init__(x=x, y=y, layer=layer, active=True)
        self.scale = max(0.8, scale)
        self.life = self.MAX_LIFE
        self.max_life = self.MAX_LIFE

    def update(self) -> None:
        if not self.active:
            return

        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self) -> None:
        if not self.active:
            return

        progress = 1.0 - (self.life / self.max_life)

        inner_r = max(1, int(round((3.0 + 3.0 * progress) * self.scale)))
        outer_r = max(2, int(round((5.0 + 9.0 * progress) * self.scale)))
        ray_len = max(2, int(round((7.0 + 10.0 * progress) * self.scale)))

        cx = int(round(self.x))
        cy = int(round(self.y))

        pyxel.circ(cx, cy, inner_r, 10)
        pyxel.circb(cx, cy, outer_r, 7)
        pyxel.circb(cx, cy, max(1, outer_r - 2), 9)

        pyxel.line(cx - ray_len, cy, cx + ray_len, cy, 10)
        pyxel.line(cx, cy - ray_len, cx, cy + ray_len, 10)

        diag = max(1, int(round(ray_len * 0.72)))
        pyxel.line(cx - diag, cy - diag, cx + diag, cy + diag, 7)
        pyxel.line(cx - diag, cy + diag, cx + diag, cy - diag, 7)


class BulletCancelSpriteEffect(BaseEffect):
    FRAME_COUNT = 8
    FRAME_HOLD = 2
    SPRITE_BANK = 0
    SPRITE_U = 224
    SPRITE_V = 0
    SPRITE_SIZE = 16
    COLKEY = 0

    def __init__(self, x: float, y: float, scale: float = 1.0, layer: int = 11):
        super().__init__(x=x, y=y, layer=layer, active=True)
        self.scale = max(0.8, scale)
        self.frame_index = 0
        self.frame_timer = 0

    def update(self) -> None:
        if not self.active:
            return

        self.frame_timer += 1
        if self.frame_timer < self.FRAME_HOLD:
            return

        self.frame_timer = 0
        self.frame_index += 1
        if self.frame_index >= self.FRAME_COUNT:
            self.active = False

    def draw(self) -> None:
        if not self.active or self.frame_index >= self.FRAME_COUNT:
            return

        draw_size = self.SPRITE_SIZE * self.scale
        draw_x = int(round(self.x - draw_size / 2.0))
        draw_y = int(round(self.y - draw_size / 2.0))
        pyxel.blt(
            draw_x,
            draw_y,
            self.SPRITE_BANK,
            self.SPRITE_U,
            self.SPRITE_V + self.frame_index * self.SPRITE_SIZE,
            self.SPRITE_SIZE,
            self.SPRITE_SIZE,
            self.COLKEY,
            0.0,
            self.scale,
        )


class EffectManager:
    def __init__(self, max_effects: int = 72):
        self.effects: list[BaseEffect] = []
        self.max_effects = max_effects

    def clear(self) -> None:
        self.effects.clear()

    def add(self, effect: BaseEffect) -> None:
        self.effects.append(effect)
        if len(self.effects) > self.max_effects:
            overflow = len(self.effects) - self.max_effects
            if overflow > 0:
                self.effects = self.effects[overflow:]

    def spawn_enemy_burst(self, x: float, y: float, scale: float = 1.0, layer: int = 10) -> None:
        self.add(EnemyBurstEffect(x=x, y=y, scale=scale, layer=layer))

    def spawn_hit_spark(self, x: float, y: float, scale: float = 1.0, layer: int = 11) -> None:
        self.add(HitSparkEffect(x=x, y=y, scale=scale, layer=layer))

    def spawn_laser_impact(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        scale: float = 1.0,
        layer: int = 12,
    ) -> None:
        self.add(LaserImpactEffect(x=x, y=y, vx=vx, vy=vy, scale=scale, layer=layer))

    def spawn_bomb_launch_flash(self, x: float, y: float, scale: float = 1.0, layer: int = 9) -> None:
        self.add(BombLaunchFlashEffect(x=x, y=y, scale=scale, layer=layer))

    def spawn_bullet_cancel_sprite(self, x: float, y: float, scale: float = 1.0, layer: int = 11) -> None:
        self.add(BulletCancelSpriteEffect(x=x, y=y, scale=scale, layer=layer))

    def update(self) -> None:
        for effect in self.effects:
            effect.update()
        self.effects = [effect for effect in self.effects if effect.active]

    def draw(self) -> None:
        for effect in sorted(self.effects, key=lambda effect: effect.layer):
            effect.draw()
