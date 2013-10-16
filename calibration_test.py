#!/usr/bin/env python

from __future__ import division

import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)),"pyviewx.client"))
sys.path.insert(1, os.path.join(os.path.dirname(os.path.realpath(__file__)),"pyviewx.pygame"))

from pyglet import resource
from pyglet.gl import *
from pyglet.window import key

from cocos.director import *
from cocos.menu import *
from cocos.layer import *
from cocos.text import *
from cocos.scenes.transitions import *

from odict import OrderedDict

import pygletreactor
pygletreactor.install()
from twisted.internet import reactor

from pyviewx.client import iViewXClient, Dispatcher
from calibrator import CalibrationLayer

from menu import BetterMenu, GhostMenuItem, BetterEntryMenuItem
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
        self.set_eyetracker_extras(value)
        
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
        super(MainMenu, self).__init__("SMI Calibration Test")
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
        filebase = "pySnake_%s" % (getDateTimeStamp())
        director.settings['filebase'] = filebase
        director.scene.dispatch_event('start_task')

    def on_quit(self):
        reactor.callFromThread(reactor.stop)
        
class Task(ColorLayer, pyglet.event.EventDispatcher):
    
    d = Dispatcher()
    
    states = ["INIT", "CALIBRATE", "IGNORE_INPUT", "TASK", "DONE"]
    STATE_INIT = 0
    STATE_CALIBRATE = 1
    STATE_IGNORE_INPUT = 2
    STATE_TASK = 3
    STATE_DONE = 4
    
    is_event_handler = True
    
    def __init__(self, client):
        self.screen = director.get_window_size()
        super(Task, self).__init__(0, 0, 0, 255, self.screen[0], self.screen[1])
        self.state = self.STATE_INIT
        
    def game_over(self):
        self.state = self.STATE_GAME_OVER
        
    def clear(self):
        pass
        
    def reset(self):
        self.clear()
        self.state = self.STATE_TASK
        
    def one_time(self):
        pass
            
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
        self.one_time()
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
        pass
        
    @d.listen('ET_SPL')
    def iViewXEvent(self, inResponse):
        pass
        
    def on_mouse_press(self, x, y, buttons, modifiers):
        pass

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
        
class CalibrationTest(object):
    
    title = "SMI Calibration Test"
        
    def __init__(self):
        
        if not os.path.exists("data"): os.mkdir("data")
            
        pyglet.resource.path.append('resources')
        pyglet.resource.reindex()
        pyglet.resource.add_font('cutouts.ttf')
        
        p = pyglet.window.get_platform()
        d = p.get_default_display()
        s = d.get_default_screen()
        
        director.init(width=s.width, height=s.height,
                  caption=self.title, visible=False, resizable=True)
        director.window.set_size(int(s.width * .75), int(s.height * .75))
        
        director.window.pop_handlers()
        #director.window.push_handlers(DefaultHandler())
                    
        director.settings = {'eyetracker': True,
                             'eyetracker_ip': '127.0.0.1',
                             'eyetracker_out_port': '4444',
                             'eyetracker_in_port': '5555',
                             'calibration_speed': 1,
                             'calibration_wait': 1,
                             'calibration_random': 1,
                             'calibration_level': 3,
                             'calibration_auto': 0,
                             'calibration_points': 9,
                             'calibration_eye': 0
                            }
        
        self.client = None
        
        self.client = iViewXClient(director.settings['eyetracker_ip'], int(director.settings['eyetracker_out_port']))
        self.listener = reactor.listenUDP(int(director.settings['eyetracker_in_port']), self.client)

        director.set_show_FPS(False)
        director.window.set_fullscreen(True)
        director.window.set_mouse_visible(False)
                
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
    cal = CalibrationTest()
    cal.show_intro_scene()
    reactor.run()