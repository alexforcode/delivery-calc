from abc import ABCMeta, abstractmethod
import json


class DeliveryAPI(metaclass=ABCMeta):
    """ Superclass for API subclasses """
    def __init__(self, delivery_info: dict):
        """
        delivery_info: info about delivery (arrival_city, derival_city, produce_date, cargo specs)
        """
        self.result = {
            'name': '',
            'cost': 'Ошибка',
            'days': 'Ошибка',
            'error': ''
        }
        self.derival_city = delivery_info['derival_city']
        self.arrival_city = delivery_info['arrival_city']
        self.derival_region = delivery_info['derival_region']
        self.arrival_region = delivery_info['arrival_region']
        self.cargo = delivery_info['cargo']
        self.date = delivery_info['produce_date']
        self.body = self._get_request_body()

    @abstractmethod
    def _get_request_body(self):
        pass

    @abstractmethod
    def _get_delivery_calc(self):
        pass

    @abstractmethod
    def calculate(self):
        pass

    @staticmethod
    def _get_clean_region(region: str):
        """ Get region for search in api json
        region: region name
        Return: cleaned region name for search
        """
        region = region.lower()
        check_list = ['край', 'область', 'округ', 'республика']
        if any([x in region for x in check_list]):
            region = region.split(' ')[0]

        return region

    @staticmethod
    def _save_json_to_file(data: dict, name: str):
        """ Save json data to file
        data: dict to save
        name: file name
        """
        with open(f'assets/data/{name}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
