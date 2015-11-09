# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OnlineRoutingMapper
                                 A QGIS plugin
 Generate routes by using online services (Google Directions etc.)
                             -------------------
        begin                : 2015-10
        copyright            : (C) 2015 by Mehmet Selim BILGIN
        email                : mselimbilgin.yahoo.com
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
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load OnlineRoutingMapper class from file OnlineRoutingMapper.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .onlineroutingmapper import OnlineRoutingMapper
    
    return OnlineRoutingMapper(iface)
