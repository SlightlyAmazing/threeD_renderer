from common_libs import *    
import pygame as pyg
from time import sleep
import math
from threading import Lock

Xyz = Xyz.Xyz
Xy = Xy.Xy
pygameManager = pygame_interface.pygameManager
gameManager = game_manager.gameManager
threadManager = coroutines_threads.threadManager()
settingsManager = settings_manager.settingsManager()
callbackManager = callbacks.callbackManager()
timedCallback = callbacks.timedCallback
debugManager = debug_manager.debugManager()

default_draw_color = (255,255,0)    #yellow
default_bg_color = (0,0,0)          #black
default_width = 2

RIGHTMOUSEBUTTON = 2
MIDDLEMOUSEBUTTON = 1
LEFTMOUSEBUTTON = 0

moveAmount = 10
angleMoveAmount = math.radians(1)
keydownRepeatTime = 0.01

# x = right
# y = away from camera
# z = up

class Effect():

    def __init__(self, direction, magnitude):
        self.direction = direction # "Theta"; "Phi"; "Nu"; "Right"; "Forward"; "Up"; "y"; "x"; "z"; "Zoom";
        self.magnitude = magnitude 
 
class threeDManager(base_classes.baseManager):

    def onInit(self,scene,screen_size = None,bg_color = None,veiwPoint = None):
        self.bg_color = default_bg_color
        if bg_color != None:
            self.bg_color = bg_color
        self.scene = scene
        self.display_lock = Lock()
        gameManager.Current.registerObj(self)
        self.veiwPoint = Xyz(0,500,0)
        if veiwPoint != None:
            self.veiwPoint = veiwPoint
        self.relativePos = Xyz(self.veiwPoint)
        self.zoom = 50
        self.currentPositions = []
        self.mappedPositions = {}
        self.effects = []
        self.newEffects = []
        self.positionsUpdated = []
        self.screen_size = Xy(gameManager.Current.scenes[self.scene].get_size())
        if screen_size != None:
            self.screen_size = screen_size

        self.update()

    def resetEffects(self): #f4
        with self.display_lock:
            self.effects = []
        self.resetMappedPositions()

    def resetMappedPositions(self): #f5
        with self.display_lock:
            self.mappedPositions = {}
            self.relativePos = Xyz(self.veiwPoint)
            self.zoom = 50
            for effect in self.effects:
                if effect.direction == "Zoom":
                    self.zoom += effect.magnitude

            for threeDObject in self.currentPositions:
                threeDObject.resetMappedPositions()
        
    def addEffects(self,*effects):
        with self.display_lock:
            self.effects.extend(effects)
            self.newEffects.extend(effects)
            for effect in effects:
                match effect.direction:
                    case "Zoom":
                        self.zoom += effect.magnitude
            
    def addObjects(self,*objects):
        with self.display_lock:
            self.currentPositions.extend(objects)
    
    def getMappedPosition(self,xyz):
        if xyz not in self.mappedPositions.keys():
            self.mappedPositions[xyz] = self.calculateNewPoint(xyz,self.effects)
            self.positionsUpdated.append(xyz)
        elif xyz not in self.positionsUpdated:
            self.mappedPositions[xyz] = self.calculateNewPoint(self.mappedPositions[xyz],self.newEffects)
            self.positionsUpdated.append(xyz)
        return self.mappedPositions[xyz]

    def getFullyMappedXyPosition(self,xyz):
        return self.calculateNewXyPoint(self.getMappedPosition(xyz))

    def getFullyMappedXyPositions(self,xyzs):
        return [self.getFullyMappedXyPosition(xyz) for xyz in xyzs]
        
    def calculateNewPoint(self,xyz,effects):

        newXyz = Xyz(xyz)
        
        radius = math.sqrt(xyz.x**2 + xyz.y**2 + xyz.z**2)

        theta = 0
        phi = 0
        nu = 0
        forward = 0 # y
        right = 0 # x
        up = 0 # z
                
        for effect in effects:
            match effect.direction:
                case "Phi":
                    if radius == 0:
                        continue
                    phi += effect.magnitude
                    theta = math.acos(newXyz.z/radius)
                    phi = math.atan2(newXyz.y,newXyz.x) + effect.magnitude
                    newXyz = Xyz(radius*math.sin(theta)*math.cos(phi),radius*math.sin(theta)*math.sin(phi),radius*math.cos(theta))
                case "Theta":
                    if radius == 0:
                        continue  
                    theta += effect.magnitude          
                    theta = math.acos(newXyz.x/radius)
                    phi = math.atan2(newXyz.y,newXyz.z) + effect.magnitude
                    newXyz = Xyz(radius*math.cos(theta),radius*math.sin(theta)*math.sin(phi),radius*math.sin(theta)*math.cos(phi))
                case "Nu":
                    if radius == 0:
                        continue
                    nu += effect.magnitude
                    theta = math.acos(newXyz.y/radius)
                    phi = math.atan2(newXyz.x,newXyz.z) + effect.magnitude
                    newXyz = Xyz(radius*math.sin(theta)*math.sin(phi),radius*math.cos(theta),radius*math.sin(theta)*math.cos(phi))
                case "Forward":
                    forward += effect.magnitude
                    newXyz.y += effect.magnitude
                    radius = math.sqrt(newXyz.x**2 + newXyz.y**2 + newXyz.z**2)
                case "Right":
                    right += effect.magnitude
                    newXyz.x -= effect.magnitude
                    radius = math.sqrt(newXyz.x**2 + newXyz.y**2 + newXyz.z**2)
                case "Up":
                    up += effect.magnitude
                    newXyz.z -= effect.magnitude
                    radius = math.sqrt(newXyz.x**2 + newXyz.y**2 + newXyz.z**2)
                
        return newXyz

    def calculateNewXyPoint(self, xyz):
        if self.zoom > 100:
            self.zoom = 100
        elif self.zoom <= 0:
            self.zoom = 1
        y_plane =((self.veiwPoint.y**(1/50))**self.zoom)/(xyz.y if xyz.y > 0 else 1)
        xy = Xy((y_plane*(xyz.x)),-(y_plane*(xyz.z)))
        xy+=self.screen_size//2
        return xy
                    
    def display(self):
        with self.display_lock:
            for obj3D in self.currentPositions:
                for line in obj3D.getLines():
                    pyg.draw.aaline(gameManager.Current.scenes[self.scene],line.color,*self.getFullyMappedXyPositions(line))
                for polygon in obj3D.getPolygons():
                    pyg.draw.aalines(gameManager.Current.scenes[self.scene],polygon.color,True,self.getFullyMappedXyPositions(polygon))

    def cleanUp(self):
        with self.display_lock:
            delPos = []
            for xyz in self.mappedPositions.keys():
                if xyz not in self.positionsUpdated:
                    delPos.append(xyz)
            for xyz in delPos:
                del self.mappedPositions[xyz]
            self.newEffects = []
            self.positionsUpdated = []
        
    def onEarlyUpdate(self):
        gameManager.Current.scenes[self.scene].fill(self.bg_color)
        
    def onUpdate(self):
        self.display()
        self.cleanUp()

    def printPositions(self): #f1
        with self.display_lock:
            for obj3D in self.currentPositions:
                for line in obj3D.lines:
                    for xyz in line:
                        print(xyz,self.getMappedPosition(xyz))
                       
    def onDestroy(self):
        gameManager.Current.unRegisterObj(self)

