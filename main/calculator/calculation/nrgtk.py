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
            return None, None

    def user_logout(self):
        """ Logout user and delete all opened sessions
        """
        url = f'{self.base_api_url}/{self.account_id}/logout'
        requests.get(url, headers=self.request_header, params={'token': self.user_token})

    def get_cities_id(self, derival_city, arrival_city):
        """ Get city ids of derival and arrival cities
        derival_city: derival city name
        arrival_city: arrival city name
        Return: (derival_id, arrival_id) or (None, None)
        """
        url = f'{self.base_api_url}/cities'
        resp = requests.get(url, headers=self.request_header, params={'token': self.user_token})

        derival_id = 0
        arrival_id = 0

        if resp.status_code == 200:
            resp_json = resp.json()
            for city in resp_json['cityList']:
                if city['name'].lower().startswith(derival_city.lower()):
                    derival_id = city['id']
                if city['name'].lower().startswith(arrival_city.lower()):
                    arrival_id = city['id']
                if derival_id and arrival_id:
                    return derival_id, arrival_id

        return None, None

    def calculate(self, body):
        """ Get results of calculation in json format
        body: data for request
        Return: results or None
        """
        url = f'{self.base_api_url}/price'
        resp = requests.post(url, headers=self.request_header, json=body)
        self.user_logout()

        if resp.status_code == 200:
            return resp.json()

        return None


def get_request_body(api: NrgtkAPI, delivery_info: dict):
    """ Get final body for request to API
    api: NrgtkAPI instance to communicate with API
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: request body
    """
    derival_id, arrival_id = api.get_cities_id(delivery_info['derival_city'], delivery_info['arrival_city'])

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


def nrgtk_calc(config, delivery_info: dict):
    """ Main function to calculate delivery cost and time
    config: instance of ConfigParser, reading config.ini
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: result dictionary
    """
    result = {
        'name': 'Энергия',
        'cost': 'Ошибка',
        'days': 'Ошибка'
    }

    api = NrgtkAPI(config)
    request_body = get_request_body(api, delivery_info)
    calculation = api.calculate(request_body)

    if calculation:
        try:
            cost = round(float(calculation['transfer'][0]['price']), 2)
            days = calculation['transfer'][0]['interval'].split()[0]
            result['cost'] = f'{cost:.2f}'
            result['days'] = days
        except KeyError or IndexError:
            pass

    return result
