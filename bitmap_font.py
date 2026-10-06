from __future__ import annotations

from collections import OrderedDict

import pyxel


# Software text images contain palette indices, not RGB values. Blitting applies
# the screen palette/clip/camera exactly as the original rectangle drawing does.
TEXT_CACHE_MAX_ENTRIES = 128
TEXT_CACHE_MAX_PIXELS = 262144
HUD_CACHE_MAX_SLOTS = 32
HUD_CACHE_MAX_PIXELS = 65536


class _TextCache:
    def __init__(self, max_entries: int, max_pixels: int):
        self.max_entries = max_entries
        self.max_pixels = max_pixels
        self.entries = OrderedDict()
        self.pixels = 0

    def clear(self) -> None:
        self.entries.clear()
        self.pixels = 0

    def get(self, slot, signature):
        entry = self.entries.get(slot)
        if entry is None:
            return None
        if entry[0] != signature:
            self.pixels -= entry[2]
            del self.entries[slot]
            return None
        self.entries.move_to_end(slot)
        return entry[1]

    def put(self, slot, signature, value, pixels: int) -> None:
        if pixels > self.max_pixels:
            return
        while self.entries and (
            len(self.entries) >= self.max_entries or self.pixels + pixels > self.max_pixels
        ):
            _, entry = self.entries.popitem(last=False)
            self.pixels -= entry[2]
        self.entries[slot] = (signature, value, pixels)
        self.pixels += pixels


_text_cache = _TextCache(TEXT_CACHE_MAX_ENTRIES, TEXT_CACHE_MAX_PIXELS)
_hud_cache = _TextCache(HUD_CACHE_MAX_SLOTS, HUD_CACHE_MAX_PIXELS)


def clear_text_cache() -> None:
    """Invalidate after changing glyph definitions or restarting the renderer."""
    _text_cache.clear()
    _hud_cache.clear()


