# Empyrean Adventure

import pygame
import sys
import random
import json
import time
from lineofsight import get_line


pygame.init()
pygame.font.init()
clock = pygame.time.Clock()

#########################################################

# DEFINE GLOBALS AND CONSTANTS
BLACK = 0, 0, 0
RED = 255, 0, 0
WHITE = 255, 255, 255
TILESIZE = 90
WINDOWTILEWIDTH = 9 #Must be odd number
#STARTINGMAP = "britania"
MAP = None
PLAYER_X = 0
PLAYER_Y = 0
TILES = {}
PLAYER = {}
MAP = {}
GAMEFONT = pygame.font.SysFont("monospace", 20)
FONTHEIGHT = 20

MAXINVETORY = 10

WEAPONS = {
    "dagger": {"range": 1, "damage": 4, "value": 6, "type": "melee"},
    "short sword": {"range": 1, "damage": 6, "value": 10, "type": "melee"},
    "long sword": {"range": 1, "damage": 10, "value": 18, "type": "melee"},
    "short bow:": {"range": 4, "damage": 4, "value": 15, "type": "range"},
    "long bow": {"range": 4, "damage": 8, "value": 20, "type": "range"}
}

ARMOR = {
    "leather": {"protection": 12, "str_requirement": 1, "value": 6, "type": "light armor"},
    "studded leather": {"protection": 13, "str_requirement": 1, "value": 8, "type": "light armor"}
}

# Spells have a magic cost, an action (heal, fire, shock, blast), a range, and a target (tells how many enemies the spell affects -- if 0, then it works on the player)
SPELLS = {
    "heal": {"cost": 10, "action": "heal", "range": 1, "target": 0}
}

## create the Rect to hold the info panel text
INFOPANELRECT = pygame.Rect(TILESIZE*WINDOWTILEWIDTH, 0, TILESIZE*3, TILESIZE*WINDOWTILEWIDTH)

#########################################################

# METHODS
def loadPlayer(id):
    result = "{}"
    with open(id+".json", "r") as f:
        result = json.load(f)
    f.close()
    return result

def loadMap(id):
    global MAP
    with open(id+".json", "r") as f:
        MAP = json.load(f)
        MAP["mapheight"] = len(MAP["terrain"])
        MAP["mapwidth"] = len(MAP["terrain"][0])
        #MAP["player_x"] = MAP["player_start_x"]
        #MAP["player_y"] = MAP["player_start_y"]
        print(MAP["player_start_x"])
    f.close()
    
def save(id):
    global PLAYER_X, PLAYER_Y
    MAP["player_start_x"] = PLAYER_X
    MAP["player_start_y"] = PLAYER_Y
    with open(id+".json", "w") as f:
        json.dump(MAP, f)
    f.close()
    
    with open("player.json", "w") as f:
        json.dump(PLAYER, f)
    f.close()
    
def changeMap(x,y):
    global MAP, PLAYER_X, PLAYER_Y
    key = "("+str(x)+","+str(y)+")"
    newmapname = MAP["portals"][key]
    save(MAP["mapname"])
    loadMap(newmapname)
    PLAYER_X = MAP["player_start_x"]
    PLAYER_Y = MAP["player_start_y"]
    drawMap()
    
def getTileType(tileCode):
    if   tileCode == ".": return "grass"
    elif tileCode == "M": return "mountain"
    elif tileCode == "w": return "water-shallow"
    elif tileCode == "W": return "water-deep"
    elif tileCode == "T": return "forrest"
    elif tileCode == "-": return "desert"
    elif tileCode == "m": return "hills"
    elif tileCode == "s": return "swamp"
    elif tileCode == "C": return "castle"
    elif tileCode == "R": return "runis"
    elif tileCode == "o": return "cave"
    elif tileCode == "^": return "town"
    elif tileCode == "L": return "whitestone"
    elif tileCode == "l": return "whitestone"
    elif tileCode == "o": return "cave"
    elif tileCode == "R": return "ruins"
    elif tileCode == "^": return "town"
    elif tileCode == "+": return "road-gravel"
    elif tileCode == "#": return "road-brick"
    elif tileCode == "D": return "door"
    else: return "grass"

