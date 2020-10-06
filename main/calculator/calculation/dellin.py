# https://dev.dellin.ru/api/calculation/calculator/

import datetime
import json
import math

import requests


class DellinAPI:
    """ Class provides communicate with API service """
    def __init__(self, config, delivery_info):
        """
        config: instance of ConfigParser, reading config.ini
        delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
        """
        self.result = {
            'name': 'Деловые Линии',
            'cost': 'Ошибка',
            'days': 'Ошибка',
            'error': ''
        }
        self.base_api_url = 'https://api.dellin.ru'
        self.appkey = config['dellin']['appkey']
        self.login = config['dellin']['login']
        self.password = config['dellin']['pass']
        self.derival_city = delivery_info['derival_city']
        self.arrival_city = delivery_info['arrival_city']
        self.cargo = delivery_info['cargo']
        self.date = delivery_info['produce_date']
        self.session_id = self._get_session_id()
        self.body = self._get_request_body()

    def _get_session_id(self):
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
            self.result['error'] = 'Ошибка соединения'

        return None

    def _get_city_code(self, city: str):
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
                self.result['error'] = f'{city}: нет терминала'
        else:
            self.result['error'] = 'Ошибка соединения'

        return None

    @staticmethod
    def _get_terminal_id(city_code: str):
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

    def _get_request_body(self):
        """ Create final body for request to API
        Return: request body
        """
        arrival_code = self._get_city_code(self.arrival_city)
        derival_code = self._get_city_code(self.derival_city)

        if arrival_code and derival_code:
            body = {
                'appkey': self.appkey,
                'sessionID': self.session_id,
                'delivery': {
                    'deliveryType': {
                        'type': 'auto'
                    },
                    'arrival': {
                        'variant': 'terminal',
                        'city': arrival_code,
                    },
                    'derival': {
                        'produceDate': self.date,
                        'variant': 'terminal',
                        'terminalID': self._get_terminal_id(derival_code)
                    },
                },
                'members': {
                    'requester': {
                        'role': 'sender'
                    }
                },
                'cargo': {
                    'length': self.cargo['length'],
                    'width': self.cargo['width'],
                    'height': self.cargo['height'],
                    'totalVolume': self.cargo['volume'],
                    'totalWeight': self.cargo['weight'],
                    'hazardClass': 0
                },
                'payment': {
                    'paymentCity': arrival_code,
                    'type': 'cash'
                }
            }

            if self.cargo['weight'] >= 80:
                weight = self.cargo['weight']
                quantity = math.ceil(weight / 75)
                body['cargo']['quantity'] = quantity
                body['cargo']['weight'] = round(weight / quantity, 1)

            return body
        else:
            return None

    def _get_delivery_calc(self):
        """ Get result of calculation in json format
        Return: calculation result or None
        """
        url = f'{self.base_api_url}/v2/calculator.json'

        if not self.result['error']:
            resp = requests.post(url,
                                 json=self.body,
                                 headers={'content-type': 'application/json'})

            if resp.status_code == 200:
                return resp.json()
            else:
                self.result['error'] = 'Ошибка расчета'

        return None

    def calculate(self):
        """ Main function to calculate delivery cost and time
        Return: result dictionary
        """
        if not self.session_id or not self.body:
            return self.result

        calculation = self._get_delivery_calc()
        if not calculation:
            return self.result

        try:
            derival_date = datetime.datetime.strptime(
                self.date,
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

            self.result['cost'] = f'{total_price:.2f}'
            self.result['days'] = days_delta.days
        except KeyError or IndexError:
            self.result['error'] = 'Ошибка расчета данных'

        return self.result
