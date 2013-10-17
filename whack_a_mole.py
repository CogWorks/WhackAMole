#!/usr/bin/env python

from __future__ import division

import sys, os, random

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)),"pyviewx.client"))
sys.path.insert(1, os.path.join(os.path.dirname(os.path.realpath(__file__)),"pyviewx.pygame"))

from pyglet import resource, clock, text
from pyglet.gl import *
from pyglet.window import key
from pyglet.media import Player, StaticSource

from cocos.director import *
from cocos.menu import *
from cocos.layer import *
from cocos.text import *
from cocos.scenes.transitions import *
from cocos.sprite import Sprite
from cocos.tiles import RectMapLayer
from cocos.actions.instant_actions import CallFunc
from cocos.actions.interval_actions import Delay, MoveTo, AccelDeccel, FadeTo
from cocos.collision_model import CollisionManagerBruteForce, AARectShape

from primitives import Polygon

from odict import OrderedDict

import pygletreactor
pygletreactor.install()
from twisted.internet import reactor

from pyviewx.client import iViewXClient, Dispatcher
from calibrator import CalibrationLayer

from menu import BetterMenu, GhostMenuItem, BetterEntryMenuItem
from handler import DefaultHandler
from scene import Scene

from pycogworks.logging import getDateTimeStamp

class OptionsMenu(BetterMenu):

    def __init__(self):
        super(OptionsMenu, self).__init__('Options')
        self.screen = director.get_window_size()
        
        ratio = self.screen[1] / self.screen[0]
        
        self.font_title['font_size'] = self.screen[0] / 18
        self.font_title['color'] = (255, 255, 255, 255)
        
        self.font_item['color'] = (255, 255, 255, 255)
        self.font_item['font_size'] = self.screen[1] / 16 * ratio
        self.font_item_selected['color'] = (0, 0, 255, 255)
        self.font_item_selected['font_size'] = self.screen[1] / 16 * ratio
        
        self.items = OrderedDict()
        
        self.speed_opts = ['SLOW','FAST']
        self.level_opts = ['NONE','WEAK','MEDIUM','STRONG']
        self.eye_opts = ['NONE','RIGHT','LEFT']
        self.points_opts = ['2','5','9','13']
        
        self.items['overlay'] = ToggleMenuItem('Debug Overlay:', self.on_overlay, director.settings['overlay'])
        self.items['eyetracker'] = ToggleMenuItem('EyeTracker:', self.on_eyetracker, director.settings['eyetracker'])
        self.items['eyetracker_ip'] = EntryMenuItem('EyeTracker IP:', self.on_eyetracker_ip, director.settings['eyetracker_ip'])
        self.items['eyetracker_in_port'] = EntryMenuItem('EyeTracker In Port:', self.on_eyetracker_in_port, director.settings['eyetracker_in_port'])
        self.items['eyetracker_out_port'] = EntryMenuItem('EyeTracker Out Port:', self.on_eyetracker_out_port, director.settings['eyetracker_out_port'])
        self.items['calibration_points'] = MultipleMenuItem('Calibration Points:', self.on_cal_points, self.points_opts, self.points_opts.index(str(director.settings['calibration_points'])))
        self.items['calibration_eye'] = MultipleMenuItem('Calibration Eye:', self.on_cal_eye, self.eye_opts, director.settings['calibration_eye'])
        self.items['calibration_level'] = MultipleMenuItem('Calibration Check Level:', self.on_cal_level, self.level_opts, director.settings['calibration_level'])
        self.items['calibration_speed'] = MultipleMenuItem('Calibration Speed:', self.on_cal_speed, self.speed_opts, director.settings['calibration_speed'])
        self.items['calibration_auto'] = ToggleMenuItem('Calibration Auto-accept:', self.on_cal_auto, director.settings['calibration_auto'])
        self.items['calibration_wait'] = ToggleMenuItem('Calibration Wait For Good:', self.on_cal_wait, director.settings['calibration_wait'])
        self.items['calibration_random'] = ToggleMenuItem('Calibration Randomize:', self.on_cal_random, director.settings['calibration_random'])
        
        self.create_menu(self.items.values(), zoom_in(), zoom_out())

    def on_overlay(self, value):
        director.settings['overlay'] = value

    def on_eyetracker(self, value):
        director.settings['eyetracker'] = value
    
    def on_cal_points(self, value):
        director.settings['calibration_points'] = int(self.points_opts[value])
    
    def on_cal_eye(self, value):
        director.settings['calibration_speed'] = value
    
    def on_cal_level(self, value):
        director.settings['calibration_speed'] = value
    
    def on_cal_speed(self, value):
        director.settings['calibration_speed'] = value
    
    def on_cal_auto(self, value):
        director.settings['calibration_auto'] = value
        
    def on_cal_wait(self, value):
        director.settings['calibration_wait'] = value
        
    def on_cal_random(self, value):
        director.settings['calibration_random'] = value
    
    def on_enter(self):
        super(OptionsMenu, self).on_enter()
        self.orig_values = (director.settings['eyetracker_ip'],
                            director.settings['eyetracker_in_port'],
                            director.settings['eyetracker_out_port'])
    
    def on_exit(self):
        super(OptionsMenu, self).on_exit()
        new_values = (director.settings['eyetracker_ip'],
                            director.settings['eyetracker_in_port'],
                            director.settings['eyetracker_out_port'])
        if new_values != self.orig_values:
            director.scene.dispatch_event("eyetracker_info_changed")    
        
    def on_eyetracker(self, value):
        director.settings['eyetracker'] = value
        
    def on_eyetracker_ip(self, ip):
        director.settings['eyetracker_ip'] = ip
    
    def on_eyetracker_in_port(self, port):
        director.settings['eyetracker_in_port'] = port
    
    def on_eyetracker_out_port(self, port):
        director.settings['eyetracker_out_port'] = port
            
    def on_quit(self):
        self.parent.switch_to(0)

