from common_libs import *    
import pygame as pyg
import pygame.gfxdraw as pyg_gfxdraw
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
colorManager = colors_manager.colorManager()

default_draw_color = colorManager.Yellow
default_bg_color = colorManager.Black
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
        self.direction = direction # "Theta"; "Phi"; "Nu"; "Right"; "Forward"; "Up"; "y"; "x"; "z"; "FOV";
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
        self.fov = 90
        self.prev_fov = -1
        self.prev_veiwPoint = Xyz(-1)
        self.currentPositions = []
        self.mappedPositions = {}
        self.effects = []
        self.positionsUpdated = []
        self.offset = Xyz(0)
        self.mappedOffset = Xyz(self.offset)
        self.screen_size = Xy(gameManager.Current.scenes[self.scene].get_size())
        if screen_size != None:
            self.screen_size = screen_size

        self.forward = Xyz(0,1,0)
        self.up = Xyz(0,0,1)
        self.right = Xyz(1,0,0)

        self.update()

    def resetEffects(self): #f4
        with self.display_lock:
            self.effects = []
        
        for threeDObject in self.currentPositions:
            threeDObject.resetEffects()

        self.resetMappedPositions()

    def resetMappedPositions(self): #f5
        with self.display_lock:
            self.mappedPositions = {}
            self.mappedOffset = self.calculateNewOffset(self.offset,self.effects)
            self.relativePos = Xyz(self.veiwPoint)
            self.zoom = 50
            self.fov = 90
            self.forward = self.calculateNewPoint(Xyz(0,1,0),self.effects,True).getNormalised()
            self.up = self.calculateNewPoint(Xyz(0,0,1),self.effects,True).getNormalised()
            self.right = self.calculateNewPoint(Xyz(1,0,0),self.effects,True).getNormalised()
            for effect in self.effects:
                if effect.direction == "Zoom":
                    self.zoom += effect.magnitude
                elif effect.direction == "FOV":
                    self.fov -= effect.magnitude

            for threeDObject in self.currentPositions:
                threeDObject.resetMappedPositions()
        
    def addEffects(self,*effects):
        with self.display_lock:
            self.effects.extend(effects)
            for xyz in self.mappedPositions.keys():
                self.mappedPositions[xyz] = self.calculateNewPoint(self.mappedPositions[xyz],effects)
            self.mappedOffset = self.calculateNewOffset(self.mappedOffset,effects)
            self.forward = self.calculateNewPoint(self.forward,effects,True).getNormalised()
            self.up = self.calculateNewPoint(self.up,effects,True).getNormalised()
            self.right = self.calculateNewPoint(self.right,effects,True).getNormalised()
            for effect in effects:
                match effect.direction:
                    case "Zoom":
                        self.zoom += effect.magnitude
                    case "FOV":
                        self.fov -= effect.magnitude
            
    def addObjects(self,*objects):
        with self.display_lock:
            self.currentPositions.extend(objects)
    
    def getMappedPosition(self,xyz):
        if xyz not in self.mappedPositions.keys():
            self.mappedPositions[xyz] = self.calculateNewPoint(xyz,self.effects)
        if xyz not in self.positionsUpdated:
            self.positionsUpdated.append(xyz)
        return self.mappedPositions[xyz]

    def getFullyMappedXyPosition(self,xyz):
        return self.calculateNewXyPoint(self.mappedOffset+self.getMappedPosition(xyz))

    def getFullyMappedXyPositions(self,xyzs):
        return [self.getFullyMappedXyPosition(xyz) for xyz in xyzs]
        
    def calculateNewPoint(self,xyz,effects,cardinal_direction = False):

        newXyz = Xyz(xyz)
        
        radius = xyz.getMagnitude()

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
                    if cardinal_direction:
                        phi = math.atan2(newXyz.y,newXyz.x) - effect.magnitude
                    else:
                        phi = math.atan2(newXyz.y,newXyz.x) + effect.magnitude
                    newXyz = Xyz(radius*math.sin(theta)*math.cos(phi),radius*math.sin(theta)*math.sin(phi),radius*math.cos(theta))
                case "Theta":
                    if radius == 0:
                        continue  
                    theta += effect.magnitude          
                    theta = math.acos(newXyz.x/radius)
                    if cardinal_direction:
                        phi = math.atan2(newXyz.y,newXyz.z) - effect.magnitude
                    else:
                        phi = math.atan2(newXyz.y,newXyz.z) + effect.magnitude
                    newXyz = Xyz(radius*math.cos(theta),radius*math.sin(theta)*math.sin(phi),radius*math.sin(theta)*math.cos(phi))
                case "Nu":
                    if radius == 0:
                        continue
                    nu += effect.magnitude
                    theta = math.acos(newXyz.y/radius)
                    if cardinal_direction:
                        phi = math.atan2(newXyz.x,newXyz.z) - effect.magnitude
                    else:
                        phi = math.atan2(newXyz.x,newXyz.z) + effect.magnitude
                    newXyz = Xyz(radius*math.sin(theta)*math.sin(phi),radius*math.cos(theta),radius*math.sin(theta)*math.cos(phi))
                case "Forward":
                    if not cardinal_direction:
                        forward += effect.magnitude
                        newXyz.y += effect.magnitude
                        radius = math.sqrt(newXyz.x**2 + newXyz.y**2 + newXyz.z**2)
                case "Right":
                    if not cardinal_direction:
                        right += effect.magnitude
                        newXyz.x -= effect.magnitude
                        radius = math.sqrt(newXyz.x**2 + newXyz.y**2 + newXyz.z**2)
                case "Up":
                    if not cardinal_direction:
                        up += effect.magnitude
                        newXyz.z -= effect.magnitude
                        radius = math.sqrt(newXyz.x**2 + newXyz.y**2 + newXyz.z**2)
                
        return newXyz

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

        return newXyz

    def calculateNewXyPoint(self, xyz):
        if self.fov != self.prev_fov or self.veiwPoint.y != self.prev_veiwPoint.y:
            if self.fov > 179:
                self.fov = 179
            elif self.fov < 1:
                self.fov = 1
            self.prev_fov = self.fov
            self.prev_veiwPoint = self.veiwPoint
            self.veiwPoint_y_value = ((self.veiwPoint.y)+((self.screen_size.y//2)/math.tan(math.radians(self.fov/2))))
        
        y_plane = self.veiwPoint_y_value/(xyz.y if xyz.y > 0 else 1)
        y_plane = y_plane if y_plane >= 0 else 0
        xy = Xy((y_plane*(xyz.x)),-(y_plane*(xyz.z)))
        xy+=self.screen_size//2
        return xy

    def display(self):
        with self.display_lock:
            for obj3D in self.currentPositions:
                for line in obj3D.getLines():
                    #print(line,line.xyzs,line.color5)
                    pyg.draw.aaline(gameManager.Current.scenes[self.scene],line.color,*self.getFullyMappedXyPositions(line))
                for polygon in obj3D.getPolygons():
                    formed_polygon = (gameManager.Current.scenes[self.scene],self.getFullyMappedXyPositions(polygon),polygon.color)
                    pyg_gfxdraw.aapolygon(*formed_polygon)
                    if obj3D.opaque and polygon.solid_fill:
                        pyg_gfxdraw.filled_polygon(*formed_polygon)
                for sphere in obj3D.getSpheres():
                    centre = self.getFullyMappedXyPosition(sphere.center).__round__()
                    radius = int(round((self.getFullyMappedXyPosition(sphere.center+self.right*sphere.radius)-self.getFullyMappedXyPosition(sphere.center)).getMagnitude()))
                    if radius > 9999 or radius <= 0 or max(centre)>9999 or min(centre)<-9999:
                        continue
                    formed_circle = (gameManager.Current.scenes[self.scene],*centre,radius,sphere.color)
                    pyg_gfxdraw.aacircle(*formed_circle)
                    if obj3D.opaque and sphere.solid_fill:
                        pyg_gfxdraw.filled_circle(*formed_circle)
            if debugManager.Current:
                pyg.draw.aaline(gameManager.Current.scenes[self.scene],colorManager.Yellow,*self.getFullyMappedXyPositions([Xyz(0),Xyz(0,15,0)]))
                centre = self.getFullyMappedXyPosition(Xyz(0)).__round__()
                if not (max(centre)>9999 or min(centre)<-9999):
                    pyg_gfxdraw.aacircle(gameManager.Current.scenes[self.scene],*centre,10,colorManager.Yellow)

    def cleanUp(self):
        with self.display_lock:
            delPos = []
            for xyz in self.mappedPositions.keys():
                if xyz not in self.positionsUpdated:
                    delPos.append(xyz)
            for xyz in delPos:
                del self.mappedPositions[xyz]
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

    def __new__(cls,*args,over_wright= None,**kwargs):
        self = super().__new__(cls)
        if isinstance(over_wright,cls):
            self.color = over_wright.color
            self.width = over_wright.width
            self.solid_fill = over_wright.solid_fill
        else:
            self = super().__new__(cls)
            self.solid_fill = False
        return self

    def __init__(self,*args, color = None,width = None, solid_fill = None,over_wright= None):
        if color != None:
            self.color = color
        if width != None:
            self.width = width
        if solid_fill != None:
            self.solid_fill = solid_fill
        if args != None:
            self.onInit(*args)

    def onInit(self):
        pass

class Polygon(twoDObject):

    def onInit(self,xyz1,xyz2,*xyzs):
        self.xyzs = [xyz1,xyz2,*xyzs]

    def __iter__(self):
        return tuple([*self.xyzs]).__iter__() 

class Line(Polygon):

    def onInit(self,xyz1,xyz2):
        self.xyzs = [xyz1,xyz2]

class Sphere(twoDObject):

    def onInit(self,center,radius):
        self.center = center
        self.radius = radius

class threeDObject(base_classes.baseObject):
    
    Manager = threeDManager

    def onInit(self,lines=None,polygons = None,offset = None,lineWidth=None,opaque:bool = False):
        #self.lineWidth = default_width
        
        self.offset = Xyz(0,0,0)
        self.forward = Xyz(0,1,0)
        self.up = Xyz(0,0,1)
        self.right = Xyz(1,0,0)
        
        self.effects = []

        self.lines = []
        self.polygons = []
        self.spheres = []
        self.mappedPositions = {}

        self.opaque = opaque

        self.addPoints(lines,polygons,offset,lineWidth)
        
        self.mappedOffset = Xyz(self.offset)

        self.update()

    def addPoints(self,lines,polygons,offset,lineWidth):
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
        self.forward = self.calculateNewPoint(self.forward,effects)
        self.up = self.calculateNewPoint(self.up,effects)
        self.right = self.calculateNewPoint(self.right,effects)

    def resetEffects(self):
        self.effects = []

    def resetMappedPositions(self):
        self.mappedPositions = {}
        self.forward = self.calculateNewPoint(Xyz(0,1,0),self.effects)
        self.up = self.calculateNewPoint(Xyz(0,0,1),self.effects)
        self.right = self.calculateNewPoint(Xyz(1,0,0),self.effects)
        self.mappedOffset = self.calculateNewOffset(Xyz(self.offset),self.effects)
            
    def getMappedPosition(self,xyz):
        if xyz not in self.mappedPositions.keys():
            self.mappedPositions[xyz] = self.calculateNewPoint(xyz,self.effects)
        return self.mappedPositions[xyz]
        
    def getLines(self):
        lines = [Line((self.getMappedPosition(line.xyzs[0])+self.mappedOffset),(self.getMappedPosition(line.xyzs[1])+self.mappedOffset),over_wright=line) for line in self.lines]
        if debugManager.Current:
            lines.append(Line(self.forward*75+self.mappedOffset+self.getMappedPosition(Xyz(0)),self.getMappedPosition(Xyz(0))+self.mappedOffset,color=colorManager.Yellow, width=default_width))
        return lines
    
    def getPolygons(self):
        return [Polygon(*[self.getMappedPosition(xyz)+self.mappedOffset for xyz in polygon.xyzs],over_wright=polygon) for polygon in self.polygons]

    def getSpheres(self):
        spheres = [Sphere(self.getMappedPosition(sphere.centre)+self.mappedOffset,sphere.radius,over_wright=sphere) for sphere in self.spheres]
        if debugManager.Current:
            spheres.append(Sphere(self.mappedOffset+self.getMappedPosition(Xyz(0)),75,color=colorManager.Yellow,width=default_width))
        return spheres

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
                    #print(self.forward,math.sqrt(self.forward.x**2+self.forward.y**2+self.forward.z**2))
                    newXyz += self.forward*effect.magnitude
                case "Up":
                    newXyz += self.up*effect.magnitude
                case "Right":
                    newXyz +=  self.right*effect.magnitude


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
                threeDManager.Current.addEffects(Effect("FOV",event.y*2))

if __name__ == "__main__":
    import threeD_test
    threeD_test.start()