def validTile(newTile):
    if newTile == "M" or newTile == "W" or newTile == "L":
        return False
    else: return True

def normalTerrain(tile):
    # some terrain types slow movement down randomly
    move = 1
    if tile == "T" or tile == "w" or tile == "s":
        move = random.randrange(1,3)
    if move > 1: return 0
    else: return 1

def isPortal(key):
    portal = None
    portal = MAP["portals"].get(key)
    if portal != None:
        return True
    return False
    
def blockingTile(tile):
    if tile == "M" or tile == "l" or tile == "L" or tile == "D": return True
    return False
    
def isVisible(x1, y1, x2, y2):
    # determines if the map tile location is visible to the player
    # line of site will be blocked by mountains, walls
    if (x1 - x2 == 0): #vertical line
        ystep = 1 if y1 < y2 else -1
        for y in range(y1, y2, ystep):
            if (y != y1) and (y != y2):
                if blockingTile(MAP["terrain"][y][x1]): return False
    elif (y1 - y2 == 0): #horizontal line
        xstep = 1 if x1 < x2 else -1
        for x in range(x1, x2, xstep):
            if (x != x1) and (x != x2):
                if blockingTile(MAP["terrain"][y1][x]): return False
    else:
        linePoints = get_line((x1,y1), (x2,y2))
        for point in linePoints:
            x, y = point
            if not (x == x1 and y == y1):
                if blockingTile(MAP["terrain"][y][x]): return False
    return True

def textPanelNewLine(x, y, text, invert=False):
    if not (invert):
        textimage = GAMEFONT.render(text, 1, WHITE, BLACK)
    else: textimage = GAMEFONT.render(text, 1, BLACK, WHITE)
    SCREEN.blit(textimage, (x, y))
    return y + FONTHEIGHT
    
def drawInfoPanel():
    ypos = INFOPANELRECT.top + 10
    xpos = INFOPANELRECT.left + 10
    ypos = textPanelNewLine(xpos, ypos, "HP: "+str(PLAYER["hp"]))
    ypos = textPanelNewLine(xpos, ypos, "magic: "+str(PLAYER["magic"]))
    ypos = textPanelNewLine(xpos, ypos, "gold: "+str(PLAYER["gold"]))
    ypos = textPanelNewLine(xpos, ypos, "level: "+str(PLAYER["level"]))
    ypos = textPanelNewLine(xpos, ypos, "weapon: "+str(PLAYER["weapon"]))
    ypos = textPanelNewLine(xpos, ypos, "armor: "+str(PLAYER["armor"]))
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "-----ITEMS-----")
    for item in PLAYER["items"]:
        ypos = textPanelNewLine(xpos, ypos, item)
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "-----SPELLS----")
    for spell in PLAYER["spells"]:
        ypos = textPanelNewLine(xpos, ypos, spell)
    
    textPanelNewLine(xpos, INFOPANELRECT.bottom-FONTHEIGHT-10, "(H)elp")
    
def drawMap():
    global PLAYER_X, PLAYER_Y
    SCREEN.fill(BLACK)
    offset = int((WINDOWTILEWIDTH - 1)/2)
    for y in range((PLAYER_Y - offset), (PLAYER_Y + offset + 1)):
        s_y = abs((PLAYER_Y - offset) - y)
        for x in range((PLAYER_X - offset), (PLAYER_X + offset + 1)):
            if x >= 0 and x < MAP["mapwidth"] and y >= 0 and y < MAP["mapheight"]:
                if isVisible(x,y,PLAYER_X,PLAYER_Y):
                    rawTile = MAP["terrain"][y][x]
                    indexTile = getTileType(rawTile)
                    s_x = abs((PLAYER_X - offset) - x)
                    SCREEN.blit(TILES[indexTile], (s_x*TILESIZE, s_y*TILESIZE))
    SCREEN.blit(PLAYERTILE, (4*TILESIZE, 4*TILESIZE))

