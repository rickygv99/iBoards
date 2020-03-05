#!/usr/bin/env python3

import sys
import json
import xml.etree.ElementTree as ET
import os
import subprocess
from collections import namedtuple
import re

baseXML = """<?xml version="1.0" encoding="UTF-8"?>
<module fritzingVersion="0.9.3b.04.19.5c895d327c44a3114e5fcc9d8260daf0cbb52806">
    <views>
        <view name="breadboardView" backgroundColor="#ffffff" gridSize="0.1in" showGrid="1" alignToGrid="1" viewFromBelow="0"/>
        <view name="schematicView" backgroundColor="#ffffff" gridSize="0.1in" showGrid="1" alignToGrid="1" viewFromBelow="0"/>
        <view name="pcbView" backgroundColor="#333333" gridSize="0.05in" showGrid="1" alignToGrid="1" viewFromBelow="0"/>
    </views>
    <instances>
    </instances>
</module>"""

# pin1J
# x2="-243.379" y2="178.619"

# pin3Z
# x2="-225.362" y2="142.619"

# pin3J
# x2="-225.379" y2="178.619"

# pin61Z
# x2="296.635" y2="142.619"

# pin63F
# x2="314.617" y2="214.619"

# pin63A
# x2="314.617" y2="277.619"

# pin1E
# x2="-243.379" y2="241.619"

# pin3X
# x2="-225.362" y2="304.619"

# pin61W
# x2="126.379" y2="-204.737"


Point = namedtuple("Point", "x y")
DoublePoint = namedtuple("DoublePoint", "x y x2 y2")

def getWireCoordinate(pinValue0, pinValue1):
    pin = getCoordinate(pinValue0)
    pin2 = getCoordinate(pinValue1)

    x = pin.x + 19
    y = pin.y + 4
    x2 = pin2.x - pin.x
    y2 = pin2.y - pin.y

    wire_points = DoublePoint(x, y, x2, y2)
    return wire_points



def getCoordinate(pinValue):
    number = int(re.findall(r"\d+", pinValue)[0])
    letter = pinValue[-1] 

    # 9 is the increment for pins
    x_coord = -243.379 + 200 + 9*(number-1)
    y_coord = 0.0

    # If Y,Z (top)
    # pin3Z y="142.619"
    if letter in "YZ":
        y_coord = 142.619 - 100 + 9 * (ord('Z') - ord(letter))
    
    # If F,G,H,I,J
    # pin 1J y="178.619"
    # J = 74, F = 70
    if letter in "FGHIJ":
        y_coord = 178.619 - 100 + 9 * (ord('J') - ord(letter))

    # If A,B,C,D,E
    # pin1E y="241.619"
    if letter in "ABCDE":
        y_coord = 241.619 - 100 + 9 * (ord('E') - ord(letter))

    # If W, X (bottom)
    # pin3X y="304.619"
    if letter in "WX":
        y_coord = 304.619 - 100 + 9 * (ord('X') - ord(letter))


    pin_point = Point(x_coord, y_coord)
    return pin_point

# connector0 is always the default "starting" position of the resistor
def getResistorPinOffset(modulename, connector, pinValueTarget):

    module = root.find("./instances/instance/[title='" + modulename + "']")
    geometry = module.find("./views/breadboardView/geometry")

    x = geometry.get("x")
    y = geometry.get("y")

    # pinStart will be at x="-1.3095" y="0" in reference to the resistor's "origin"
    pinStart = Point(x,y)
    pinTarget = getCoordinate(pinValueTarget)

    xDiff = float(pinTarget.x) - float(pinStart.x)
    yDiff = float(pinTarget.y) - float(pinStart.y)

    if connector == "connector0":
        x_coord = -1.3095 + xDiff + 18
    else:
        x_coord = 1.3095 + xDiff - 18
    y_coord = 0 + yDiff

    pin_point = Point(x_coord, y_coord)
    return pin_point

XIncrement = 70.0
YIncrement = 70.0

