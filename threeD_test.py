from common_libs import *    
import pygame as pyg
from time import sleep
import math
from threading import Lock

try:
    import threeD
except:
    from threeD_renderer import threeD
    
Xyz = Xyz.Xyz
Xy = Xy.Xy
pygameManager = pygame_interface.pygameManager
gameManager = game_manager.gameManager
threadManager = coroutines_threads.threadManager()
settingsManager = settings_manager.settingsManager()
callbackManager = callbacks.callbackManager()
timedCallback = callbacks.timedCallback
threeDManager = threeD.threeDManager
threeDObject = threeD.threeDObject
debugManager = debug_manager.debugManager()
Effect = threeD.Effect
Line = threeD.Line
Polygon = threeD.Polygon
colorManager = colors_manager.colorManager()

default_width = 2
screen_size = Xy(1200,600)

class threeDTestManager(base_classes.baseManager):

    def onInit(self):

        gameManager.Current.registerObj(self)

        threeDManager("3D",bg_color = colorManager.Black,veiwPoint = Xyz(0,500,0))

        threeDManager.Current.addEffects(Effect("Right",threeDManager.Current.veiwPoint.x),Effect("Forward",threeDManager.Current.veiwPoint.y),Effect("Up",threeDManager.Current.veiwPoint.z))
        
        self.cube = threeDObject(lines = [Line(Xyz(100,100,-100),Xyz(-100,100,-100),color = colorManager.Cyan,width = default_width),Line(Xyz(100,-100,-100),Xyz(-100,-100,-100),color = colorManager.Cyan,width = default_width),Line(Xyz(100,-100,100),Xyz(-100,-100,100),color = colorManager.Cyan,width = default_width),Line(Xyz(100,100,100),Xyz(-100,100,100),color = colorManager.Cyan,width = default_width)] ,polygons = [Polygon(Xyz(100,100,100),Xyz(100,-100,100),Xyz(100,-100,-100),Xyz(100,100,-100),color = colorManager.Cyan,width = default_width),Polygon(Xyz(-100,100,100),Xyz(-100,-100,100),Xyz(-100,-100,-100),Xyz(-100,100,-100),color = colorManager.Cyan,width = default_width)])
        threeDManager.Current.addObjects(self.cube)
        
        self.triangularBasedPyramidRight = threeDObject(offset = Xyz(400,0,0), polygons = [Polygon(Xyz(100,100,100),Xyz(100,-100,100),Xyz(100,0,-100), solid_fill=True,color = colorManager.Red,width = default_width),Polygon(Xyz(-100,0,0),Xyz(100,-100,100),Xyz(100,0,-100), solid_fill=True,color = colorManager.Red,width = default_width),Polygon(Xyz(100,100,100),Xyz(-100,0,0),Xyz(100,0,-100), solid_fill=True,color = colorManager.Red,width = default_width),Polygon(Xyz(100,100,100),Xyz(100,-100,100),Xyz(-100,0,0), solid_fill=True,color = colorManager.Red,width = default_width)], opaque = True)
        threeDManager.Current.addObjects(self.triangularBasedPyramidRight)

        self.triangularBasedPyramidLeft = threeDObject(offset = Xyz(-400,0,0),  polygons = [Polygon(Xyz(100,100,100),Xyz(100,-100,100),Xyz(100,0,-100), solid_fill=True,color = colorManager.Red,width = default_width),Polygon(Xyz(-100,0,0),Xyz(100,-100,100),Xyz(100,0,-100), solid_fill=True,color = colorManager.Red,width = default_width),Polygon(Xyz(100,100,100),Xyz(100,-100,100),Xyz(100,0,-100), solid_fill=True,color = colorManager.Red,width = default_width),Polygon(Xyz(100,100,100),Xyz(100,-100,100),Xyz(100,0,-100), solid_fill=True,color = colorManager.Red,width = default_width)],opaque = True)
        threeDManager.Current.addObjects(self.triangularBasedPyramidLeft)
        self.triangularBasedPyramidLeft.addEffects(Effect("Phi",math.radians(180)),Effect("Theta",math.radians(180)))
        
        threeD.defaultThreeDControlScheme("Main", self.inputHandler)

    def inputHandler(self,events):
        
        for event in events:
            if event.type == pyg.KEYDOWN:
                match event.key:
                    case pyg.K_p:
                        self.cube.addEffects(Effect("y",10))
                    case pyg.K_i:
                        self.cube.addEffects(Effect("Forward",10))
                    case pyg.K_k:
                        self.cube.addEffects(Effect("Forward",-10))
                    case pyg.K_l:
                        self.cube.addEffects(Effect("Right",10))
                    case pyg.K_j:
                        self.cube.addEffects(Effect("Right",-10))
                    case pyg.K_y:
                        self.cube.addEffects(Effect("Up",10))
                    case pyg.K_h:
                        self.cube.addEffects(Effect("Up",-10))
                    case pyg.K_g:
                        self.cube.addEffects(Effect("Theta",math.radians(20)))
                    case pyg.K_t:
                        self.cube.addEffects(Effect("Theta",-math.radians(20)))
                    case pyg.K_m:
                        self.cube.addEffects(Effect("Phi",-math.radians(20)))
                    case pyg.K_n:
                        self.cube.addEffects(Effect("Phi",math.radians(20)))
                    case pyg.K_o:
                        self.cube.addEffects(Effect("Nu",math.radians(5)))
                    case pyg.K_u:
                        self.cube.addEffects(Effect("Nu",-math.radians(5)))

    def onLateUpdate(self):
        gameManager.Current.scenes["Main"].blit(gameManager.Current.scenes["3D"],Xy(0))
        pyg.draw.aaline(gameManager.Current.scenes["Main"],colorManager.White,Xy(gameManager.Current.scenes["Main"].get_size())//2-Xy(0,5),Xy(gameManager.Current.scenes["Main"].get_size())//2+Xy(0,5))
        pyg.draw.aaline(gameManager.Current.scenes["Main"],colorManager.White,Xy(gameManager.Current.scenes["Main"].get_size())//2-Xy(5,0),Xy(gameManager.Current.scenes["Main"].get_size())//2+Xy(5,0))

        if debugManager.Current:
            gameManager.Current.scenes["Main"].blit(pygameManager.Current.very_small_font.render("FPS: "+str(gameManager.Current.actual_fps),True,colorManager.White),Xy(5)) # difference is 17 y
            gameManager.Current.scenes["Main"].blit(pygameManager.Current.very_small_font.render("∆T: "+str(gameManager.Current.delta_time),True,colorManager.White),Xy(5,21))
            gameManager.Current.scenes["Main"].blit(pygameManager.Current.very_small_font.render("FOV: "+str(threeDManager.Current.fov),True,colorManager.White),Xy(5,38))
            gameManager.Current.scenes["Main"].blit(pygameManager.Current.very_small_font.render("Pos: "+str(threeDManager.Current.mappedOffset),True,colorManager.White),Xy(5,55))
                
    def onExit(self):
        threeDManager.Current.exit()

def start():
    debugManager.Current.setTrue()
    settingsManager.Current.addSettingsFile("data","3D","settings")
    gameManager(
        -1,
        {"3D":pyg.Surface(screen_size),"Main":pyg.Surface(screen_size)},
        None,
        None
        )
    threadManager.Current.startTasks([pygameManager,screen_size,"3D stuff",gameManager.Current.userInput])
    #pygameManager(screen_size,"")
    gameManager(
        None,
        None,
        None,
        None,
        {"Main":[threeDTestManager]}
        )
    sleep(0.3)
    gameManager.Current.changeScene("Main")

if __name__ == '__main__':
    start()
