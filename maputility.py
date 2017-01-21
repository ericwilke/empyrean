# maputility.py

import sys

print("Map file name for parsing: ")
filename = input().rstrip()

MAP = []

with open(filename) as mapfile:
        for line in mapfile:
            line = line.rstrip()
            linedata = line.split(" ")
            MAP.append(linedata)

print ("map size: " + str(len(MAP[0])) + " by " + str(len(MAP)))
print ("===============MAP DATA STRCTURE===============")
output = "["
for row in MAP:
    output = output + str(row)
output = output + "]"
output = output.replace("'", '"')
output = output.replace("][", "],[")
print(output)