import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from backend.logger import log

# Playwright вместо selenium

class GoogleService:
    _email = ""
    _password = ""
    _driver = None

    def __init__(self, password:str, email:str, driver):
        self._email = email
        self._password = password
        self._driver = driver

    def login(self):
        log.info('пытаемся войти в гугл аккаунт...')
        try:
            log.debug('получаем ссылку для входа в гугл')
            self._driver.get(
                'https://accounts.google.com/ServiceLogin?hl=en&passive=true&continue=https://www.google.com/&ec=GAZAAQ')
            time.sleep(2)

            log.debug('отправляем почту для входа')
            self._driver.find_element(By.ID, "identifierId").send_keys(self._email)
            time.sleep(2)

            log.debug('нажимаем кнопку "Далее"')
            self._driver.find_element(By.ID, "identifierNext").click()
            time.sleep(3)

            log.debug('вводим пароль от почты')
            self._driver.find_element(By.XPATH,
                                '//*[@id="password"]/div[1]/div/div[1]/input').send_keys(self._password)
            time.sleep(2)

            log.debug('жмём далее после ввода пароля')
            self._driver.find_element(By.ID, "passwordNext").click()
            time.sleep(5)

            log.info('вход в аккаунт гугл был выполнен')
        except Exception:
            log.exception('неизвесная ошибка при попытки войти в аккаунт')

    def turn_off_cam_mic(self):
        log.info('попытка выключить камеру и микрофон...')
        wait = WebDriverWait(self._driver, 10)

        cam_button_xpath = ('/html/body/div[1]/c-wiz/div/div/div[64]/div[3]/div/div[2]/div[4]'
                            '/div/div/div[1]/div[1]/div/div[7]/div[2]/div/div/div/div[1]')

        mic_button_xpath = ('/html/body/div[1]/c-wiz/div/div/div[64]/div[3]/div/div[2]/div[4]'
                            '/div/div/div[1]/div[1]/div/div[7]/div[1]/div/div/div/div/div[1]')

        try:
            log.debug('поиск и нажатие на кнопку камеры')
            cam_button = wait.until(ec.element_to_be_clickable((By.XPATH, cam_button_xpath)))
            cam_button.click()

            time.sleep(2)
        except Exception:
            log.exception('неизвестная ошибка при поиске и нажатие на кнопку камеры')

        try:
            log.debug('поиск и нажатие на кнопку микрофона')
            mic_button = wait.until(ec.element_to_be_clickable((By.XPATH, mic_button_xpath)))
            mic_button.click()

            time.sleep(2)
        except Exception:
            log.exception('неизвестная ошибка при поиске и нажатие на кнопку микрофона')

        log.info('камера и микрофон отключены')

    def join_the_meeting(self):
        log.info('пытаемся подключится к встрече')
        wait = WebDriverWait(self._driver, 10)

        join_button_xpath = ('/html/body/div[1]/c-wiz/div/div/div[64]/div[3]/div/div[2]/div[4]/div/div/'
                             'div[2]/div[1]/div[2]/div[1]/div/div/span/div[1]/button')

        try:
            log.debug('ожидаем кнопку "Присоединиться"')

            time.sleep(2)
            join_button = wait.until(ec.element_to_be_clickable((By.XPATH, join_button_xpath)))
            join_button.click()

            log.info('удалось присоединиться к встрече')
        except Exception:
            log.exception('неизвестная ошибка при попытке присоединиться к встерче')

    def exit_from_meeting(self):
        log.info('пробуем отключится от встречи')
        wait = WebDriverWait(self._driver, 10)

        exit_button_xpath = ('/html/body/div[1]/c-wiz/div/div/div[62]'
                             '/div[3]/div/div[8]/div/div/div[2]/div/div[8]/span/button')

        try:
            log.debug('ожидаем кнопку "Завершить встречу"')

            join_button = wait.until(ec.element_to_be_clickable((By.XPATH, exit_button_xpath)))
            join_button.click()

            log.info('удалось отключиться от встречи')
        except Exception:
            log.warning('что-то пошло не так при отключении от встречи')
            log.debug('попытка просто перейти на страницу гугла')

            self._driver.get('https://www.google.com/')

            if "Google" in self._driver.title:
                log.info('выход со встречи произведен')
            else:
                log.info('не удалось выйти со встречи второй раз. мы все еще на встречи!')

            log.exception('неизвестная ошибка, которая вызвала суматоху')

    def check_log_pass(self) -> bool:
        if not self._email or not self._password: return False
        return True