from qgis.core import *
from random import shuffle
from pathlib import Path
from PyQt6.QtCore import QMetaType
import xml.etree.cElementTree as ET
from datetime import datetime
import json
import math
import random
import struct
import traceback

CATEGORY = 'VectorToTreesBIN'

#Path to the JSON config file
config_file_path = "C:/Users/user/Projects/Games/Cities Skylines 2/Map/Forests/config_file_template.json"

#Change this to True if you wish to only preview how the trees will be placed in single feature/polygon (the first feature in the layer)
#Changing this to True will also not generate the treesBIN file
preview_mode = False

class Position:
    def __init__(self, x: float, y: float):
        self.X = x
        self.Y = y

class BufferedTrees:
    def __init__(self, id, positions : list[Position]):
        self.ID = id
        self.Positions = positions

class BufferedTreesCollection:
    def __init__(self):
        self.BufferedTrees : list[BufferedTrees] = []

class TreesBIN:
    def __init__(self, listID : list[int]):
        self.Width = 14336
        self.Height = 14336
        self.TreeCount = 0
        self.Mode = 0x00
        self.ListID = listID
        self.Buffers : list[BufferedTreesCollection] = []


class TaskData:
    def __init__(self, layerName, playAreaTreesCount, nonPlayAreaTreesCount, fields, fieldIDS : list[int], fieldColors, playAreaExtent, mapAreaExtent, outputPath, treeXmlLayerName, treeXmlPointsLayerName, previewMode):
        self.layerName = layerName
        self.playAreaTreesCount = playAreaTreesCount
        self.nonPlayAreaTreesCount = nonPlayAreaTreesCount
        self.fields = fields
        self.fieldIDS = fieldIDS
        self.fieldColors = fieldColors
        self.playAreaExtent = playAreaExtent
        self.mapAreaExtent = mapAreaExtent
        self.outputPath = outputPath
        self.treeXmlLayerName = treeXmlLayerName
        self.treeXmlPointsLayerName = treeXmlPointsLayerName
        self.previewMode = previewMode
        self.timeStart = datetime.now()
        self.generatedCount = 0

    def setPointsLayer(self, pointsLayer, renderer):
        self.pointsLayer = pointsLayer
        self.renderer = renderer

    def setGeneratedCount(self, generatedCount):
        self.generatedCount = generatedCount

def writeBinaryFile(treesBIN : TreesBIN, filePath):
    print('Generating TreesBIN file')
    with open(filePath, "wb") as writer:
        uint16_format = "<H"

        #File Header
        writer.write(b'\x00')
        writer.write(b"ForestSkylines")
        writer.write(b'\x89')
        writer.write(b'D')
        writer.write(b'\x01')

        #Data Block
        #0 as vector mode
        writer.write(b'\x00')
        #Width and height of raster
        writer.write(struct.pack(uint16_format, treesBIN.Width)) #Type: UInt16, Offset: 0x01
        writer.write(struct.pack(uint16_format, treesBIN.Height)) #Type: UInt16, Offset: 0x03
        #Tree count
        writer.write(struct.pack("<i", treesBIN.TreeCount)) #Type: Int32, Offset: 0x05

        #Write list ID count
        writer.write(struct.pack(uint16_format, len(treesBIN.ListID))) #Type: UInt16, Offset: 0x09
        for _id in treesBIN.ListID:
            writer.write(struct.pack(uint16_format, _id)) #Type: Int32, Offset 0x0b

        #Write buffers count
        writer.write(struct.pack(uint16_format, len(treesBIN.Buffers))) #Type: UInt16, Offset: 0x0d
        #Write buffers
        for col in treesBIN.Buffers:
            #Write buffered trees count
            writer.write(struct.pack(uint16_format, len(col.BufferedTrees))) #Type: UInt16, Offset: 0x11
            #Write buffered trees
            for trees in col.BufferedTrees:
                #Write ID and count of positions
                writer.write(struct.pack(uint16_format, trees.ID)) #Type: UInt16, Offset: 0x13
                writer.write(struct.pack(uint16_format, len(trees.Positions))) #Type: UInt16, Offset: 0x15

                #Write positions of trees
                for position in trees.Positions:
                    #Write X and Y tree location on the map
                    writer.write(struct.pack("<f", position.X))
                    writer.write(struct.pack("<f", position.Y))

# Get the intersecting point if the point lies on the line
def getIntersection(k, n, x1, y1, x2, y2, i):
    if x1 == x2:
        i[0] = x1
        i[1] = k * i[0] + n
        if i[1] >= y1 and i[1] <= y2:
            return True
    
    if y1 == y2:
        i[1] = y1
        i[0] = (n - i[1]) / -k
        if i[0] >= x1 and i[0] <= x2:
            return True

    return False

