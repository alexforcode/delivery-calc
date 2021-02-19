import requests

from .api import DeliveryAPI


class BaikalAPI(DeliveryAPI):
    """ Class provides communicate with API service """
    def __init__(self, config, delivery_info: dict):
        """
        config: instance of ConfigParser, reading config.ini
        delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
        """
        self.base_api_url = 'https://api.baikalsr.ru/v1'
        self.apikey = config['baikal']['apikey']
        self.request_headers = {'Content-Type': 'application/json'}
        super().__init__(delivery_info)
        self.result['name'] = 'Байкал Сервис'

    def _get_city_guid(self, check_city: str, check_region: str):
        """ Get guid (code) of city
        check_city: city name
        check_region: region name
        Return: guid or None
        """
        url = f'{self.base_api_url}/fias/cities?text={check_city.lower()}'
        resp = requests.get(url, auth=(self.apikey, ''), headers=self.request_headers)

        if resp.status_code == 200:
            cities = resp.json()
            try:
                if check_region:
                    region = self._get_clean_region(check_region)
                    for city in cities:
                        if region in city['parents'].lower():
                            return city['guid']
                return cities[0]['guid']
            except IndexError or KeyError:
                self.result['error'] = f'{check_city}: нет доставки'
        else:
            self.result['error'] = 'Ошибка соединения'

        return None

    def _get_request_body(self):
        """ Create final body for request to API
        Return: request body
        """
        derival_city_id = self._get_city_guid(self.derival_city, self.derival_region)
        arrival_city_id = self._get_city_guid(self.arrival_city, self.arrival_region)

        if derival_city_id and arrival_city_id:
            body = {
                'from': {
                    'guid': derival_city_id,
                    'delivery': 0,
                    'loading': 0
                },
                'to': {
                    'guid': arrival_city_id,
                    'delivery': 0,
                    'loading': 0
                },
                'insurance': 0,
                'return_docs': 0,
                'cargo': {
                    'weight': self.cargo['weight'],
                    'volume': self.cargo['volume'],
                    'units': 1,
                    'max': {
                        'weight': self.cargo['weight'],
                        'length': self.cargo['length'],
                        'width': self.cargo['width'],
                        'height': self.cargo['height']
                    },
                    'pack': {
                        'crate': 0,
                        'pallet': 0,
                        'sealed_pallet': 0,
                        'bubble_wrap': 0,
                        'big_bag': 0,
                        'medium_bag': 0,
                        'small_bag': 0
                    }
                },
                'netto': 0
            }

            return body

        return None

    def _get_delivery_calc(self):
        """ Get result of calculation in json format
        Return: calculation result or None
        """
        url = f'{self.base_api_url}/calculator'

        if not self.result['error']:
            resp = requests.post(url, json=self.body, auth=(self.apikey, ''), headers=self.request_headers)

            if resp.status_code == 200:
                return resp.json()
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
            cost = round(float(calculation['total']['int']) * 0.8, 2)  # 20% discount
            days = calculation['transit']['int']
            self.result['cost'] = f'{cost:.2f}'
            self.result['days'] = days
        except KeyError:
            self.result['error'] = 'Ошибка расчета данных'

        return self.result
