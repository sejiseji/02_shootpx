"""Actual trajectory, segment collision, immunity, cooldown and reward regressions."""
import math,random,types,unittest
from pathlib import Path
from unittest.mock import patch
import offscreen_support as s
from game_models import HomingLaser

def laser(x=180,y=400,speed=9.3):
    return HomingLaser(x,y,0,-speed,speed,.052,180,180,7,5,2,trail=[(x,y)])

class HomingLaserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=s.game('normal')
    def setUp(self):
        self.g.enemies=[];self.g.enemy_bullets=[];self.g.boss=None;self.g.homing_lasers=[]
    def enemy(self,x,y):
        e=self.g._create_enemy(x,'basic');e.x=x;e.y=y;e.hit_half_w=e.hit_half_h=6.5;e.invincible_timer=0;e.hp=20
        self.g.enemies.append(e);return e

    def test_collision_redirect_never_spends_an_extra_turn(self):
        g=self.g;l=laser();self.enemy(280,390);g.homing_lasers=[l]
        g._update_homing_lasers();a=math.atan2(l.vy,l.vx)
        self.assertLessEqual(abs(g._wrap_angle(a+math.pi/2)),l.turn_rate+1e-10)
        for _ in range(6):g._force_homing_laser_redirect(l)
        self.assertEqual(a,math.atan2(l.vy,l.vx));self.assertIsNone(l.target_id)
        g._update_homing_lasers()
        self.assertLessEqual(abs(g._wrap_angle(math.atan2(l.vy,l.vx)-a)),l.turn_rate+1e-10)
        self.assertAlmostEqual(math.hypot(l.vx,l.vy),9.3)

    def test_steering_snap_and_bit_cone_entry_obey_the_same_budget(self):
        g=self.g
        for angle in (-math.pi/2,0,math.pi,-.1,-3.0):
            for desired in (-math.pi/2,-math.pi/2+.052*1.1):
                vx,vy=g._rotate_homing_velocity_quaternion(math.cos(angle)*10,math.sin(angle)*10,desired,.052,10)
                self.assertLessEqual(abs(g._wrap_angle(math.atan2(vy,vx)-angle)),.052+1e-10)
                self.assertAlmostEqual(math.hypot(vx,vy),10)
        l=laser();l.vx,l.vy=l.speed,0;g.homing_lasers=[l]
        for _ in range(12):
            angle=math.atan2(l.vy,l.vx);g._update_homing_lasers()
            self.assertLessEqual(abs(g._wrap_angle(math.atan2(l.vy,l.vx)-angle)),.052+1e-10)

    def test_tip_and_between_samples_hit_without_widening_the_box(self):
        g=self.g;l=laser(speed=14.3);l.trail=[(180,400-i*14.3) for i in range(10)];l.x,l.y=l.trail[-1]
        e=self.enemy(*l.trail[-1]);self.assertTrue(g._is_laser_hitting_enemy(l,e))
        e.y=(l.trail[4][1]+l.trail[6][1])/2
        self.assertTrue(g._is_laser_hitting_enemy(l,e))
        e.x=180+6.5+l.band_width+.01;self.assertFalse(g._is_laser_hitting_enemy(l,e))
        l.trail=[(180,600-i*14.3) for i in range(28)];l.x,l.y=l.trail[-1];e.x,e.y=l.trail[0]
        self.assertFalse(g._is_laser_hitting_enemy(l,e))

    def test_immunity_retreat_degenerate_segments_and_boss_shield(self):
        g=self.g;l=laser();e=self.enemy(l.x,l.y);g.homing_lasers=[l]
        for state,invincible in [('normal',5),('retreating',0)]:
            e.state=state;e.invincible_timer=invincible;hp=e.hp;score=g.score
            self.assertFalse(g._is_laser_hitting_enemy(l,e));g._handle_homing_laser_enemy_collisions()
            self.assertEqual((e.hp,g.score),(hp,score))
        e.state='normal';e.invincible_timer=0;l.trail=[(l.x,l.y)]*3
        self.assertTrue(g._is_laser_hitting_enemy(l,e))
        from boss_system import spawn_boss
        g.boss=spawn_boss(width=360,entry_target_y=200,max_hp=100,spawn_count=1)
        g.boss.x=180;g.boss.y=400;g.boss.hp=100;g.boss.entry_invulnerable=True
        center=g._boss_hit_center(g.boss);l.x,l.y=center;l.trail=[center];g._handle_homing_laser_boss_collisions()
        self.assertEqual(g.boss.hp,100)
        g.boss.entry_invulnerable=False;g.boss.shield_timer=5;l.hit_cooldowns.clear()
        g._handle_homing_laser_boss_collisions();self.assertEqual(g.boss.hp,100)

    def test_damage_score_cooldown_speed_and_target_loss_remain_defined(self):
        g=self.g;l=laser();e=self.enemy(l.x,l.y);g.homing_lasers=[l]
        g._handle_homing_laser_enemy_collisions();self.assertEqual(e.hp,18)
        self.assertEqual(l.hit_cooldowns[id(e)],8)
        g._handle_homing_laser_enemy_collisions();self.assertEqual(e.hp,18)
        l.hit_cooldowns.clear();e.hp=2;score=g.score;value=e.score_value
        g._handle_homing_laser_enemy_collisions();self.assertEqual(g.score,score+value)
        g._handle_homing_laser_enemy_collisions();self.assertEqual(g.score,score+value)
        l=laser();e=self.enemy(180,300);l.target_id=id(e);l.reacquire_timer=10
        g.enemies.remove(e);replacement=self.enemy(200,290);g.homing_lasers=[l]
        old=(l.x,l.y);g._update_homing_lasers()
        self.assertEqual(l.target_id,id(replacement));self.assertAlmostEqual(math.dist(old,(l.x,l.y)),9.3)
        self.assertEqual(l.life,179);self.assertEqual(l.damage,2)

if __name__=='__main__':unittest.main()
