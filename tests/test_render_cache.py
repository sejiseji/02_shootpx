"""Run with: python -m unittest discover -s tests -v (requires Pyxel 2.7).

No window, audio, save files or resource writes. The regression oracle is the
unchanged pre-optimization commit; GPU/browser presentation is not exercised.
"""
import ctypes
import dataclasses
import os
from pathlib import Path
import random
import subprocess
import types
import unittest
from unittest.mock import patch

import offscreen_support as support
import bitmap_font as font

BASELINE_COMMIT = "840c3d74d0ec843cd0387dad579623c167f2676f"


def baseline_module(filename):
    baseline_dir = os.environ.get("SUSHI_BASELINE_DIR")
    source = (Path(baseline_dir) / f"{filename}.py").read_text() if baseline_dir else subprocess.check_output(
        ["git", "show", f"{BASELINE_COMMIT}:{filename}.py"], cwd=support.REPO, text=True
    )
    module = types.ModuleType(f"baseline_{filename}")
    exec(compile(source, f"baseline/{filename}.py", "exec"), module.__dict__)
    return module


def pixels(image):
    return ctypes.string_at(image.data_ptr(), image.width * image.height)


def freeze(value, identities=None):
    identities = identities or {}
    if isinstance(value, int) and value in identities:
        return identities[value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if dataclasses.is_dataclass(value):
        return tuple((f.name, freeze(getattr(value, f.name), identities)) for f in dataclasses.fields(value))
    if isinstance(value, dict):
        return {freeze(k, identities): freeze(v, identities) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v, identities) for v in value)
    if isinstance(value, set):
        return frozenset(freeze(v, identities) for v in value)
    # Native image storage/audio stubs are not gameplay state.
    return type(value).__name__


class RenderCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_font = baseline_module("bitmap_font")
        cls.original_game = baseline_module("shootpx")
        cls.original_game.AudioSystem = support.SilentAudio
        for name in ("draw_big_text", "draw_scaled_text", "draw_hud_value_text"):
            setattr(cls.original_game, name, getattr(cls.original_font, name))

    def setUp(self):
        font.clear_text_cache()
        support.screen.clip()
        support.screen.camera()
        support.screen.pal()

    def test_font_pixels_shadow_zero_clipping_palette_and_camera(self):
        cases = (
            ("draw_big_text", ("Ab0!? /", 1, 0), {"shadow_color": 7}),
            ("draw_big_text", ("SCORE 1234567", 2, 7), {"shadow_color": 1}),
            ("draw_big_text", ("ZERO", 3, 1), {}),
            ("draw_scaled_text", ("REWARD", 2, 3, 12), {"shadow_color": 0, "advance_x": 9}),
            ("draw_hud_value_text", ("X 12 C 3/5", 7), {"shadow_color": 1}),
            ("draw_big_text", ("", 1, 7), {}),
        )
        for clipping in (False, True):
            for name, args, kwargs in cases:
                with self.subTest(name=name, args=args, clipping=clipping):
                    support.screen.clip(0, 0, 100, 24) if clipping else support.screen.clip()
                    support.screen.camera(3, 2)
                    support.screen.pal(7, 10)
                    support.screen.cls(13)
                    getattr(self.original_font, name)(-2, 3, *args, **kwargs)
                    expected = pixels(support.screen)
                    support.screen.cls(13)
                    getattr(font, name)(-2, 3, *args, **kwargs)
                    self.assertEqual(expected, pixels(support.screen))

    def test_hud_reuses_unchanged_and_replaces_changed_signature(self):
        draw = font.draw_big_text
        draw(0, 0, "0000001", 2, 7, shadow_color=1, cache_slot="score")
        first = font._hud_cache.entries[("big", "score")][1][0]
        draw(5, 5, "0000001", 2, 7, shadow_color=1, cache_slot="score")
        self.assertIs(first, font._hud_cache.entries[("big", "score")][1][0])
        for value in range(200):
            draw(0, 0, str(value), 2, 7, shadow_color=1, cache_slot="score")
        self.assertEqual(1, len(font._hud_cache.entries))
        self.assertIsNot(first, font._hud_cache.entries[("big", "score")][1][0])
        draw(0, 0, "199", 2, 12, shadow_color=1, cache_slot="score")
        self.assertEqual(12, font._hud_cache.entries[("big", "score")][0][3])

    def test_bounded_caches_and_invalidation(self):
        for i in range(300):
            font.draw_big_text(0, 0, str(i), 2, 7)
            font.draw_hud_value_text(0, 0, str(i), 7, cache_slot=str(i))
        for cache in (font._text_cache, font._hud_cache):
            self.assertLessEqual(len(cache.entries), cache.max_entries)
            self.assertLessEqual(cache.pixels, cache.max_pixels)
            self.assertEqual(cache.pixels, sum(e[2] for e in cache.entries.values()))
        # Oversized text falls back without retaining a large native allocation.
        font.draw_big_text(0, 0, "A" * 7000, 1, 7)
        self.assertLessEqual(font._text_cache.pixels, font.TEXT_CACHE_MAX_PIXELS)
        font.clear_text_cache()
        self.assertEqual((0, 0), (font._text_cache.pixels, font._hud_cache.pixels))

    def make_pair(self, scene):
        self.identities = [{}, {}]
        with patch.object(support.shootpx, "ShootGame", self.original_game.ShootGame):
            original = support.game(scene)
        original_rng = random.getstate()
        current = support.game(scene)
        if scene == "fever":
            # This fixture assigns equipment fields directly, bypassing the
            # game's equipment setters. Normalize it before the first draw.
            original._sync_active_weapon_slots()
            current._sync_active_weapon_slots()
        return original, current, original_rng, random.getstate()

    def compare_frame(self, original, current, rng_a, rng_b, frame, action=None):
        results = []
        for index, (game, rng) in enumerate(((original, rng_a), (current, rng_b))):
            random.setstate(rng)
            if action is not None:
                action(game)
            game.player.invincible_timer = 9999
            game.player.x = 180 + support.math.sin(frame * .021) * 70
            game.update()
            game.draw()
            identities = self.identities[index]
            targets = [game.boss] + game.enemies + game.enemy_bullets + game.weapon_items
            for target in targets:
                if target is not None and id(target) not in identities:
                    identities[id(target)] = ("object", len(identities))
            image = pixels(support.screen)
            if game.reward_notice_kind.startswith("weapon_") and game.reward_notice_timer > 0:
                # Weapon cards intentionally replace the old notice. Preserve
                # the full underlying game/HUD oracle; test_weapon_cutin checks
                # the new pixels, timing, footprint, and draw-state isolation.
                with patch.object(game, "_draw_reward_notice"):
                    game.draw()
                image = pixels(support.screen)
            results.append((image, freeze(vars(game), identities), random.getstate()))
        self.assertEqual(results[0][0], results[1][0], f"pixels at frame {frame}")
        for name in results[0][1]:
            self.assertEqual(results[0][1][name], results[1][1][name], f"{name} at frame {frame}")
        self.assertEqual(results[0][2], results[1][2], f"RNG at frame {frame}")
        self.assertEqual(original.audio.events, current.audio.events, f"audio events at frame {frame}")
        return results[0][2], results[1][2]

    def test_representative_frames_and_gameplay_state_match(self):
        for scene in ("start", "normal", "boss", "fever", "reward"):
            with self.subTest(scene=scene):
                original, current, rng_a, rng_b = self.make_pair(scene)
                # Verify the initial frame, before any update.
                images = []
                for game in (original, current):
                    game.draw()
                    images.append(pixels(support.screen))
                self.assertEqual(*images)
                for frame in range(90):
                    rng_a, rng_b = self.compare_frame(original, current, rng_a, rng_b, frame)

    def test_reward_and_start_selection_have_no_delayed_weapon_display(self):
        for scene in ("start", "reward"):
            original, current, rng_a, rng_b = self.make_pair(scene)
            action = (
                (lambda game: game._move_start_weapon_selection(1)) if scene == "start"
                else (lambda game: game._apply_reward_choice(game.reward_choices[0]))
            )
            self.compare_frame(original, current, rng_a, rng_b, 0, action)

    def test_draw_never_calls_weapon_synchronizers(self):
        for scene in ("start", "normal", "fever", "reward"):
            game = support.game(scene)
            game.update()
            state = (game.current_weapon_family, list(game.active_weapon_slots), dict(game.weapon_levels))
            with patch.object(game, "_sync_active_weapon_slots", side_effect=AssertionError("draw sync")), \
                 patch.object(game, "_sync_start_preview_weapon_state", side_effect=AssertionError("draw sync")):
                game.draw()
            self.assertEqual(state, (game.current_weapon_family, game.active_weapon_slots, game.weapon_levels))


if __name__ == "__main__":
    unittest.main()