#Get the normalized distance (0-1) of the point between the play area and map area extent 
def getNormalizedDistance(point, map_center, play_area_extent, map_area_extent):
    #Calculate closest point of the point to the edge of the play area and map area
    pi = [0,0]
    mi = [0,0]

    if(point.x() == map_center.x()):
        #Point is vertical perpendicular to map center 
        pi[0] = point.x()
        mi[0] = point.x()

        #Check if point lies above play area
        if point.y() >= play_area_extent.yMaximum():
            pi[1] = play_area_extent.yMaximum()
            mi[1] = map_area_extent.yMaximum()
        #Else it lies underneath play area
        else:
            pi[1] = play_area_extent.yMinimum()
            mi[1] = map_area_extent.yMinimum()

    elif(point.y() == map_center.y()):
        #Point is horizontal perpendicular to map center
        pi[1] = point.y()
        mi[1] = point.y()
        #Check if point lies to the left of the play area
        if point.x() <= play_area_extent.xMinimum():
            pi[0] = play_area_extent.xMinimum()
            mi[0] = map_area_extent.xMinimum()
        #Else it lies to the right side of the play area
        else:
            pi[0] = play_area_extent.xMaximum()
            mi[0] = map_area_extent.xMaximum()

    else:
        k = (point.y() - map_center.y()) / (point.x() - map_center.x())
        n = point.y() - k * point.x()

        #Calculate intersection point with left side of play area
        if point.x() <= play_area_extent.xMinimum() and getIntersection(k, n, play_area_extent.xMinimum(), play_area_extent.yMinimum(), play_area_extent.xMinimum(), play_area_extent.yMaximum(), pi):
            getIntersection(k, n, map_area_extent.xMinimum(), map_area_extent.yMinimum(), map_area_extent.xMinimum(), map_area_extent.yMaximum(), mi)
        #Calculate intersection point with right side of play area
        elif point.x() >= play_area_extent.xMaximum() and getIntersection(k, n, play_area_extent.xMaximum(), play_area_extent.yMinimum(), play_area_extent.xMaximum(), play_area_extent.yMaximum(), pi):
            getIntersection(k, n, map_area_extent.xMaximum(), map_area_extent.yMinimum(), map_area_extent.xMaximum(), map_area_extent.yMaximum(), mi)
        #Calculate intersection point with top side of play area
        elif point.y() >= play_area_extent.yMaximum() and getIntersection(k, n, play_area_extent.xMinimum(), play_area_extent.yMaximum(), play_area_extent.xMaximum(), play_area_extent.yMaximum(), pi):
            getIntersection(k, n, map_area_extent.xMinimum(), map_area_extent.yMaximum(), map_area_extent.xMaximum(), map_area_extent.yMaximum(), mi)
        #Calculate intersection point with bottom side of play area
        elif point.y() <= play_area_extent.yMinimum() and getIntersection(k, n, play_area_extent.xMinimum(), play_area_extent.yMinimum(), play_area_extent.xMaximum(), play_area_extent.yMinimum(), pi):
            getIntersection(k, n, map_area_extent.xMinimum(), map_area_extent.yMinimum(), map_area_extent.xMaximum(), map_area_extent.yMinimum(), mi)

    distance_to_map_area = abs(math.sqrt(math.pow(mi[0] - point.x(), 2) + math.pow(mi[1] - point.y(), 2)))
    distance_to_play_area= abs(math.sqrt(math.pow(point.x() - pi[0], 2) + math.pow(point.y() - pi[1], 2)))

    return distance_to_play_area / (distance_to_map_area + distance_to_play_area) 

#Create a equal grid points with a jitter on top of the polygon
def genJitterGrid(polygon, map_area_extent, total_points, jitter):
    points = []

    bbo = polygon.boundingBox()

    #Determine the min distances
    nx = (bbo.width() / bbo.height() * total_points) ** 0.5
    ny = total_points / nx

    min_distance_x = bbo.width() / nx
    min_distance_y = bbo.height() / ny
    
    #print('min_dx: {} | min_dy: {} | po: {}, | wid: {} | hei: {}'.format(min_distance_x, min_distance_y, total_points, bbo.width(), bbo.height()))
    
    rx = 0
    ry = 0

    x = bbo.xMinimum()
    while x < bbo.xMaximum():
        y = bbo.yMinimum()
        while y < bbo.yMaximum():
            rx = x + random.uniform(-jitter, jitter)
            ry = y + random.uniform(-jitter, jitter)

            if polygon.contains(rx, ry) and (rx > map_area_extent.xMinimum() and rx < map_area_extent.xMaximum() and ry < map_area_extent.yMaximum() and ry > map_area_extent.yMinimum()):
                points.append(QgsPointXY(rx, ry))
            
            y += min_distance_y
        x += min_distance_x

    return points



