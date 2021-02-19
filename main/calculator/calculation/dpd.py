from xml.etree import ElementTree as et
import csv

import requests

from .api import DeliveryAPI


class DPDApi(DeliveryAPI):
    """ Class provides communicate with API service """
    def __init__(self, config, delivery_info: dict):
        """
        config: instance of ConfigParser, reading config.ini
        delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
        """
        self.base_api_url = 'http://wstest.dpd.ru/services'
        self.client_num = config['dpd']['client_num']
        self.client_key = config['dpd']['client_key']
        super().__init__(delivery_info)
        self.result['name'] = 'DPD'

    def _get_city_id(self, check_city: str, check_region: str):
        """ Get id of terminal branch in city from dpd-terminals.xml file in data folder
        check_city: city name
        check_region: region name
        Return: branch id or None
        """
        matches = []

        with open('assets/data/dpd-geography.csv', encoding='windows-1251', newline='') as file:
            reader = csv.reader(file, delimiter=';')
            for row in reader:
                if row and row[3].lower() == check_city.lower():
                    matches.append(row)

        if len(matches) == 1:
            return matches[0][0]
        elif len(matches) > 1:
            if check_region:
                region = self._get_clean_region(check_region)
                for address in matches:
                    if region in address[4].lower():
                        return address[0]
                self.result['error'] = f'{check_city} ({check_region}): нет терминала'
            else:
                self.result['error'] = f'Уточните регионы'
        else:
            self.result['error'] = f'{check_city}: нет доставки'

        return None

    @staticmethod
    def _check_arrival_terminal(city_id: str):
        """ Check if terminal in the city
        city_id: city name
        return True or False
        """
        with open('assets/data/dpd-terminals.xml', 'r') as f:
            content = f.read()
            root = et.fromstring(content)

        for terminal_id in root.findall('.//cityId'):
            if city_id == terminal_id.text:
                return True

        return False

    def _get_request_body(self):
        """ Create final body for request to API
        Return: request body or None
        """
        derival_city_id = self._get_city_id(self.derival_city, self.derival_region)
        arrival_city_id = self._get_city_id(self.arrival_city, self.arrival_region)

        if derival_city_id and arrival_city_id:
            body = f"""<?xml version="1.0" encoding="UTF-8"?>
                <soap:Envelope
                    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
                    xmlns:ns0="http://dpd.ru/ws/calculator/2012-03-20"
                    xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <soap:Body>
                        <ns0:getServiceCost2>
                            <request>
                                <auth>
                                    <clientNumber>{self.client_num}</clientNumber>
                                    <clientKey>{self.client_key}</clientKey>
                                </auth>
                                <pickup>
                                    <cityId>{derival_city_id}</cityId>
                                    <countryCode>RU</countryCode>
                                </pickup>
                                <delivery>
                                    <cityId>{arrival_city_id}</cityId>
                                    <countryCode>RU</countryCode>
                                </delivery>
                                <selfPickup>true</selfPickup>
                                <selfDelivery>true</selfDelivery>
                                <weight>{self.cargo['weight']}</weight>
                                <volume>{self.cargo['volume']}</volume>
                            </request>
                        </ns0:getServiceCost2>
                    </soap:Body>
                </soap:Envelope>"""

            if not self._check_arrival_terminal(arrival_city_id):
                body = body.replace(
                    '<selfDelivery>true</selfDelivery>',
                    '<selfDelivery>false</selfDelivery>'
                )

            return body

        return None

    def _get_delivery_calc(self):
        """ Get results of calculation in xml format
        Return: results or None
        """
        url = f'{self.base_api_url}/calculator2?wsdl'

        if not self.result['error']:
            resp = requests.post(url,
                                 data=self.body,
                                 headers={'content-type': 'text/xml; charset=utf-8'})
            if resp.status_code == 200:
                return resp.content
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

        costs = []

        tariffs = et.fromstring(calculation).findall('.//return')
        for tariff in tariffs:
            costs.append((
                tariff.find('.//cost').text,
                tariff.find('.//days').text
            ))

        costs = sorted(costs, key=lambda item: float(item[0]))
        self.result['cost'] = costs[0][0]
        self.result['days'] = costs[0][1]

        return self.result
