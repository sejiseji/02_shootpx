import types
import unittest

import offscreen_support as support
from game_models import Bullet, WeaponItem


class WeaponReactionTests(unittest.TestCase):
    def game(self):
        game = support.shootpx.ShootGame.__new__(support.shootpx.ShootGame)
        game.weapon_icon_images = {}
        game.frame_count = 0
        game.player = types.SimpleNamespace(x=180, y=560)
        game.unlocked_weapon_families = [game.WEAPON_FAMILY_FAN, game.WEAPON_FAMILY_LANCE]
        game.weapon_items = [WeaponItem(100, 200, 0, 1, game.WEAPON_FAMILY_FAN)]
        game.bullets = [Bullet(100, 200, 0)]
        return game

    def test_hit_immediately_switches_without_changing_lock_or_hitbox(self):
        game = self.game()
        item = game.weapon_items[0]
        game._handle_bullet_weapon_item_collisions()
        self.assertEqual(game.WEAPON_FAMILY_LANCE, item.family)
        self.assertEqual(72, item.switch_lock_timer)
        self.assertEqual(8, item.radius)
        self.assertEqual(8, item.reaction_timer)
        self.assertEqual([], game.bullets)
        game.bullets = [Bullet(item.x, item.y, 0)]
        game._handle_bullet_weapon_item_collisions()
        self.assertEqual(game.WEAPON_FAMILY_LANCE, item.family)
        self.assertEqual(1, len(game.bullets))

    def test_reaction_finishes_in_eight_updates_and_render_is_read_only(self):
        game = self.game()
        item = game.weapon_items[0]
        item.reaction_timer = 8
        scale, dy, rotation = game._weapon_item_visual_state(item)
        self.assertLess(scale, 1)
        self.assertEqual(360, rotation)
        states = []
        for _ in range(8):
            before = dict(vars(item))
            game._draw_weapon_items()
            self.assertEqual(before, vars(item))
            states.append(game._weapon_item_visual_state(item))
            game._update_weapon_items()
        self.assertGreater(max(s[0] for s in states), 1)
        self.assertLess(min(s[1] for s in states), 0)
        self.assertEqual((1, 0, 0), game._weapon_item_visual_state(item))
        self.assertEqual(0, item.reaction_timer)
        for family in game.WEAPON_FAMILY_ORDER:
            game._weapon_icon_image(family)
        self.assertEqual(len(game.WEAPON_FAMILY_ORDER), len(game.weapon_icon_images))


if __name__ == "__main__":
    unittest.main()
