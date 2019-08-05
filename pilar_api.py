import requests

class ExceptionAPI(Exception):
    def __init__(self, error_id=None, msg=None):
        self.error_id = error_id
        self.msg = msg

class ExceptionPilarAPI(ExceptionAPI):
    pass

class RESTAPI:

    def __init__(self, api_key, password, url):
        self.api_key = password
        self.password = api_key
        self.url = url

    def _error_handling(self, r):
        if r.status_code == 200 or r.status_code == 201:
            return r.json()
        elif r.status_code == 400:
            raise ExceptionAPI(error_id=400, msg='Field "%s" is missing' % r.json().keys())
        elif r.status_code == 404:
            raise ExceptionAPI(error_id=404, msg='Page not found')
        else:
            raise ExceptionAPI('Error! Status code: %d, %s')

    def _write(self, endpoint, data):
        return requests.post(self.url + endpoint, json=data)

    def _read(self, endpoint):
        return requests.get(self.url + endpoint)

    def _update(self, endpoint, data):
        return requests.put(self.url + endpoint, json=data)

    def _delete(self, endpoint):
        return requests.delete(self.url + endpoint)

    def _modify(self, endpoint, data):
        return requests.patch(self.url + endpoint, json=data)


class PilarAPI(RESTAPI):

    def __init__(self):
        super().__init__('', '', 'https://pilar-sncn.boxfish.studio/')

        self.endpoints = [
            "articles",
            "articleTypes",
            "productionOrders",
            "assemblies",
            "reworks",
            "reworkActions",
            "tests",
            "testTypes",
            "testResults",
            "valueTypes",
            "values",
            "boxTypes",
            "boxes",
            "deliveries",
            "processLoops",
            "userTypes",
            "users",
            "stations",
            "stationTypes",
            "events",
            "settings",
        ]

    def search(self, endpoint, key):
        if not endpoint in self.endpoints:
            ExceptionPilarAPI('Endpoint "%s" not valid', endpoint)

        _list = self._read(endpoint)


