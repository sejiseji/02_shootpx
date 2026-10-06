"""Real native card rasterization, triggers, state isolation, and bounded storage."""
import ctypes
import random
import unittest
from unittest.mock import patch
import offscreen_support as s
from game_models import GamePhase, RewardChoice
from test_render_cache import freeze

def pixels(image):return ctypes.string_at(image.data_ptr(), image.width * image.height)

def state(game):
    scalars={k:v for k,v in vars(game).items() if v is None or isinstance(v,(str,int,float,bool))}
    return (scalars,freeze(game.player),dict(game.weapon_levels),dict(game.weapon_overdrive_bonus),
            tuple(game.active_weapon_slots),tuple(game.unlocked_weapon_families),
            freeze(game.enemies),freeze(game.bullets),freeze(game.enemy_bullets),
            tuple((id(im),offset) for im,offset in game.weapon_cutin_frames))

class WeaponCutinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.game=s.game('normal')

    def setUp(self):
        self.g=self.game;self.g._reset_play_state();self.g.phase=GamePhase.PLAYING
        self.g.audio.events.clear();s.screen.clip();s.screen.camera();s.screen.pal()

    def cache_images(self):return {id(image):image for image,offset in self.g.weapon_cutin_frames}.values()

    def assert_card(self,family,label,title,desc):
        g=self.g
        self.assertEqual((label,title,desc),(g.reward_notice_label,g.reward_notice_text,g.reward_notice_desc))
        self.assertEqual(g.reward_notice_timer,72)
        self.assertEqual(len(g.weapon_cutin_frames),72)
        images=list(self.cache_images());self.assertLessEqual(len(images),13)
        self.assertLessEqual(sum(im.width*im.height for im in images),150000)
        # Every source field fits completely, without clipping or elision.
        for text,y,preferred in [(title,20,2),(desc,49,1)]:
            im=s.pyxel.Image(236,68)
            sx,sy,lines=g._weapon_card_text(im,77,y,text,1,preferred)
            self.assertEqual(' '.join(lines),text)
            self.assertTrue(all(len(line)*6*sx-sx<=153 for line in lines))
            self.assertLessEqual(y+(len(lines)-1)*8+7*sy,65)
        rng=random.getstate();events=list(g.audio.events)
        for elapsed in range(72):
            g.reward_notice_timer=72-elapsed
            before_draw=state(g);s.screen.cls(5);g._draw_reward_notice()
            self.assertEqual(before_draw,state(g))
            if elapsed in (0,5,10,24,60,66,71):
                data=pixels(s.screen)
                self.assertTrue(all(c==5 for i,c in enumerate(data) if not(i%360<244 and 124<=i//360<192)))
        mask=s.pyxel.Image(236,68);mask.cls(0);mask.rect(0,0,208,68,1);mask.tri(208,0,236,0,208,68,1)
        pairs={id(im):(im,offset) for im,offset in g.weapon_cutin_frames}.values()
        for im,offset in pairs:
            for y in range(im.height):
                for x in range(im.width):
                    if im.pget(x,y)!=g.WEAPON_CUTIN_TRANSPARENT:
                        self.assertNotEqual(mask.pget(x+offset,y),0)
        self.assertEqual(rng,random.getstate());self.assertEqual(events,g.audio.events)

    def test_five_weapons_all_acquisition_states_and_levels(self):
        g=self.g
        for family in g.WEAPON_FAMILY_ORDER:
            for mode in ('unlock','switch','boost','drive'):
                with self.subTest(family=family,mode=mode):
                    g._reset_play_state();g.phase=GamePhase.PLAYING
                    other=next(f for f in g.WEAPON_FAMILY_ORDER if f!=family)
                    g.unlocked_weapon_families=[other];g.current_weapon_family=other
                    g.weapon_levels={f:-1 for f in g.WEAPON_FAMILY_ORDER};g.weapon_levels[other]=0
                    if mode!='unlock':g._unlock_weapon_family(family,equip_now=False)
                    if mode=='boost':g.current_weapon_family=family
                    if mode=='drive':g.current_weapon_family=family;g.weapon_levels[family]=g.SHOT_LEVEL_MAX
                    g._upgrade_weapon_family(family)
                    name=g._weapon_name(family)
                    expected={'unlock':('WEAPON GET',name+' UNLOCK','Now using '+name),
                        'switch':('WEAPON CHANGE',name+' READY','Switched from '+g._weapon_name(other)),
                        'boost':('SHOT UP',name+' BOOST','Now '+g._shot_level_name(1)),
                        'drive':('MAX POWER',name+' DRIVE','ATK +1')}[mode]
                    self.assert_card(family,*expected)
            for level in range(g.SHOT_LEVEL_MAX):
                g._unlock_weapon_family(family);g.weapon_levels[family]=level
                g._upgrade_weapon_family(family,switch_if_needed=False)
                self.assertEqual(g.weapon_levels[family],level+1)
                self.assertEqual(g.reward_notice_desc,'Now '+g._shot_level_name(level+1))
            # Native cap behavior: no new notice once max overdrive is reached.
            g.weapon_overdrive_bonus[family]=g.WEAPON_OVERDRIVE_CAP
            g.reward_notice_timer=19;frames=g.weapon_cutin_frames
            g._upgrade_weapon_family(family,switch_if_needed=False)
            self.assertEqual(g.reward_notice_timer,19);self.assertIs(g.weapon_cutin_frames,frames)

    def test_overwrite_pause_expiry_end_and_restart(self):
        g=self.g;g._upgrade_weapon_family('beam');old=g.weapon_cutin_frames
        g.reward_notice_timer=15;g._upgrade_weapon_family('lance')
        self.assertIsNot(old,g.weapon_cutin_frames);self.assertEqual(g.reward_notice_kind,'weapon_lance')
        self.assertEqual(g.reward_notice_timer,72)
        g.reward_notice_timer=48;s.screen.cls(5);g._draw_reward_notice();paused=pixels(s.screen)
        for i in range(4):
            g.frame_count+=10;s.screen.cls(5);g._draw_reward_notice();self.assertEqual(paused,pixels(s.screen))
        self.assertEqual(g.reward_notice_timer,48)
        for phase in (GamePhase.START,GamePhase.GAME_OVER,GamePhase.RESULT,GamePhase.REWARD_SELECT):
            g.phase=phase
            with patch.object(g,'_update_frame'),patch.object(g,'_update_sushi_sets'):g.update()
            self.assertEqual(g.reward_notice_timer,0);self.assertEqual(g.weapon_cutin_frames,())
            g.phase=GamePhase.PLAYING;s.screen.cls(5);g._draw_reward_notice()
            self.assertTrue(all(c==5 for c in pixels(s.screen)))
            g._show_notice(label='WEAPON GET',title='LANCE UNLOCK',description='Now using LANCE',accent=8,kind='weapon_lance')
        g.reward_notice_timer=1
        with patch.object(g,'_update_frame',side_effect=g._update_ui_timers),patch.object(g,'_update_sushi_sets'):g.update()
        self.assertEqual(g.weapon_cutin_frames,());g._reset_play_state()
        self.assertEqual(g.reward_notice_timer,0);self.assertEqual(g.weapon_cutin_frames,())
        g.phase=GamePhase.PLAYING
        g._upgrade_weapon_family('beam');g.player.hp=0;g.update()
        self.assertEqual(g.phase,GamePhase.GAME_OVER)
        self.assertEqual(g.reward_notice_timer,0);self.assertEqual(g.weapon_cutin_frames,())
        g._enter_result_state();g._reset_play_state()
        self.assertEqual(g.reward_notice_timer,0);self.assertEqual(g.weapon_cutin_frames,())

    def test_weapon_rewards_and_nonweapon_notice(self):
        g=self.g
        for family in g.WEAPON_FAMILY_ORDER:
            for kind in ('unlock','boost','overdrive'):
                g._reset_play_state();g.phase=GamePhase.REWARD_SELECT
                g._apply_reward_choice(RewardChoice(kind+'_'+family,'title','description',10))
                self.assertEqual(g.phase,GamePhase.PLAYING)
                self.assertEqual(g.reward_notice_kind,'weapon_'+family)
                self.assertEqual(len(g.weapon_cutin_frames),72)
        g._show_notice(label='REWARD GET',title='REPAIR',description='HP restored',accent=10)
        self.assertEqual(g.weapon_cutin_frames,())
        s.screen.cls(5);g._draw_reward_notice()

    def test_long_numbers_and_repeated_notices_remain_bounded(self):
        g=self.g
        for n in range(80):
            family=g.WEAPON_FAMILY_ORDER[n%5]
            rng=random.getstate()
            g._show_notice(label='MAX POWER',title=g._weapon_name(family)+' DRIVE',description='ATK +'+str(99999999+n),accent=10,kind='weapon_'+family)
            self.assertEqual(rng,random.getstate())
            self.assertLessEqual(len(list(self.cache_images())),13)
            self.assertEqual(len(g.weapon_cutin_frames),72)
        im=s.pyxel.Image(236,68)
        sx,sy,lines=g._weapon_card_text(im,77,49,'Switched from LANCE / POWER TRIPLE',1)
        self.assertEqual(' '.join(lines),'Switched from LANCE / POWER TRIPLE')
        self.assertEqual(len(lines),2)

if __name__=='__main__':unittest.main()
