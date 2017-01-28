# gameobjects.py

import json

def loadMap(id):
    result = "{}"
    with open(id+".json", "r") as f:
        jsontext = f.read()
        dict = json.loads(jsontext)
        dict["mapheight"] = len(dict["terrain"])
        dict["mapwidth"] = len(dict["terrain"][0])
        result = MapObject(**dict)
    return result

class MapObject(object):

    def __init__(self, mapname="main", terrain=[], player_start_x=0, player_start_y=0, mapwidth=30, mapheight=30):
        self.mapname = mapname
        self.setPlayerXY(player_start_x,player_start_y)
        self.terrain = terrain
        self.mapwidth = mapwidth
        self.mapheight = mapheight
        
    def setPlayerXY(self, x,y):
        self.player_x = x
        self.player_y = y
        
    def addMapRow(self, s):
        self.terrain.append(s.split(" "))
        self.mapheight = len(terrain)
        
    def getName(self):
        return self.mapname
    
class Player(object):

    def __init__(self, currentMap="britania", i=10, d=10, s=10):
        self.map             = currentMap
        self.int             = i
        self.dex             = d
        self.str             = s
        self.xp              = 0
        self.level           = 1
        self.gold            = 10
        self.max_HP          = 10
        self.HP              = 10
        self.max_magic       = 10
        self.magic           = 10
        self.magicRegenRate  = 1
        self.primaryWeapon   = "short sword"
        self.secondaryWeapon = ""
        self.armor           = ""