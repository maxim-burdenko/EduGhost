import os

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as Service_Firefox

from backend.config import firefox_options
from backend.logger import log


class BrowserServices:
    _driver = None

    def __init__(self):
        self._service_path_firefox = os.path.join(os.path.dirname(__file__), "geckodriver.exe")
        self._service_firefox = Service_Firefox(executable_path=self._service_path_firefox)
        self._options_firefox = firefox_options

    def get_driver(self):
        try:
            log.info('пробуем получить драйвер')
            self._driver = webdriver.Firefox(service=self._service_firefox, options=self._options_firefox)
            log.info('драйвер был успешно получен')
            return self._driver
        except Exception:
            log.exception('при попытке получить драйвер неизвестная ошибка')

    def is_driver_available(self):
        return self._driver is not None

    def get_window(self, for_="meet"):
        tabs = self._driver.window_handles

        if len(tabs) > 2:
            log.warning('дело пахнет керосином. Больше двух табов')

        if for_ == "meet":
            return tabs[0]
        elif for_ == "dl":
            return tabs[1]
        else:
            log.error('не правильно передан параметр for_')
            return
