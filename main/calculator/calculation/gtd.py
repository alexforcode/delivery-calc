# https://gtdel.com/developers/api-doc

import requests


class GtdAPI:
    """ Class provides communicate with API service """
    def __init__(self, config):
        """
        config: instance of ConfigParser, reading config.ini
        """
        self.base_api_url = 'https://capi.gtdel.com/1.0'
        self.apikey = config['gtd']['apikey']
        self.request_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.apikey}'
        }

    def get_city_codes(self, derival_city: str, arrival_city: str):
        """ Get city codes of derival and arrival cities
        derival_city: derival city name
        arrival_city: arrival city name
        Return: (derival_code, arrival_code) or (None, None)
        """
        url = f'{self.base_api_url}/tdd/city/get-list/'
        resp = requests.post(url, headers=self.request_headers)

        if resp.status_code == 200:
            cities = resp.json()
            derival_code = 0
            arrival_code = 0

            for city in cities:
                if city['name'].lower().startswith(derival_city.lower()):
                    derival_code = city['code']
                if city['name'].lower().startswith(arrival_city.lower()):
                    arrival_code = city['code']
                if derival_code and arrival_code:
                    return derival_code, arrival_code

        return None, None

    def calculate(self, body: dict):
        """ Get results of calculation in json format
        body: data for request
        Return: results or None
        """
        url = f'{self.base_api_url}/order/calculate'
        resp = requests.post(url, json=body, headers=self.request_headers)

        if resp.status_code == 200:
            return resp.json()

        return None


def get_request_body(api: GtdAPI, delivery_info: dict):
    """ Get final body for request to API
    api: GtdAPI instance to communicate with API
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: request body
    """
    derival_code, arrival_code = api.get_city_codes(delivery_info['derival_city'], delivery_info['arrival_city'])

    body = {
        'city_pickup_code': derival_code,
        'city_delivery_code': arrival_code,
        'declared_price': 100,
        'pick_up': 0,
        'delivery': 0,
        'insurance': 0,
        'have_doc': 0,
        'places': [
            {
                'count_place': 1,
                'height': delivery_info['cargo']['height'] * 100,
                'width': delivery_info['cargo']['width'] * 100,
                'length': delivery_info['cargo']['length'] * 100,
                'weight': delivery_info['cargo']['weight'],
                'volume': delivery_info['cargo']['volume']
            },
        ]
    }

    return body


def gtd_calc(config, delivery_info: dict):
    """ Main function to calculate delivery cost and time
    config: instance of ConfigParser, reading config.ini
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: result dictionary
    """
    result = {
        'name': 'GTD',
        'cost': 'Ошибка',
        'days': 'Ошибка'
    }

    api = GtdAPI(config)
    request_body = get_request_body(api, delivery_info)
    calculation = api.calculate(request_body)

    if calculation:
        try:
            cost = 0
            services = calculation[0]['standart']['detail']
            for service in services:
                if service['code'] in ('S031', 'S039'):
                    cost += service['price']
            days = calculation[0]['standart']['time']

            result['cost'] = f'{cost:.2f}'
            result['days'] = days
        except KeyError or IndexError:
            pass

    return result
