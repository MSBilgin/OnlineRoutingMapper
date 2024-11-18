import json
from urllib.request import urlopen

from .abstract_provider import AbstractProvider


class TomTom(AbstractProvider):

    def __init__(self):
        super().__init__('TomTom Routing API', 'tomtom')

    def solve(self, start_point, end_point):
        url = 'https://api.tomtom.com/routing/1/calculateRoute/{0}:{1}/jsonp?key={2}&traffic=true'\
            .format(start_point, end_point, super().get_apikey())
        response = urlopen(url).read().decode("utf-8")

        response_data = json.loads(response[9:-1])
        coors = response_data['routes'][0]['legs'][0]['points']

        useful_coor_list = []
        for i in coors:
            useful_coor_list.extend([i['longitude'], i['latitude']])

        coor_pair = [useful_coor_list[i:i + 2] for i in range(0, len(useful_coor_list), 2)]
        useful_poly = []
        for i in coor_pair:
            useful_poly.append(" ".join(map(str, i)))
        wkt = 'LineString(%s)' % (','.join(useful_poly))
        return wkt
