import json
import os
from abc import ABC, abstractmethod

__APIKEYS_FILEPATH__ = os.path.join(os.path.dirname(__file__), 'apikeys.json')


class AbstractProvider(ABC):

    def __init__(self, title, name):
        self.title = title
        self.__name = name

    @abstractmethod
    def solve(self, start_point, end_point):
        pass

    def get_apikey(self):
        with open(__APIKEYS_FILEPATH__) as file:
            data = json.load(file)
            if not data[self.__name]:
                raise Exception('You must set API key for the selected service')

            return data[self.__name]

    def set_apikey(self, value):
        with open(__APIKEYS_FILEPATH__, 'r+') as file:
            data = json.load(file)
            print(data)
            data[self.__name] = value
            print(data)
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
