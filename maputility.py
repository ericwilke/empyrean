# maputility.py

import sys

filename = input("Map file name for parsing: ").rstrip()

if filename == "" or filename == None:
    quit()

MAP = []

with open(filename) as mapfile:
        for line in mapfile:
            line = line.rstrip()
            linedata = line.split(" ")
            MAP.append(linedata)

print(" ")
print("map size: " + str(len(MAP[0])) + " by " + str(len(MAP)))
print("===============MAP DATA STRCTURE===============")
output = "["
for row in MAP:
    output = output + str(row)
output = output + "]"
output = output.replace("'", '"')
output = output.replace("][", "],[")
print(output)
print("==================END OF FILE==================")