def _draw_cached_text(x, y, text, sx, sy, color, shadow, advance, mode, slot):
    # Keep legacy rasterization for fractional positions or unusual dimensions.
    if x != int(x) or y != int(y) or sx < 1 or sy < 1 or advance < 1:
        return False
    text = text.upper()
    if not text:
        return True
    ox = (sx if mode == "big" else max(1, sx // 2)) if shadow is not None else 0
    oy = sy if shadow is not None else 0
    if mode == "hud":
        ox = oy = 1 if shadow is not None else 0
    width = (len(text) - 1) * advance + (9 if mode == "hud" else 5 * sx) + ox
    height = 7 * sy + oy
    cache = _text_cache if slot is None else _hud_cache
    signature = (text, sx, sy, color, shadow, advance, mode)
    key = signature if slot is None else (mode, slot)
    value = cache.get(key, signature)
    if value is None:
        if width * height > cache.max_pixels:
            return False
        transparent = next(c for c in range(16) if c != color and c != shadow)
        image = pyxel.Image(width, height)
        image.cls(transparent)
        layers = [(ox, oy, shadow), (0, 0, color)] if shadow is not None else [(0, 0, color)]
        for dx, dy, ink in layers:
            for i, ch in enumerate(text):
                for row, bits in enumerate(BIG_FONT.get(ch, BIG_FONT[" "])):
                    for col, bit in enumerate(bits):
                        if bit == "1":
                            gx = HUD_VALUE_COL_X[col] if mode == "hud" else col * sx
                            gw = HUD_VALUE_COL_W[col] if mode == "hud" else sx
                            image.rect(i * advance + dx + gx, dy + row * sy, gw, sy, ink)
        value = (image, width, height, transparent)
        cache.put(key, signature, value, width * height)
    image, width, height, transparent = value
    pyxel.blt(x, y, image, 0, 0, width, height, transparent)
    return True


BIG_FONT = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00100", "01000", "10000", "00000", "00000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00001", "00001", "00001", "00001", "10001", "10001", "01110"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


def draw_big_text(
    x: int,
    y: int,
    text: str,
    scale: int,
    color: int,
    shadow_color: int | None = None,
    *,
    cache_slot: str | None = None,
) -> None:
    if _draw_cached_text(x, y, text, scale, scale, color, shadow_color, 6 * scale, "big", cache_slot):
        return
    if shadow_color is not None:
        _draw_big_text_core(x + scale, y + scale, text, scale, shadow_color)
    _draw_big_text_core(x, y, text, scale, color)


def draw_scaled_text(
    x: int,
    y: int,
    text: str,
    scale_x: int,
    scale_y: int,
    color: int,
    shadow_color: int | None = None,
    advance_x: int | None = None,
) -> None:
    advance = 6 * scale_x if advance_x is None else advance_x
    if _draw_cached_text(x, y, text, scale_x, scale_y, color, shadow_color, advance, "scaled", None):
        return
    if shadow_color is not None:
        _draw_scaled_text_core(
            x + max(1, scale_x // 2),
            y + max(1, scale_y),
            text,
            scale_x,
            scale_y,
            shadow_color,
            advance_x,
        )
    _draw_scaled_text_core(x, y, text, scale_x, scale_y, color, advance_x)


def _draw_big_text_core(x: int, y: int, text: str, scale: int, color: int) -> None:
    cursor_x = x
    for ch in text.upper():
        glyph = BIG_FONT.get(ch, BIG_FONT[" "])
        for row_index, row_bits in enumerate(glyph):
            for col_index, bit in enumerate(row_bits):
                if bit == "1":
                    pyxel.rect(
                        cursor_x + col_index * scale,
                        y + row_index * scale,
                        scale,
                        scale,
                        color,
                    )
        cursor_x += 6 * scale


def _draw_scaled_text_core(
    x: int,
    y: int,
    text: str,
    scale_x: int,
    scale_y: int,
    color: int,
    advance_x: int | None = None,
) -> None:
    cursor_x = x
    step_x = advance_x if advance_x is not None else 6 * scale_x
    for ch in text.upper():
        glyph = BIG_FONT.get(ch, BIG_FONT[" "])
        for row_index, row_bits in enumerate(glyph):
            for col_index, bit in enumerate(row_bits):
                if bit == "1":
                    pyxel.rect(
                        cursor_x + col_index * scale_x,
                        y + row_index * scale_y,
                        scale_x,
                        scale_y,
                        color,
                    )
        cursor_x += step_x


def big_text_width(text: str, scale: int) -> int:
    return len(text) * 6 * scale - scale


def scaled_text_width(text: str, scale_x: int, advance_x: int | None = None) -> int:
    step_x = advance_x if advance_x is not None else 6 * scale_x
    return len(text) * step_x - scale_x


HUD_VALUE_COL_X = (0, 2, 4, 6, 8)
HUD_VALUE_COL_W = (2, 2, 2, 2, 1)
HUD_VALUE_ROW_Y = (0, 1, 2, 3, 4, 5, 6)


def draw_hud_value_text(
    x: int,
    y: int,
    text: str,
    color: int,
    shadow_color: int | None = None,
    *,
    cache_slot: str | None = None,
) -> None:
    if _draw_cached_text(x, y, text, 1, 1, color, shadow_color, 10, "hud", cache_slot):
        return
    if shadow_color is not None:
        _draw_hud_value_text_core(x + 1, y + 1, text, shadow_color)
    _draw_hud_value_text_core(x, y, text, color)


def _draw_hud_value_text_core(x: int, y: int, text: str, color: int) -> None:
    cursor_x = x
    for ch in text.upper():
        glyph = BIG_FONT.get(ch, BIG_FONT[" "])
        for row_index, row_bits in enumerate(glyph):
            py = y + HUD_VALUE_ROW_Y[row_index]
            for col_index, bit in enumerate(row_bits):
                if bit == "1":
                    pyxel.rect(
                        cursor_x + HUD_VALUE_COL_X[col_index],
                        py,
                        HUD_VALUE_COL_W[col_index],
                        1,
                        color,
                    )
        cursor_x += 10


def hud_value_text_width(text: str) -> int:
    return len(text) * 10 - 1
