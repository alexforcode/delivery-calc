# https://gtdel.com/developers/api-doc

import requests

from .api import DeliveryAPI


class GtdAPI(DeliveryAPI):
    """ Class provides communicate with API service """
    def __init__(self, config, delivery_info: dict):
        """
        config: instance of ConfigParser, reading config.ini
        delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
        """
        self.base_api_url = 'https://capi.gtdel.com/1.0'
        self.apikey = config['gtd']['apikey']
        self.request_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.apikey}'
        }
        super().__init__(delivery_info)
        self.result['name'] = 'GTD'

    def _get_region_code(self, check_region: str):
        """ Get region code for region
        check_region: region name
        Return: region code or None
        """
        url = f'{self.base_api_url}/tdd/region/get-list/'
        resp = requests.post(url, headers=self.request_headers)

        if resp.status_code == 200:
            regions = resp.json()
            clean_region = self._get_clean_region(check_region)

            for region in regions:
                if clean_region in region['name'].lower():
                    code = region['code']
                    return code
        else:
            self.result['error'] = 'Ошибка соединения'

        return None

    def _get_city_code(self, check_city: str, check_region: str):
        """ Get city codes for city
        check_city: city name
        check_region: region name
        Return: city code or None
        """
        url = f'{self.base_api_url}/tdd/city/get-list/'
        resp = requests.post(url, headers=self.request_headers)

        if resp.status_code == 200:
            cities = resp.json()
            code = 0
            region_code = None
            if check_region:
                region_code = self._get_region_code(check_region)

            for city in cities:
                if region_code:
                    if city['name'].lower().startswith(check_city.lower()) and city['region_code'] == region_code:
                        code = city['code']
                        return code
                else:
                    if city['name'].lower().startswith(check_city.lower()):
                        code = city['code']
                        return code

            if not code:
                self.result['error'] = f'{check_city} ({check_region}): нет терминала'
        else:
            self.result['error'] = 'Ошибка соединения'

        return None

    def _get_request_body(self):
        """ Create final body for request to API
        Return: request body
        """
        derival_code = self._get_city_code(self.derival_city, self.derival_region)
        arrival_code = self._get_city_code(self.arrival_city, self.arrival_region)

        if derival_code and arrival_code:
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
                        'height': self.cargo['height'] * 100,
                        'width': self.cargo['width'] * 100,
                        'length': self.cargo['length'] * 100,
                        'weight': self.cargo['weight'],
                        'volume': self.cargo['volume']
                    },
                ]
            }

            return body
        else:
            return None

    def _get_delivery_calc(self):
        """ Get results of calculation in json format
        Return: results or None
        """
        url = f'{self.base_api_url}/order/calculate'

        if not self.result['error']:
            resp = requests.post(url, json=self.body, headers=self.request_headers)

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
            cost = 0
            services = calculation[0]['standart']['detail']
            for service in services:
                if service['code'] in ('S031', 'S039'):
                    cost += service['price']
            days = calculation[0]['standart']['time']

            self.result['cost'] = f'{cost:.2f}'
            self.result['days'] = days
        except KeyError or IndexError:
            self.result['error'] = 'Ошибка расчета данных'

        return self.result
