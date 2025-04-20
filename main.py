import eel
import middle.utils_middle

from backend.logger import log

if __name__ == "__main__":
    try:
        log.info('запуск главного окна')
        eel.init('client')
        eel.start('index.html', mode='default')
    except:
        log.exception('при запуске/выполнении главного окна')