class twoDObject(base_classes.baseStruct):
    pass

class Line(twoDObject):

    def __init__(self,color,xyz1,xyz2):
        self.xyz1 = xyz1
        self.xyz2 = xyz2
        self.color = color

    def __iter__(self):
        return (self.xyz1,self.xyz2).__iter__()

class Polygon(twoDObject):

    def __init__(self,color,xyz1,xyz2,*xyzs):
        self.xyzs = [xyz1,xyz2,*xyzs]
        self.color = color

    def __iter__(self):
        return tuple([*self.xyzs]).__iter__() 

class threeDObject(base_classes.baseObject):
    
    Manager = threeDManager

    def onInit(self, *args, **kwargs):
        self.lineWidth = default_width
        
        self.offset = Xyz(0,0,0)
        self.forward = Xyz(0,1,0)
        
        self.effects = []

        self.lines = []
        self.polygons = []
        self.mappedPositions = {}

        self.addPoints(*args, **kwargs)
        
        self.mappedOffset = Xyz(self.offset)

        self.update()

    def addPoints(self,lines=None,polygons = None,offset = None,lineWidth=None):
        if lines != None:
            self.lines.extend(lines)
        if polygons != None:
            self.polygons.extend(polygons)
        if offset != None:
            self.offset = offset
        if lineWidth != None:
            self.lineWidth = lineWidth

    def addEffects(self,*effects):
        self.effects.extend(effects)
        for xyz in self.mappedPositions.keys():
            self.mappedPositions[xyz] = self.calculateNewPoint(self.mappedPositions[xyz],effects)
        self.mappedOffset = self.calculateNewOffset(self.mappedOffset,effects)

    def resetMappedPositions(self):
        self.mappedPositions = {}
        self.mappedOffset = self.calculateNewOffset(Xyz(self.offset),self.effects)
            
    def getMappedPosition(self,xyz):
        if xyz not in self.mappedPositions.keys():
            self.mappedPositions[xyz] = self.calculateNewPoint(xyz,self.effects)
        return self.mappedPositions[xyz]
        
    def getLines(self):
        return [Line(line.color,self.getMappedPosition(line.xyz1)+self.mappedOffset,self.getMappedPosition(line.xyz2)+self.mappedOffset) for line in self.lines]

    def getPolygons(self):
        return [Polygon(polygon.color,*[self.getMappedPosition(xyz)+self.mappedOffset for xyz in polygon.xyzs]) for polygon in self.polygons]

    def calculateNewOffset(self,offset,effects):

        newXyz = Xyz(offset)
        
        forward = 0 # y
        right = 0 # x
        up = 0 # z
        
        for effect in effects:
            match effect.direction:
                case "y":
                    forward += effect.magnitude
                    newXyz.y += effect.magnitude
                case "x":
                    right += effect.magnitude
                    newXyz.x -= effect.magnitude
                case "z":
                    up += effect.magnitude
                    newXyz.z -= effect.magnitude
                case "Forward":
                    print(self.forward,math.sqrt(self.forward.x**2+self.forward.y**2+self.forward.z**2))
                    newXyz += self.forward*effect.magnitude

        return newXyz
        
    def calculateNewPoint(self,xyz,effects):

        newXyz = Xyz(xyz)
        
        radius = math.sqrt(xyz.x**2 + xyz.y**2 + xyz.z**2)

        if radius == 0:
            return newXyz
                
        for effect in effects:
            match effect.direction:
                case "Phi":
                    theta = math.acos(newXyz.z/radius)
                    phi = math.atan2(newXyz.y,newXyz.x) + effect.magnitude
                    newXyz = Xyz(radius*math.sin(theta)*math.cos(phi),radius*math.sin(theta)*math.sin(phi),radius*math.cos(theta))
                case "Theta":       
                    theta = math.acos(newXyz.x/radius)
                    phi = math.atan2(newXyz.y,newXyz.z) + effect.magnitude
                    newXyz = Xyz(radius*math.cos(theta),radius*math.sin(theta)*math.sin(phi),radius*math.sin(theta)*math.cos(phi))

                    th = math.acos(self.forward.x)
                    ph = math.atan2(self.forward.y,self.forward.z) + effect.magnitude
                    self.forward = Xyz(math.cos(th),math.sin(th)*math.sin(ph),math.sin(th)*math.cos(ph))
                case "Nu":
                    theta = math.acos(newXyz.y/radius)
                    phi = math.atan2(newXyz.x,newXyz.z) + effect.magnitude
                    newXyz = Xyz(radius*math.sin(theta)*math.sin(phi),radius*math.cos(theta),radius*math.sin(theta)*math.cos(phi))
                        
        return newXyz
    
