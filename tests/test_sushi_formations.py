import copy,math,random,unittest
from unittest.mock import patch
import offscreen_support as s
from enemy_system import update_enemies
from game_models import GamePhase

class SushiFormationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=s.game('normal')
    def setUp(self):
        g=self.g;g.enemies=[];g.enemy_bullets=[];g.sushi_sets={};g.next_sushi_set_id=0
        g.settle_plate_set_count=0;g.phase=GamePhase.PLAYING;g._drift_x_bias=lambda v:0

    def spawn(self,cursor,x=180):
        self.g.sushi_set_theme_cursor=cursor;self.assertTrue(self.g._spawn_sushi_set(x))
        return next(iter(self.g.sushi_sets.values()))

    def test_four_layouts_keep_native_members_randomness_and_budget(self):
        g=self.g
        for cursor in range(12):
            g.enemies=[];g.sushi_sets={}
            theme=('salmon','tuna','adult')[cursor%3]
            types={'salmon':('zigzag',)*3,'tuna':('basic',)*3,'adult':('zigzag','basic','aimer')}[theme]
            random.seed(774)
            expected=[g._create_enemy(180+(i-1)*34,typ) for i,typ in enumerate(types)];rng=random.getstate()
            random.seed(774);group=self.spawn(cursor)
            self.assertEqual(random.getstate(),rng)
            self.assertEqual(group.formation,g.SUSHI_SET_FORMATIONS[cursor%4])
            self.assertEqual(len(g.enemies),3)
            for e,ref in zip(g.enemies,expected):
                for name in ('hp','max_hp','score_value','display_scale','hit_half_w','hit_half_h','shoot_cooldown','fire_interval','bullet_speed'):
                    self.assertEqual(getattr(e,name),getattr(ref,name))
                self.assertEqual(e.vy,min(e.vy for e in expected))
            self.assertEqual(sum(e.set_has_wasabi for e in g.enemies),1 if theme=='adult' else 0)
            y=[e.y for e in g.enemies]
            if group.formation=='row':self.assertAlmostEqual(max(y),min(y))
            if group.formation=='vee':self.assertAlmostEqual(y[1]-y[0],18);self.assertEqual(y[0],y[2])
            if group.formation in ('diagonal','sway'):
                self.assertEqual(y,[ref.y-i*14 for i,ref in enumerate(expected)])

    def test_common_sway_preserves_spacing_circle_edges_and_freezes_off_play(self):
        g=self.g
        for x in (-100,180,1000):
            g.enemies=[];g.sushi_sets={};group=self.spawn(3,x)
            spacing=[g.enemies[i].x-g.enemies[0].x for i in range(3)]
            offsets=[];rng=random.getstate()
            for t in range(360):
                g.frame_count=t;g._update_enemies();g._update_sushi_sets();offsets.append(group.motion_offset)
                self.assertEqual(random.getstate(),rng)
                for i,e in enumerate(g.enemies):
                    self.assertAlmostEqual(e.x-g.enemies[0].x,spacing[i])
                    self.assertGreaterEqual(e.x,g.SIDE_MARGIN+g.ENEMY_HALF_W*e.display_scale-1e-8)
                    self.assertLessEqual(e.x,g.WIDTH-g.SIDE_MARGIN-g.ENEMY_HALF_W*e.display_scale+1e-8)
                    self.assertLessEqual(math.hypot(e.x-group.x,e.y-group.y)+max(e.hit_half_w,e.hit_half_h)+8,group.radius+1e-8)
            self.assertLessEqual(max(abs(o) for o in offsets),18+1e-8)
            self.assertGreater(max(offsets),0);self.assertLess(min(offsets),0)
            age=group.motion_age
            g.phase=GamePhase.REWARD_SELECT
            with patch.object(g,'_update_reward_select_input'):g.update()
            self.assertEqual(group.motion_age,age)
            g.phase=GamePhase.PLAYING

    def test_native_shot_frequency_and_vertical_speed_are_preserved(self):
        g=self.g
        for cursor in (8,5,2,11):
            g.enemies=[];g.sushi_sets={};group=self.spawn(cursor)
            reference=copy.deepcopy(g.enemies);actual=[];expected=[]
            with patch.object(g,'_append_enemy_bullet',side_effect=lambda **kw:actual.append(kw) or True):
                for t in range(180):
                    g.frame_count=t;g._update_enemies()
                    update_enemies(enemies=reference,frame_count=t,side_margin=g.SIDE_MARGIN,width=g.WIDTH,
                        enemy_half_w=g.ENEMY_HALF_W,player_x=g.player.x,player_y=g.player.y,
                        enemy_bullet_max_count=g.ENEMY_BULLET_MAX_COUNT,current_enemy_bullet_count=0,
                        append_enemy_bullet=lambda **kw:expected.append(kw) or True)
            self.assertEqual(len(actual),len(expected))
            for e,ref in zip(g.enemies,reference):
                self.assertEqual(e.y,ref.y);self.assertEqual(e.vy,ref.vy)
                self.assertEqual(e.shoot_cooldown,ref.shoot_cooldown)

    def test_each_formation_escape_and_recovery_have_existing_reward_semantics(self):
        g=self.g
        for cursor in range(4):
            g.enemies=[];g.sushi_sets={};g.settle_plate_set_count=0;group=self.spawn(cursor)
            g.enemies[0].y=g.HEIGHT+999;g._remove_offscreen_enemies();g._update_sushi_sets()
            self.assertEqual(g.sushi_sets,{});self.assertEqual(g.settle_plate_set_count,0)
            g.enemies=[];group=self.spawn(cursor);score=g.score
            for e in list(g.enemies):g._record_sushi_set_defeat(e);g.enemies.remove(e)
            g._update_sushi_sets();self.assertEqual(group.state,'recovering')
            for _ in range(26):g._update_sushi_sets()
            self.assertEqual(g.settle_plate_set_count,1);self.assertEqual(g.score,score)

if __name__=='__main__':unittest.main()
