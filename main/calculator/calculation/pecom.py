# https://kabinet.pecom.ru/api/v1/help/calculator#toc-method-calculateprice

import requests


class PecomAPI:
    """ Class provides communicate with API service """
    def __init__(self, config):
        """
        config: instance of ConfigParser, reading config.ini
        """
        self.base_api_url = 'https://kabinet.pecom.ru/api/v1'
        self.login = config['pecom']['login']
        self.apikey = config['pecom']['apikey']
        self.error = ''

    def get_error(self):
        return self.error

    def get_branch_id(self, city: str):
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
                    self.error = f'{city}: нет терминала'
            else:
                self.error = self.error = f'{city}: нет терминала'
        else:
            self.error = 'Ошибка соединения'

        return None

    def calculate(self, body: dict):
        """ Get results of calculation in json format
        body: data for request
        Return: results or None
        """
        url = f'{self.base_api_url}/calculator/calculateprice/'

        if not self.error:
            resp = requests.post(url,
                                 auth=(self.login, self.apikey),
                                 json=body,
                                 headers={'content-type': 'application/json'})

            if resp.status_code == 200:
                resp_json = resp.json()
                if 'error' not in resp_json.keys():
                    return resp_json
                else:
                    self.error = 'Ошибка соединения'
            else:
                self.error = 'Ошибка соединения'

        return None


def get_request_body(api: PecomAPI, delivery_info: dict):
    """ Get final body for request to API
    api: PecomAPI instance to communicate with API
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: request body
    """
    derival_city_id = api.get_branch_id(delivery_info['derival_city'].capitalize())
    arrival_city_id = api.get_branch_id(delivery_info['arrival_city'].capitalize())

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
            'calcDate': delivery_info['produce_date'],
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
                'length': delivery_info['cargo']['length'],
                'width': delivery_info['cargo']['width'],
                'height': delivery_info['cargo']['height'],
                'volume': delivery_info['cargo']['volume'],
                'maxSize': max(delivery_info['cargo']['length'],
                               delivery_info['cargo']['width'],
                               delivery_info['cargo']['height']),
                'isHP': False,
                'sealingPositionsCount': 0,
                'weight': delivery_info['cargo']['weight'],
                'overSize': False
            }]
        }

        return body
    else:
        return None


def pecom_calc(config, delivery_info: dict):
    """ Main function to calculate delivery cost and time
    config: instance of ConfigParser, reading config.ini
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: result dictionary
    """
    result = {
        'name': 'ПЭК',
        'cost': 'Ошибка',
        'days': 'Ошибка',
        'error': ''
    }

    api = PecomAPI(config)

    request_body = get_request_body(api, delivery_info)
    if not request_body:
        result['error'] = api.get_error()
        return result

    calculation = api.calculate(request_body)
    if not calculation:
        result['error'] = api.get_error()
        return result

    try:
        cost = 0
        for transfer in calculation['transfers']:
            if transfer['transportingType'] == 1:
                cost = round(transfer['costTotal'] * 0.9, 2)

        result['cost'] = f'{cost:.2f}'
        result['days'] = calculation["commonTerms"][0]["transporting"][0]
    except KeyError or IndexError:
        result['error'] = 'Ошибка расчета данных'

    return result