def inventoryManagement():
    # TO DO
    #  - list weapon, armor, current items
    # Should (S)ell be implemented if near NPC that can buy?
    
    invRect = pygame.Rect(0, 0, TILESIZE*WINDOWTILEWIDTH, TILESIZE*WINDOWTILEWIDTH)
    
    selectedItem = 0
    
    pause = True
    pygame.event.clear()
    
    while pause:
        SCREEN.fill(BLACK, invRect)
    
        ypos = invRect.top + 10
        xpos = invRect.left + 10
    
        ypos = textPanelNewLine(xpos, ypos, "INVENTORY MANAGEMENT")
        ypos = textPanelNewLine(xpos, ypos, " ")
        ypos = textPanelNewLine(xpos, ypos, "(SPACE) to select item.")
        ypos = textPanelNewLine(xpos, ypos, "(D)rop item")
        ypos = textPanelNewLine(xpos, ypos, "(M)ake item active weapon/armor")
        ypos = textPanelNewLine(xpos, ypos, "(U)se item")
        ypos = textPanelNewLine(xpos, ypos, "(Q)uit")
        ypos = textPanelNewLine(xpos, ypos, " ")
        ypos = textPanelNewLine(xpos, ypos,  "------------------------------")
        ypos = textPanelNewLine(xpos, ypos, "weapon: "+str(PLAYER["weapon"]))
        ypos = textPanelNewLine(xpos, ypos, "armor: "+str(PLAYER["armor"]))
        ypos = textPanelNewLine(xpos, ypos,  "------------------------------")
        ypos = textPanelNewLine(xpos, ypos, " ")
        for item in PLAYER["items"]:
            if (PLAYER["items"][selectedItem]) == item:
                ypos = textPanelNewLine(xpos, ypos, item, True)
            else:
                ypos = textPanelNewLine(xpos, ypos, item)
        pygame.display.flip()
        event = pygame.event.wait()
        if event.type == pygame.KEYDOWN:
            if event.key == 113: # Q
                pause = False
            elif event.key == 32: # (SPACE)
                selectedItem = selectedItem + 1
                if selectedItem == len(PLAYER["items"]):
                    selectedItem = 0
            elif event.key == 100 and PLAYER["items"]: # D
                # drop item after confirmation
                ypos = textPanelNewLine(xpos, ypos, " ")
                ypos = textPanelNewLine(xpos, ypos, "Press (Y) to confirm dropping item: "+PLAYER["items"][selectedItem])
                pygame.display.flip()
                pygame.event.clear()
                pause2 = True
                while pause2:
                    event = pygame.event.wait()
                    if event.type == pygame.KEYDOWN:
                        if event.key == 121:
                            del PLAYER["items"][selectedItem]
                            selectedItem = selectedItem - 1
                            if selectedItem < 0: selectedItem = 0
                            pause2 = False
                        else: pause2 = False
            elif event.key == 109: # M key
                if PLAYER["items"][selectedItem] in WEAPONS:
                    PLAYER["weapon"], PLAYER["items"][selectedItem] = PLAYER["items"][selectedItem], PLAYER["weapon"]
                    if PLAYER["items"][selectedItem] == "none":
                        del PLAYER["items"][selectedItem]
                        selectedItem = selectedItem - 1
                        if selectedItem < 0: selectedItem = 0
                if PLAYER["items"][selectedItem] in ARMOR:
                    PLAYER["armor"], PLAYER["items"][selectedItem] = PLAYER["items"][selectedItem], PLAYER["armor"]
                    if PLAYER["items"][selectedItem] == "none":
                        del PLAYER["items"][selectedItem]
                        selectedItem = selectedItem - 1
                        if selectedItem < 0: selectedItem = 0
            elif event.key == 117: # U key
                if "potion" in PLAYER["items"][selectedItem]:
                    print("use potion")
                elif "scroll" in PLAYER["items"][selectedItem]:
                    print("use scroll")
                else:
                    ypos = textPanelNewLine(xpos, ypos, " ")
                    ypos = textPanelNewLine(xpos, ypos, "That item cannot be used at this time.")
                    pygame.display.flip()
                    pygame.time.wait(1500)
    
