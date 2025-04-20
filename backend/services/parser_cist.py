import asyncio
import re
import aiohttp

from bs4 import BeautifulSoup
from bs4.element import Tag
from datetime import datetime, timedelta

from backend.logger import log
from backend.config import GROUPS_JSON_PATH
from backend.utils import read_json, write_json, TYPE_LESSON_MAP

class ParserCist:

    _base_url = ('https://cist.nure.ua/ias/app/tt/f?p=778:201:4339783663749301:::'
                 '201:P201_FIRST_DATE,P201_LAST_DATE,P201_GROUP,P201_POTOK:')
    _home_cist = 'https://cist.nure.ua/ias/app/tt/f?p=778:2:277102197691492::NO#'
    _name_group = ''
    _stream = ''
    _headers = {"User-Agent": "Mozilla/5.0"}
    _schedule = []
    _today = datetime.today().strftime('%d.%m.%Y')

    def __init__(self, name_group:str, stream='0'):
        self._name_group = name_group
        self._stream = stream

    async def _get_group_id(self) -> int:
        if not self._name_group:
            log.error('нет названия группы')
            return -1

        groups = read_json(GROUPS_JSON_PATH)

        if not groups:
            log.warning('не было получено групп из файла')
            groups = await self._group_formation()

            if not groups: return -1

            log.info('группы были получены с сайта')

        if self._name_group in groups:
            return groups[self._name_group]

        log.error('группа не была найдена')
        return -1

    async def _create_schedule_url(self) -> str:
        log.info('попытка сформировать ссылку...')
        id_group = await self._get_group_id()

        if id_group < 0:
            log.error('не было получено id группы %s', self._name_group)
            return ''

        log.debug('получено дату и групу, формируем ссылку...')
        url = self._base_url + '%s,%s,%s,%s' % (self._today, self._today, id_group, self._stream)
        log.info('ссылка сформирована')
        return url

    async def _get_page(self, url: str) -> BeautifulSoup:
        log.debug('пытаемся получить страницу...')
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.request(
                    method='GET',
                    url=url,
                    headers=self._headers
                )
                response.raise_for_status()
                html = await response.text()
                log.debug('страница %r была получена', url)
                return BeautifulSoup(html, "lxml")

        except aiohttp.ClientResponseError as e:
            log.error("HTTP ошибка при получении страницы %r: %s %s", url, e.status, e.message)
        except aiohttp.ClientError as e:
            log.error("сетевая ошибка при получении страницы %r: %s", url, str(e))
        except Exception:
            log.exception("неизвестная ошибка при получении страницы %r", url)

        return BeautifulSoup('', 'lxml')

    async def _get_target_row(self) -> Tag | None:
        log.info('попытка получить целевую строку...')

        url = await self._create_schedule_url()
        schedule_page = await self._get_page(url)

        if not url or not schedule_page:
            log.error('не было получено ссылку на пары или таблицу пар')
            return None

        table = schedule_page.find("table", class_="MainTT")

        log.debug('поиск целевой строки в таблице...')
        for tr in table.find_all("tr"):
            if self._today in tr.text:
                log.info('получили целевую строку')
                return tr

    @staticmethod
    def _pair_creation(row):
        tds = row.find_all("td")
        if len(tds) >= 3:
            log.debug('создаем пару...')

            pair_number = tds[0].text.strip()  # Номер пары
            time_range = tds[1].text.strip()  # Время начала и окончания пары
            pair_details = tds[2].text.strip()  # Название и тип пары

            # Разделяем время начала и окончания
            start_time, end_time = time_range.split(" ") if len(time_range.split()) == 2 else ("", "")

            # Разделяем название и тип пары
            parts = pair_details.split()

            if len(parts) >= 2:
                pair_name = parts[0]  # Первое слово — это название
                pair_type = parts[1]  # Второе слово — это тип пары
            else:
                log.warning('название и тип пары равен пустрой строке')
                pair_name, pair_type = parts[0], ""  # Если частей меньше, то тип пары будет пустым

            mapped_type = TYPE_LESSON_MAP[pair_type]

            pair_info = {
                "number": pair_number,
                "name": pair_name,
                "type": mapped_type,
                "start": start_time,
                "end": end_time,
            }
            log.debug('пара %r была создана',pair_info["name"])
            return pair_info

    async def creation_schedule(self):
        log.info('попытка сформировать расписание на сегодня...')

        target_row = await self._get_target_row()

        if not target_row:
            log.error('не получена целевая строка сегодняшнего дня')
            return []

        next_rows = target_row.find_all_next("tr")
        tomorrow = (datetime.today() + timedelta(days=1)).strftime("%d.%m.%Y")
        pairs = []

        log.debug('формируем сегодняшние расписание для группы %r', self._name_group)
        for row in next_rows:
            if tomorrow in row.text: break

            info = self._pair_creation(row)
            if info:
                pairs.append(info)

        log.info('закончено формирование расписания на сегодня')
        return pairs

    async def _group_formation(self) -> dict:
        log.info('выполняем запись данных о групах в файл...')
        log.debug('попытка получить главную страницу расписания')
        page = await self._get_page(self._home_cist)

        if not page:
            log.error('страница не была получена')
            return {}

        log.debug('страница получена, извлекаем данные...')
        # получаю id групп только для факультета КН
        try:
            table = page.select(selector='#GROUPS_AJAX > table:nth-child(2)')[0]
        except Exception:
            log.exception('при получении таблицы факультетов')
            return {}

        log.debug('получение всех ссылок с группами')


        links = table.find_all('a')

        if not links:
            log.error('не удалось получть ссылки с группами')
            return {}

        groups = {}
        log.debug('попытка получить id групп..')

        for link in links:
            onclick = link.get('onclick')

            match = re.search(r"IAS_ADD_Group_in_List\('([^']+)',(\d+)\)", onclick)

            if match:
                group_name = match.group(1)
                group_id = int(match.group(2))
                groups[group_name] = group_id

        if not groups:
            log.error('не удалось сформировать id групп')

        log.debug('выполняем запись в файл %r', GROUPS_JSON_PATH)
        write_json(GROUPS_JSON_PATH, groups)
        log.info('файл с группами записан')

        return groups

# ps = ParserCist('ІТУ-22-1')
# async def start():
#     print(await ps.creation_schedule())
#
# asyncio.run(start())