class MainMenu(BetterMenu):

    def __init__(self):
        super(MainMenu, self).__init__("Whack A Mole")
        self.screen = director.get_window_size()
        
        ratio = self.screen[1] / self.screen[0]

        self.font_title['font_size'] = self.screen[0] / 18
        self.font_title['color'] = (255, 255, 255, 255)

        self.font_item['color'] = (255, 255, 255, 255)
        self.font_item['font_size'] = self.screen[1] / 16 * ratio
        self.font_item_selected['color'] = (0, 0, 255, 255)
        self.font_item_selected['font_size'] = self.screen[1] / 16 * ratio

        self.menu_anchor_y = 'center'
        self.menu_anchor_x = 'center'

        self.items = OrderedDict()
        
        self.items['start'] = MenuItem('Start', self.on_start)
        self.items['options'] = MenuItem('Options', self.on_options)
        self.items['quit'] = MenuItem('Quit', self.on_quit)
        
        self.create_menu(self.items.values(), zoom_in(), zoom_out())
        
    def on_options(self):
        self.parent.switch_to(1)
        
    def on_start(self):
        filebase = "WhackAMole_%s" % (getDateTimeStamp())
        director.settings['filebase'] = filebase
        director.scene.dispatch_event('start_task')

    def on_quit(self):
        reactor.callFromThread(reactor.stop)
                
