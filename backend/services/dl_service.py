import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from backend.logger import log


class DlService:

    _login = ''
    _password = ''
    _driver = ''

    def __init__(self, login, password, driver):
        self._login = login
        self._password = password
        self._driver = driver

    def login(self):
        log.info('пытаемся зайти на дл...')
        try:
            log.debug('пытаемся открыть новое окно со входом на dl')
            self._driver.execute_script("window.open('https://dl.nure.ua/login/index.php');")
            time.sleep(3)

            log.debug('переключаемся на новое открытое окно')
            self._driver.switch_to.window(self._driver.window_handles[-1])
        except Exception:
            log.exception('при попытке открыть новое окно с входом')
            return

        try:
            log.debug('пытаемся найти элементы для входа')
            log_input = self._driver.find_element(By.XPATH, '//*[@id="username"]')
            pass_input = self._driver.find_element(By.XPATH, '//*[@id="password"]')
            login_btn = self._driver.find_element(By.XPATH, '//*[@id="loginbtn"]')

            time.sleep(2)
            log_input.send_keys(self._login)
            time.sleep(3)
            pass_input.send_keys(self._password)
            time.sleep(5)

            login_btn.click()

            time.sleep(2)
            if self._check_login():
                log.info('успешно вошли на дл')
            else:
                log.info('не удалось войти в DL, неверен логин или пароль')
        except Exception:
            log.exception('при попытке поиска и входа в дл')

    def _check_login(self):

        error_block_xpath = '//*[@id="loginerrormessage"]'

        try:
            self._driver.find_element(By.XPATH, error_block_xpath)
            return False
        except NoSuchElementException:
            return True
        except:
            log.exception('непонятная ошибка при попытке проверить вход на DL')
            return False

    def mark_attendance(self):

        try:
            # Ищем ссылку по тексту
            link = self._driver.find_element(
                By.XPATH,
                '//a[contains(text(), "Відправити відвідуваність") or contains(text(), "Submit attendance")]'
            )
            link.click()
            log.info("Клик по ссылке выполнен успешно.")
        except NoSuchElementException:
            log.error("Ссылка 'Відправити відвідуваність' не найдена.")
        except Exception as e:
            log.exception(f"Ошибка при попытке кликнуть по ссылке: {e}")

    def check_log_pass(self):
        if not self._login or not self._password: return False
        return True
