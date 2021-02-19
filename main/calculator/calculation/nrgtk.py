import requests

from .api import DeliveryAPI


class NrgtkAPI(DeliveryAPI):
    """ Class provides communicate with API service """
    def __init__(self, config, delivery_info: dict):
        """
        config: instance of ConfigParser, reading config.ini
        delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
        """
        self.base_api_url = 'https://mainapi.nrg-tk.ru/v3'
        self.dev_token = config['nrgtk']['dev_token']
        self.user = config['nrgtk']['login']
        self.password = config['nrgtk']['pass']
        self.request_header = {'NrgApi-DevToken': self.dev_token}
        self.user_token, self.account_id = self._user_login()
        super().__init__(delivery_info)
        self.result['name'] = 'Энергия'

    def _user_login(self):
        """ Get token and accountId to communicate with API
        Return: (user_token, account_id) or (None, None)
        """
        url = f'{self.base_api_url}/login'

        resp = requests.get(url, headers=self.request_header, params={
            'user': self.user,
            'password': self.password
        })

        if resp.status_code == 200:
            resp_json = resp.json()
            return resp_json['token'], resp_json['accountId']
        else:
            self.result['error'] = 'Ошибка соединения'

        return None, None

    def _user_logout(self):
        """ Logout user and delete all opened sessions
        """
        url = f'{self.base_api_url}/{self.account_id}/logout'
        requests.get(url, headers=self.request_header, params={'token': self.user_token})

    def _get_city_id(self, check_city: str, check_region: str):
        """ Get city ids of derival and arrival cities
        check_city: city name
        check_region: region name
        Return: city id or None
        """
        url = f'{self.base_api_url}/cities'
        resp = requests.get(url, headers=self.request_header, params={'token': self.user_token})

        if resp.status_code == 200:
            resp_json = resp.json()
            matches = []

            for city in resp_json['cityList']:
                if city['name'].lower().startswith(check_city.lower()):
                    matches.append(city)

            if len(matches) == 1:
                return matches[0]['id']
            elif len(matches) > 1:
                if check_region:
                    region = self._get_clean_region(check_region)
                    for city in matches:
                        if region in city['description'].lower():
                            return city['id']
                    self.result['error'] = f'{check_city} ({check_region}): нет терминала'
                else:
                    return matches[0]['id']
            else:
                self.result['error'] = f'{check_city}: нет доставки'
        else:
            self.result['error'] = 'Ошибка соединения'

        return None

    def _get_request_body(self):
        """ Create final body for request to API
        Return: request body
        """
        derival_id = self._get_city_id(self.derival_city, self.derival_region)
        arrival_id = self._get_city_id(self.arrival_city, self.arrival_region)

        if derival_id and arrival_id:

            body = {
                'idCityFrom': derival_id,
                'idCityTo': arrival_id,
                'cover': 0,
                'items': [
                    {
                        'weight': self.cargo['weight'],
                        'width': self.cargo['width'],
                        'height': self.cargo['width'],
                        'length': self.cargo['length'],
                        'isStandardSize': True
                    }
                ],
            }

            return body

        return None

    def _get_delivery_calc(self):
        """ Get results of calculation in json format
        Return: results or None
        """
        url = f'{self.base_api_url}/price'

        if not self.result['error']:
            resp = requests.post(url, headers=self.request_header, json=self.body)
            self._user_logout()

            if resp.status_code == 200:
                return resp.json()
            else:
                self.result['error'] = 'Ошибка соединения'

        self._user_logout()
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
            for transfer in calculation['transfer']:
                if transfer['typeId'] in (1, 3):
                    cost = round(float(transfer['price']), 2)
                    days = transfer['interval'].split()[0]

                    if transfer['typeId'] == 1:
                        self.result['cost'] = f'{cost:.2f}'
                    else:
                        self.result['cost'] = f'{cost:.2f} (ж/д)'
                    self.result['days'] = days
                    break
                else:
                    self.result['error'] = 'Ошибка: нет автодоставки'
        except KeyError or IndexError:
            self.result['error'] = 'Ошибка расчета данных'

        return self.result