def helpMenu():
    helpRect = pygame.Rect(0, 0, TILESIZE*WINDOWTILEWIDTH, TILESIZE*WINDOWTILEWIDTH)
    SCREEN.fill(BLACK, helpRect)
    
    ypos = helpRect.top + 10
    xpos = helpRect.left + 10
    
    ypos = textPanelNewLine(xpos, ypos, "EMPYREAN ADVENTURE SYSTEM")
    ypos = textPanelNewLine(xpos, ypos, "-------------------------")
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "Move using arrow keys.")
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "(S)ave")
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "(I)nventory")
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "Version 0.5")
    ypos = textPanelNewLine(xpos, ypos, "Written by: Eric Wilke")
    
    pause = True
    pygame.event.clear()
    pygame.display.flip()
    while pause:
        event = pygame.event.wait()
        if event.type == pygame.KEYDOWN: pause = False

def drawText(txt, color, rect, aa=False, bkg=None):
    SCREEN.fill(BLACK)
    y = rect.top
    lineSpacing = 0
    
    lines = txt.splitlines()
    
    for text in lines:
 
        while text:
            i = 1
     
            # determine if the row of text will be outside our area
            if y + FONTHEIGHT > rect.bottom:
                break
     
            # determine maximum width of line
            while GAMEFONT.size(text[:i])[0] < rect.width and i < len(text):
                i += 1
     
            # if we've wrapped the text, then adjust the wrap to the last word      
            if i < len(text): 
                i = text.rfind(" ", 0, i) + 1
     
            # render the line and blit it to the surface
            if bkg:
                image = GAMEFONT.render(text[:i], 1, color, bkg)
                image.set_colorkey(bkg)
            else:
                image = GAMEFONT.render(text[:i], aa, color)
     
            SCREEN.blit(image, (rect.left, y))
            y += FONTHEIGHT + lineSpacing
     
            # remove the text we just blitted
            text = text[i:]
        
def loadMonsters():
    result = "{}"
    with open("monsters.json", "r") as f:
        #jsontext = f.read()
        dict = json.load(f)
    f.close()
    return dict
        
def d20roll():
    return random.randrange(1,21)
        
def monsterAttack(bonus, attacktype):
    resistance = False
    for item in PLAYER["items"]:
        if ("resistance" in item) and (attacktype in item):
            resistance = True
    player_bonus = PLAYER["dex"]
    if ARMOR[PLAYER["armor"]]["type"] == "heavy armor":
        player_bonus = PLAYER["str"]
    player_armor = ARMOR[PLAYER["armor"]]["protection"]
    if d20roll() + bonus >= player_bonus + player_armor:
        print("HIT!!")
    else: print("mised...")
    
def platerAttack():
    pass

def combat():
    msg = "Hello.\nThis is a test of the drawText method.\n \nWondering if newlines will work with the untested method in my Python game. What do you think of it so far?\n\nI need to work on the combat system..."
    
    combatRect = pygame.Rect(0,0,TILESIZE * WINDOWTILEWIDTH + TILESIZE*3,TILESIZE*WINDOWTILEWIDTH)
    
    drawText(msg, WHITE, combatRect)
    
    pause = True
    
    pygame.event.clear()
    pygame.display.flip()
    
    while pause:
        event = pygame.event.wait()
        if event.type == pygame.KEYDOWN: pause = False
        
    monsterAttack(MONSTERS["kobold"]["attack"][0]["bonus"], MONSTERS["kobold"]["attack"][0]["type"])


#########################################################        
# LOAD TILES FROM FILES

