from __future__ import annotations

import math


def normalize_vector(x: float, y: float, z: float) -> tuple[float, float, float]:
    length = math.sqrt(x * x + y * y + z * z)
    if length <= 1e-8:
        return 0.0, 0.0, 1.0
    inv = 1.0 / length
    return x * inv, y * inv, z * inv


def quaternion_from_axis_angle(axis: tuple[float, float, float], angle: float) -> tuple[float, float, float, float]:
    ax, ay, az = normalize_vector(*axis)
    half = angle * 0.5
    s = math.sin(half)
    return math.cos(half), ax * s, ay * s, az * s


def quaternion_multiply(
    q1: tuple[float, float, float, float],
    q2: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return (
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    )


def rotate_vector_by_quaternion(
    vector: tuple[float, float, float],
    quaternion: tuple[float, float, float, float],
) -> tuple[float, float, float]:
    vx, vy, vz = vector
    qvec = (0.0, vx, vy, vz)
    w, x, y, z = quaternion
    conj = (w, -x, -y, -z)
    rotated = quaternion_multiply(quaternion_multiply(quaternion, qvec), conj)
    return rotated[1], rotated[2], rotated[3]
