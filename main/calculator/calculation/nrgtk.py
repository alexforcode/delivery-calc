import requests


class NrgtkAPI:
    """ Class provides communicate with API service """
    def __init__(self, config):
        """
        config: instance of ConfigParser, reading config.ini
        """
        self.base_api_url = 'https://mainapi.nrg-tk.ru/v3'
        self.dev_token = config['nrgtk']['dev_token']
        self.user = config['nrgtk']['login']
        self.password = config['nrgtk']['pass']
        self.request_header = {'NrgApi-DevToken': self.dev_token}
        self.user_token, self.account_id = self.user_login()
        self.error = ''

    def get_error(self):
        return self.error

    def user_login(self):
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
            self.error = 'Ошибка соединения'

        return None, None

    def user_logout(self):
        """ Logout user and delete all opened sessions
        """
        url = f'{self.base_api_url}/{self.account_id}/logout'
        requests.get(url, headers=self.request_header, params={'token': self.user_token})

    def get_cities_id(self, check_city):
        """ Get city ids of derival and arrival cities
        check_city: city name
        Return: city id or None
        """
        url = f'{self.base_api_url}/cities'
        resp = requests.get(url, headers=self.request_header, params={'token': self.user_token})

        if resp.status_code == 200:
            resp_json = resp.json()
            city_id = 0
            for city in resp_json['cityList']:
                if city['name'].lower().startswith(check_city.lower()):
                    city_id = city['id']
                    return city_id
            if not city_id:
                self.error = f'{check_city}: нет терминала'
        else:
            self.error = 'Ошибка соединения'

        return None

    def calculate(self, body):
        """ Get results of calculation in json format
        body: data for request
        Return: results or None
        """
        url = f'{self.base_api_url}/price'

        if not self.error:
            resp = requests.post(url, headers=self.request_header, json=body)
            self.user_logout()

            if resp.status_code == 200:
                return resp.json()
            else:
                self.error = 'Ошибка соединения'

        self.user_logout()
        return None


def get_request_body(api: NrgtkAPI, delivery_info: dict):
    """ Get final body for request to API
    api: NrgtkAPI instance to communicate with API
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: request body
    """
    derival_id = api.get_cities_id(delivery_info['derival_city'])
    arrival_id = api.get_cities_id(delivery_info['arrival_city'])

    if derival_id and arrival_id:

        body = {
            'idCityFrom': derival_id,
            'idCityTo': arrival_id,
            'cover': 0,
            'items': [
                {
                    'weight': delivery_info['cargo']['weight'],
                    'width': delivery_info['cargo']['width'],
                    'height': delivery_info['cargo']['width'],
                    'length': delivery_info['cargo']['length'],
                    'isStandardSize': True
                }
            ],
        }

        return body
    else:
        return None


def nrgtk_calc(config, delivery_info: dict):
    """ Main function to calculate delivery cost and time
    config: instance of ConfigParser, reading config.ini
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: result dictionary
    """
    result = {
        'name': 'Энергия',
        'cost': 'Ошибка',
        'days': 'Ошибка',
        'error': ''
    }

    api = NrgtkAPI(config)

    request_body = get_request_body(api, delivery_info)
    if not request_body:
        result['error'] = api.get_error()
        return result

    calculation = api.calculate(request_body)
    if not calculation:
        result['error'] = api.get_error()
        return result

    try:
        cost = round(float(calculation['transfer'][0]['price']), 2)
        days = calculation['transfer'][0]['interval'].split()[0]
        result['cost'] = f'{cost:.2f}'
        result['days'] = days
    except KeyError or IndexError:
        result['error'] = 'Ошибка расчета данных'

    return result
