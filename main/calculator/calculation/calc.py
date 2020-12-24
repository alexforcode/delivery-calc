from configparser import ConfigParser
from datetime import date, timedelta
from queue import Queue
from threading import Thread

from .dellin import DellinAPI
from .pecom import PecomAPI
from .gtd import GtdAPI
from .baikal import BaikalAPI
from .nrgtk import NrgtkAPI


class Calculator:
    """ Calculator class that gathers all delivery calculators and
    transfers config and delivery info to them.
    """
    def __init__(self, delivery_info: dict):
        self.config = ConfigParser()
        self.config.read('assets/data/config.ini')
        self.delivery_info = delivery_info
        self.delivery_info['produce_date'] = self.get_date()
        self.calculators = [
            DellinAPI,
            PecomAPI,
            GtdAPI,
            BaikalAPI,
            NrgtkAPI,
        ]
        self.result = []

    def thread_run(self, work: Queue, result: Queue):
        """ Function for running in threads
        work: queue with calc functions
        param: queue to put results from calc functions
        """
        while not work.empty():
            api_class = work.get_nowait()
            api = api_class(self.config, self.delivery_info)
            res = api.calculate()
            result.put_nowait(res)
            work.task_done()

    def calculate(self):
        """ Get result massages from all calc from self.calculators using queues and
        concatenate them in self.result string.
        Return: result massage
        """
        thread_count = len(self.calculators)
        work_queue = Queue()
        result_queue = Queue()

        for calc in self.calculators:
            work_queue.put(calc)

        for _ in range(thread_count):
            thread = Thread(target=self.thread_run, args=(work_queue, result_queue), daemon=True)
            thread.start()

        work_queue.join()

        while not result_queue.empty():
            self.result.append(result_queue.get_nowait())

        return sorted(self.result, key=lambda x: x['name'])

    @staticmethod
    def get_date():
        """ Get current date plus one day
        Return: date
        """
        elapsed_date = date.today() + timedelta(days=1)

        return elapsed_date.strftime('%Y-%m-%d')
