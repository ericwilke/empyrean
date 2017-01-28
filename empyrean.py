# Empyrean Adventure

import pygame
import sys
import random
import json
import time
from math import sqrt


pygame.init()
pygame.font.init()
clock = pygame.time.Clock()

#########################################################

# TO DO
#
#  - Add resistance to combat system with monsters
#  - NPC logic
#       Embed NPC data into MAP JSON -- that way status is saved, OR
#       have associated mapname.npc.json file with the NPC data
#  - Questing system

#########################################################

# DEFINE GLOBALS AND CONSTANTS
BLACK = 0, 0, 0
RED = 255, 0, 0
WHITE = 255, 255, 255
TILESIZE = 90
WINDOWTILEWIDTH = 9 #Must be odd number

PLAYER_X = 0
PLAYER_Y = 0
TILES = {}
PLAYER = {}
MAP = {}
NPC = {}
GAMEFONT = pygame.font.SysFont(None, 20)
FONTHEIGHT = 20
SPELLSELECTION = 0

# Used for message display in the info pannel
INFOMSG = [""]

MAXINVENTORY = 15
MAXSPELLS = 10


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

# Spells have a magic cost, an action (heal, fire, shock, blast, undead), a range, and a target (tells how many enemies the spell affects -- if 0, then it works on the player)
SPELLS = {
    "heal": {"cost": 10, "action": "heal", "range": 1, "target": 0, "damage": 10},
    "turn undead": {"cost": 15, "action": "undead", "range": 4, "target": 5, "damage": 12},
    "magic missle": {"cost": 6, "action": "shock", "range": 4, "target": 1, "damage": 6}
}

## create the Rect to hold the info panel text
INFOPANELRECT = pygame.Rect(TILESIZE*WINDOWTILEWIDTH, 0, TILESIZE*3, TILESIZE*WINDOWTILEWIDTH)

#########################################################

# METHODS

