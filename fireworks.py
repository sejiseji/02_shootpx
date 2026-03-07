from __future__ import annotations

import math
import random
from cmath import exp

import pyxel


def radial_burst(z: complex, num_particles: int, expansion_rate: float) -> list[complex]:
    return [
        z + exp(1j * 2 * math.pi * i / num_particles) * expansion_rate
        for i in range(num_particles)
    ]


def star_burst(z: complex, expansion_rate: float) -> list[complex]:
    particles: list[complex] = []
    random_offset = random.uniform(0, 2 * math.pi)

    for i in range(5):
        angle = i * 2 * math.pi * 2 / 5 + random_offset
        particles.append(z + complex(math.cos(angle), math.sin(angle)) * expansion_rate)

    inner_expansion_rate = expansion_rate * 0.5
    for i in range(5):
        angle = i * 2 * math.pi * 2 / 5 + math.pi / 5 + random_offset
        particles.append(z + complex(math.cos(angle), math.sin(angle)) * inner_expansion_rate)

    return particles


def ring_burst(z: complex, expansion_rate: float, num_particles: int, width: float) -> list[complex]:
    particles: list[complex] = []
    base_angle = random.uniform(0, 2 * math.pi)
    for i in range(num_particles):
        angle = 2 * math.pi * i / num_particles
        distance = expansion_rate + (i % 10) + width
        particles.append(z + exp(1j * (base_angle + angle)) * distance)
    return particles


def multi_ring_burst(
    z: complex,
    expansion_rate: float,
    num_rings: int,
    num_particles: int,
) -> list[complex]:
    particles: list[complex] = []
    base_angle = random.uniform(0, 2 * math.pi)
    for j in range(num_rings):
        for i in range(num_particles):
            angle = 2 * math.pi * i / num_particles
            distance = expansion_rate * (j + 1)
            particles.append(z + exp(1j * (base_angle + angle)) * distance)
    return particles


def rotate_point(point: complex, angle: float, center: complex) -> complex:
    return exp(1j * angle) * (point - center) + center


def elliptical_burst(z: complex, a: float, b: float, num_particles: int) -> list[complex]:
    angle = random.uniform(0, 2 * math.pi)
    return [
        rotate_point(
            z + complex(
                a * math.cos(2 * math.pi * i / num_particles),
                b * math.sin(2 * math.pi * i / num_particles),
            ),
            angle,
            z,
        )
        for i in range(num_particles)
    ]


def radiating_sphere_projection_burst(
    z: complex,
    r: float,
    num_particles: int,
    expansion_rate: float,
    life_ratio: float,
    rotation_angle: float = 0.0,
) -> list[complex]:
    particles: list[complex] = []
    if num_particles <= 0:
        return particles

    dist = r + expansion_rate * life_ratio

    for i in range(num_particles):
        t = (i + 0.5) / num_particles
        theta = math.acos(1 - 2 * t)
        phi = math.sqrt(num_particles * math.pi) * theta + rotation_angle * 0.75

        x_relative = dist * math.sin(theta) * math.cos(phi)
        y_relative = dist * math.sin(theta) * math.sin(phi)
        z_relative = dist * math.cos(theta)

        y_rotated = y_relative * math.cos(rotation_angle) - z_relative * math.sin(rotation_angle)

        x_final = z.real + x_relative
        y_final = z.imag + y_rotated
        particles.append(complex(x_final, y_final))

    return particles