"""
if len(sys.argv) != 2:
    print("Requires a single command line argument: the name of the json text file to import")
    exit()

filename = sys.argv[1];
with open(filename) as jsonFile:
    jsonData = json.load(jsonFile)

components = jsonData["components"]
connections = jsonData["connections"]
"""
#power0VConnector = "connector0"
#powerPositiveConnector = "connector1"
#powerNegativeConnector = "connector2"

tree = ET.parse('blank.fz')
root = tree.getroot()

portLocations = {}

globalIndex = 1
moduleX = 1.0
moduleY = 1.0

def addInstance(moduleIdRef, title, geometry, properties):
    global root
    global globalIndex

    instances = root.find("instances")
    retval = str(globalIndex)

    #create new instance and increment index
    newinstance = ET.SubElement(instances, "instance", {"moduleIdRef" : moduleIdRef, "modelIndex" : str(globalIndex)})
    globalIndex += 1

    #add properties, if any
    for key, value in properties.iteritems():
        ET.SubElement(newinstance, "property", {"name" : key, "value" : value})

    #add modulename as title
    newtitle = ET.SubElement(newinstance, "title")
    newtitle.text = title

    #add views
    newviews = ET.SubElement(newinstance, "views")
    newschematicview = ET.SubElement(newviews, "schematicView", {"layer" : "schematic"})
    newbreadboardview = ET.SubElement(newviews, "breadboardView", {"layer" : "breadboard"})
    newpcbview = ET.SubElement(newviews, "pcbView", {"layer" : "copper0"})

    #add geometries and increment location
    newschematicgeometry = ET.SubElement(newschematicview, "geometry", geometry)
    newbreadboardgeometry = ET.SubElement(newbreadboardview, "geometry", geometry)    
    newpcbgeometry = ET.SubElement(newpcbview, "geometry", geometry)
    return retval

def addResistor(title, pin1, pin2, resistance):
    # place resistor in midpoint between pins
    pin1_coord = getCoordinate(pin1)
    pin2_coord = getCoordinate(pin2)
    x = (pin1_coord.x + pin2_coord.x)/2
    y = (pin1_coord.y + pin2_coord.y)/2
    addInstance("ResistorModuleID", title, {"x" : str(x), "y" : str(y), "z" : "2.5"}, {"resistance" : str(resistance)})
    addBreadboardConn(title, pin1, pin2)
    insertResistorPins(title, pin1, pin2)


# not supported rn
def addCapacitor(title, x, y, capacitance):
    addInstance("100milCeramicCapacitorModuleID", title, {"x" : str(x), "y" : str(y), "z" : "2.5"}, {"capacitance" : str(capacitance)})


# modulename1 = resistor
# connectorID1 = resistor pin (ex: connector0, connector1)
# modulename2 = breadboard
# connectorID2 = breadboard pin (ex: pin34J)
# NEED TO ALWAYS assign connector0 of resistor before connector1 OR IT WON'T WORK
# visually, connector0 is the right side and connector1 is the left side of a resistor place on the breadboard

