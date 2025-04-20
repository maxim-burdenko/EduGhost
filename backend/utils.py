import ctypes
import json
import os
import aiohttp

from datetime import datetime, timedelta

from backend.logger import log
from backend.config import SETTINGS_USER_JSON_PATH
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

TYPE_LESSON_MAP={'Лк': "lecture", "Пз": "practice", "Лб": "laboratory"}
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

def read_json(filepath:str) -> dict:
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            if not content.strip() or content == '{}':
                log.error('файл %r пуст', filepath)
                return {}
            return json.loads(content)
    except FileNotFoundError:
        log.error('файл %r не найден', filepath)
    except json.JSONDecodeError:
        log.error('при декодирование файла %r', filepath)
    except ValueError:
        log.exception('не был найден ключ')
    except Exception:
        log.exception('неизвестная ошибка при чтение файла %r', filepath)

    return {}

def write_json(filepath:str, data:dict):
    if not filepath:
        log.error('пустой путь к файлу или пусты данные')
        return

    if not data:
        log.warning('словарь с данными пуст!')

    try:
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(json_data)
    except FileNotFoundError:
        log.error('файл %r не найден', filepath)
    except Exception:
        log.exception('неизвестная ошибка при записи файла %r', filepath)

def update_json(filepath:str, data:dict):
    if not data or not filepath:
        log.error('пустой путь к файлу или пусты данные')
        return

    exist_data = read_json(filepath)

    try:
        deep_update(exist_data, data)
    except Exception:
        log.exception('неизвестная ошибка при обновлении данных словаря')

    write_json(filepath, exist_data)

def deep_update(orig: dict, new: dict):
    for key, val in new.items():
        if isinstance(val, dict) and isinstance(orig.get(key), dict):
            deep_update(orig[key], val)
        else:
            orig[key] = val


def get_settings_user(key:str, filepath:str=SETTINGS_USER_JSON_PATH)->str:
    data = read_json(filepath)
    if data: return data['settings'][key]
    return ''

_cached_time = None
_last_fetched = None

async def get_kyiv_now(format_datetime=False):
    global _cached_time, _last_fetched

    log.info('запрос киевского времени...')

    # Если кеш свежий (меньше 60 секунд) — используем его
    if _cached_time and _last_fetched and datetime.utcnow() - _last_fetched < timedelta(minutes=1):
        log.debug('используем закешированное время')
        if format_datetime:
            return datetime.strptime(_cached_time, "%Y-%m-%d %H:%M:%S")
        return _cached_time

    url = (f'http://api.timezonedb.com/v2.1/get-time-zone?'
           f'key={os.getenv("TOKEN_TIMEZONE")}&format=json&by=zone&zone=Europe/Kyiv')
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)

            log.debug('отправлен запрос на получение времени...')

            # Проверяем статус и тип контента
            if response.status == 200 and response.content_type == 'application/json':
                data = await response.json()
                if data['status'] == 'OK':
                    log.info('киевское время получено успешно')
                    _cached_time = data['formatted']
                    _last_fetched = datetime.utcnow()

                    if format_datetime:
                        return datetime.strptime(_cached_time, "%Y-%m-%d %H:%M:%S")
                    return _cached_time
                else:
                    log.warning('ответ API не OK: %s', data)
            else:
                text = await response.text()
                log.warning('неправильный ответ: %s, %s', response.status, response.content_type)
                log.debug('ответ:\n%s', text)

    except Exception:
        log.exception('ошибка при получении киевского времени')

    # Фолбэк: если ничего не вышло, возвращаем кеш, если он есть
    if _cached_time:
        log.warning('возвращаем устаревшее кешированное время')
        if format_datetime:
            return datetime.strptime(_cached_time, "%Y-%m-%d %H:%M:%S")
        return _cached_time

    return None

def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )
    log.debug('включено предотвращение сна')

def allow_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    log.debug('предотвращение сна отключено — система работает штатно')