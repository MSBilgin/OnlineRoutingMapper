# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OnlineRoutingMapper
                                 A QGIS plugin
 Generate routes by using online services (Google Directions etc.)
                              -------------------

        copyright            : (C) 2015 by Mehmet Selim BILGIN
        email                : mselimbilgin@yahoo.com
        web                  : cbsuygulama.wordpress.com
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

from routeprovider import RouteProvider

from qgis.gui import QgsMapToolEmitPoint
from qgis.core import *

import resources

from onlineroutingmapper_dialog import OnlineRoutingMapperDialog

import os,urllib2

class OnlineRoutingMapper(object):
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

    def clickHandler(self, QgsPoint):
        whichTextBox.setText(str(QgsPoint.x()) + ',' +str(QgsPoint.y()))
        self.dlg.showNormal()
        self.canvas.unsetMapTool(self.clickTool) #I dont need it no more. Let it free

    def toolActivator(self, QLineEdit):
        self.dlg.showMinimized()
        global whichTextBox
        whichTextBox = QLineEdit #I find this way to control it
        self.clickTool.canvasClicked.connect(self.clickHandler)
        self.canvas.setMapTool(self.clickTool) #clickTool is activated

    def crsTransform(self, inputPointStr):
        sourceCRS = self.canvas.mapSettings().destinationCrs() #getting the project CRS
        destinationCRS = QgsCoordinateReferenceSystem(4326) #google uses this CRS
        transformer = QgsCoordinateTransform(sourceCRS,destinationCRS) #defining a CRS transformer
        inputQgsPoint = QgsPoint(float(inputPointStr.split(',')[0]), float(inputPointStr.split(',')[1]))
        outputQgsPoint = transformer.transform(inputQgsPoint)

        return str(outputQgsPoint.y()) + ',' + str(outputQgsPoint.x())

    def checkNetConnection(self):
        try:
            urllib2.urlopen('http://www.google.com',timeout=7)
            return True
        except urllib2.URLError as err:
            pass
        return False

    def routeMaker(self, wktLineString):
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromWkt(wktLineString))
        vectorLayer = QgsVectorLayer('LineString?crs=epsg:4326', 'Routing Result', 'memory')
        layerProvider = vectorLayer.dataProvider()
        vectorLayer.startEditing()
        layerProvider.addFeatures([feature])
        vectorLayer.commitChanges()
        vectorLayer.updateExtents()
        vectorLayer.loadNamedStyle(self.plugin_dir + os.sep + 'OnlineRoutingMapper.qml')
        QgsMapLayerRegistry.instance().addMapLayer(vectorLayer)
        destinationCRS = self.canvas.mapSettings().destinationCrs() #getting the project CRS
        sourceCRS = QgsCoordinateReferenceSystem(4326)
        transformer = QgsCoordinateTransform(sourceCRS,destinationCRS)
        extentForZoom = transformer.transform(vectorLayer.extent())
        self.canvas.setExtent(extentForZoom)
        self.canvas.zoomScale(self.canvas.scale()*1.03) #zoom out a little bit.
        QMessageBox.information(self.dlg, 'Information' ,'The analysis result was added to the canvas.')


    def runAnalysis(self):
        if len(self.dlg.startTxt.text())>0 and len(self.dlg.stopTxt.text())>0:
            if self.checkNetConnection():
                startPoint = self.crsTransform(self.dlg.startTxt.text())
                stopPoint = self.crsTransform(self.dlg.stopTxt.text())

                if self.dlg.serviceCombo.currentIndex() == 0: #google
                    try:
                        wkt,url = self.routeEngine.google(startPoint,stopPoint)
                        # these comment lines maybe useful for debugging.
                        # QgsMessageLog.logMessage(url)
                        # QgsMessageLog.logMessage(wkt)
                        self.routeMaker(wkt)
                    except Exception as err:
                        QgsMessageLog.logMessage(str(err))
                        QMessageBox.warning(self.dlg,'Analysis Error',
                                            "Cannot calculate the route between the start and stop locations that you entered. Please use other Service APIs.")

                elif self.dlg.serviceCombo.currentIndex() == 1: #here
                    try:
                        wkt,url = self.routeEngine.here(startPoint,stopPoint)
                        # QgsMessageLog.logMessage(url)
                        # QgsMessageLog.logMessage(wkt)
                        self.routeMaker(wkt)
                    except Exception as err:
                        QgsMessageLog.logMessage(str(err))
                        QMessageBox.warning(self.dlg,'Analysis Error',
                                            "Cannot calculate the route between the start and stop locations that you entered. Please use other Service APIs.")

                elif self.dlg.serviceCombo.currentIndex() == 2: #yourNavigation
                    try:
                        wkt,url = self.routeEngine.yourNavigation(startPoint,stopPoint)
                        # QgsMessageLog.logMessage(url)
                        # QgsMessageLog.logMessage(wkt)
                        self.routeMaker(wkt)
                    except Exception as err:
                        QgsMessageLog.logMessage(str(err))
                        QMessageBox.warning(self.dlg,'Analysis Error',
                                            "Cannot calculate the route between the start and stop locations that you entered. Please use other Service APIs.")

                elif self.dlg.serviceCombo.currentIndex() == 3: #mapbox
                    try:
                        wkt,url = self.routeEngine.mapBox(startPoint,stopPoint)
                        # QgsMessageLog.logMessage(url)
                        # QgsMessageLog.logMessage(wkt)
                        self.routeMaker(wkt)
                    except Exception as err:
                        QgsMessageLog.logMessage(str(err))
                        QMessageBox.warning(self.dlg,'Analysis Error',
                                            "Cannot calculate the route between the start and stop locations that you entered. Please use other Service APIs.")

                elif self.dlg.serviceCombo.currentIndex() == 4: #grapHopper
                    try:
                        wkt,url = self.routeEngine.graphHopper(startPoint,stopPoint)
                        # QgsMessageLog.logMessage(url)
                        # QgsMessageLog.logMessage(wkt)
                        self.routeMaker(wkt)
                    except Exception as err:
                        QgsMessageLog.logMessage(str(err))
                        QMessageBox.warning(self.dlg,'Analysis Error',
                                            "Cannot calculate the route between the start and stop locations that you entered. Please use other Service APIs.")

                elif self.dlg.serviceCombo.currentIndex() == 5: #tomtom
                    try:
                        wkt,url = self.routeEngine.tomtom(startPoint,stopPoint)
                        # QgsMessageLog.logMessage(url)
                        # QgsMessageLog.logMessage(wkt)
                        self.routeMaker(wkt)
                    except Exception as err:
                        QgsMessageLog.logMessage(str(err))
                        QMessageBox.warning(self.dlg,'Analysis Error',
                                            "Cannot calculate the route between the start and stop locations that you entered. Please use other Service APIs.")

                elif self.dlg.serviceCombo.currentIndex() == 6: #mapQuest
                    try:
                        wkt, url = self.routeEngine.mapQuest(startPoint, stopPoint)
                        # QgsMessageLog.logMessage(url)
                        # QgsMessageLog.logMessage(wkt)
                        self.routeMaker(wkt)
                    except Exception as err:
                        QgsMessageLog.logMessage(str(err))
                        QMessageBox.warning(self.dlg, 'Analysis Error',
                                            "Cannot calculate the route between the start and stop locations that you entered. Please use other Service APIs.")

                elif self.dlg.serviceCombo.currentIndex() == 7: #mapQuest
                    try:
                        wkt, url = self.routeEngine.osrm(startPoint, stopPoint)
                        # QgsMessageLog.logMessage(url)
                        # QgsMessageLog.logMessage(wkt)
                        self.routeMaker(wkt)
                    except Exception as err:
                        QgsMessageLog.logMessage(str(err))
                        QMessageBox.warning(self.dlg, 'Analysis Error',
                                            "Cannot calculate the route between the start and stop locations that you entered. Please use other Service APIs.")

            else:
                QMessageBox.warning(self.dlg, 'Network Error!', 'There is no internet connection.')
        else:
            QMessageBox.information(self.dlg,'Warning', 'Please choose Start Location and Stop Location.')

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
        self.routeEngine = RouteProvider()
        self.canvas = self.iface.mapCanvas()
        self.dlg = OnlineRoutingMapperDialog()
        self.dlg.setFixedSize(self.dlg.size())
        self.clickTool = QgsMapToolEmitPoint(self.canvas) #clicktool instance generated in here.
        self.dlg.startBtn.clicked.connect(lambda : self.toolActivator(self.dlg.startTxt))
        self.dlg.stopBtn.clicked.connect(lambda : self.toolActivator(self.dlg.stopTxt))
        self.dlg.runBtn.clicked.connect(self.runAnalysis)

        self.dlg.show()