def genTreeBIN(task, taskData):
    try:
        #Center point of map area
        map_center = taskData.mapAreaExtent .center()

        layer = QgsProject.instance().mapLayersByName(taskData.layerName)[0]

        #Sum the area field of all features inside the play area, and outside
        sum_of_all_play_area = 0
        sum_of_all_non_play_area = 0
        for feature in layer.getFeatures():
            feature_area = feature.geometry().area()
            if feature.geometry().boundingBox().intersects(taskData.playAreaExtent):
                sum_of_all_play_area += feature_area
            else:
                sum_of_all_non_play_area += feature_area

        treesBIN = TreesBIN(taskData.fieldIDS)

        #Create new vector point layer
        layer_crs = layer.crs().authid()
        points_layer = QgsVectorLayer('Point?crs={epsg}'.format(epsg=layer_crs), taskData.treeXmlPointsLayerName, 'memory')
        data_provider = points_layer.dataProvider()

        #Enter edit mode
        points_layer.startEditing()

        #Add fields
        data_provider.addAttributes([
            QgsField('fieldType', QMetaType.Type.QString)
        ])

        points_layer.updateFields()

        task.setProgress(0)
        
        feature_index = 0
        maxArea_feature_id = None
        maxArea_feature = None

        #If preview mode is true, get the ID of the biggest feature by area and use it for for the preview feature
        if task_data.previewMode: 
            for feature in layer.getFeatures():
                geomArea = feature.geometry().area()
                if maxArea_feature is None or geomArea > maxArea_feature:
                    maxArea_feature = geomArea
                    maxArea_feature_id = feature.id()


        for feature in layer.getFeatures():
            feature_index += 1
            task.setProgress((feature_index * 100) / layer.featureCount())

            if task_data.previewMode and maxArea_feature_id != feature.id():
                continue

            geom = feature.geometry()
            center_point = geom.centroid().asPoint()

            points_per_feature = 0

            #Check if feature lies withing play area
            if feature.geometry().boundingBox().intersects(taskData.playAreaExtent):
                points_per_feature = int(taskData.playAreaTreesCount * (geom.area() / sum_of_all_play_area))
            else:
                #Calculate the area weight
                area_weight = geom.area() / sum_of_all_non_play_area
            
                #Calculate the normalized distance (0-1) to the closeness of the play area
                normalized_distance = getNormalizedDistance(center_point, map_center, taskData.playAreaExtent, taskData.mapAreaExtent)

                #Closer features get higher weight
                distance_weight = 1 - normalized_distance

                points_per_feature = int(taskData.nonPlayAreaTreesCount * area_weight * distance_weight)

            #Get the attribute percentages
            percentages = [feature[field] for field in taskData.fields]
            counts = [round(points_per_feature * (p / 100)) for p in percentages]

            #Generate a list of id labels based on counts
            id_labels = []
            for i, count in enumerate(counts):
                id_labels.extend([task_data.fieldIDS[i]] * count)

            points_per_feature = len(id_labels)

            if points_per_feature > 0:

                #Shuffle the id labels randomly
                shuffle(id_labels)

                points = []

                if points_per_feature > 8:
                    #Generate grid with a jitter inside the polygon
                    points.extend(genJitterGrid(geom, taskData.mapAreaExtent, points_per_feature, 2))
                
                #Calculate the random number of points from the leftover
                random_points_per_feature = points_per_feature - len(points)

                if random_points_per_feature > 0:
                    #Generate random points inside the polygon
                    points.extend(geom.randomPointsInPolygon(random_points_per_feature, 23))

                col = BufferedTreesCollection()

                treesPerID = {}

                for i in range(len(points)):
                    id = id_labels[i]
                    point = points[i]

                    _pos : list[Position] = []
                    if id in treesPerID: 
                        _pos = treesPerID[id]
                    
                    _pos.append(Position(point.x() - taskData.mapAreaExtent.xMinimum() - 7168.0, point.y() - taskData.mapAreaExtent.yMinimum() - 7168.0))
                    treesPerID[id] = _pos

                    point_feature = QgsFeature()
                    point_feature.setGeometry(QgsGeometry.fromPointXY(point))
                    point_feature.setAttributes([str(id)])
                    data_provider.addFeature(point_feature)

                
                for _id, _positions in treesPerID.items():
                    col.BufferedTrees.append(BufferedTrees(_id, _positions))

                treesBIN.TreeCount += points_per_feature
                treesBIN.Buffers.append(col)

                points_layer.commitChanges()

        taskData.setGeneratedCount(treesBIN.TreeCount)
        
        writeBinaryFile(treesBIN, taskData.outputPath)
        #    xmlTree = serializeTreeXML(treesBIN)
        #    xmlTree.write(taskData.outputPath, encoding='utf-8', xml_declaration=True)

        #Create categorized symbology
        fieldCategories = []

        for index in range(len(taskData.fields)):
            #Define the style for the category
            layer_style = {}
            layer_style['color'] = taskData.fieldColors[index]
            layer_style['outline'] = "#000000"
            layer_style['size'] = "8.0"
            layer_style['size_unit'] = "MapUnit"
            layer_style['size_map_unit_scale'] = "0,1,0,0,0,0"
            point_symbol = QgsMarkerSymbol.createSimple(layer_style)

            #Create renderer category
            category = QgsRendererCategory(str(taskData.fieldIDS[index]), point_symbol.clone(), str(taskData.fields[index]))
            fieldCategories.append(category)

        renderer = QgsCategorizedSymbolRenderer('fieldType', fieldCategories)

        if points_layer is not None:
            taskData.setPointsLayer(points_layer, renderer)
        
    except Exception as e:
        print('{}: Error: {}'.format(CATEGORY, str(e)))
        traceback.print_exc()
        return None

    return taskData