class BackgroundFirework:
    def __init__(self, x: int, y: int):
        self.x = float(x)
        self.y = float(y)
        self.draw_x = float(x)
        self.draw_y = float(y)

        self.peak = self.draw_y - random.randrange(90, 190)
        self.vy = random.uniform(2.6, 6.8)

        self.active = True
        self.life = random.randrange(48, 78)
        self.burst: list[complex] | None = None
        self.size_scale = random.uniform(1.5, 3.0)

        self.burst_name = random.choice(
            [
                "radial",
                "star",
                "ring",
                "multi_ring",
                "ellipse",
            ]
        )

    def update(self) -> None:
        if self.life <= 0:
            return

        if self.active:
            if self.draw_y > self.peak:
                self.draw_y -= self.vy
            else:
                self.burst = self._create_burst()
                self.active = False
        else:
            self._expand_burst()
            self.life -= 1

    def is_dead(self) -> bool:
        return (not self.active) and self.life <= 0

    def _create_burst(self) -> list[complex]:
        center = complex(self.draw_x, self.draw_y)

        if self.burst_name == "radial":
            return radial_burst(center, 24, random.uniform(10, 22) * self.size_scale)

        if self.burst_name == "star":
            return star_burst(center, random.uniform(12, 26) * self.size_scale)

        if self.burst_name == "ring":
            return ring_burst(
                center,
                random.choice([8, 12, 16]) * self.size_scale,
                24,
                3 * self.size_scale,
            )

        if self.burst_name == "multi_ring":
            return multi_ring_burst(
                center,
                random.choice([5, 7, 9]) * self.size_scale,
                3,
                16,
            )

        if self.burst_name == "ellipse":
            major = random.randrange(18, 30) * self.size_scale
            minor = random.randrange(10, 18) * self.size_scale
            return elliptical_burst(center, major, minor, 28)

        return radial_burst(center, 20, 14 * self.size_scale)

    def _expand_burst(self) -> None:
        if not self.burst:
            return

        expansion_factor = 1.015
        center = complex(self.draw_x, self.draw_y)

        relative = [pt - center for pt in self.burst]
        expanded = [pt * expansion_factor for pt in relative]
        self.burst = [center + pt for pt in expanded]

    def draw(self, frame_count: int) -> None:
        if self.active:
            x = int(self.draw_x)
            y = int(self.draw_y)

            pyxel.line(x, y + 4, x, y + 10, 15)
            pyxel.line(x, y, x, y + 3, 7)
            pyxel.pset(x, y - 1, frame_count % 16)
            return

        if not self.burst:
            return

        color = self._pick_color(frame_count)

        if self.burst_name == "star" and len(self.burst) >= 10:
            outer_points = self.burst[:5]
            inner_points = self.burst[5:]
            connection_indices = [3, 4, 0, 1, 2]

            for i in range(5):
                pyxel.line(
                    int(outer_points[i].real),
                    int(outer_points[i].imag),
                    int(inner_points[i].real),
                    int(inner_points[i].imag),
                    color,
                )
                pyxel.line(
                    int(inner_points[i].real),
                    int(inner_points[i].imag),
                    int(outer_points[connection_indices[i]].real),
                    int(outer_points[connection_indices[i]].imag),
                    color,
                )

        for pt in self.burst:
            x = int(pt.real)
            y = int(pt.imag)

            if 0 <= x < pyxel.width and 0 <= y < pyxel.height:
                pyxel.pset(x, y, color)

                if self.life > 28:
                    if x + 1 < pyxel.width:
                        pyxel.pset(x + 1, y, color)
                    if y + 1 < pyxel.height:
                        pyxel.pset(x, y + 1, color)

    def _pick_color(self, frame_count: int) -> int:
        if self.life > 50:
            return random.choice([7, 10, 11, 14])
        if 50 >= self.life > 30:
            return random.choice([8, 9, 12, 13])
        if 30 >= self.life > 12:
            return random.choice([2, 3, 6, 7])
        return frame_count % 16


class ImpactFirework:
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.life = random.randrange(12, 22)
        self.max_life = self.life
        self.expansion_factor = random.uniform(1.02, 1.06)

        self.kind = random.choice(["radial", "star", "ring"])
        self.points = self._create_burst()

    def _create_burst(self) -> list[complex]:
        center = complex(self.x, self.y)
        size = random.uniform(5.0, 12.0)

        if self.kind == "radial":
            return radial_burst(center, 10, size)
        if self.kind == "star":
            return star_burst(center, size)
        return ring_burst(center, size * 0.6, 10, 1.5)

    def update(self) -> None:
        if self.life <= 0:
            return

        center = complex(self.x, self.y)
        new_points: list[complex] = []

        for pt in self.points:
            rel = pt - center
            rel *= self.expansion_factor
            rel *= exp(1j * 0.03)
            new_points.append(center + rel)

        self.points = new_points
        self.life -= 1

    def is_dead(self) -> bool:
        return self.life <= 0

    def draw(self, frame_count: int) -> None:
        color = self._pick_color(frame_count)

        if self.kind == "star" and len(self.points) >= 10:
            outer_points = self.points[:5]
            inner_points = self.points[5:]
            connection_indices = [3, 4, 0, 1, 2]

            for i in range(5):
                pyxel.line(
                    int(outer_points[i].real),
                    int(outer_points[i].imag),
                    int(inner_points[i].real),
                    int(inner_points[i].imag),
                    color,
                )
                pyxel.line(
                    int(inner_points[i].real),
                    int(inner_points[i].imag),
                    int(outer_points[connection_indices[i]].real),
                    int(outer_points[connection_indices[i]].imag),
                    color,
                )

        for pt in self.points:
            x = int(pt.real)
            y = int(pt.imag)
            if 0 <= x < pyxel.width and 0 <= y < pyxel.height:
                pyxel.pset(x, y, color)

                if self.life > self.max_life // 2:
                    if x + 1 < pyxel.width:
                        pyxel.pset(x + 1, y, color)
                    if y + 1 < pyxel.height:
                        pyxel.pset(x, y + 1, color)

    def _pick_color(self, frame_count: int) -> int:
        if self.life > self.max_life * 0.66:
            return random.choice([7, 10, 14, 15])
        if self.life > self.max_life * 0.33:
            return random.choice([8, 9, 11, 12])
        return frame_count % 16