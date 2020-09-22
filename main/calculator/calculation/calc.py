from configparser import ConfigParser
from datetime import date, timedelta
from queue import Queue
from threading import Thread

from .dellin import dellin_calc
from .pecom import pecom_calc
from .gtd import gtd_calc
from .baikal import baikal_calc
from .nrgtk import nrgtk_calc
# from .mgtrans import mgtrans_calc


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
            dellin_calc,
            pecom_calc,
            gtd_calc,
            baikal_calc,
            nrgtk_calc,
            # mgtrans_calc,
        ]
        self.result = []

    def thread_run(self, work: Queue, result: Queue):
        """ Function for running in threads
        work: queue with calc functions
        param: queue to put results from calc functions
        """
        while not work.empty():
            calc = work.get_nowait()
            res = calc(self.config, self.delivery_info)
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
