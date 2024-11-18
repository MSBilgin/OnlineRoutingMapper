import json
from urllib.request import urlopen

from .abstract_provider import AbstractProvider


class GraphHopper(AbstractProvider):

    def __init__(self):
        super().__init__('GraphHopper Directions API', 'graphhopper')

    def solve(self, start_point, end_point):
        url = 'https://graphhopper.com/api/1/route?point={0}&point={1}' \
              '&profile=car&locale=en&calc_points=true&points_encoded=false&instructions=false&key={2}' \
            .format(start_point, end_point, super().get_apikey())
        response = urlopen(url).read().decode("utf-8")

        response_data = json.loads(response)
        coordinates = response_data['paths'][0]['points']['coordinates']

        useful_coordinates = []
        for i in coordinates:
            useful_coordinates.append(" ".join(map(str, i)))

        wkt = 'LineString(%s)' % (','.join(useful_coordinates))
        return wkt