class Mole(Sprite, AARectShape):
    
    def __init__(self, images, x, y):
        self.images = images
        super(Mole, self).__init__(self.images[0], anchor=(0,0), position=(x,y))
        self.position_out = self.position
        self.position_in = (self.position[0],self.position[1]-130)
        self.position = self.position_in
        self.bottom = self.position_in[1] + 200
        self.cshape = self
        self.active = False
        
        self.player_thump = StaticSource(pyglet.resource.media('ow.mp3'))
        self.player_laugh = StaticSource(pyglet.resource.media('laugh.mp3'))
        
        self.STATE_IDLE = 0
        self.STATE_HIT = 1
        self.STATE_MISS = 2
        self.state = self.STATE_IDLE
        
    def __getattribute__(self,name):
        if name=='center':
            return (self.position[0]+89, (self.position[1]+self.bottom+200)/2 - 20)
        elif name=='rx':
            return 89
        elif name=='ry':
            return (self.position[1]+200-self.bottom)/2 + 20
        else:
            return object.__getattribute__(self, name)
        
    def setImage(self, index):
        self.image = self.images[index]
        
    def setImageFunc(self, index):
        return CallFunc(self.setImage, index)
    
    def checkHitState(self):
        if self.state == self.STATE_IDLE:
            self.laugh()
            self.state = self.STATE_MISS
    
    def setActive(self, value):
        self.active = value
        
    def setState(self, value):
        self.state = value
            
    def display(self):
        self.setImage(0)
        self.position = self.position_in
        self.do(CallFunc(self.setActive, True) + 
                AccelDeccel(MoveTo(self.position_out, 1)) +
                Delay(.5) + 
                CallFunc(self.checkHitState) + 
                AccelDeccel(MoveTo(self.position_in, 1)) +
                CallFunc(self.setActive, False) +
                CallFunc(self.setState, 0))
        
    def laugh(self):
        self.player_laugh.play()
        self.do(self.setImageFunc(1)+Delay(.1)+
                self.setImageFunc(2)+Delay(.1)+
                self.setImageFunc(3)+Delay(.1)+
                self.setImageFunc(2)+Delay(.1)+
                self.setImageFunc(3)+Delay(.1)+
                self.setImageFunc(1)+Delay(.1))
        
    def thump(self):
        self.player_thump.play()
        self.do(self.setImageFunc(4)+Delay(.1)+
                self.setImageFunc(5)+Delay(.1)+
                self.setImageFunc(6)+Delay(.1)+
                self.setImageFunc(4)+Delay(.1)+
                self.setImageFunc(5)+Delay(.1)+
                self.setImageFunc(6)+Delay(.1))
        
