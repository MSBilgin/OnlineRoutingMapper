import json
from urllib.request import urlopen

from .abstract_provider import AbstractProvider
from .polyline_decoder import PolylineDecoder


class Atlas(AbstractProvider):

    def __init__(self):
        super().__init__('Atlas Routing API', 'atlas')

    def solve(self, start_point, end_point):
        start_point = ','.join(start_point.split(',')[::-1])
        end_point = ','.join(end_point.split(',')[::-1])
        url = 'https://atlas.harita.gov.tr/analiz/rota/route/v1/driving/{0};{1}.json' \
            .format(start_point, end_point)
        response = urlopen(url).read().decode("utf-8")

        response_data = json.loads(response)
        encoded_polyline = response_data['routes'][0]['geometry']       
        decoded_polyline = PolylineDecoder.decode(encoded_polyline)
        
        useful_coordinates = []
        for i in decoded_polyline:
            useful_coordinates.append('{0} {1} '.format(i[1], i[0]))

        wkt = 'LineString(%s)' % (','.join(useful_coordinates))
        return wkt
