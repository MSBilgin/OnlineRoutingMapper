import json
from urllib.request import urlopen

from .abstract_provider import AbstractProvider


class Openrouteservice(AbstractProvider):

    def __init__(self):
        super().__init__('Openrouteservice Directions API', 'openrouteservice')

    def solve(self, start_point, end_point):
        start_point = ','.join(start_point.split(',')[::-1])
        end_point = ','.join(end_point.split(',')[::-1])
        url = 'https://api.openrouteservice.org/v2/directions/driving-car?start={0}&end={1}&api_key={2}' \
            .format(start_point, end_point, super().get_apikey())

        response = urlopen(url).read().decode("utf-8")

        response_data = json.loads(response)
        coordinates = response_data['features'][0]['geometry']['coordinates']

        useful_coordinates = []
        for i in coordinates:
            useful_coordinates.append(" ".join(map(str, i)))

        wkt = 'LineString(%s)' % (','.join(useful_coordinates))
        return wkt