def addtoBreadboard(modulename1, connectorID1, modulename2, connectorID2):

    m1 = root.find("./instances/instance/[title='" + modulename1 + "']")
    m2 = root.find("./instances/instance/[title='" + modulename2 + "']")

    modelIndex1 = m1.get("modelIndex")
    modelIndex2 = m2.get("modelIndex")

    try:
        #specify connections between wire instance and both end connectors
        conns1_s = m1.find("./views/schematicView/connectors")
        if conns1_s is None:
            conns1_s = ET.SubElement(m1.find("./views/schematicView"), "connectors")
        conns1_b = m1.find("./views/breadboardView/connectors")
        if conns1_b is None:
            conns1_b = ET.SubElement(m1.find("./views/breadboardView"), "connectors")
        conns1_p = m1.find("./views/pcbView/connectors")
        if conns1_p is None:
            conns1_p = ET.SubElement(m1.find("./views/pcbView"), "connectors")

        c1_s = conns1_s.find("./connector[@connectorId='" + connectorID1 + "']")
        if c1_s is None:
            c1_s = ET.SubElement(conns1_s, "connector", {"connectorId" : connectorID1, "layer" : "schematic"})
        c1_b = conns1_b.find("./connector[@connectorId='" + connectorID1 + "']")
        if c1_b is None:
            c1_b = ET.SubElement(conns1_b, "connector", {"connectorId" : connectorID1, "layer" : "breadboard"})
        c1_p = conns1_p.find("./connector[@connectorId='" + connectorID1 + "']")
        if c1_p is None:
            c1_p = ET.SubElement(conns1_p, "connector", {"connectorId" : connectorID1, "layer" : "copper0"})
        
        connects1_s = c1_s.find("./connects")
        if connects1_s is None:
            connects1_s = ET.SubElement(c1_s, "connects")
        ET.SubElement(connects1_s, "connect", {"connectorId" : connectorID2, "modelIndex" : modelIndex2, "layer" : "schematicTrace"})
        connects1_b = c1_b.find("./connects")
        if connects1_b is None:
            connects1_b = ET.SubElement(c1_b, "connects")
        ET.SubElement(connects1_b, "connect", {"connectorId" : connectorID2, "modelIndex" : modelIndex2, "layer" : "breadboardWire"})
        connects1_p = c1_p.find("./connects")
        if connects1_p is None:
            connects1_p = ET.SubElement(c1_p, "connects")
        ET.SubElement(connects1_p, "connect", {"connectorId" : connectorID2, "modelIndex" : modelIndex2, "layer" : "copper0trace"})

        conns2_s = m2.find("./views/schematicView/connectors")
        if conns2_s is None:
            conns2_s = ET.SubElement(m2.find("./views/schematicView"), "connectors")
        conns2_b = m2.find("./views/breadboardView/connectors")
        if conns2_b is None:
            conns2_b = ET.SubElement(m2.find("./views/breadboardView"), "connectors")
        conns2_p = m2.find("./views/pcbView/connectors")
        if conns2_p is None:
            conns2_p = ET.SubElement(m2.find("./views/pcbView"), "connectors")

        c2_s = conns2_s.find("./connector[@connectorId='" + connectorID2 + "']")
        if c2_s is None:
            c2_s = ET.SubElement(conns2_s, "connector", {"connectorId" : connectorID2, "layer" : "schematic"})
        c2_b = conns2_b.find("./connector[@connectorId='" + connectorID2 + "']")
        if c2_b is None:
            c2_b = ET.SubElement(conns2_b, "connector", {"connectorId" : connectorID2, "layer" : "breadboard"})
        c2_p = conns2_p.find("./connector[@connectorId='" + connectorID2 + "']")
        if c2_p is None:
            c2_p = ET.SubElement(conns2_p, "connector", {"connectorId" : connectorID2, "layer" : "copper0"})

        connects2_s = c2_s.find("./connects")
        if connects2_s is None:
            connects2_s = ET.SubElement(c2_s, "connects")
        ET.SubElement(connects2_s, "connect", {"connectorId" : connectorID1, "modelIndex" : modelIndex1, "layer" : "schematicTrace"})
        connects2_b = c2_b.find("./connects")
        if connects2_b is None:
            connects2_b = ET.SubElement(c2_b, "connects")
        ET.SubElement(connects2_b, "connect", {"connectorId" : connectorID1, "modelIndex" : modelIndex1, "layer" : "breadboardWire"})
        connects2_p = c2_p.find("./connects")
        if connects2_p is None:
            connects2_p = ET.SubElement(c2_p, "connects")
        ET.SubElement(connects2_p, "connect", {"connectorId" : connectorID1, "modelIndex" : modelIndex1, "layer" : "copper0trace"})


    except NameError:
        print("Could not find matching instances for connection")

