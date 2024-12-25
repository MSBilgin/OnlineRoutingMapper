import json
from urllib.request import urlopen

from .abstract_provider import AbstractProvider


class Yandex(AbstractProvider):

    def __init__(self):
        super().__init__('Yandex.Routing', 'yandex')

    def solve(self, start_point, end_point):
        url = 'https://api.routing.yandex.net/v2/route?waypoints={0}|{1}&mode=driving&apikey={2}'\
            .format(start_point, end_point, super().get_apikey())

        response = urlopen(url).read().decode("utf-8")

        response_data = json.loads(response)
        steps = response_data['route']['legs'][0]['steps']

        useful_coor_list = []
        for i in steps:
            points = i['polyline']['points']
            for j in points:
                j.reverse()
                useful_coor_list.extend(j)

        coor_pair = [useful_coor_list[i:i + 2] for i in range(0, len(useful_coor_list), 2)]
        useful_poly = []
        for i in coor_pair:
            useful_poly.append(" ".join(map(str, i)))
        wkt = 'LineString(%s)' % (','.join(useful_poly))
        return wkt