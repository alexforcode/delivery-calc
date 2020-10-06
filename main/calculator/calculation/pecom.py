# https://kabinet.pecom.ru/api/v1/help/calculator#toc-method-calculateprice

import requests


class PecomAPI:
    """ Class provides communicate with API service """
    def __init__(self, config, delivery_info: dict):
        """
        config: instance of ConfigParser, reading config.ini
        delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
        """
        self.result = {
            'name': 'ПЭК',
            'cost': 'Ошибка',
            'days': 'Ошибка',
            'error': ''
        }
        self.base_api_url = 'https://kabinet.pecom.ru/api/v1'
        self.login = config['pecom']['login']
        self.apikey = config['pecom']['apikey']
        self.derival_city = delivery_info['derival_city']
        self.arrival_city = delivery_info['arrival_city']
        self.cargo = delivery_info['cargo']
        self.date = delivery_info['produce_date']
        self.body = self._get_request_body()

    def _get_branch_id(self, city: str):
        """ Get id of terminal branch in city
        city: city name
        Return: branch id or None
        """
        url = f'{self.base_api_url}/branches/findbytitle/'
        resp = requests.post(url,
                             auth=(self.login, self.apikey),
                             json={'title': city},
                             headers={'content-type': 'application/json'})

        if resp.status_code == 200:
            cities = resp.json()
            if cities['success']:
                try:
                    return int(cities['items'][0]['branchId'])
                except IndexError or KeyError:
                    self.result['error'] = f'{city}: нет терминала'
            else:
                self.result['error'] = f'{city}: нет терминала'
        else:
            self.result['error'] = 'Ошибка соединения'

        return None

    def _get_request_body(self):
        """ Create final body for request to API
        Return: request body
        """
        derival_city_id = self._get_branch_id(self.derival_city.capitalize())
        arrival_city_id = self._get_branch_id(self.arrival_city.capitalize())

        if derival_city_id and arrival_city_id:
            body = {
                'senderCityId': derival_city_id,
                'receiverCityId': arrival_city_id,
                'isOpenCarSender': False,
                'senderDistanceType': 0,
                'isDayByDay': False,
                'isOpenCarReceiver': False,
                'receiverDistanceType': 0,
                'isHyperMarket': False,
                'calcDate': self.date,
                'isInsurance': False,
                'isInsurancePrice': 0,
                'isPickUp': False,
                'isDelivery': False,
                'pickupServices': {
                    'isLoading': False,
                    'floor': 0,
                    'carryingDistance': 0,
                    'isElevator': False
                },
                'deliveryServices': {
                    'isLoading': False,
                    'floor': 0,
                    'carryingDistance': 0,
                    'isElevator': False
                },
                'Cargos': [{
                    'length': self.cargo['length'],
                    'width': self.cargo['width'],
                    'height': self.cargo['height'],
                    'volume': self.cargo['volume'],
                    'maxSize': max(self.cargo['length'], self.cargo['width'], self.cargo['height']),
                    'isHP': False,
                    'sealingPositionsCount': 0,
                    'weight': self.cargo['weight'],
                    'overSize': False
                }]
            }

            return body
        else:
            return None

    def _get_delivery_calc(self):
        """ Get results of calculation in json format
        body: data for request
        Return: results or None
        """
        url = f'{self.base_api_url}/calculator/calculateprice/'

        if not self.result['error']:
            resp = requests.post(url,
                                 auth=(self.login, self.apikey),
                                 json=self.body,
                                 headers={'content-type': 'application/json'})

            if resp.status_code == 200:
                resp_json = resp.json()
                if 'error' not in resp_json.keys():
                    return resp_json
                else:
                    self.result['error'] = 'Ошибка соединения'
            else:
                self.result['error'] = 'Ошибка соединения'

        return None

    def calculate(self):
        """ Main function to calculate delivery cost and time
        Return: result dictionary
        """
        if not self.body:
            return self.result

        calculation = self._get_delivery_calc()
        if not calculation:
            return self.result

        try:
            cost = 0
            for transfer in calculation['transfers']:
                if transfer['transportingType'] == 1:
                    cost = round(transfer['costTotal'] * 0.9, 2)

            self.result['cost'] = f'{cost:.2f}'
            self.result['days'] = calculation["commonTerms"][0]["transporting"][0]
        except KeyError or IndexError:
            self.result['error'] = 'Ошибка расчета данных'

        return self.result