def genComplete(task, taskData=None):
    if taskData is not None:
        time_end = datetime.now()
        eclipsed = (time_end - taskData.timeStart).total_seconds() / 60.0
        minutes = math.floor(eclipsed)
        seconds = math.floor((eclipsed - minutes) * 60)
        print('{}: Done generating {} trees for treesBIN file in {} minutes, {} seconds'.format(CATEGORY, taskData.generatedCount, minutes, seconds))

        if taskData.pointsLayer is not None:
            points_layer = taskData.pointsLayer
            QgsProject.instance().addMapLayer(points_layer)

            if taskData.renderer is not None:
                points_layer.setRenderer(taskData.renderer)
            points_layer.triggerRepaint()


if config_file_path.endswith(".json"):
    configError = False
    polygon_layer_name : str = None
    total_trees_count : int = None
    attributes : list[str] = None
    attributes_ids : list[int] = None
    attributes_colors : list[str] = None
    extent : list[int] = None
    treesBIN_path : str = None
    non_play_area_tree_count : int = None
    play_area_offset : int = None

    with open(config_file_path, "r") as jsonFile:
        try:
            jsonConfig : dict = json.load(jsonFile)
            vectorConfig : dict = jsonConfig['vector']

            polygon_layer_name = vectorConfig['polygon_layer']
            total_trees_count = vectorConfig['trees_count']
            attributes = vectorConfig['attributes']
            attributes_ids = jsonConfig['id_list']
            attributes_colors = jsonConfig['color_to_id']
            extent = vectorConfig['map_extent']
            treesBIN_path = jsonConfig['trees_bin_path']
            non_play_area_tree_count = vectorConfig['non_play_area_tree_count']
            play_area_offset = vectorConfig['play_area_offset']
        except Exception as ex:
            print('There was an error parsing the JSON config file:\n {}'.format(ex))
            configError = True

    if (configError is not True and 
        polygon_layer_name is not None and 
        total_trees_count is not None and 
        attributes is not None and 
        attributes_colors is not None and 
        attributes_ids is not None and
        extent is not None and
        treesBIN_path is not None and
        non_play_area_tree_count is not None and
        play_area_offset is not None):
    
        if extent[1] - extent[0] == 14336 and extent[2] - extent[3] == 14336:
            play_area_tree_count = total_trees_count - non_play_area_tree_count

            #Calculate play area extent [Left, Bottom, Right, Top]
            play_area_extent = QgsRectangle(extent[0] + play_area_offset, extent[3] + play_area_offset, extent[1] - play_area_offset, extent[2] - play_area_offset)
            map_area_extent = QgsRectangle(extent[0], extent[3], extent[1], extent[2])

            #Determine filename of the tree BIN file
            treesBIN_layer_name = Path(treesBIN_path).stem

            #Check if vector point layer already exists
            points_layers_name = '{ln}_points'.format(ln=treesBIN_layer_name)
            for l in QgsProject.instance().mapLayers():
                if l.startswith(points_layers_name):
                    QgsProject.instance().removeMapLayer(l)

            task_data = TaskData(polygon_layer_name, play_area_tree_count, non_play_area_tree_count, attributes, attributes_ids, attributes_colors, play_area_extent, map_area_extent, treesBIN_path, treesBIN_layer_name, points_layers_name, preview_mode)

            globals()['treesTask'] = QgsTask.fromFunction('Generate treesBIN file', genTreeBIN, on_finished=genComplete, taskData=task_data)
            QgsApplication.taskManager().addTask(globals()['treesTask'])
        else:
            print('{}: Extent is not 14336x14336 meters'.format(CATEGORY))
    else: 
        print('Make sure the JSON file is correctly formatted!')
else:
    print('Config file must be a json file!')