def get_line(start, end):
    """Bresenham's Line Algorithm
    Produces a list of tuples from start and end
 
    >>> points1 = get_line((0, 0), (3, 4))
    >>> points2 = get_line((3, 4), (0, 0))
    >>> assert(set(points1) == set(points2))
    >>> print points1
    [(0, 0), (1, 1), (1, 2), (2, 3), (3, 4)]
    >>> print points2
    [(3, 4), (2, 3), (1, 2), (1, 1), (0, 0)]
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
 
    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)
 
    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
 
    # Swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True
 
    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1
 
    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1
 
    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx
 
    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points
    

def loadPlayer(id):
    with open(id+".json", "r") as f:
        result = json.load(f)
    f.close()
    return result


def loadNpcs(id):
    result = {}
    print("Trying to load NPCs...")
    try:
        with open(id+".npc.json", "r") as f:
            result = json.load(f)
        f.close()
        return result
    except IOError:
        return result
    
    
def loadMap(id):
    global MAP, NPC
    with open(id+".json", "r") as f:
        MAP = json.load(f)
        MAP["mapheight"] = len(MAP["terrain"])
        MAP["mapwidth"] = len(MAP["terrain"][0])
        #MAP["player_x"] = MAP["player_start_x"]
        #MAP["player_y"] = MAP["player_start_y"]
        print(MAP["player_start_x"])
    f.close()
    NPC = loadNpcs(MAP["mapname"])

    
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
    PLAYER["currentmap"] = newmapname
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
    elif tileCode == "d": return "door"
    elif tileCode == "I": return "stairs"
    else: return "grass"


def validTile(x, y):
    """Checks to see if the tile is a valid tile to move a
    character into.
    
    Returns False is the tile is one that the player cannot
    enter (e.g. mountains, wall), otherwise returns True."""
    
    tile = MAP["terrain"][y][x]
    
    if (tile == "M" or tile == "W" or tile == "L"):
        return False
    elif (x == PLAYER_X and y == PLAYER_Y):
        return False
    else:
        for monster in MAP["monsters"]:
            if (monster["x"] == x and monster["y"] == y):
                return False
    return True


def normalTerrain(x,y):
    # some terrain types slow movement down randomly
    tile = MAP["terrain"][y][x]
    move = 1
    if tile == "T" or tile == "w" or tile == "s":
        move = random.randrange(1,3)
    if move > 1: return 0
    else: return 1


def isPortal(key):
    """Takes a string that is comprised of the X and Y coordinates
    on the map, and compares that string key to a list of portals
    within the MAP.
    
    Returns False if not a portal, True if it is a portal."""
    
    portal = None
    portal = MAP["portals"].get(key)
    if portal != None:
        return True
    return False
    

def blockingTile(tile):
    """Checks to see if the tile is of the type that would block
    line of sight for the player.
    
    Returns True if the tile would block line of sight."""
    
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
    global INFOMSG
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
    for index, spell in enumerate(PLAYER["spells"]):
        if SPELLSELECTION == index: invert = True
        else: invert = False
        ypos = textPanelNewLine(xpos, ypos, spell, invert)
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "----MESSAGE----")
    if len(INFOMSG) > 15:
        INFOMSG = INFOMSG[:15]
    for item in INFOMSG:
        ypos = textPanelNewLine(xpos, ypos, item)
    
    textPanelNewLine(xpos, INFOPANELRECT.bottom-FONTHEIGHT-10, "(H)elp")
    

def drawMap(cursor=False, cursor_x=0, cursor_y=0):
    # if a cursor is to be included, set cursor=True and provide x & y position
    global PLAYER_X, PLAYER_Y, NPC
    SCREEN.fill(BLACK)
    offset = int((WINDOWTILEWIDTH - 1)/2)
    
    # draw terrain
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
    if cursor:
        SCREEN.blit(CURSOR, (cursor_x*TILESIZE, cursor_y*TILESIZE))
    
    # draw monsters
    for monster in MAP["monsters"]:
        if ( (monster["x"] - (PLAYER_X - offset) >= 0) and (monster["y"] - (PLAYER_Y - offset) >=0) and (monster["x"] - (PLAYER_X - offset) < WINDOWTILEWIDTH) and (monster["y"] - (PLAYER_Y - offset) < WINDOWTILEWIDTH) ):
            if isVisible(monster["x"], monster["y"], PLAYER_X, PLAYER_Y):
                SCREEN.blit(TILES[monster["name"]], ( (monster["x"] - (PLAYER_X - offset)) * TILESIZE, (monster["y"] - (PLAYER_Y - offset)) * TILESIZE))

    # draw NPCs
    for key in NPC:
        if ( (NPC[key]["x"] - (PLAYER_X - offset) >= 0) and (NPC[key]["y"] - (PLAYER_Y - offset) >=0) and (NPC[key]["x"] - (PLAYER_X - offset) < WINDOWTILEWIDTH) and (NPC[key]["y"] - (PLAYER_Y - offset) < WINDOWTILEWIDTH) ):
            if isVisible(NPC[key]["x"], NPC[key]["y"], PLAYER_X, PLAYER_Y):
                SCREEN.blit(TILES[NPC[key]["tile"]], ( (NPC[key]["x"] - (PLAYER_X - offset)) * TILESIZE, (NPC[key]["y"] - (PLAYER_Y - offset)) * TILESIZE))


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
    ypos = textPanelNewLine(xpos, ypos, "(A)ttack")
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "(SPACE) to select spell")
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "(C)ast spell")
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "(I)nventory")
    ypos = textPanelNewLine(xpos, ypos, " ")
    ypos = textPanelNewLine(xpos, ypos, "(S)ave")
    ypos = textPanelNewLine(xpos, ypos, " ")
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


def drawText(txt, color, rect, aa=True, bkg=None):
    """Draws a text message to a rect with word wrapping."""
    
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
            
            
def noNPC(x, y):
    # check to make sure the space where the player wants to move to is not occupied
    # by a NPC or a monster. Return True if the space is open, return False if occupied.
    for key in NPC:
        if NPC[key]["x"] == x and NPC[key]["y"] == y: return False
    for monster in MAP["monsters"]:
        if monster["x"] == x and monster["y"] == y: return False
    return True
        


def movePlayer(x, y):
    """Move the player to a new tile if valid.
    Check for portals, NPCs, etc."""
    global PLAYER_X, PLAYER_Y
    
    if y < 0: y = 0
    if y > MAP["mapheight"] - 1: y = MAP["mapheight"] - 1
    
    if x < 0: x = 0
    if x > MAP["mapwidth"] - 1: x = MAP["mapwidth"] - 1
    
    if isPortal("("+str(x)+","+str(y)+")"):
        changeMap(x,y)
    elif validTile(x,y) and normalTerrain(x,y) and noNPC(x,y):
        PLAYER_X, PLAYER_Y = x, y

        
def loadMonsters():
    result = "{}"
    with open("monsters.json", "r") as f:
        #jsontext = f.read()
        dict = json.load(f)
    f.close()
    return dict

        
def d20roll():
    return random.randint(1,20)
    

def distance(x1, y1, x2, y2):
    return int(sqrt((x1-x2)**2 + (y1-y2)**2))
    
    
def randomFromStr(str):
    items = str.split(":")
    a = int(items[0])
    b = int(items[1])
    return random.randint(a,b)

        
def monsterAttack(monstername):
    global INFOMSG
    combatMessageRect = pygame.Rect(0,0,TILESIZE * WINDOWTILEWIDTH, FONTHEIGHT)
    resistance = False
    for item in PLAYER["items"]:
        if ("resistance" in item) and (MONSTER[monstername]["attack"]["type"] in item):
            resistance = True
    player_bonus = PLAYER["dex"]
    if ARMOR[PLAYER["armor"]]["type"] == "heavy armor":
        player_bonus = PLAYER["str"]
    player_armor = ARMOR[PLAYER["armor"]]["protection"]
    if d20roll() + MONSTERS[monstername]["attack"]["bonus"] >= player_bonus + player_armor:
        print("HIT!!")
        damage = random.randint(1,MONSTERS[monstername]["attack"]["damage"])
        if resistance: damage = int(damage / 2)
        PLAYER["hp"] -= damage
        hitRect = pygame.Rect(((WINDOWTILEWIDTH - 1)/2) * TILESIZE, ((WINDOWTILEWIDTH - 1)/2) * TILESIZE, TILESIZE, TILESIZE)
        pygame.draw.rect(SCREEN, RED, hitRect)
        INFOMSG.insert(0, "----------")
        INFOMSG.insert(0, str(damage) + " damage!")
        INFOMSG.insert(0, monstername.upper() + " hit you!")
        #drawText(msg, WHITE, combatMessageRect, True, BLACK)
        pygame.display.update()
        pygame.time.wait(100)
    else:
        INFOMSG.insert(0, "----------")
        INFOMSG.insert(0, monstername.upper() + " missed.")
    

def spawnMonster():
    if MAP["spawnfrequency"] == 0: return
    spawnchance = random.randint(1,100)
    if spawnchance <= MAP["spawnfrequency"]:
        x = random.randint(0, MAP["mapwidth"]-1)
        y = random.randint(0, MAP["mapheight"]-1)
        
        flag = validTile(x,y)
        
        while flag == False:
            x = random.randint(0, MAP["mapwidth"]-1)
            y = random.randint(0, MAP["mapheight"]-1)
            flag = validTile(x,y)
            
        numberofchoices = len(MAP["spawntypes"])
        flag = True
        while flag:
            ran = random.randint(1,numberofchoices)
            monstertype = MAP["spawntypes"][ran-1]
            rare = random.randint(1,100)
            if MONSTERS[monstertype]["prevelance"] == "frequent" and rare <= 50:
                flag = False
            elif MONSTERS[monstertype]["prevelance"] == "common" and rare <= 80:
                flag = False
            elif MONSTERS[monstertype]["prevelance"] == "rare" and rare <= 95:
                flag = False
            elif MONSTERS[monstertype]["prevelance"] == "very rare" and rare <= 100:
                flag = False

        hp = randomFromStr(MONSTERS[monstertype]["hp"])
        
        print("Adding "+monstertype+" at position "+str(x)+", "+str(y))
        print("Map tile value at monster position is: " + MAP["terrain"][y][x])
        print("Position is valid: " + str(validTile(x,y)))
        
        MAP["monsters"].append({"name": monstertype, "x": x, "y": y, "hp": hp})
        
        
    
def monsterMoveAndAttack():
    """
    If monster can see player, move toward player.
    Otherwise, move randomly.
    """
    offset = (WINDOWTILEWIDTH - 1)/2
    for monster in MAP["monsters"]:
        new_x = monster["x"]
        new_y = monster["y"]
        
        if (monster["x"] >= PLAYER_X - offset and monster["x"] <= PLAYER_X + offset and monster["y"] >= PLAYER_Y - offset and monster["y"] <= PLAYER_Y + offset):
            # monster is within the visible map
            # either move monster toward player or attack
            if isVisible(PLAYER_X, PLAYER_Y, monster["x"], monster["y"]):
                
                d=distance(PLAYER_X,PLAYER_Y,monster["x"],monster["y"])

                if d <= MONSTERS[monster["name"]]["attack"]["range"]:
                    #attack player
                    print("attacking player")
                    monsterAttack(monster["name"])
                xy = random.randint(0,1)
                if xy == 0 and monster["x"] != PLAYER_X:
                    #move in the x direction toward player
                    if new_x < PLAYER_X: new_x += 1
                    elif new_x> PLAYER_X: new_x -= 1
                else:
                    #move in the y direction toward player
                    if new_y < PLAYER_Y: new_y += 1
                    elif new_y > PLAYER_Y: new_y -= 1
                if new_x < 0: new_x = 0
                if new_y < 0: new_y = 0
                if new_x > MAP["mapwidth"] - 1: new_x = MAP["mapwidth"] - 1
                if new_y > MAP["mapheight"] - 1: new_y = MAP["mapheight"] - 1
                if validTile(new_x, new_y) and normalTerrain(new_x, new_y):
                    if not (new_x == PLAYER_X and new_y == PLAYER_Y):
                        monster["x"] = new_x
                        monster["y"] = new_y  
        
        else:
            # monster is not within visible map, move according to movement settings
            if MONSTERS[monster["name"]]["movement"] == "random":
                if random.randint(0,1) == 1:
                    new_x += random.randint(-1, 1)
                else:
                    new_y += random.randint(-1, 1)
                if new_x < 0: new_x = 0
                if new_y < 0: new_y = 0
                if new_x > MAP["mapwidth"] - 1: new_x = MAP["mapwidth"] - 1
                if new_y > MAP["mapheight"] - 1: new_y = MAP["mapheight"] - 1
                if (validTile(new_x, new_y) and normalTerrain(new_x, new_y)):
                    if not (new_x == PLAYER_X and new_y == PLAYER_Y):
                        monster["x"] = new_x
                        monster["y"] = new_y

    
def damageMonster(monster, damage, index, critical=False):
    # monster
    center = (WINDOWTILEWIDTH-1) / 2
    if critical: damage = damage * 2
    monster["hp"] -= damage
    INFOMSG.insert(0, monster["name"]+" hit for "+str(damage)+" damage.")
    hitRect = pygame.Rect((monster["x"] - (PLAYER_X - center)) * TILESIZE, (monster["y"] - (PLAYER_Y - center)) * TILESIZE, TILESIZE, TILESIZE)
    pygame.draw.rect(SCREEN, RED, hitRect)
    pygame.display.update()
    pygame.time.wait(100)
    if monster["hp"] < 1:
        # add XP to player
        PLAYER["xp"] += MONSTERS[monster["name"]]["xp"]
        # add gold to player
        PLAYER["gold"] += randomFromStr(MONSTERS[monster["name"]]["gold"])
        questEvent()
        del(MAP["monsters"][index])
    

def selectTarget(range, action="attack"):
    """Draws the map with the cursor visible and lets player select a target
    to attack. Arrow keys will move cursor. SPACE will attack.
    
    Takes one argument 'range' which is the range of the weapon or spell.
    
    Set action="talk" to check against NPCs instead of monters.
    """
    
    msg = "SELECT TARGET: use ARROW keys to select target, SPACE to attack, ESC to exit."
    
    combatMessageRect = pygame.Rect(0,0,TILESIZE * WINDOWTILEWIDTH, FONTHEIGHT)
    
    center = (WINDOWTILEWIDTH-1) / 2
    cursor_x = center
    cursor_y = center
    
    attackMode = True
    
    while attackMode:
    
        drawMap(True, cursor_x, cursor_y)
        pygame.draw.rect(SCREEN, BLACK, combatMessageRect)
        drawText(msg, WHITE, combatMessageRect)
        drawInfoPanel()
        pygame.display.flip()
        
        pauseforinput = True
        while pauseforinput:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                pauseforinput = False
                if event.key == 273:
                    cursor_y -= 1
                elif event.key == 274:
                    cursor_y += 1
                elif event.key == 275:
                    cursor_x += 1
                elif event.key == 276:
                    cursor_x -= 1
                elif event.key == 32:
                    # pressed the SPACE key, check to see if there is a target
                    # set attackMode to False so monster turn will cycle
                    attackMode = False
                    target_x = PLAYER_X + (cursor_x - center)
                    target_y = PLAYER_Y + (cursor_y - center)
                    if action == "attack":
                        for index, monster in enumerate(MAP["monsters"]):
                            if (monster["x"] == target_x) and (monster["y"] == target_y):
                                return index, monster
                        else: return -1, None
                    elif action == "talk":
                        for index in NPC:
                            if NPC[index]["x"] == target_x and NPC[index]["y"] == target_y:
                                return index
                elif event.key == 27:
                    # pressed the ESC key, exit out of attack mode
                    attackMode = False
                    return -1, None
                
            if cursor_x < 0: cursor_x = 0
            if cursor_y < 0: cursor_y = 0
            if cursor_x > WINDOWTILEWIDTH: cursor_x = WINDOWTILEWIDTH
            if cursor_y > WINDOWTILEWIDTH: cursor_y = WINDOWTILEWIDTH
            
            if (cursor_x) > center + range:
                cursor_x = center + range
            if (cursor_x) < center - range:
                cursor_x = center - range
            if (cursor_y) > center + range:
                cursor_y = center + range
            if (cursor_y) < center - range:
                cursor_y = center - range
    


def playerAttack():
    """Draws the map with the cursor visible and lets player select a target
    to attack. Arrow keys will move cursor. SPACE will attack."""
    
    range = WEAPONS[PLAYER["weapon"]]["range"]
    index, monster = selectTarget(range)
    
    if monster:
        # roll for attack and damage
        roll = d20roll()
        if roll > 1:
            bonus = 0
            armorclass = MONSTERS[monster["name"]]["armor class"]
            if WEAPONS[PLAYER["weapon"]]["type"] == "range":
                bonus = PLAYER["dex"]
            if WEAPONS[PLAYER["weapon"]]["type"] == "melee":
                bonus = PLAYER["str"]
            if (roll + bonus > armorclass) or roll == 20:
                damage = random.randint(1,WEAPONS[PLAYER["weapon"]]["damage"])
                crit = False
                if roll == 20:
                    crit = True
                damageMonster(monster, damage, index, crit)

    
    
def talk():
    """Create the systemt to talk with an NPC"""
    index = selectTarget(1, "talk")
    if index:
        talkRect = pygame.Rect(int(TILESIZE*WINDOWTILEWIDTH*0.20), int(TILESIZE*WINDOWTILEWIDTH*0.4), int(TILESIZE*WINDOWTILEWIDTH*0.6), int(TILESIZE*WINDOWTILEWIDTH*0.3))
        SCREEN.fill(BLACK, talkRect)
        
        msg = random.randint(0, len(NPC[index]["greeting"])-1)
        txt = NPC[index]["name"]+" says:\n" + NPC[index]["greeting"][msg]+"\n"
        
        if NPC[index]["give_item"]:
            print("Give an item to player.")
            if len(PLAYER["items"]) >= MAXINVENTORY:
                txt += "I would like to give you something, but it looks like you are carrying too much.\n"
                INFOMSG.insert(0, "too much.")
                INFOMSG.insert(0, "but it looks like you are carring")
                INFOMSG.insert(0, "I would like to give you something,")
        if NPC[index]["heal"] == "yes":
            if PLAYER["hp"] < PLAYER["max_hp"]:
                PLAYER["hp"] = PLAYER["max_hp"]
                INFOMSG.insert(0, "Let me heal your wounds.")
                txt += "Let me heal your wounds...\n"
            if PLAYER["magic"] < PLAYER["max_magic"]:
                PLAYER["magic"] = PLAYER["max_magic"]
                INFOMSG.insert(0, "Your magic power is restored.")
                txt += "I have restored your magic."
        if NPC[index]["buy_sell"] == "yes":
            print("Buy/sell stuff to player")
        
        INFOMSG.insert(0, NPC[index]["greeting"][msg])
        INFOMSG.insert(0, NPC[index]["name"]+" says:")
        questEvent()
        
        drawText(txt, WHITE, talkRect, True, BLACK)
        
        pause = True
        pygame.event.clear()
        pygame.display.flip()
        while pause:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN: pause = False
    
    
def castSpell():
    """Create the systemt to cast spells"""
    spell = PLAYER["spells"][SPELLSELECTION]
    if PLAYER["magic"] >= SPELLS[spell]["cost"]:
        if SPELLS[spell]["target"] == 0:
            # spell works on player
            if spell == "heal":
                PLAYER["hp"] += random.randint(1, SPELLS[spell]["damage"])
                PLAYER["magic"] -= SPELLS[spell]["cost"]
            if PLAYER["hp"] > PLAYER["max_hp"]: PLAYER["hp"] = PLAYER["max_hp"]
            INFOMSG.insert(0, "You cast HEAL.")
        else:
            if spell == "turn undead":
                INFOMSG.insert(0, "You cast TURN UNDEAD.")
                PLAYER["magic"] -= SPELLS[spell]["cost"]
                for index, monster in enumerate(MAP["monsters"]):
                    if ("zombie" in monster["name"]) or ("skeleton" in monster["name"]) or ("ghost" in monster["name"]) or ("wraith" in monster["name"]) or ("litch" in monster["name"]) or ("mummy" in monster["name"]):
                        d=distance(PLAYER_X,PLAYER_Y,monster["x"],monster["y"])
                        if d <= SPELLS[spell]["range"]:
                            damage = random.randint(1,SPELLS[spell]["damage"]+PLAYER["level"])
                            damageMonster(monster, damage, index)
            if spell == "magic missle":
                range = SPELLS[spell]["range"]
                index, monster = selectTarget(range)
                if monster != None:
                    INFOMSG.insert(0, "You cast MAGIC MISSLE.")
                    PLAYER["magic"] -= SPELLS[spell]["cost"]
                    damage = random.randint(1,SPELLS[spell]["damage"]+PLAYER["level"])
                    damageMonster(monster, damage, index)


def questEvent():
    pass
    
    
#########################################################        

# LOAD TILES FROM FILES

PLAYERTILE = pygame.image.load('player1.png')
CURSOR = pygame.image.load('cursor.png')

TILES["king"] = pygame.image.load('king.png')

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
TILES["stairs"] = pygame.image.load('stairs.png')

TILES["kobold"] = pygame.image.load('kobold.png')
TILES["scorpion"] = pygame.image.load('scorpion.png')
TILES["rat"] = pygame.image.load('rat.png')
TILES["skeleton"] = pygame.image.load('skeleton.png')
TILES["zombie"] = pygame.image.load('zombie.png')
TILES["zombieking"] = pygame.image.load('zombieking.png')
TILES["mummy"] = pygame.image.load('mummy.png')

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


#########################################################

# MAIN GAME LOOP

regenerate = 1
clearmsg = 1

while True:

    drawMap()
    drawInfoPanel()
    pygame.display.flip()
    
    framesPerSecond = clock.tick(20) # max value is 40
    
    pygame.time.wait(200)
    
    if len(MAP["monsters"]) < 20:
        spawnMonster()
        
    INFOMSG.insert(0, " ")
    
    waitforinput = True
    while waitforinput:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                waitforinput = False
                print("keypress: " + str(event.key))
                if event.key == 273:
                    # pressed UP key
                    new_y = PLAYER_Y - 1
                    movePlayer(PLAYER_X, new_y)
                elif event.key == 274:
                    # pressed DOWN key
                    new_y = PLAYER_Y + 1
                    movePlayer(PLAYER_X, new_y)
                elif event.key == 275:
                    # pressed RIGHT key
                    new_x = PLAYER_X + 1
                    movePlayer(new_x, PLAYER_Y)
                elif event.key == 276:
                    # pressed LEFT key
                    new_x = PLAYER_X - 1
                    movePlayer(new_x, PLAYER_Y)
                elif event.key == 115:
                    # pressed S key
                    save(MAP["mapname"])
                elif event.key == 104:
                    # pressed H key
                    helpMenu()
                elif event.key == 105:
                    # pressed I key
                    inventoryManagement()
                elif event.key == 97:
                    # pressed A key
                    playerAttack()
                elif event.key == 116:
                    # pressed T key
                    talk()
                elif event.key == 99:
                    # pressed C key
                    castSpell()
                elif event.key == 113:
                    # pressed Q key
                    sys.exit()
                elif event.key == 32:
                    # pressed SPACE key
                    if PLAYER["spells"]:
                        SPELLSELECTION += 1
                        if SPELLSELECTION > len(PLAYER["spells"])-1:
                            SPELLSELECTION = 0
    
    print("X: " + str(PLAYER_X) + ", Y: " + str(PLAYER_Y))
    #print(PLAYER["currentmap"])
    monsterMoveAndAttack()
    
    regenerate += 1
    if regenerate > 50:
        #regenerate HP and magic
        PLAYER["hp"] += PLAYER["hp_regen"]
        PLAYER["magic"] += PLAYER["magic_regen"]
        if PLAYER["hp"] > PLAYER["max_hp"]: PLAYER["hp"] = PLAYER["max_hp"]
        if PLAYER["magic"] > PLAYER["max_magic"]: PLAYER["magic"] = PLAYER["max_magic"]
        regenerate = 1
    
    if PLAYER["hp"] < 1:
        print("The valiant adventurer is dead...")
        msg = " \n \n                    The valiant adventurer is dead...\n                    Press 'Q' to start from last save."
        deadMessageRect = pygame.Rect(0,TILESIZE * (WINDOWTILEWIDTH -1)/2,TILESIZE * WINDOWTILEWIDTH, 120)
        pygame.draw.rect(SCREEN, BLACK, deadMessageRect)
        drawText(msg, RED, deadMessageRect)
        pygame.display.update()
        waitforinput = True
        pygame.event.clear()
        while waitforinput:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key == 113:
                    waitforinput = False
        # LOAD PLAYER DATA FORM JSON FILE
        PLAYER = loadPlayer("player")

        # LOAD MAP AND SET PLAYER X & Y
        loadMap(PLAYER["currentmap"])
        PLAYER_X = MAP["player_start_x"]
        PLAYER_Y = MAP["player_start_y"]
        


    
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
d = door (locked)
I = stairs

^ = town
o = cave
C = castle
R = ruins
"""