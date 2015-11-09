# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OnlineRoutingMapper
                                 A QGIS plugin
 Generate routes by using online services (Google Directions etc.)
                              -------------------
        begin                : 2015-10
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Mehmet Selim BILGIN
        email                : mselimbilgin@yahoo.com
        web					 : http://cbsuygulama.wordpress.com		
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from qgis.gui import *
from qgis.core import *

import resources

from onlineroutingmapper_dialog import OnlineRoutingMapperDialog

import os, urllib2, json, datetime
from xml.dom import minidom


class OnlineRoutingMapper:
    def __init__(self, iface):
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Online Routing Mapper')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'OnlineRoutingMapper')
        self.toolbar.setObjectName(u'OnlineRoutingMapper')

    def tr(self, message):
        return QCoreApplication.translate('OnlineRoutingMapper', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
   

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        icon_path = self.plugin_dir + os.sep + 'icon.png'

        self.add_action(
            icon_path,
            text=self.tr(u'Online Routing Mapper'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def clickHandler(self, point):
        whichTextBox.setText(str(point.x()) + ',' +str(point.y()))
        self.dlg.showNormal()
        self.canvas.unsetMapTool(self.clickTool) #I dont need it no more. Let it free

    def toolIActivator(self, txtbox):
        self.dlg.showMinimized()
        global whichTextBox
        whichTextBox = txtbox #I find this way to control it
        self.clickTool.canvasClicked.connect(self.clickHandler) #sending signals to the function
        self.canvas.setMapTool(self.clickTool) #clickTool is activated

    def crsTransform(self, inputPointStr, startOrstop):
        sourceCRS = self.canvas.mapSettings().destinationCrs() #getting the project CRS
        destinationCRS = QgsCoordinateReferenceSystem(4326) #google uses this CRS
        transformer = QgsCoordinateTransform(sourceCRS,destinationCRS) #defining a CRS transformer
        inputQgsPoint = QgsPoint(float(inputPointStr.split(',')[0]), float(inputPointStr.split(',')[1]))
        outputQgsPoint = transformer.transform(inputQgsPoint)

        if startOrstop == 1:
            self.startPoint = str(outputQgsPoint.y()) + ',' + str(outputQgsPoint.x())
        else:
            self.stopPoint = str(outputQgsPoint.y()) + ',' + str(outputQgsPoint.x())
        # QMessageBox.information(None,'1', inputQgsPoint.toString() + '---' + lonlatpoint)

    def checkNetConnection(self):
        try:
            urllib2.urlopen('http://www.google.com',timeout=3)
            return True
        except urllib2.URLError as err:
            pass
        return False

    def getData(self, origin, destination):
        url =''
        dataType = ''
        if self.dlg.serviceCombo.currentText() == 'Google Direction API':
            url = 'https://maps.googleapis.com/maps/api/directions/json?origin=' + origin + '&destination=' + destination + '&mode=driving'
            dataType = 'json'
        elif self.dlg.serviceCombo.currentText() == 'HERE Routing API':
            now = datetime.datetime.now()
            departureParameter = str(now.year)+'-'+str('%02d' % now.month) +'-'+ str('%02d' % now.day)+'T'+str('%02d' % now.hour)+':'+str('%02d' % now.minute)+':'+str('%02d' % now.second)
            url = 'https://route.api.here.com/routing/7.2/calculateroute.json?alternatives=0&app_code=djPZyynKsbTjIUDOBcHZ2g&app_id=xWVIueSv6JL0aJ5xqTxb&departure=' + departureParameter + '&jsonAttributes=41&language=en_US&legattributes=all&linkattributes=none,sh,ds,rn,ro,nl,pt,ns,le&maneuverattributes=all&metricSystem=imperial&mode=fastest;car;traffic:enabled;&routeattributes=none,sh,wp,sm,bb,lg,no,li,tx&transportModeType=car&waypoint0=geo!' + origin + '&waypoint1=geo!' + destination
            dataType = 'json'
        elif self.dlg.serviceCombo.currentText() == 'YourNavigation API':
            url = 'http://www.yournavigation.org/api/dev/route.php?flat=' +  origin.split(',')[0] + '&flon=' + origin.split(',')[1] + '&tlat=' + destination.split(',')[0] + '&tlon=' + destination.split(',')[1] + '&v=motorcar&fast=0&layer=mapnik&instructions=0'
            dataType = 'xml'

        try:
             response = urllib2.urlopen(url)
             if dataType == 'json':
                 return json.loads(response.read())
             elif dataType == 'xml':
                 return minidom.parseString(response.read())
        except Exception as err:
            QMessageBox.warning(None, 'Error!', err.msg)
            return False

    def coorOrganizer(self, input):
        #Coordinates in [1.2, 5.7, 6.8, 9.1] style is converted to LineString (LineString(1.2 5.7, 6.8 9.1)) style by this function.
        coorPair = [input[i:i + 2] for i in range(0, len(input), 2)]
        usefulPoly = []
        for i in coorPair:
            usefulPoly.append(" ".join(map(str, i)))
        wkt = 'LineString(' + ','.join(usefulPoly) +')'
        return wkt

    def routeMaker(self, responseData):
        wktPolyline = '' #the object that inserted into the line feature

        if self.dlg.serviceCombo.currentText() == 'Google Direction API':
            polylines = []
            steps = responseData['routes'][0]['legs'][0]['steps']
            for i in steps:
                polylines.append(self.gPolyDecode(str(i['polyline']['points'])))

        #A polyline includes several lines. Every line has start and stop point.
        #First line's stop point is second line's start point. So this causes duplication.
        #In here I clear them except first line.
            for i in polylines[1:]:
                i.pop(0)

            usefulCoorList = []
            for i in polylines:
                for j in i:
                    usefulCoorList.extend(j)

            wktPolyline = self.coorOrganizer(usefulCoorList)
            # wktPolyline = 'LineString('
            #
            # for i in usefulPoly:
            #         wktPolyline += ' '.join(map(str, i)) + ','
            # wktPolyline = wktPolyline[:-1] + ')'

        elif self.dlg.serviceCombo.currentText() == 'HERE Routing API':
            #HERE API's response coordinates are reverse so this problem is handled in here.
            coors = responseData['response']['route'][0]['shape']
            coorPair = [coors[i:i + 2] for i in range(0, len(coors), 2)]
            usefulCoorList = []
            for i in coorPair:
                i.reverse()
                usefulCoorList.extend(i)
            wktPolyline = self.coorOrganizer(usefulCoorList)

        elif self.dlg.serviceCombo.currentText() == 'YourNavigation API':
            coors = responseData.getElementsByTagName('coordinates')[0].firstChild.nodeValue.strip()
            commaCoors = coors.replace('\n',',')
            usefulCoorList = []
            for i in commaCoors.split(','):
                usefulCoorList.append(float(i))

            wktPolyline = self.coorOrganizer(usefulCoorList)

        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromWkt(wktPolyline))
        vectorLayer = QgsVectorLayer('LineString?crs=epsg:4326', 'Routing Result', 'memory')
        layerProvider = vectorLayer.dataProvider()
        vectorLayer.startEditing()
        layerProvider.addFeatures([feature])
        vectorLayer.commitChanges()
        vectorLayer.updateExtents()
        vectorLayer.loadNamedStyle(self.plugin_dir + os.sep + 'OnlineRoutingMapper.qml')
        QgsMapLayerRegistry.instance().addMapLayer(vectorLayer)
        QMessageBox.information(None, 'Information' ,'The analysis result was added to the canvas.')
        destinationCRS = self.canvas.mapSettings().destinationCrs() #getting the project CRS
        sourceCRS = QgsCoordinateReferenceSystem(4326)
        transformer = QgsCoordinateTransform(sourceCRS,destinationCRS)
        extentForZoom = transformer.transform(vectorLayer.extent())
        self.canvas.setExtent(extentForZoom)
        self.canvas.zoomScale(self.canvas.scale()*1.03) #zoom out a little bit.

    #Google's encoded polyline decoder algorithm. Inspired by MapBox polyline.js JavaScript library.
    def gPolyDecode(self, encodedPolyline):
        index = 0
        lat = 0
        lng = 0
        coordinates = []
        factor = 1e5

        while index < len(encodedPolyline):
            shift = 0
            result = 0

            while True:
                byte = ord(encodedPolyline[index]) -63
                result = result | ((byte & 0x1f) << shift)
                shift += 5
                index += 1
                if not (byte >= 0x20):
                    break

            if (result & 1):
                latitude_change = ~(result >> 1)
            else:
                latitude_change = result >> 1

            shift = result = 0 #resetting variables

            while True:
                byte = ord(encodedPolyline[index]) -63
                result = result | ((byte & 0x1f) << shift)
                shift += 5
                index += 1
                if not (byte >= 0x20):
                    break

            if (result & 1):
                longitude_change = ~(result >> 1)
            else:
                longitude_change = result >> 1

            lat += float(latitude_change)
            lng += float(longitude_change)

            coordinates.append([lng/factor, lat/factor])

        return coordinates

    def runAnalysis(self):
        if len(self.dlg.startTxt.text())>0 and len(self.dlg.stopTxt.text())>0:
            if self.checkNetConnection():
                resultData = self.getData(self.startPoint,self.stopPoint) #getting service result
                if self.dlg.serviceCombo.currentText() == 'Google Direction API':
                    if resultData['status'] == 'OK':
                        self.routeMaker(resultData)
                    elif resultData['status'] == 'ZERO_RESULTS':
                        QMessageBox.warning(None,'Analysis Error',"Cannot calculate the route between the start and stop locations that you entered. Plesase use other Service APIs.")
                    elif resultData['status'] == 'OVER_QUERY_LIMIT':
                        QMessageBox.information(None,'Blocked by Google', 'Please re-run the analysis to get result.')

                elif self.dlg.serviceCombo.currentText() == 'HERE Routing API':
                    try:
                        self.routeMaker(resultData)
                    except:
                        QMessageBox.warning(None,'Analysis Error',"Cannot calculate the route between the start and stop locations that you entered. Plesase use other Service APIs.")

                elif self.dlg.serviceCombo.currentText() == 'YourNavigation API':
                    coors = resultData.getElementsByTagName('coordinates')[0].firstChild.nodeValue.strip()

                    if coors == '':
                        QMessageBox.warning(None,'Analysis Error',"Cannot calculate the route between the start and stop locations that you entered. Plesase use other Service APIs.")
                    else:
                        self.routeMaker(resultData)

            else:
                QMessageBox.warning(None, 'Network Error!', 'There is no internet connection.')
        else:
            QMessageBox.information(None,'Warning', 'Please choose Start Location and Stop Location.')

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Online Routing Mapper'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):

        self.canvas = self.iface.mapCanvas()
        self.dlg = OnlineRoutingMapperDialog()
        self.clickTool = QgsMapToolEmitPoint(self.canvas) #clicktool instance generated in here.
        self.dlg.startBtn.clicked.connect(lambda : self.toolIActivator(self.dlg.startTxt))
        self.dlg.stopBtn.clicked.connect(lambda : self.toolIActivator(self.dlg.stopTxt))
        self.dlg.runBtn.clicked.connect(self.runAnalysis)

        #these two variables are used for holding start and stop lanlot points.
        self.startPoint = ''
        self.stopPoint = ''
        self.dlg.startTxt.textChanged.connect(lambda: self.crsTransform(self.dlg.startTxt.text(), 1))
        self.dlg.stopTxt.textChanged.connect(lambda: self.crsTransform(self.dlg.stopTxt.text(), 2))

        self.dlg.setFixedSize(450,390)
        self.dlg.show()
