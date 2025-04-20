import asyncio

from backend.logger import log
from backend.services.browser_service import BrowserServices
from backend.services.google_service import GoogleService
from backend.services.dl_service import DlService
from backend.services.parser_cist import ParserCist
from backend.services.manager import Manager
from backend.utils import get_settings_user, prevent_sleep, allow_sleep
from backend.config import firefox_binary

async def start():
    web_driver = None
    try:
        if not firefox_binary: log.error('не найден браузер Firefox'); return

        # тут бы проверять есть ли сегодня вообще пары и стоит ли вообще что-то делать...

        prevent_sleep() # предотвращает сон
        bs = BrowserServices()
        web_driver = bs.get_driver()

        g_login = get_settings_user('GOOGLE_LOGIN')
        g_password = get_settings_user('GOOGLE_PASSWORD')
        gs = GoogleService(email=g_login,password=g_password, driver=web_driver)

        dl_login = get_settings_user('DL_LOGIN')
        dl_password = get_settings_user('DL_PASSWORD')
        dl = DlService(login=dl_login, password=dl_password, driver=web_driver)

        parser = ParserCist(get_settings_user('GROUP'))

        manager = Manager(parser_=parser, google_=gs, dl_=dl, driver_=web_driver, obs_=None)


        if not dl.check_log_pass() and not gs.check_log_pass():
            log.error('нет не Google не DL. Делать нечего')
            return

        if gs.check_log_pass():
            gs.login()
        else:
            log.warning('пароля или логина для Google нет')

        if dl.check_log_pass():
            dl.login()
        else:
            log.warning('пароля или логина для DL нет')

        async with asyncio.TaskGroup() as tg:
            tg.create_task(manager.google_meet_processing())
            tg.create_task(manager.attendance_processing())

        log.info('на сегодня всё. Скрипт завершил свое выполнение без критических ошибок')
    except:
        log.exception('неизвестная ошибка при запуске/выполнение скрипта')
    finally:
        log.info('завершаем работу скрипта...')
        if web_driver: web_driver.quit()
        allow_sleep() # работает как обычно
        log.info('работа скрипта завершена')

def run():
    asyncio.run(start())