class threeDControlSchemeBase(base_classes.baseManager):

    def onInit(self,scene,otherInputHandler = None):
        timedCallback("Forward",keydownRepeatTime,threeDManager.Current.addEffects,Effect("Forward",-moveAmount)).call()
        timedCallback("Back",keydownRepeatTime,threeDManager.Current.addEffects,Effect("Forward",moveAmount)).call()
        timedCallback("Left",keydownRepeatTime,threeDManager.Current.addEffects,Effect("Right",-moveAmount)).call()
        timedCallback("Right",keydownRepeatTime,threeDManager.Current.addEffects,Effect("Right",moveAmount)).call()
        timedCallback("RollRight",keydownRepeatTime,threeDManager.Current.addEffects,Effect("Nu",-angleMoveAmount*2)).call()
        timedCallback("RollLeft",keydownRepeatTime,threeDManager.Current.addEffects,Effect("Nu",angleMoveAmount*2)).call()
        timedCallback("Up",keydownRepeatTime,threeDManager.Current.addEffects,Effect("Up",moveAmount)).call()
        timedCallback("Down",keydownRepeatTime,threeDManager.Current.addEffects,Effect("Up",-moveAmount)).call()
        timedCallback("ZoomIn",keydownRepeatTime,threeDManager.Current.addEffects,Effect("Zoom",moveAmount/100)).call()
        timedCallback("ZoomOut",keydownRepeatTime,threeDManager.Current.addEffects,Effect("Zoom",-moveAmount/100)).call()
        
        gameManager(None,None,None,{scene:self.inputHandlerExternal})

        self.otherInputHandler = otherInputHandler

    def inputHandlerExternal(self,events):
        for event in events:
            if event.type == pyg.KEYUP:
                match event.key:
                    case pyg.K_F5:
                        threeDManager.Current.resetMappedPositions()
                    case pyg.K_F4:
                        threeDManager.Current.resetEffects()
                    case pyg.K_F3:
                        debugManager.Current.cycle()
                    case pyg.K_F1:
                        threeDManager.Current.printPositions()
                        
        self.inputHandler(events)
                        
        if self.otherInputHandler != None:
            self.otherInputHandler(events)

    def inputHandler(self,events):
        pass