# resistor title, connector0, connector1
def insertResistorPins(modulename, pinValue0, pinValue1):
    module = root.find("./instances/instance/[title='" + modulename + "']")
    conns_b = module.find("./views/breadboardView/connectors")


    for connector in ["connector0", "connector1"]:
        c_b = conns_b.find("./connector[@connectorId='" + connector + "']")
        connectPin = c_b.find("./connects/connect[@modelIndex='1']")

        # for end of the pin -> need to go to 
        # breadboardview / connectors / connector / leg / the 2nd point in the leg changes where the resistor pin connects to
        c_leg = ET.SubElement(c_b, "leg")
        childPoint = ET.Element("point", {"x": "0", "y": "0"})
        childBezier = ET.Element("bezier")
        c_leg.append(childPoint)
        c_leg.append(childBezier)

        if connector == "connector0":
            offset_coord = getResistorPinOffset(modulename, connector, pinValue0)
        else:
            offset_coord = getResistorPinOffset(modulename, connector, pinValue1)
        childPoint = ET.Element("point", {"x": str(offset_coord.x), "y": str(offset_coord.y)})
        childBezier = ET.Element("bezier")
        c_leg.append(childPoint)
        c_leg.append(childBezier)

# hardcoded coordinate for power
def insertPowerPins(modulename):
    module = root.find("./instances/instance/[title='" + modulename + "']")
    conns_b = module.find("./views/breadboardView/connectors")


    for connector in ["connector0", "connector1"]:
        c_b = conns_b.find("./connector[@connectorId='" + connector + "']")
        connectPin = c_b.find("./connects/connect[@modelIndex='1']")

        # for end of the pin -> need to go to 
        # breadboardview / connectors / connector / leg / the 2nd point in the leg changes where the resistor pin connects to
        c_leg = ET.SubElement(c_b, "leg")
        childPoint = ET.Element("point", {"x": "0", "y": "0"})
        childBezier = ET.Element("bezier")
        c_leg.append(childPoint)
        c_leg.append(childBezier)

        if connector == "connector0":
            offset_coord = Point(44, -16-9*8)
        else:
            offset_coord = Point(35, 10+9*10)

        childPoint = ET.Element("point", {"x": str(offset_coord.x), "y": str(offset_coord.y)})
        childBezier = ET.Element("bezier")
        c_leg.append(childPoint)
        c_leg.append(childBezier)


