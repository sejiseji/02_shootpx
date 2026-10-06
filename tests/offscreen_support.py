"""Full app callbacks with native Pyxel offscreen rasterization.
No window, audio, browser or save. Input/RNG are controlled substitutes.
Do not interpret these timings as native onscreen or Web/iPhone FPS.
"""
import collections
import cProfile
import gc
import hashlib
import json
import math
from pathlib import Path
import pstats
import random
import statistics
import sys
import time
import tomllib
import zipfile

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[1]

sys.path.insert(0,str(REPO))
import pyxel
import shootpx
from game_models import GamePhase, OrbitSushiEntry
from boss_system import spawn_boss
from effects import HitSparkEffect

class SilentAudio:
    def __init__(self):self.events=[]
    def update(self,*a):pass
    def play_bgm(self,*a):self.events.append(('bgm',a))
    def play_se(self,*a):self.events.append(('se',a));return True
    def stop_bgm(self,*a):self.events.append(('stop',a))

with zipfile.ZipFile(REPO/'shootpx.pyxres') as z:
    resource=tomllib.loads(z.read('pyxel_resource.toml').decode())
images=[]
for spec in resource['images']:
    im=pyxel.Image(spec['width'],spec['height'])
    for y,row in enumerate(spec['data']):
        for x,color in enumerate(row):im.pset(x,y,color)
    images.append(im)
maps=[]
for spec in resource['tilemaps']:
    tm=pyxel.Tilemap(spec['width'],spec['height'],images[spec['imgsrc']])
    for y,row in enumerate(spec['data']):
        for x in range(len(row)//2):tm.pset(x,y,(row[2*x],row[2*x+1]))
    maps.append(tm)

screen=pyxel.Image(360,640)
pyxel.width=360;pyxel.height=640
pyxel.mouse_x=180;pyxel.mouse_y=500
pyxel.image=lambda bank:images[bank]
init_arguments=[]
pyxel.init=lambda *a,**k:init_arguments.append((a,k))
pyxel.load=lambda *a,**k:None
pyxel.run=lambda *a,**k:None
pyxel.mouse=lambda *a,**k:None
pyxel.btn=lambda key:key==pyxel.KEY_RETURN
pyxel.btnp=lambda *a,**k:False
pyxel.rndi=lambda a,b:random.randint(a,b)
pyxel.rndf=lambda a,b:random.uniform(a,b)
shootpx.AudioSystem=SilentAudio

def blt(x,y,source,u,v,w,h,*a,**k):
    if isinstance(source,int):source=images[source]
    screen.blt(x,y,source,u,v,w,h,*a,**k)
def bltm(x,y,source,u,v,w,h,*a,**k):
    if isinstance(source,int):source=maps[source]
    screen.bltm(x,y,source,u,v,w,h,*a,**k)
DRAW_NAMES=('cls','pset','line','rect','rectb','circ','circb','elli','ellib','tri','trib','text')
native_draw={name:getattr(screen,name) for name in DRAW_NAMES}
native_draw.update(blt=blt,bltm=bltm)
for name,fn in native_draw.items():setattr(pyxel,name,fn)

def stats(samples):
    s=sorted(samples)
    return dict(median_ms=statistics.median(s),p95_ms=s[math.ceil(.95*len(s))-1],
                p99_ms=s[math.ceil(.99*len(s))-1],max_ms=max(s))

def game(scene):
    random.seed(20261006)
    g=shootpx.ShootGame()
    if scene=='start':return g
    g.phase=GamePhase.PLAYING
    g.next_boss_kill_threshold=10**9;g.next_boss_score_threshold=10**9
    if scene in ('boss','fever'):
        g.boss_spawn_count=4
        g.boss_event_started=True
        g.boss=spawn_boss(width=360,entry_target_y=200,max_hp=9999,spawn_count=4)
        g.boss.y=200;g.boss.entry_done=True;g.boss.entry_invulnerable=False
        g.assign_buff_to_current_boss();g._select_boss_pattern()
    if scene=='fever':
        g.boss_buff_state.overload_active=True
        g.boss_buff_state.acquired_cycle_buffs=set(g.BUFF_IDS)
        g.orbit_sushi_queue=[OrbitSushiEntry('tuna','basic',i) for i in range(10)]
        g.sushi_settle_threshold=20
        g.current_weapon_family=g.WEAPON_FAMILY_BEAM
        g.unlocked_weapon_families=list(g.WEAPON_FAMILY_ORDER)
        g.weapon_levels[g.WEAPON_FAMILY_BEAM]=g.SHOT_LEVEL_POWER_TRIPLE
        g.active_weapon_slots=[g.WEAPON_FAMILY_BEAM]
    if scene=='reward':
        g._start_reward_selection()
        # Exclude already investigated one-time precomputation from timed samples.
        while g.pending_orbit_pattern_build>0:g.maybe_build_orbit_pattern_in_nonbattle()
        while g.pending_bomb_pattern_build>0:g.maybe_build_bomb_pattern_in_reward()
    return g