class Task(ColorLayer, pyglet.event.EventDispatcher):
    
    d = Dispatcher()
    
    states = ["INIT", "CALIBRATE", "IGNORE_INPUT", "TASK", "DONE"]
    STATE_INIT = 0
    STATE_CALIBRATE = 1
    STATE_IGNORE_INPUT = 2
    STATE_TASK = 3
    STATE_DONE = 4
    
    BG_TILE_SIZE = (1024,128)
    FG_TILE_SIZE = (1024,128)
    
    is_event_handler = True
    
    def __init__(self, client=None):
        self.screen = director.get_window_size()
        super(Task, self).__init__(0, 0, 0, 255, 1024, int(768*1.1))
        self.client = client
        self.state = self.STATE_INIT
        
        self.mole_images = [resource.image('mole_1.png'),
                            resource.image('mole_laugh1.png'),
                            resource.image('mole_laugh2.png'),
                            resource.image('mole_laugh3.png'),
                            resource.image('mole_thump1.png'),
                            resource.image('mole_thump2.png'),
                            resource.image('mole_thump3.png'),
                            resource.image('mole_thump4.png')]
        
        self.music = Player()
        self.music.queue(pyglet.resource.media('whack.mp3'))
        self.music.eos_action = 'loop'
        
        self.cm = CollisionManagerBruteForce()
        
        self.moles = []
        for i in range(0,3):
            mole = Mole(self.mole_images, (112 + (i * 310)), (127-80))
            self.moles.append(mole)
            self.add(mole, 55)
            self.cm.add(mole)
        for i in range(3,6):
            mole = Mole(self.mole_images, (112 + ((i-3) * 310)), (383-80))
            self.moles.append(mole)
            self.add(mole, 35)
            self.cm.add(mole)
        for i in range(6,9):
            mole = Mole(self.mole_images, (112 + ((i-6) * 310)), (639-80))
            self.moles.append(mole)
            self.add(mole, 15)
            self.cm.add(mole)
            
        self.text_batch = BatchNode()
        self.add(self.text_batch, z=100)
        
        self.score = 0
            
        scorey = int((768 + int(768*1.1))/2)
        self.score_num = text.Label("%06d" % self.score, font_name="Score Board", font_size=48, x=512, y=scorey, color=(255, 255, 255, 255),
                                    anchor_x='center', anchor_y='center', batch=self.text_batch.batch)
                                            
        self.fix = Label('G', font_name='Cut Outs for 3D FX', font_size=48,
                          position=(0,0), color=(255, 0, 0, 192), anchor_x='center', anchor_y='center')
        self.fix.visible = False
        self.add(self.fix, z=100000)

        self.add(Sprite(resource.image('bg_dirt128.png'), anchor=(0,0), position=(0,0)))
        self.add(Sprite(resource.image('bg_dirt128.png'), anchor=(0,0), position=(0,128)))
        self.add(Sprite(resource.image('bg_dirt128.png'), anchor=(0,0), position=(0,256)))
        self.add(Sprite(resource.image('bg_dirt128.png'), anchor=(0,0), position=(0,384)))
        self.add(Sprite(resource.image('bg_dirt128.png'), anchor=(0,0), position=(0,512)))
        self.add(Sprite(resource.image('bg_dirt128.png'), anchor=(0,0), position=(0,640)))
        
        self.add(Sprite(resource.image('grass_lower128.png'), anchor=(0,0), position=(0,0)), z=60)
        self.add(Sprite(resource.image('grass_upper128.png'), anchor=(0,0), position=(0,128)), z=50)
        self.add(Sprite(resource.image('grass_lower128.png'), anchor=(0,0), position=(0,256)), z=40)
        self.add(Sprite(resource.image('grass_upper128.png'), anchor=(0,0), position=(0,384)), z=30)
        self.add(Sprite(resource.image('grass_lower128.png'), anchor=(0,0), position=(0,512)), z=20)
        self.add(Sprite(resource.image('grass_upper128.png'), anchor=(0,0), position=(0,640)), z=10)
        
        
    def set_score(self):
        self.score_num.begin_update()
        self.score_num.text = "%06d" % self.score
        self.score_num.end_update()
        
    def visit(self):
        super(Task, self).visit()
        if director.settings["overlay"]:
            for mole in self.moles:
                if mole.opacity > -1:
                    if mole.state == 1:
                        color = (.3,0.0,0.0,.7)
                    else:
                        color = (.3,0.2,0.5,.7)
                    p = Polygon([(mole.center[0]-mole.rx, mole.center[1]-mole.ry), 
                                 (mole.center[0]+mole.rx, mole.center[1]-mole.ry),
                                 (mole.center[0]+mole.rx, mole.center[1]+mole.ry),
                                 (mole.center[0]-mole.rx, mole.center[1]+mole.ry)],
                                color=color)
                    p.render()
        
    def animate(self, dt):
        moles = [mole for mole in self.moles if not mole.active]
        if moles:
            random.choice(moles).display()
                    
    def game_over(self):
        self.state = self.STATE_GAME_OVER
        
    def clear(self):
        self.music.pause()
        self.music.seek(0)
        for mole in self.moles:
            mole.active = False
            mole.state = 0
            mole.position = mole.position_in
        pyglet.clock.unschedule(self.animate)
        if self.client:
            self.client.removeDispatcher(self.d)
            self.client.stopDataStreaming()
            self.client.stopFixationProcessing()
        
    def reset(self):
        self.clear()
        if self.client:
            self.client.addDispatcher(self.d)
            #self.client.setDataFormat('%TS %ET %SX %SY %DX %DY %EX %EY %EZ')
            #self.client.startDataStreaming()
            self.client.startFixationProcessing()
        self.state = self.STATE_TASK
        self.score = 0
        pyglet.clock.schedule_interval(self.animate, .5)
        self.music.play()
        
    def on_enter(self):
        if isinstance(director.scene, TransitionScene): return
        super(Task, self).on_enter()
        
        if director.settings['eyetracker']:
            self.state = self.STATE_CALIBRATE
            self.dispatch_event("start_calibration", self.calibration_ok, self.calibration_bad)
        else:
            self.reset()
            
    def calibration_ok(self):
        self.dispatch_event("stop_calibration")
        self.reset()
        
    def calibration_bad(self):
        self.dispatch_event("stop_calibration")
        director.scene.dispatch_event("show_intro_scene")
        
    def on_exit(self):
        if isinstance(director.scene, TransitionScene): return
        super(Task, self).on_exit()
        self.clear()

    @d.listen('ET_FIX')
    def iViewXEvent(self, inResponse):
        if inResponse[0] == 'l':
            x = int(float(inResponse[2]))
            y = int(float(inResponse[3]))
            if director.settings["overlay"]:
                self.fix.position = (x, y)
                self.fix.visible = True
            self.handle_mouse_press(x, y)
    
    @d.listen('ET_EFX')
    def iViewXEvent(self, inResponse):
        if inResponse[0] == 'l':
            if director.settings["overlay"]:
                self.fix.visible = False
    
    @d.listen('ET_SPL')
    def iViewXEvent(self, inResponse):
        pass
        
    def handle_mouse_press(self, x, y):
        for obj in self.cm.objs_touching_point(x, y):
            if obj.active:
                if obj.state == 0:
                    obj.state = 1
                    obj.thump()
                    self.score += 10
                elif obj.state == 2:
                    self.score -= 10
                self.set_score()
        
    def on_mouse_press(self, x, y, buttons, modifiers):
        posx, posy = director.get_virtual_coordinates(x, y)
        self.handle_mouse_press(posx, posy)

    def on_mouse_motion(self, x, y, dx, dy):
        pass
        
    def on_key_press(self, symbol, modifiers):
        if self.state < self.STATE_IGNORE_INPUT: return
        if symbol == key.W and (modifiers & key.MOD_ACCEL):
            director.scene.dispatch_event("show_intro_scene")
            True
        if self.state == self.STATE_TASK:
            pass
        elif self.state == self.STATE_DONE:
            pass