class defaultThreeDControlScheme(threeDControlSchemeBase):

    def inputHandler(self,events):
        for event in events:
            if event.type in [pyg.KEYDOWN,pyg.KEYUP]:
                match event.key:
                    case pyg.K_w:
                        callbackManager.Current.call("Forward")
                    case pyg.K_s:
                        callbackManager.Current.call("Back")
                    case pyg.K_d:
                        callbackManager.Current.call("Right")
                    case pyg.K_a:
                        callbackManager.Current.call("Left")
                    case pyg.K_SPACE:
                        callbackManager.Current.call("Up")
                    case pyg.K_LCTRL:
                        callbackManager.Current.call("Down")
                    case pyg.K_q:
                        callbackManager.Current.call("RollLeft")
                    case pyg.K_e:
                        callbackManager.Current.call("RollRight")
                        
            elif event.type == pyg.MOUSEMOTION and event.buttons[LEFTMOUSEBUTTON] == 1:
                threeDManager.Current.addEffects(Effect("Phi", event.rel[0]*math.radians(0.25)),Effect("Theta", -event.rel[1]*math.radians(0.25)))
            elif event.type == pyg.MOUSEBUTTONDOWN and event.button-1 ==  MIDDLEMOUSEBUTTON:
                threeDManager.Current.zoom = 50
            elif event.type == pyg.MOUSEWHEEL:
                threeDManager.Current.addEffects(Effect("Zoom",event.y*2))