PLAYERTILE = pygame.image.load('player1.png')
TILES["grass"] = pygame.image.load('grass-90x90.png')
TILES["mountain"] = pygame.image.load('mountain-1.png')
TILES["water-shallow"] = pygame.image.load('water-shallow.png')
TILES["water-deep"] = pygame.image.load('water-deep.png')
TILES["forrest"] = pygame.image.load('tree-1.png')
TILES["castle"] = pygame.image.load('castle-1.png')
TILES["whitestone"] = pygame.image.load('stone.png')
TILES["brownstone"] = pygame.image.load('stone-2.png')
TILES["road-gravel"] = pygame.image.load('road-gravel.png')
TILES["road-brick"] = pygame.image.load('road-brick.png')
TILES["cave"] = pygame.image.load('cave.png')
TILES["swamp"] = pygame.image.load('swamp.png')
TILES["desert"] = pygame.image.load('desert.png')
TILES["runis"] = pygame.image.load('ruins-1.png')
TILES["town"] = pygame.image.load('town-2.png')
TILES["door"] = pygame.image.load('door.png')

#########################################################

# SET UP SCREEN
SCREEN = pygame.display.set_mode((TILESIZE * WINDOWTILEWIDTH + TILESIZE*3,TILESIZE*WINDOWTILEWIDTH))

# LOAD PLAYER DATA FORM JSON FILE
PLAYER = loadPlayer("player")

# LOAD MAP AND SET PLAYER X & Y
loadMap(PLAYER["currentmap"])
PLAYER_X = MAP["player_start_x"]
PLAYER_Y = MAP["player_start_y"]

# LOAD MONSTER DATA
MONSTERS = loadMonsters()
monster = MONSTERS["kobold"]
print(monster["attack"])
print(len(monster["attack"]))
print(monster["attack"][0])

#########################################################

# MAIN GAME LOOP
while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            print("keypress: " + str(event.key))
            if event.key == 273:
                # pressed UP key
                new_y = PLAYER_Y - 1
                if new_y < 0: new_y = 0
                newTile = MAP["terrain"][new_y][PLAYER_X]
                if isPortal("("+str(PLAYER_X)+","+str(new_y)+")"):
                    changeMap(PLAYER_X,new_y)
                elif validTile(newTile) and normalTerrain(newTile):
                    PLAYER_Y = new_y
            elif event.key == 274:
                # pressed DOWN key
                new_y = PLAYER_Y + 1
                if new_y > MAP["mapheight"] - 1: new_y = MAP["mapheight"] - 1
                newTile = MAP["terrain"][new_y][PLAYER_X]
                if isPortal("("+str(PLAYER_X)+","+str(new_y)+")"):
                    changeMap(PLAYER_X, new_y)
                elif validTile(newTile) and normalTerrain(newTile):
                    PLAYER_Y = new_y
            elif event.key == 275:
                # pressed RIGHT key
                new_x = PLAYER_X + 1
                if new_x > MAP["mapwidth"] - 1: new_x = MAP["mapwidth"] - 1
                newTile = MAP["terrain"][PLAYER_Y][new_x]
                if isPortal("("+str(new_x)+","+str(PLAYER_Y)+")"):
                    changeMap(new_x, PLAYER_Y)
                elif validTile(newTile) and normalTerrain(newTile):
                    PLAYER_X = new_x
            elif event.key == 276:
                # pressed LEFT key
                new_x = PLAYER_X - 1
                if new_x < 0: new_x = 0
                newTile = MAP["terrain"][PLAYER_Y][new_x]
                if isPortal("("+str(new_x)+","+str(PLAYER_Y)+")"):
                    changeMap(new_x, PLAYER_Y)
                elif validTile(newTile) and normalTerrain(newTile):
                    PLAYER_X = new_x
            elif event.key == 115:
                # pressed S key
                save(MAP["mapname"])
            elif event.key == 104:
                # pressed H key
                helpMenu()
            elif event.key == 105:
                # pressed I key
                inventoryManagement()
            elif event.key == 99:
                combat()
    
    drawMap()
    drawInfoPanel()
    pygame.display.flip()
    
    framesPerSecond = clock.tick(20) # max value is 40

    
"""
+===========+
| MAP CODES |
+===========+

. = grass
T = forest
w = water (shallow)
W = water (deep)
- = desert
m = hills
M = moutains
s = swamp
l = white stone wall (secret door)
L = white stone wall
+ = gravel road
# = brick road
D = door

^ = town
o = cave
C = castle
R = ruins
"""