class EyetrackerScrim(ColorLayer):
    
    def __init__(self):
        self.screen = director.get_window_size()
        super(EyetrackerScrim, self).__init__(0, 0, 0, 224, self.screen[0], self.screen[1])
        l = Label("Reconnecting to eyetracker...", position=(self.screen[0] / 2, self.screen[1] / 2), font_name='', font_size=32, bold=True, color=(255, 255, 255, 255), anchor_x='center', anchor_y='center')
        self.add(l)
        
class WhackAMole(object):
    
    title = "Whack A Mole"
        
    def __init__(self):
        
        if not os.path.exists("data"): os.mkdir("data")
            
        pyglet.resource.path.append('resources')
        pyglet.resource.reindex()
        pyglet.resource.add_font('cutouts.ttf')
        pyglet.resource.add_font('scoreboard.ttf')
        
        director.init(width=int(1024*1.0), height=int(768*1.1),
                  caption=self.title, visible=False, resizable=True)
        director.window.set_size(int(1024*1.0), int(768*1.1))
        
        director.window.pop_handlers()
        director.window.push_handlers(DefaultHandler())
                    
        director.settings = {'overlay': True,
                             'eyetracker': True,
                             'eyetracker_ip': '127.0.0.1',
                             'eyetracker_out_port': '4444',
                             'eyetracker_in_port': '5555',
                             'calibration_speed': 1,
                             'calibration_wait': 1,
                             'calibration_random': 1,
                             'calibration_level': 3,
                             'calibration_auto': 1,
                             'calibration_points': 5,
                             'calibration_eye': 0
                            }
        
        self.client = None
        
        self.client = iViewXClient(director.settings['eyetracker_ip'], int(director.settings['eyetracker_out_port']))
        self.listener = reactor.listenUDP(int(director.settings['eyetracker_in_port']), self.client)

        director.set_show_FPS(False)
        director.window.set_fullscreen(False)
        if director.settings['eyetracker']:
            director.window.set_mouse_visible(False)
        else:
            director.window.set_mouse_visible(True)
                
        # Intro scene and its layers        
        self.introScene = Scene()
                    
        self.mainMenu = MainMenu()
        self.optionsMenu = OptionsMenu()
        self.eyetrackerScrim = EyetrackerScrim()
        
        self.mplxLayer = MultiplexLayer(self.mainMenu, self.optionsMenu)
        self.introScene.add(self.mplxLayer, 1)
        
        self.introScene.register_event_type('start_task')
        self.introScene.register_event_type('eyetracker_info_changed')
        self.introScene.push_handlers(self)
                
        # Task scene and its layers
        self.taskScene = Scene()
        self.taskLayer = Task(self.client)

        self.calibrationLayer = CalibrationLayer(self.client)
        self.calibrationLayer.register_event_type('show_headposition')
        self.calibrationLayer.register_event_type('hide_headposition')
        self.calibrationLayer.push_handlers(self)
        
        self.taskLayer.register_event_type('new_trial')
        self.taskLayer.register_event_type('start_calibration')
        self.taskLayer.register_event_type('stop_calibration')
        self.taskLayer.push_handlers(self)
                
        self.taskScene.add(self.taskLayer, 1)
        
        self.taskScene.register_event_type('show_intro_scene')
        self.taskScene.push_handlers(self)
            
        director.window.set_visible(True)
        
    def start_calibration(self, on_success, on_failure):
        self.calibrationLayer.on_success = on_success
        self.calibrationLayer.on_failure = on_failure
        self.calibrationLayer.points = director.settings['calibration_points']
        self.calibrationLayer.eye = director.settings['calibration_eye']
        self.calibrationLayer.level = director.settings['calibration_level']
        self.calibrationLayer.speed = director.settings['calibration_speed']
        self.calibrationLayer.auto = director.settings['calibration_auto']
        self.calibrationLayer.wait = director.settings['calibration_wait']
        self.calibrationLayer.random = director.settings['calibration_random']
        self.taskScene.add(self.calibrationLayer, 2)
        
    def stop_calibration(self):
        self.taskScene.remove(self.calibrationLayer)
            
    def eyetracker_listen(self, _):
        self.listener = reactor.listenUDP(int(director.settings['eyetracker_in_port']), self.client)
        self.introScene.remove(self.eyetrackerScrim)
        self.introScene.enable_handlers(True)
        
    def eyetracker_info_changed(self):
        if self.client.remoteHost != director.settings['eyetracker_ip'] or \
        self.client.remotePort != int(director.settings['eyetracker_out_port']):
            self.client.remoteHost = director.settings['eyetracker_ip']
            self.client.remotePort = int(director.settings['eyetracker_out_port'])
        else:
            self.introScene.add(self.eyetrackerScrim, 2)
            self.introScene.enable_handlers(False)
            d = self.listener.stopListening()
            d.addCallback(self.eyetracker_listen)
        
    def show_intro_scene(self):
        self.mplxLayer.switch_to(0)
        director.replace(self.introScene)
        
    def start_task(self):
        director.replace(SplitRowsTransition(self.taskScene))
                 
if __name__ == '__main__':
    cal = WhackAMole()
    cal.show_intro_scene()
    reactor.run()