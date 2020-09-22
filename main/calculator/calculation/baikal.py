import requests


class BaikalAPI:
    """ Class provides communicate with API service """
    def __init__(self, config):
        """
        config: instance of ConfigParser, reading config.ini
        """
        self.base_api_url = 'https://api.baikalsr.ru/v1'
        self.apikey = config['baikal']['apikey']
        self.request_headers = {'Content-Type': 'application/json'}
        self.error = ''

    def get_error(self):
        return self.error

    def get_city_guid(self, city: str):
        """ Get guid (code) of city
        city: city name
        Return: guid or None
        """
        url = f'{self.base_api_url}/fias/cities?text={city.lower()}'
        resp = requests.get(url, auth=(self.apikey, ''), headers=self.request_headers)

        if resp.status_code == 200:
            resp_json = resp.json()
            try:
                guid = resp_json[0]['guid']
                return guid
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
        url = f'{self.base_api_url}/calculator'

        if not self.error:
            resp = requests.post(url, json=body, auth=(self.apikey, ''), headers=self.request_headers)

            if resp.status_code == 200:
                return resp.json()
            else:
                self.error = 'Ошибка соединения'

        return None


def get_request_body(api: BaikalAPI, delivery_info: dict):
    """ Get final body for request to API
    api: BaikalAPI instance to communicate with API
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: request body
    """
    derival_city_id = api.get_city_guid(delivery_info['derival_city'])
    arrival_city_id = api.get_city_guid(delivery_info['arrival_city'])

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
                'weight': delivery_info['cargo']['weight'],
                'volume': delivery_info['cargo']['volume'],
                'units': 1,
                'max': {
                    'weight': delivery_info['cargo']['weight'],
                    'length': delivery_info['cargo']['length'],
                    'width': delivery_info['cargo']['width'],
                    'height': delivery_info['cargo']['height']
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
    else:
        return None


def baikal_calc(config, delivery_info: dict):
    """ Main function to calculate delivery cost and time
    config: instance of ConfigParser, reading config.ini
    delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
    Return: result dictionary
    """
    result = {
        'name': 'Байкал Сервис',
        'cost': 'Ошибка',
        'days': 'Ошибка',
        'error': ''
    }

    api = BaikalAPI(config)

    request_body = get_request_body(api, delivery_info)
    if not request_body:
        result['error'] = api.get_error()
        return result

    calculation = api.calculate(request_body)
    if not calculation:
        result['error'] = api.get_error()
        return result

    try:
        cost = round(float(calculation['total']['int']) * 0.8, 2)  # 20% discount
        days = calculation['transit']['int']
        result['cost'] = f'{cost:.2f}'
        result['days'] = days
    except KeyError:
        result['error'] = 'Ошибка расчета данных'

    return result
