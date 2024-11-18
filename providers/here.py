import json
from urllib.request import urlopen

from .abstract_provider import AbstractProvider
from .flexpolyline import decode


class Here(AbstractProvider):

    def __init__(self):
        super().__init__('HERE Routing API', 'here')

    def solve(self, start_point, end_point):
        url = 'https://router.hereapi.com/v8/routes?transportMode=car&traffic=enabled&origin={0}&destination={1}&return=polyline&apiKey={2}' \
            .format(start_point, end_point, super().get_apikey())
        response = urlopen(url).read().decode("utf-8")

        response_data = json.loads(response)
        encoded_polyline = response_data['routes'][0]['sections'][0]['polyline']
        decoded_polyline = decode(encoded_polyline)
        print(decoded_polyline)

        useful_coordinates = []
        for i in decoded_polyline:
            useful_coordinates.append('{0} {1} '.format(i[1], i[0]))

        wkt = 'LineString(%s)' % (','.join(useful_coordinates))
        return wkt
