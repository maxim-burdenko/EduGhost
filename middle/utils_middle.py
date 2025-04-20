import os
import time

import eel

from dotenv import set_key, load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

from backend.logger import log
from backend.config import LINKS_JSON_PATH, GROUPS_JSON_PATH, SETTINGS_USER_JSON_PATH
from backend.utils import update_json, read_json, write_json
from backend.run import run


@eel.expose
def send_link(data):
    return update_json(LINKS_JSON_PATH, data)

@eel.expose
def get_links():
    return read_json(LINKS_JSON_PATH)

@eel.expose()
def delete_lesson(key):
    data = read_json(LINKS_JSON_PATH)

    if not data: return

    if key in data:
        log.info('была найдена пара для удаления')
        del data[key]
        log.info('из словаря была удалена пара %r', key)
    else:
        log.warning('ключ не найден в файле ссылок')
        return

    write_json(LINKS_JSON_PATH, data)

@eel.expose
def write_env(key:str, value:str):
    data = {'settings':{key:value}}
    update_json(SETTINGS_USER_JSON_PATH, data)

@eel.expose
def check_env(key:str) -> bool:
    data = read_json(SETTINGS_USER_JSON_PATH)
    if data["settings"][key]: return True
    return False

@eel.expose
def start_script():
    run()

@eel.expose
def get_groups():
    return list(read_json(GROUPS_JSON_PATH).keys())

@eel.expose
def check_group():
    try:
        return read_json(SETTINGS_USER_JSON_PATH)["settings"]["GROUP"]
    except KeyError:
        log.error('не получили значение по ключу GROUP')
    except:
        log.exception('неизвестная ошибка при получение проверке группы')