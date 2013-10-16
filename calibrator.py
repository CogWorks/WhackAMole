from pyviewx.client import iViewXClient, Dispatcher

from cocos.director import director
from cocos.scene import Scene
from cocos.sprite import Sprite
from cocos.text import Label
from cocos.batch import BatchNode
from cocos.layer import ColorLayer, Layer
from cocos.actions.interval_actions import MoveTo, RotateBy
from cocos.actions.base_actions import Repeat
from cocos.scenes.transitions import TransitionScene

from pyglet import font, resource, event
from pyglet.window import key

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)
    
class FixationLayer(Layer):
    
    d = Dispatcher()
    
    def __init__(self, client):
        super(FixationLayer, self).__init__()
        self.client = client
        
        self.screen = director.get_window_size()
        
        self.font = font.load('Cut Outs for 3D FX', 64)
        fix_img = self.font.get_glyphs("G")[0].get_texture(True)
        fix_img.anchor_x = 'center'
        fix_img.anchor_y = 'center'
        
        self.fix = Sprite(fix_img, position=(self.screen[0] / 2, self.screen[1] / 2), color=(255, 255, 0), opacity=0, scale=.75)
        self.add(self.fix)
        
    def on_enter(self):
        super(FixationLayer, self).on_enter()
        if isinstance(director.scene, TransitionScene): return
        self.client.addDispatcher(self.d)
        self.client.startFixationProcessing(25, 50)
        
    def on_exit(self):
        super(FixationLayer, self).on_exit()
        if isinstance(director.scene, TransitionScene): return
        self.client.removeDispatcher(self.d)
        self.client.stopFixationProcessing()
        
    @d.listen('ET_FIX')
    def iViewXEvent(self, inResponse):
        self.fix.set_position(float(inResponse[2]), float(inResponse[3]))
        self.fix.opacity = 96

    @d.listen('ET_EFX')
    def iViewXEvent(self, inResponse):
        self.fix.opacity = 0
        
class HeadPositionLayer(Layer):
    
    d = Dispatcher()
    
    def __init__(self, client):
        super(HeadPositionLayer, self).__init__()
        self.client = client
        
        self.screen = director.get_window_size()
        
        self.font = font.load('Cut Outs for 3D FX', 384)
        arrow1_img = self.font.get_glyphs("I")[0].get_texture(True)
        arrow1_img.anchor_x = 'center'
        arrow1_img.anchor_y = 'center'
        arrow2_img = self.font.get_glyphs("J")[0].get_texture(True)
        arrow2_img.anchor_x = 'center'
        arrow2_img.anchor_y = 'center'
        
        self.arrows = [Sprite(arrow1_img, position=(self.screen[0] / 2, self.screen[1] / 8 * 7), color=(255, 0, 0), opacity=0, scale=.75, rotation=270),
                       Sprite(arrow1_img, position=(self.screen[0] / 2, self.screen[1] / 8 * 7), color=(255, 0, 0), opacity=0, scale=.75, rotation=90),
                       Sprite(arrow1_img, position=(self.screen[0] / 8, self.screen[1] / 2), color=(255, 0, 0), opacity=0, scale=.75, rotation=0),
                       Sprite(arrow1_img, position=(self.screen[0] / 8 * 7, self.screen[1] / 2), color=(255, 0, 0), opacity=0, scale=.75, rotation=180),
                       Sprite(arrow2_img, position=(self.screen[0] / 2, self.screen[1] / 8), color=(255, 0, 0), opacity=0, scale=.75, rotation=90),
                       Sprite(arrow2_img, position=(self.screen[0] / 2, self.screen[1] / 8), color=(255, 0, 0), opacity=0, scale=.75, rotation=270)]
        
        for arrow in self.arrows:
            self.add(arrow)
            
        self.head = (0,0,0)
        
    def on_enter(self):
        super(HeadPositionLayer, self).on_enter()
        if isinstance(director.scene, TransitionScene): return
        self.client.addDispatcher(self.d)
        
    def on_exit(self):
        super(HeadPositionLayer, self).on_exit()
        if isinstance(director.scene, TransitionScene): return
        self.client.removeDispatcher(self.d)
        
    @d.listen('ET_SPL')
    def iViewXEvent(self, inResponse):
        if len(inResponse) == 16:
            eye_position = map(float, inResponse[10:])
            hx = clamp(round((eye_position[0] + eye_position[1]) / 2 / 99.999, 2), -1.0, 1.0)
            hy = clamp(round((eye_position[2] + eye_position[3]) / 2 / 99.999, 2), -1.0, 1.0)
            hz = clamp(round(((eye_position[4] + eye_position[5]) / 2 - 700) / 150.0, 2), -1.0, 1.0)
            
            self.head = (hx, hy, hz)
            
            if hy >= -.5 and hy <= .5:
                self.arrows[0].opacity = 0
                self.arrows[1].opacity = 0
            elif hy > .5:
                hy = (abs(hy) - .5) / .5
                self.arrows[0].opacity = 0
                self.arrows[1].opacity = 192
                yellow = (1 - hy) * 255
                self.arrows[1].color = (255, yellow, 0)
            elif hy < -.5:
                hy = (abs(hy) - .5) / .5
                self.arrows[0].opacity = 192
                self.arrows[1].opacity = 0
                yellow = (1 - hy) * 255
                self.arrows[0].color = (255, yellow, 0)
                
            if hx >= -.5 and hx <= .5:
                self.arrows[2].opacity = 0
                self.arrows[3].opacity = 0
            elif hx > .5:
                hx = (abs(hx) - .5) / .5
                self.arrows[2].opacity = 0
                self.arrows[3].opacity = 192
                yellow = (1 - hx) * 255
                self.arrows[3].color = (255, yellow, 0)
            elif hx < -.5:
                hx = (abs(hx) - .5) / .5
                self.arrows[2].opacity = 192
                self.arrows[3].opacity = 0
                yellow = (1 - hx) * 255
                self.arrows[2].color = (255, yellow, 0)
            
            if eye_position[4] != 0 and eye_position[5] != 0:
                if hz >= -.5 and hz <= .5:
                    self.arrows[4].opacity = 0
                    self.arrows[5].opacity = 0
                elif hz > .5:
                    hz = (abs(hz) - .5) / .5
                    self.arrows[4].opacity = 0
                    self.arrows[5].opacity = 192
                    yellow = (1 - hz) * 255
                    self.arrows[5].color = (255, yellow, 0)
                elif hz < -.5:
                    hz = (abs(hz) - .5) / .5
                    self.arrows[4].opacity = 192
                    self.arrows[5].opacity = 0
                    yellow = (1 - hz) * 255
                    self.arrows[4].color = (255, yellow, 0)
        
