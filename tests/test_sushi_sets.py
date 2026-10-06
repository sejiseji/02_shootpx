import unittest

import offscreen_support as support


class SushiSetTests(unittest.TestCase):
    def game(self):
        game = support.shootpx.ShootGame.__new__(support.shootpx.ShootGame)
        game.enemies = []
        game.sushi_sets = {}
        game.boss_spawn_count = 0
        game.next_sushi_set_id = game.sushi_set_theme_cursor = 0
        game.settle_plate_set_count = game.settle_plate_bounce_timer = 0
        game.regular_spawn_count = 0
        game.score = 180
        return game

    def test_themes_native_hitboxes_wasabi_and_two_set_bound(self):
        game = self.game()
        for cursor, theme in enumerate(("salmon", "tuna", "adult")):
            game.sushi_sets.clear()
            game.enemies.clear()
            self.assertTrue(game._spawn_sushi_set(180))
            group = next(iter(game.sushi_sets.values()))
            self.assertEqual(theme, group.theme)
            self.assertEqual(3, len(game.enemies))
            self.assertEqual(1 if theme == "adult" else 0, sum(e.set_has_wasabi for e in game.enemies))
            for enemy in game.enemies:
                self.assertAlmostEqual(max(6.5, game.ENEMY_HALF_W * enemy.display_scale * .76), enemy.hit_half_w)
                self.assertAlmostEqual(max(6.5, game.ENEMY_HALF_H * enemy.display_scale * .72), enemy.hit_half_h)
        game = self.game()
        self.assertTrue(game._spawn_sushi_set(180))
        self.assertTrue(game._spawn_sushi_set(180))
        self.assertFalse(game._spawn_sushi_set(180))
        self.assertEqual(6, len(game.enemies))

    def test_three_spawn_slots_are_charged_for_three_members(self):
        game = self.game()
        game.regular_spawn_count = 8
        game.spawn_timer = 1
        game._drift_x_bias = lambda value: 0
        game._current_spawn_interval_sec = lambda: 1.2
        game._update_spawning()
        self.assertEqual(3, len(game.enemies))
        self.assertEqual(216, game.spawn_timer)

    def test_circle_contrasts_with_blue_and_gray_backgrounds(self):
        game = self.game()
        game._spawn_sushi_set(180)
        group = next(iter(game.sushi_sets.values()))
        group.x, group.y, group.radius = 160, 240, 50
        support.screen.camera()
        support.screen.clip()
        support.screen.pal()
        for background in (5, 13):
            game.play_bg_color = background
            support.screen.cls(background)
            game._draw_sushi_sets(recovering=False)
            self.assertNotEqual(background, support.screen.pget(210, 240))
        group.state, group.age = "recovering", 9
        support.screen.cls(13)
        game._draw_sushi_sets(recovering=True)
        self.assertNotEqual(13, support.screen.pget(163, 240))

    def test_complete_defeat_recovers_once_without_bonus_score(self):
        game = self.game()
        game._spawn_sushi_set(180)
        members = list(game.enemies)
        group = next(iter(game.sushi_sets.values()))
        for index, enemy in enumerate(members):
            game._record_sushi_set_defeat(enemy)
            game._record_sushi_set_defeat(enemy)
            game.enemies.remove(enemy)
            game._update_sushi_sets()
            self.assertEqual(2-index, group.remaining)
        self.assertEqual("recovering", group.state)
        self.assertEqual(0, game.settle_plate_set_count)
        for _ in range(26):game._update_sushi_sets()
        self.assertEqual(1, game.settle_plate_set_count)
        self.assertEqual({}, game.sushi_sets)
        self.assertEqual(180, game.score)
        game._update_sushi_sets()
        self.assertEqual(1, game.settle_plate_set_count)

    def test_one_escape_or_scene_clear_never_counts_as_complete(self):
        for clear_scene in (False, True):
            game = self.game()
            game._spawn_sushi_set(180)
            if clear_scene:
                game.enemies.clear()
            else:
                game.enemies[0].y = game.HEIGHT + 999
                game._remove_offscreen_enemies()
            game._update_sushi_sets()
            self.assertEqual({}, game.sushi_sets)
            for enemy in list(game.enemies):game._record_sushi_set_defeat(enemy)
            game.enemies.clear()
            for _ in range(40):game._update_sushi_sets()
            self.assertEqual(0, game.settle_plate_set_count)

    def test_real_damage_hook_scores_each_enemy_once_and_reset_clears_sets(self):
        game = support.game("normal")
        game.sushi_set_theme_cursor = 2
        game._spawn_sushi_set(180)
        game._update_sushi_sets()
        members = list(game.enemies)
        expected = sum(enemy.score_value for enemy in members)
        for enemy in members:
            game._damage_enemy(enemy, enemy.hp)
        game._update_sushi_sets()
        self.assertEqual(expected, game.score)
        self.assertEqual(3, game.enemy_kill_count)
        self.assertEqual(1, sum(entry.has_wasabi for entry in game.orbit_sushi_queue))
        for _ in range(26):game._update_sushi_sets()
        self.assertEqual(expected, game.score)
        self.assertEqual(1, game.settle_plate_set_count)
        game._spawn_sushi_set(180)
        game._reset_play_state()
        self.assertEqual({}, game.sushi_sets)
        self.assertEqual(0, game.settle_plate_set_count)
        self.assertEqual(0, game.next_sushi_set_id)


if __name__ == "__main__":
    unittest.main()
