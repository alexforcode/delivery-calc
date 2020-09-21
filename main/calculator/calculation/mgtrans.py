import json

import requests

# TODO: comments
class MtransAPI:
    def __init__(self):
        self.base_api_url = 'http://magic-trans.ru/api/v1'
        self.request_headers = {'Content-Type': 'application/json'}

    def get_city_id(self, city: str):
        """ Return city id
        city: city name
        """
        url = f'{self.base_api_url}/dictionary/getCityList'
        resp = requests.get(url, headers=self.request_headers, params={'name': city.lower()})

        if resp.status_code == 200:
            resp_json = resp.json()
            print(resp_json)
            try:
                city_id = resp_json['result'][0]['id']
                return city_id
            except IndexError or KeyError:
                return None

        return None

    def calculate(self, body: dict):
        """ Return result of calculation in json format
        body: data for request
        """
        url = f'{self.base_api_url}/delivery/calculate'
        resp = requests.get(url, headers=self.request_headers, params=body)

        if resp.status_code == 200:
            return resp.json()

        return None


def get_request_body(api, delivery_info: dict):
    """ Return final body for request to gtd API
    apikey: API key for app
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    """
    body = {
        'from': api.get_city_id(delivery_info['derival_city']),
        'to': api.get_city_id(delivery_info['arrival_city']),
        'items': [
            {
                'count': 1,
                'weight': delivery_info['cargo']['weight'],
                'volume': delivery_info['cargo']['volume'],
                'length': delivery_info['cargo']['length'],
                'width': delivery_info['cargo']['width'],
                'height': delivery_info['cargo']['height']
            }
        ]
    }

    return body


def mgtrans_calc(config, delivery_info: dict):
    """ Return message about successful or unsuccessful calculation
    config: instance of ConfigParser, reading config.ini
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    """
    api = MtransAPI()
    request_body = get_request_body(api, delivery_info)

    if request_body['from'] and request_body['to']:
        calculation = api.calculate(request_body)
        print(calculation)
        return f'Magic Trans:\n   Все ок!\n'

    return f'Magic Trans:\n   Возникла ошибка при запросе.\n'
