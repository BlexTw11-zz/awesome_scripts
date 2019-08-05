import requests

class ExceptionAPI(Exception):
    def __init__(self, http_status=None, error_id=None, msg=None, response=None, missing_keys=None):
        self.http_status = http_status
        self.error_id = error_id
        self.msg = msg
        self._response = response
        self._keys = missing_keys

    def __str__(self):
        _m = ''
        if self.msg:
            _m += '%s' % self.msg
        if self.http_status:
            _m += '\nHTTP Status: %d' % self.http_status
        if self.error_id:
            _m += '\nError ID: %d' % self.error_id
        if self._keys:
            _m += '\nMissing keys: %s' % self._keys
        return _m

    @property
    def response(self):
        return self._response

    @property
    def missing_keys(self):
        return self._keys


class ExceptionPilarAPI(ExceptionAPI):
    pass

class RESTAPI:

    def __init__(self, api_key, password, url):
        self.api_key = password
        self.password = api_key
        self.url = url

    def _handle_response(self, r):
        if r.status_code == 200 or r.status_code == 201:
            return r.json()
        elif r.status_code == 204:
            return r
        elif r.status_code == 400:
            raise ExceptionAPI(http_status=400, msg='Field is missing', missing_keys=list(r.json().keys()) )
        elif r.status_code == 404:
            raise ExceptionAPI(http_status=404, msg='Page not found')
        else:
            raise ExceptionAPI(http_status=r.status_code, msg='Unknown error', response=r)

    def _write(self, endpoint, data):
        if endpoint[:-1] != '/':
            endpoint += '/'
        return self._handle_response(requests.post(self.url + endpoint, json=data))

    def _read(self, endpoint):
        if endpoint[:-1] != '/':
            endpoint += '/'
        return self._handle_response(requests.get(self.url + endpoint))

    def _update(self, endpoint, data):
        if endpoint[:-1] != '/':
            endpoint += '/'
        return self._handle_response(requests.put(self.url + endpoint, json=data))

    def _delete(self, endpoint):
        if endpoint[:-1] != '/':
            endpoint += '/'
        return self._handle_response(requests.delete(self.url + endpoint))

    def _modify(self, endpoint, data):
        if endpoint[:-1] != '/':
            endpoint += '/'
        return self._handle_response(requests.patch(self.url + endpoint, json=data))


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

    def search(self, endpoint, item=None, key_value=None):
        if not endpoint in self.endpoints:
            raise ExceptionPilarAPI(msg='Endpoint "%s" is not valid' % endpoint)
        _list = self._read(endpoint)
        res = []
        for e in _list:
            if item:
                for k, v in e.items():
                    if item == v:
                        res.append(e)
            elif key_value:
                _item = e.get(list(key_value.keys())[0])
                if _item and _item == list(key_value.values())[0]:
                    res.append(e)
        return res

    def get(self, endpoint, id=None):
        try:
            if id:
                endpoint += '/{}/'.format(id)
            return self._read(endpoint)

        except ExceptionAPI as e:
            if e.http_status == 404:
                return None
            else:
                raise e

    def delete(self, endpoint, id):
        try:
            self._delete(endpoint + '/{}/'.format(id))
            return True
        except ExceptionAPI as e:
            if e.http_status == 404:
                return False
            else:
                raise e

    def add(self, endpoint, data):
        try:
            self._write(endpoint, data)
            return True
        except ExceptionAPI as e:
            if e.http_status == 400:
                for k in e.missing_keys:
                    if data.get(k):
                        raise ExceptionPilarAPI(error_id=1, msg='%s = %s already in list' % (k, data[k]), missing_keys=e.missing_keys) from e
            raise e

    def update(self, endpoint, id, data):
        try:
            self._update(endpoint + '/{}/'.format(id), data)
            return True
        except ExceptionAPI as e:
            if e.http_status == 404:
                return False
            else:
                raise e





