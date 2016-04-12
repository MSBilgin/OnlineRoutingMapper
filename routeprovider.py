# -*- coding: utf-8 -*-
"""
/***************************************************************************
 routeprovider
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

import urllib2, json, datetime
from xml.dom import minidom

class RouteProvider(object):
    def __init__(self):
        self.__googleBaseURL__ = 'https://maps.googleapis.com/maps/api/directions/json?origin=%s&destination=%s&mode=driving'
        self.__yourNavigationBaseURL__ = 'http://www.yournavigation.org/api/dev/route.php?flat=%s&flon=%s&tlat=%s&tlon=%s&v=motorcar&fast=0&layer=mapnik&instructions=0'
        self.__hereBaseURL__ ='https://route.api.here.com/routing/7.2/calculateroute.json?alternatives=0&app_code=djPZyynKsbTjIUDOBcHZ2g&app_id=xWVIueSv6JL0aJ5xqTxb&departure=%s&jsonAttributes=41&language=en_US&legattributes=all&linkattributes=none,sh,ds,rn,ro,nl,pt,ns,le&maneuverattributes=all&metricSystem=imperial&mode=fastest;car;traffic:enabled;&routeattributes=none,sh,wp,sm,bb,lg,no,li,tx&transportModeType=car&waypoint0=geo!%s&waypoint1=geo!%s'
        self.__mapBoxBaseURL__ = 'https://api.tiles.mapbox.com/v4/directions/mapbox.driving/%s;%s.json?instructions=json&geometry=linestring&access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpbG10dnA3NzY3OTZ0dmtwejN2ZnUycjYifQ.1W5oTOnWXQ9R1w8u3Oo1yA'
        self.__graphHopperBaseURL__ = 'https://graphhopper.com/api/1/route?point=%s&point=%s&type=json&key=016f1b38-62f0-4a2b-88f7-dc5b743a9b56&locale=en-US&vehicle=car&weighting=fastest&elevation=false'
        self.__tomtomBaseURL__ = 'https://api.tomtom.com/routing/1/calculateRoute/%s:%s/jsonp?key=hpygzp67548xfpk69qsfwqng&traffic=false&report=effectiveSettings&travelMode=car&instructionsType=tagged&language=en-gb'
        self.__mapQuestBaseURL__ ='http://www.mapquest.com/alternateroutes?key=Cmjtd%7Cluur2108n1%2C7w%3Do5-gz8a&json={"locations":[{"latLng":{"lat":%s,"lng":%s}},{"latLng":{"lat":%s,"lng":%s}}],"maxRoutes":3,"timeOverage":99,"options":{"doReverseGeocode":false,"routeType":"fastest","enhancedNarrative":true,"narrativeType":"microformat","avoids":[],"conditionsAheadDistance":"200.00","generalize":0,"shapeFormat":"cmp6"}}'
        self.__osrmBaseURL__ = 'http://router.project-osrm.org/viaroute?instructions=false&alt=true&z=18&loc=%s&loc=%s'
        self.__serviceType__ = -1 #holds service type (google,here etc...)

    def google(self, startPoint=str, endPoint=str):
        self.__serviceType__ = 0
        url = self.__googleBaseURL__ %(startPoint,endPoint)
        response = urllib2.urlopen(url).read()
        return self.__wktMaker__(response),url

    def here(self, startPoint=str, endPoint=str):
        self.__serviceType__ = 1
        now = datetime.datetime.now()
        bingDepartureParameter = str(now.year)+'-'+str('%02d' % now.month) +'-'+ str('%02d' % now.day)+'T'+str('%02d' % now.hour)+':'+str('%02d' % now.minute)+':'+str('%02d' % now.second)
        url = self.__hereBaseURL__ %(bingDepartureParameter, startPoint,endPoint)
        response = urllib2.urlopen(url).read()
        return self.__wktMaker__(response),url

    def yourNavigation(self, startPoint=str, endPoint=str):
        self.__serviceType__ = 2
        url = self.__yourNavigationBaseURL__ %(startPoint.split(',')[0],startPoint.split(',')[1],endPoint.split(',')[0],endPoint.split(',')[1])
        response = urllib2.urlopen(url).read()
        return self.__wktMaker__(response),url

    def mapBox(self, startPoint=str, endPoint=str):
        self.__serviceType__ = 3
        url = self.__mapBoxBaseURL__ %(startPoint.split(',')[1] + ',' + startPoint.split(',')[0],endPoint.split(',')[1] + ',' + endPoint.split(',')[0])

        response = urllib2.urlopen(url).read()
        return self.__wktMaker__(response),url

    def graphHopper(self, startPoint=str, endPoint=str):
        self.__serviceType__ = 4
        url = self.__graphHopperBaseURL__ %(startPoint,endPoint)
        response = urllib2.urlopen(url).read()
        return self.__wktMaker__(response),url

    def tomtom(self, startPoint=str, endPoint=str):
        self.__serviceType__ = 5
        url = self.__tomtomBaseURL__ %(startPoint,endPoint)
        response = urllib2.urlopen(url).read()
        return self.__wktMaker__(response),url

    def mapQuest(self, startPoint=str, endPoint=str):
        self.__serviceType__ = 6
        address = self.__mapQuestBaseURL__[:self.__mapQuestBaseURL__.index('json=')+5]
        jsonParameter = self.__mapQuestBaseURL__[self.__mapQuestBaseURL__.index('json=')+5:] %(startPoint.split(',')[0],startPoint.split(',')[1],endPoint.split(',')[0],endPoint.split(',')[1])
        url = address + urllib2.quote(jsonParameter) #url must be encoded before request.
        response = urllib2.urlopen(url).read()
        return self.__wktMaker__(response), url

    def osrm(self, startPoint=str, endPoint=str):
        self.__serviceType__ = 7
        url = self.__osrmBaseURL__ % (startPoint, endPoint)
        response = urllib2.urlopen(url).read()
        return self.__wktMaker__(response), url

    #Google's encoded polyline decoder algorithm. Translated to Python from MapBox polyline.js JavaScript library.
    #Also works with GrapHopper encoded polyline and MapQuest encoded polyline
    def __gPolyDecode__(self, encodedPolyline=str, precision=int):
        index = 0
        lat = 0
        lng = 0
        coordinates = []
        factor = pow(10,precision)

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

    def __coorOrganizer__(self, input=str):
        #Coordinates in [1.2, 5.7, 6.8, 9.1] style is converted to LineString(1.2 5.7, 6.8 9.1) style by this function.
        coorPair = [input[i:i + 2] for i in range(0, len(input), 2)]
        usefulPoly = []
        for i in coorPair:
            usefulPoly.append(" ".join(map(str, i)))
        wkt = 'LineString(%s)' %(','.join(usefulPoly))
        return wkt

    def __wktMaker__(self, response=str):
        #this function generates route as WKT LineString from web service's response
        if self.__serviceType__ == 0: #google JSON
            responseData = json.loads(response)
            polylines = []
            steps = responseData['routes'][0]['legs'][0]['steps']
            for i in steps:
                polylines.append(self.__gPolyDecode__(str(i['polyline']['points']), 5))

            for i in polylines[1:]:
                i.pop(0)

            usefulCoorList = []
            for i in polylines:
                for j in i:
                    usefulCoorList.extend(j)

            return self.__coorOrganizer__(usefulCoorList)

        elif self.__serviceType__ == 1: #here JSON
            responseData = json.loads(response)
            coors = responseData['response']['route'][0]['shape']
            coorPair = [coors[i:i + 2] for i in range(0, len(coors), 2)]
            usefulCoorList = []
            for i in coorPair:
                i.reverse()
                usefulCoorList.extend(i)
            return  self.__coorOrganizer__(usefulCoorList)

        elif self.__serviceType__ == 2: #yourNavigation XML
            responseData = minidom.parseString(response)
            coors = responseData.getElementsByTagName('coordinates')[0].firstChild.nodeValue.strip()
            commaCoors = coors.replace('\n',',')
            usefulCoorList = []
            for i in commaCoors.split(','):
                usefulCoorList.append(float(i))

            return self.__coorOrganizer__(usefulCoorList)

        elif self.__serviceType__ == 3: #mapbox JSON
            responseData = json.loads(response)
            coors = responseData['routes'][0]['geometry']['coordinates']
            usefulCoorList = []
            for i in coors:
                usefulCoorList.extend(i)
            return self.__coorOrganizer__(usefulCoorList)

        elif self.__serviceType__ == 4: #graphHopper JSON
            responseData = json.loads(response)
            polylines = []
            encodePolyline = responseData['paths'][0]['points']
            polylines.extend(self.__gPolyDecode__(encodePolyline, 5))

            usefulCoorList = []
            for i in polylines:
                usefulCoorList.extend(i)

            return self.__coorOrganizer__(usefulCoorList)

        elif self.__serviceType__ == 5: #tomtom JSON
            responseData = json.loads(response[9:-1])
            coors = responseData['routes'][0]['guidance']['instructions']
            usefulCoorList = []
            for i in coors:
                usefulCoorList.extend([i['point']['longitude'], i['point']['latitude']])
            return self.__coorOrganizer__(usefulCoorList)

        elif self.__serviceType__ == 6:  #mapQuest json
            responseData = json.loads(response)
            encodePolyline = responseData['route']['shape']['shapePoints'] #this string is encoded by mapQuest algorithm
            polylines = []
            polylines.extend(self.__gPolyDecode__(encodePolyline, 6)) #mapquest use one more precision

            usefulCoorList = []
            for i in polylines:
                usefulCoorList.extend(i)

            return self.__coorOrganizer__(usefulCoorList)

        elif self.__serviceType__ == 7:  # mapQuest json
            responseData = json.loads(response)
            encodePolyline = responseData['route_geometry']
            polylines = []
            polylines.extend(self.__gPolyDecode__(encodePolyline, 6))  # mapquest use one more precision

            usefulCoorList = []
            for i in polylines:
                usefulCoorList.extend(i)

            return self.__coorOrganizer__(usefulCoorList)