#!/usr/bin/env python3

import sys
import json
import xml.etree.ElementTree as ET
import os
import subprocess


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

XIncrement = 70.0
YIncrement = 70.0

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

def addOpAmp(title, x, y):
    addInstance("a59353bd0db0225dc22770e292c622f3", title, {"x" : str(x), "y" : str(y), "z" : "2.5"}, {})

def addResistor(title, x, y, resistance):
    addInstance("ResistorModuleID", title, {"x" : str(x), "y" : str(y), "z" : "2.5"}, {"resistance" : str(resistance)})

def addCapacitor(title, x, y, capacitance):
    addInstance("100milCeramicCapacitorModuleID", title, {"x" : str(x), "y" : str(y), "z" : "2.5"}, {"capacitance" : str(capacitance)})


# for simplicity, assume every connection adds a single wire between connectors
def addToBreadboard(modulename1, connectorID1, modulename2, connectorID2):

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

# for simplicity, assume every connection adds a single wire between connectors
def addWire(modulename1, connectorID1, x, y, modulename2, connectorID2, x2, y2):

    m1 = root.find("./instances/instance/[title='" + modulename1 + "']")
    m2 = root.find("./instances/instance/[title='" + modulename2 + "']")

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
        wireId = addInstance("WireModuleID", "Wire" + str(globalIndex),
            {"x" : x, "y" : y, "x1" : "0", "y1" : "0", "x2" : x2, "y2" : y2}, {})

        newWire = root.find("./instances/instance/[title='Wire" + wireId + "']")

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
        ET.SubElement(connects1_s, "connect", {"connectorId" : "connector0", "modelIndex" : wireId, "layer" : "schematicTrace"})
        connects1_b = c1_b.find("./connects")
        if connects1_b is None:
            connects1_b = ET.SubElement(c1_b, "connects")
        ET.SubElement(connects1_b, "connect", {"connectorId" : "connector0", "modelIndex" : wireId, "layer" : "breadboardWire"})
        connects1_p = c1_p.find("./connects")
        if connects1_p is None:
            connects1_p = ET.SubElement(c1_p, "connects")
        ET.SubElement(connects1_p, "connect", {"connectorId" : "connector0", "modelIndex" : wireId, "layer" : "copper0trace"})

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
        ET.SubElement(connects2_s, "connect", {"connectorId" : "connector1", "modelIndex" : wireId, "layer" : "schematicTrace"})
        connects2_b = c2_b.find("./connects")
        if connects2_b is None:
            connects2_b = ET.SubElement(c2_b, "connects")
        ET.SubElement(connects2_b, "connect", {"connectorId" : "connector1", "modelIndex" : wireId, "layer" : "breadboardWire"})
        connects2_p = c2_p.find("./connects")
        if connects2_p is None:
            connects2_p = ET.SubElement(c2_p, "connects")
        ET.SubElement(connects2_p, "connect", {"connectorId" : "connector1", "modelIndex" : wireId, "layer" : "copper0trace"})


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
        ET.SubElement(connects4_s, "connect", {"connectorId" : connectorID2, "modelIndex" : m2.get("modelIndex"), "layer" : "schematic"})
        ET.SubElement(connects3_b, "connect", {"connectorId" : connectorID1, "modelIndex" : m1.get("modelIndex"), "layer" : "breadboard"})
        ET.SubElement(connects4_b, "connect", {"connectorId" : connectorID2, "modelIndex" : m2.get("modelIndex"), "layer" : "breadboard"})
        ET.SubElement(connects3_p, "connect", {"connectorId" : connectorID1, "modelIndex" : m1.get("modelIndex"), "layer" : "copper0"})
        ET.SubElement(connects4_p, "connect", {"connectorId" : connectorID2, "modelIndex" : m2.get("modelIndex"), "layer" : "x"})


    except NameError:
        print("Could not find matching instances for connection")


# the following is for a simple LED circuit


# breadboard
# z="2.00005" x="4.35048" y="-0.00437369"

# led on breadboard
# z="3.00005" x="120.339" y="-13.2786" 
# z="3.00005" x="129.339" y="-13.2786"
# z="3.00005" x="129.339" y="-22.2786"

# resistor on breadboard
# z="2.50002" x="52.6842" y="49.4595"
# z="2.50002" x="52.6842" y="40.4595"
# z="2.50002" x="61.6842" y="40.4595"

# breadboard
z="2.00005"
x="4.35048"
y="-0.00437369"
addInstance("Breadboard-RSR03MB102-ModuleID", "breadboard_hi", {"z" : z, "x" : x, "y" : y}, {})

# led
z="3.00005"
x="120.339"
y="-13.2786"
addInstance("5mmColorLEDModuleID", "red_led", {"z" : z, "x" : x, "y" : y}, {})

# resistor
incrementx = 61.6842-52.6842
incrementy = 49.4595-40.4595
z="2.50002"
# if I were to shift it over to the right 3 spaces and down 2 spaces
x=str(float("61.6842") + incrementx*3)
y=str(float("40.4595") + incrementy*2)
addInstance("ResistorModuleID", "resistor_hi", {"z" : z, "x" : x, "y" : y}, {})


# battery
z="3"
x="45.3454"
y="-193.233"
addInstance("1000AFDF10011leg", "power", {"z" : z, "x" : x, "y" : y}, {})


# one for each pin of the components
addToBreadboard("red_led", "connector0", "breadboard_hi", "pin13I")
addToBreadboard("red_led", "connector1", "breadboard_hi", "pin14I")
addToBreadboard("resistor_hi", "connector0", "breadboard_hi", "pin9H")
addToBreadboard("resistor_hi", "connector1", "breadboard_hi", "pin13H")


# difference between component coordinate and its pin coordinates
# x="45.3454" y="-193.233"
positiveLeadPowerDiff = 126.379 - 45.3454
negativeLeadPowerDiff = abs(-204.737) - abs(-193.233)


x="135"
y="54"
x2="126.379"
y2="-204.737"
addWire("red_led", "connector1", x,y, "power", "connector1", x2, y2)

x="261.379"
y="-133.624"
x2="-171.385"
y2="196.624"
addWire("power", "connector0", x, y, "resistor_hi", "connector0", x2, y2)


tree.write("testout1.fz")

# automatically open the file in fritzing
try:
    subprocess.call(['open', "testout1.fz"])
except Exception, e:
    print str(e)