class CalibrationLayer(ColorLayer, event.EventDispatcher):
    
    is_event_handler = True
    
    d = Dispatcher()
    
    STATE_REFUSED = -1
    STATE_INIT = 0
    STATE_CALIBRATE = 1
    STATE_VALIDATE = 2
    STATE_DONE = 3

    def __init__(self, client, points=9, eye=1, wait=1, randomize=1, auto=0, speed=1, level=3):
        super(CalibrationLayer, self).__init__(0, 0, 255, 255)
        self.client = client
        self.points = points
        self.eye = eye
        self.wait = wait
        self.randomize = randomize
        self.auto = auto
        self.speed = speed
        self.level = level
        self.on_success = None
        self.on_failure = None
        
        self.window = director.window.get_size()
        self.screen = director.get_window_size()
        self.center_x = self.screen[0] / 2
        self.center_y = self.screen[1] / 2
        self.win_scale = (self.screen[0] / self.window[0], self.screen[1] / self.window[1])

        self.font = font.load('Cut Outs for 3D FX', 32)
        self.circle_img = self.font.get_glyphs("E")[0].get_texture(True)
        self.circle_img.anchor_x = 'center'
        self.circle_img.anchor_y = 'center'
        self.pnt_img = self.font.get_glyphs("Y")[0].get_texture(True)
        self.pnt_img.anchor_x = 'center'
        self.pnt_img.anchor_y = 'center'
        
        self.circle = Sprite(self.circle_img, color=(255, 255, 0), scale=1, opacity=0)
        self.spinner = Sprite(resource.image('spinner.png'), position=(self.screen[0] / 2, self.screen[1] / 2), color=(255, 255, 255))

    def on_enter(self):
        super(CalibrationLayer, self).on_enter()
        if isinstance(director.scene, TransitionScene): return
        director.window.set_mouse_visible(False)
        self.client.addDispatcher(self.d)
        self.reset()
        self.start()
        
    def on_exit(self):
        super(CalibrationLayer, self).on_exit()
        if isinstance(director.scene, TransitionScene): return
        self.reset()
        self.client.removeDispatcher(self.d)  

    def init(self):
        self.ts = -1
        self.eye_position = None
        self.calibrationPoints = [None] * 9
        self.calibrationResults = []
        self.add(self.circle, z=2)
        self.state = self.STATE_INIT
        
    def reset(self):
        self.client.cancelCalibration()
        for c in self.get_children():
            c.stop()
            self.remove(c)
        self.batch1 = BatchNode()
        self.batch2 = BatchNode()
        self.init()
        
    def start(self):
        if self.state > self.STATE_REFUSED:
            print "start"
            self.dispatch_event("show_headposition")
            self.state = self.STATE_CALIBRATE
            self.client.stopDataStreaming()
            self.client.setSizeCalibrationArea(self.width, self.height)
            self.client.setCalibrationParam(0, self.wait)
            self.client.setCalibrationParam(1, self.randomize)
            self.client.setCalibrationParam(2, self.auto)
            self.client.setCalibrationParam(3, self.speed)
            self.client.setCalibrationCheckLevel(self.level)
            if self.eye == 1 or self.eye == 2:
                self.client.startCalibration(self.points, self.eye)
            else:
                self.client.startCalibration(self.points)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            if self.state == self.STATE_CALIBRATE and not self.circle.actions:
                self.client.acceptCalibrationPoint()
                return True
            elif self.state == self.STATE_DONE:
                self.reset()
                self.on_success()
                return True
        elif symbol == key.R:
            self.reset()
            self.start()
            return True
        elif symbol == key.W and (modifiers & key.MOD_ACCEL):
            #self.reset()
            self.on_failure()
            return True
    
    @d.listen('CONNECTION_REFUSED')
    def iViewXEvent(self, inResponse):
        self.state = self.STATE_REFUSED
        self.label = Label("Connection to iViewX server refused!", position=(self.screen[0] / 2, self.screen[1] / 2),
                           align='center', anchor_x='center', anchor_y='center', width=self.screen[0],
                           font_size=32, color=(255, 255, 255, 255), font_name="Monospace", multiline=True)
        self.add(self.label, z=1)

    @d.listen('ET_CAL')
    def iViewXEvent(self, inResponse):
        print "ET_CAL",inResponse

    @d.listen('ET_CSZ')
    def iViewXEvent(self, inResponse):
        print "ET_CSZ",inResponse

    @d.listen('ET_PNT')
    def iViewXEvent(self, inResponse):
        if self.state == self.STATE_CALIBRATE:
            print 'ET_PNT',inResponse,self.calibrationPoints
            i = int(inResponse[0]) - 1
            self.calibrationPoints[i] = (int(inResponse[1]), int(inResponse[2]))
            s = Sprite(self.pnt_img, color=(255, 0, 0), scale=.75)
            s.set_position(self.calibrationPoints[i][0],self.calibrationPoints[i][1])
            self.add(s, z=1)
        elif self.state == self.STATE_VALIDATE:
            pass

    @d.listen('ET_CHG')
    def iViewXEvent(self, inResponse):
        print 'ET_CHG',inResponse
        currentPoint = int(inResponse[0]) - 1
        x = self.calibrationPoints[currentPoint][0] * self.win_scale[0]
        y = self.calibrationPoints[currentPoint][1] * self.win_scale[1]
        self.circle.opacity = 255
        if currentPoint == 0:
            self.circle.set_position(x, y)
        else:
            self.circle.do(MoveTo((x, y), .75))

    @d.listen('ET_VLS')
    def iViewXEvent(self, inResponse):
        print "ET_VLS",inResponse
        if self.state == self.STATE_VALIDATE:
            self.calibrationResults.append(' '.join(inResponse))
            if len(self.calibrationResults) == 2:
                self.remove(self.spinner)
                self.remove(self.label)
                text = '\n'.join(self.calibrationResults).decode("cp1252")
                text += "\n\n\nPress 'R' to recalibrate, spres 'Spacebar' to continue..."
                self.label = Label(text, position=(self.screen[0] / 2, self.screen[1] / 2),
                                   align='center', anchor_x='center', anchor_y='center', width=self.screen[0],
                                   font_size=32, color=(255, 255, 255, 255), font_name="Monospace", multiline=True)
                self.add(self.label)
                self.state = self.STATE_DONE

    @d.listen('ET_CSP')
    def iViewXEvent(self, inResponse):
        sl = Sprite(self.pnt_img, color=(255, 255, 0), scale=.25, opacity=128)
        sl.set_position(int(float(inResponse[1])),int(float(inResponse[2])))
        self.batch1.add(sl)
        sr = Sprite(self.pnt_img, color=(0, 255, 0), scale=.25, opacity=128)
        sr.set_position(int(float(inResponse[3])),int(float(inResponse[4])))
        self.batch2.add(sr)

    @d.listen('ET_FIN')
    def iViewXEvent(self, inResponse):
        print "ET_FIN",inResponse
        if self.state != self.STATE_VALIDATE:
            self.add(self.batch1,z=1)
            self.add(self.batch2,z=1)
            self.dispatch_event("hide_headposition")
            self.state = self.STATE_VALIDATE
            self.remove(self.circle)
            self.add(self.spinner)
            self.spinner.do(Repeat(RotateBy(360, 1)))
            self.label = Label("CALCULATING CALIBRATION ACCURACY", position=(self.screen[0] / 2, self.screen[1] / 4 * 3),
                               font_size=32, color=(255, 255, 255, 255), font_name="Monospace", anchor_x='center', anchor_y='center')
            self.add(self.label)
            self.client.requestCalibrationResults()
            self.client.validateCalibrationAccuracy()
