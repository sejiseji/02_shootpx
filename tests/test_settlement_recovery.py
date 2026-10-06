import types
import unittest

import offscreen_support as support
from game_models import OrbitSushiEntry, OrbitSample, SushiSettleEffect


class SettlementRecoveryTests(unittest.TestCase):
    def game(self, count=10, full_barrier=False):
        game = support.shootpx.ShootGame.__new__(support.shootpx.ShootGame)
        game.player = types.SimpleNamespace(x=170, y=430)
        game.frame_count = 0
        game.orbit_enemy_sprite_sheet = None
        game.score = 0
        game.barrier_stock = game.BARRIER_STOCK_CAP if full_barrier else 0
        game.combo_counts = {}
        game.audio = support.SilentAudio()
        game.sushi_settle_effect = SushiSettleEffect()
        game.settle_plate_count = game.settle_plate_score = 0
        game.settle_plate_set_count = 0
        game.settle_plate_last_total = game.settle_plate_bounce_timer = game.settle_plate_total_timer = 0
        entries = [OrbitSushiEntry("tuna", "basic", i, anim_offset=i) for i in range(count)]
        states = [(e, OrbitSample(0, 0, 0, 1, 1), 140+i, 410, "main") for i, e in enumerate(entries)]
        game.start_sushi_settle_effect(entries, states)
        return game, entries, states

    def test_reward_once_even_if_visual_is_interrupted_or_reentered(self):
        for full in (False, True):
            game, entries, states = self.game(full_barrier=full)
            effect = game.sushi_settle_effect
            expected = game.calc_sushi_settle_score([e.sushi_type for e in entries]) * (2 if full else 1)
            self.assertEqual(expected, game.score)
            self.assertEqual(game.BARRIER_STOCK_CAP if full else 1, game.barrier_stock)
            game._confirm_sushi_settlement_reward(effect)
            game.start_sushi_settle_effect(entries, states)
            self.assertEqual(expected, game.score)
            self.assertEqual(1, len(game.audio.events))
            # A reset/scene interruption can discard visuals with no deferred award.
            game.sushi_settle_effect = SushiSettleEffect()
            for _ in range(200):game.update_sushi_settle_effect()
            self.assertEqual(expected, game.score)

    def test_fifo_arrivals_same_total_duration_and_no_draw_rewards(self):
        durations = []
        for count in (10, 20):
            game, entries, _ = self.game(count)
            effect = game.sushi_settle_effect
            initial_score = game.score
            frame = 0
            while game.sushi_settle_effect.active and frame < 200:
                game.update_sushi_settle_effect()
                done = [i for i, sushi in enumerate(effect.sushis) if sushi.done]
                self.assertEqual(list(range(len(done))), done)
                if effect.phase == game.SETTLE_PHASE_EXPLODE:
                    game._draw_settlement_recovery()
                    game._draw_settlement_plate()
                    self.assertEqual(initial_score, game.score)
                frame += 1
            self.assertFalse(game.sushi_settle_effect.active)
            self.assertEqual(count, game.settle_plate_count)
            self.assertEqual(initial_score, game.settle_plate_score)
            self.assertEqual(initial_score, game.settle_plate_last_total)
            self.assertTrue(all(s.done for s in effect.sushis))
            self.assertTrue(all(s.current_x == game.SETTLE_PLATE_X and s.current_y == game.SETTLE_PLATE_Y for s in effect.sushis))
            self.assertEqual(1, len(game.audio.events))
            durations.append(frame)
        self.assertEqual(*durations)


if __name__ == "__main__":
    unittest.main()
