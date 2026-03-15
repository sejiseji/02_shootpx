from __future__ import annotations

import pyxel


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
) -> None:
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
) -> None:
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