# for simplicity, assume every connection adds a single wire between connectors
def addWire(modulename1, connectorID1, connectorID2):

    m1 = root.find("./instances/instance/[title='" + modulename1 + "']")

    # instances = root.find("instances")
    # for m in instances.findall("instance"):
    #     if m.get("title") == modulename1:
    #         print("found")
    #         m1 = m
    #         break
    #
    # for m in instances.findall("instance"):
    #     if m.get("title") == modulename2:
    #         m2 = m
    #         break

    try:
        # add a wire instance

        wirePoints = getWireCoordinate(connectorID1, connectorID2)

        x = str(wirePoints.x)
        y = str(wirePoints.y)
        x2 = str(wirePoints.x2)
        y2 = str(wirePoints.y2)

        wire_title = "Wire" + str(globalIndex)

        wireId = addInstance("WireModuleID", wire_title,
            {"x" : x, "y" : y, "x1" : "0", "y1" : "0", "x2" : x2, "y2" : y2}, {})

        newWire = root.find("./instances/instance/[title='Wire" + wireId + "']")

        # for the newly created wire
        conns3_s = newWire.find("./views/schematicView/connectors")
        if conns3_s is None:
            conns3_s = ET.SubElement(newWire.find("./views/schematicView"), "connectors")
        conns3_b = newWire.find("./views/breadboardView/connectors")
        if conns3_b is None:
            conns3_b = ET.SubElement(newWire.find("./views/breadboardView"), "connectors")
        conns3_p = newWire.find("./views/pcbView/connectors")
        if conns3_p is None:
            conns3_p = ET.SubElement(newWire.find("./views/pcbView"), "connectors")

        c3_s = ET.SubElement(conns3_s, "connector", {"connectorId" : "connector0", "layer" : "schematicTrace"})
        c4_s = ET.SubElement(conns3_s, "connector", {"connectorId" : "connector1", "layer" : "schematicTrace"})
        c3_b = ET.SubElement(conns3_b, "connector", {"connectorId" : "connector0", "layer" : "breadboardWire"})
        c4_b = ET.SubElement(conns3_b, "connector", {"connectorId" : "connector1", "layer" : "breadboardWire"})
        c3_p = ET.SubElement(conns3_p, "connector", {"connectorId" : "connector0", "layer" : "copper0trace"})
        c4_p = ET.SubElement(conns3_p, "connector", {"connectorId" : "connector1", "layer" : "copper0trace"})

        connects3_s = ET.SubElement(c3_s, "connects")
        connects4_s = ET.SubElement(c4_s, "connects")
        connects3_b = ET.SubElement(c3_b, "connects")
        connects4_b = ET.SubElement(c4_b, "connects")
        connects3_p = ET.SubElement(c3_p, "connects")
        connects4_p = ET.SubElement(c4_p, "connects")

        ET.SubElement(connects3_s, "connect", {"connectorId" : connectorID1, "modelIndex" : m1.get("modelIndex"), "layer" : "schematic"})
        ET.SubElement(connects4_s, "connect", {"connectorId" : connectorID2, "modelIndex" : m1.get("modelIndex"), "layer" : "schematic"})
        ET.SubElement(connects3_b, "connect", {"connectorId" : connectorID1, "modelIndex" : m1.get("modelIndex"), "layer" : "breadboard"})
        ET.SubElement(connects4_b, "connect", {"connectorId" : connectorID2, "modelIndex" : m1.get("modelIndex"), "layer" : "breadboard"})
        ET.SubElement(connects3_p, "connect", {"connectorId" : connectorID1, "modelIndex" : m1.get("modelIndex"), "layer" : "copper0"})
        ET.SubElement(connects4_p, "connect", {"connectorId" : connectorID2, "modelIndex" : m1.get("modelIndex"), "layer" : "x"})

    except NameError:
        print("Could not find matching instances for connection")
    
    return wire_title

# breadboard (DON'T CHANGE THE COORDINATEs)
z="1.5"
x="-38"
y="38"
addInstance("Breadboard-RSR03MB102-ModuleID", "breadboard_hi", {"z" : z, "x" : x, "y" : y}, {})




def addBreadboardConn(modulename, pinValue0, pinValue1):
    addtoBreadboard(modulename, "connector0", "breadboard_hi", pinValue0)
    addtoBreadboard(modulename, "connector1", "breadboard_hi", pinValue1)

# for power
addInstance("1000AFDF10011leg", "power", {"z" : z, "x" : "-250", "y" : "75"}, {})
addBreadboardConn("power", "pin4Z", "pin3W")
insertPowerPins("power")
wire_title = addWire("breadboard_hi", "pin3X", "pin3Z")
wire_title = addWire("breadboard_hi", "pin4W", "pin4Y")

# wheatstone bridge example
addResistor("resistor_1", "pin8E", "pin12E", 200)
addResistor("resistor_2", "pin8A", "pin13A", 200)
addResistor("resistor_3", "pin12B", "pin13A", 200)
addResistor("resistor_4", "pin12C", "pin18B", 200)
addResistor("resistor_5", "pin13E", "pin18E", 200)

wire_title = addWire("breadboard_hi", "pin6W", "pin8C")
wire_title = addWire("breadboard_hi", "pin18A", "pin18X")

# wire_title = addWire("breadboard_hi", "pin18E", "pin62B")
# addResistor("resistor_6", "pin8E", "pin20G", 200)
# addResistor("resistor_7", "pin20G", "pin52F", 200)




tree.write("testout1.fz")

# automatically open the file in fritzing
try:
    subprocess.call(['open', "testout1.fz"])
except Exception, e:
    print str(e)
