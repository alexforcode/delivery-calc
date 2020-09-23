# https://dev.dellin.ru/api/calculation/calculator/

import datetime
import json
import math

import requests


class DellinAPI:
    """ Class provides communicate with API service """
    def __init__(self, config):
        """
        config: instance of ConfigParser, reading config.ini
        """
        self.base_api_url = 'https://api.dellin.ru'
        self.appkey = config['dellin']['appkey']
        self.login = config['dellin']['login']
        self.password = config['dellin']['pass']
        self.session_id = self.get_session_id()
        self.error = ''

    def get_error(self):
        return self.error

    def get_session_id(self):
        """ Get session id for future api requests
        Return: sessionID or None
        """
        url = f'{self.base_api_url}/v3/auth/login.json'

        resp = requests.post(url,
                             json={'appkey': self.appkey,
                                   'login': self.login,
                                   'password': self.password
                                   },
                             headers={'content-type': 'application/json'})

        if resp.status_code == 200:
            resp_json = resp.json()
            return resp_json['data']['sessionID']
        else:
            self.error = 'Ошибка соединения'

        return None

    def get_city_code(self, city: str):
        """ Get code of city
        city: city name
        Return: city code or None
        """
        url = f'{self.base_api_url}/v2/public/kladr.json'

        resp = requests.post(url,
                             json={'appkey': self.appkey,
                                   'q': city.lower(),
                                   'limit': 5},
                             headers={'content-type': 'application/json'})

        if resp.status_code == 200:
            resp_json = resp.json()
            try:
                return resp_json['cities'][0]['code']
            except IndexError or KeyError:
                self.error = f'{city}: нет терминала'
        else:
            self.error = 'Ошибка соединения'

        return None

    def calculate(self, body: dict):
        """ Get result of calculation in json format
        body: data for request
        Return: calculation result or None
        """
        url = f'{self.base_api_url}/v2/calculator.json'

        if not self.error:
            resp = requests.post(url,
                                 json=body,
                                 headers={'content-type': 'application/json'})

            if resp.status_code == 200:
                return resp.json()
            else:
                self.error = 'Ошибка расчета'

        return None


def get_terminal_id(city_code: str):
    """ Get id of dellin terminal from terminal_v3.json file in data folder
    city_code: kladr code of city
    Return: terminal id or None
    """
    # TODO: update file terminal_v3.json each month: https://dev.dellin.ru/api/catalogs/pvz/
    with open('assets/data/terminals_v3.json', 'r') as f:
        content = f.read()
        cities = json.loads(content)

    for city in cities['city']:
        if city['code'] == city_code:
            return city['terminals']['terminal'][0]['id']

    return None


def get_request_body(api: DellinAPI, delivery_info: dict):
    """ Return final body for request to API
    app: DellinAPI instance to communicate with API
    deliver_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: request body
    """
    arrival_code = api.get_city_code(delivery_info['arrival_city'])
    derival_code = api.get_city_code(delivery_info['derival_city'])

    if arrival_code and derival_code:
        body = {
            'appkey': api.appkey,
            'sessionID': api.session_id,
            'delivery': {
                'deliveryType': {
                    'type': 'auto'
                },
                'arrival': {
                    'variant': 'terminal',
                    'city': arrival_code,
                },
                'derival': {
                    'produceDate': delivery_info['produce_date'],
                    'variant': 'terminal',
                    'terminalID': get_terminal_id(derival_code)
                },
            },
            'members': {
                'requester': {
                    'role': 'sender'
                }
            },
            'cargo': {
                'length': delivery_info['cargo']['length'],
                'width': delivery_info['cargo']['width'],
                'height': delivery_info['cargo']['height'],
                'totalVolume': delivery_info['cargo']['volume'],
                'totalWeight': delivery_info['cargo']['weight'],
                'hazardClass': 0
            },
            'payment': {
                'paymentCity': arrival_code,
                'type': 'cash'
            }
        }

        if delivery_info['cargo']['weight'] >= 80:
            weight = delivery_info['cargo']['weight']
            quantity = math.ceil(weight / 75)
            body['cargo']['quantity'] = quantity
            body['cargo']['weight'] = round(weight / quantity, 1)

        return body
    else:
        return None


def dellin_calc(config, delivery_info: dict):
    """ Main function to calculate delivery cost and time
    config: instance of ConfigParser, reading config.ini
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: result dictionary
    """
    result = {
        'name': 'Деловые Линии',
        'cost': 'Ошибка',
        'days': 'Ошибка',
        'error': ''
    }

    api = DellinAPI(config)

    if not api.session_id:
        result['error'] = api.get_error()
        return result

    request_body = get_request_body(api, delivery_info)

    if not request_body:
        result['error'] = api.get_error()
        return result

    calculation = api.calculate(request_body)

    if not calculation:
        result['error'] = api.get_error()
        return result

    try:
        derival_date = datetime.datetime.strptime(
            delivery_info['produce_date'],
            '%Y-%m-%d'
        )
        arrival_date = datetime.datetime.strptime(
            calculation['data']['orderDates']['arrivalToOspReceiver'],
            '%Y-%m-%d'
        )
        days_delta = arrival_date - derival_date

        intercity_price = calculation['data']['intercity']['price'] * 0.7  # 30% discount
        insurance_price = calculation['data']['insurance']
        notify_price = calculation['data']['notify']['price']
        total_price = round(intercity_price + insurance_price + notify_price, 2)

        result['cost'] = f'{total_price:.2f}'
        result['days'] = days_delta.days
    except KeyError or IndexError:
        result['error'] = 'Ошибка расчета данных'

    return result
