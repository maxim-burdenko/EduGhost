import asyncio
import time

from datetime import datetime

import pytz

from backend.logger import log
from backend.utils import get_kyiv_now, read_json
from backend.config import LINKS_JSON_PATH


class Manager:
    """
    класс занимается сбором все воедино, то есть заходим на пары, отмечаемся на дл, выполняем запись
    и это все при условии соответствующих флагов. Класс принимает на вход соответствующие объекты классов
    """

    _parser = None
    _google = None
    _driver = None
    _obs = None
    _dl = None
    _links = {}
    _same = False
    _is_message = False

    _lessons = []
    _windows = []

    def __init__(self, parser_, google_, obs_, dl_, driver_):
        self._parser = parser_
        self._google = google_
        self._driver = driver_
        self._dl = dl_

        self._links = read_json(LINKS_JSON_PATH)
        self._is_message = False

        self._loading_schedule = None
        self._schedule_lock = asyncio.Lock()

    async def _get_schedule(self):
        try:
            log.debug('получаем расписание с парсера')
            data = await self._parser.creation_schedule()
            if not data:
                log.info('на сегодня пар нет, отдыхаем')
                return []
            return data
        except Exception:
            log.exception('не удалось получить расписание по неизвестной причине')
            return []

    async def _ensure_schedule(self):
        # Первая проверка без блокировки: быстрый выход, если всё уже есть
        if self._lessons:
            return

        async with self._schedule_lock:
            # Вторая проверка после захвата лок: чтобы не загрузить второй раз
            if self._lessons:
                return

            if self._loading_schedule is None:
                self._loading_schedule = asyncio.create_task(self._get_schedule())

        # Ждём вне локировки (чтобы другие тоже могли ждать тот же task)
        self._lessons = await self._loading_schedule

        # Очистим task только если ты был "последним", кто дождался
        async with self._schedule_lock:
            self._loading_schedule = None

    def _next_same(self, lesson, index):
        if index + 1 < len(self._lessons):
            return lesson['name'] == self._lessons[index + 1]['name']
        return False

    @staticmethod
    async def get_lesson_status(lesson):
        """Определяем статус пары
            active: уже началась пара
            upcoming: пара еще не началась
            past: пара уже прошла/пропущена
            error: произошел неизвестный сбой
        """
        now_str = await get_kyiv_now()

        if not now_str:
            log.error('не удалось получить точное киевское время')
            log.warning('берем время устройства')
            kyiv_tz = pytz.timezone('Europe/Kyiv')
            now_str = datetime.now(kyiv_tz)

        now = datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S")
        start = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {lesson['start']}", "%Y-%m-%d %H:%M")
        end = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {lesson['end']}", "%Y-%m-%d %H:%M")

        if start < now < end:
            return "active", now, start, end
        elif now < start:
            return "upcoming", now, start, end
        elif now > end:
            return "past", now, start, end
        else:
            return "error", now, start, end

    async def handle_lesson_activity(self, lesson, lesson_index, activity_type):
        """Универсальный обработчик для пар (посещение пар, отметка посещений)"""
        link = ""
        log_prefix = ''
        # Получаем соответствующую ссылку в зависимости от типа деятельности
        try:
            if activity_type == "meeting":
                log_prefix = "посещение пары"
                link = self._links[lesson["name"]][lesson["type"]]["meeting"]
            elif activity_type == "attendance":
                log_prefix = "отметки на паре"
                link = self._links[lesson["name"]][lesson["type"]]["visiting"]
            else:
                log.error("неизвестный тип активности: %s", activity_type)
                return
        except KeyError:
            log.warning('не найдено ссылки для %s %r. пропускаем', log_prefix, lesson["name"])
        except Exception:
            log.exception('неизвестная ошибка при получение ссылки для %S', log_prefix)

        if not link:
            log.warning(f'нет ссылки для {log_prefix}: %r', lesson["name"])
            return

        status, now, start, end = await self.get_lesson_status(lesson)

        if status == "past":
            log.info('пара %r уже закончилась', lesson["name"])
            return
        elif status == "error":
            log.warning('сбой при проверке времени')
            log.debug('просто пропустили')
            return
        elif status == "upcoming":
            log.info('пара %r еще не началась', lesson["name"])

            difference = start - now
            seconds_left = int(difference.total_seconds())

            log.info('продолжим выполнения скрипта через %d с.', seconds_left)
            log.debug('ожидаем начала %s...', lesson["name"])

            await asyncio.sleep(seconds_left)

        # на этом этапе урок явно активен
        if activity_type == "meeting":
            # переключаемся на соответствующее окно
            self._driver.switch_to.window(self._get_window())

            await self._handle_meeting(lesson, lesson_index, link)
        elif activity_type == "attendance":
            # переключаемся на соответствующее окно
            self._driver.switch_to.window(self._get_window("attendance"))

            await self._handle_attendance(link, self._get_window("attendance"), self._get_window())

        # ожидаем конца пары...
        now = await get_kyiv_now(format_datetime=True)

        if not now:
            log.error('не удалось получить точное киевское время')
            log.warning('берем время устройства')
            now = datetime.now()

        to_end_couple = int((end - now).total_seconds()) - 600 # -10 минут, ибо никто не сидит до конца пар

        if activity_type == "meeting":
            log.info('до окончания %r осталось %d с.', lesson['name'], to_end_couple)
            log.debug('ожидаем конца пары...')

        if to_end_couple <= 600:
            log.info('до конца %r оставалось <= 10 минут. Пропускаем данную пару', lesson['name'])
            return
        await asyncio.sleep(to_end_couple)

        # проверяем одинаковая ли следующая пара
        if self._next_same(lesson, lesson_index) and activity_type == "meeting":
            self._same = True
            log.info('следующая пара такая же, а значит остаемся на встрече')
        elif not self._next_same(lesson, lesson_index) and activity_type == "meeting":
            self._same = False
            log.info('так как следующая пара другая, то выходим с %r', lesson["name"])

            self._driver.switch_to.window(self._get_window())
            log.debug('пытаемся выйти с конференции')
            self._google.exit_from_meeting()
            log.debug('должны были выйти с meet')
        else:
            # значит тут тип активности посещение
            return


    async def _handle_meeting(self, lesson, lesson_index, meeting_link):
        """отдельный процесс посещение встреч google meet"""
        if not self._same:
            log.info('пытаемся зайти на пару...')

            log.debug('переходим по ссылке на пару')
            self._driver.get(meeting_link)
            # конкретно ожидаем загрузки, ибо не выключится микро
            #(камера, если заклеена сама отключиться, а нет, то отключит скрипт)
            await asyncio.sleep(7)

            # так как было ожидание и явно перешли на другое окно
            self._driver.switch_to.window(self._get_window())


            log.debug('перешли по ссылке, отключаем микро и камеру')
            self._google.turn_off_cam_mic()
            log.debug('должны были отключить камеру и микро')

            log.debug('пытаемся зайти на саму пару...')
            self._google.join_the_meeting()
            log.info('зашли на пару %r', lesson["name"])


    async def _handle_attendance(self, visiting_link, window, meet_window):
        """отдельный процесс для отметки на сайте dl """
        log.info('пытаемся отметится на паре...')

        log.debug('переходим по ссылке для отметки')
        self._driver.get(visiting_link)
        await asyncio.sleep(4)

        self._driver.switch_to.window(window)

        try:
            # прям весь поток, ибо бегаем между окнами как угорелые и по итогу можем и не отметиться вовсе
            time.sleep(2)
            self._dl.mark_attendance()
        except:
            log.exception('неизвестная ошибка при попытке отметится')
        finally:
            # в любом случае переходим на окно с митом
            self._driver.switch_to.window(meet_window)


    def _get_window(self, for_="meeting"):
        tabs = self._driver.window_handles

        if len(tabs) > 2:
            log.warning('дело пахнет керосином. Больше двух табов')

        if for_ == "meeting":
            return tabs[0]
        elif for_ == "attendance":
            return tabs[1]
        else:
            log.error('не правильно передан параметр for_')
            return

    # те методы которые будут вызваться для выполнения поставленных задач, то есть основные методы
    async def google_meet_processing(self):
        await self._ensure_schedule()
        if not self._lessons:
            return

        for i, lesson in enumerate(self._lessons):
            await self.handle_lesson_activity(lesson, i, "meeting")

    async def attendance_processing(self):
        await self._ensure_schedule()
        if not self._lessons:
            return

        for i, lesson in enumerate(self._lessons):
            await self.handle_lesson_activity(lesson, i, "attendance")