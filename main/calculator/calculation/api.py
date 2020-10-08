from abc import ABCMeta, abstractmethod


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
