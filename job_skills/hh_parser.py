import asyncio
import re
import os
import time
import logging
from datetime import datetime
from sqlalchemy.sql import update, select, insert
import aiopg
import requests
import ujson
import sqlalchemy as sa
from sqlalchemy.ext.automap import automap_base
from aiohttp import ClientSession
from aiopg.sa import create_engine
from psycopg2.errors import UniqueViolation


def setup_logger(name: str, log_file: str, level: int):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s"))

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


os.chdir('/code/job_skills')

try:
    app_token = open('app_token.txt', 'r').readline()
except FileNotFoundError:
    app_token = None

if app_token:
    HEADERS = {
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
        'accept': '*/*',
        'Authorization': 'Bearer ' + app_token
    }

else:
    HEADERS = {
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
        'accept': '*/*',
    }


async def get_vacancies(conn: object, tracker: object) -> None:
    """
    ассинхронная функция для парсинга hh на вакансии и заполнения ими БД
    """
    r = requests.get(f'https://api.hh.ru/vacancies/',
                     params=((('experience', f'{tracker.work_experience}') if tracker.work_experience != '' else ('', '')),
                             ('text', f'{tracker.search_text}'),
                             ('excluded_text', tracker.exclude_from_search), ('per_page', '0'),
                             *(('area', area) for area in tracker.areas),
                             *(('schedule', schedule) for schedule in tracker.work_schedule),
                             *(('employment', employment) for employment in tracker.employment_type)
                             ),
                     headers=HEADERS, )
    print(r.url)
    print(r.json())
    number_of_vacancies = r.json()['found']
    page = 0
    id_of_vacancies = []
    # Получаем все id у вакансий
    async with ClientSession() as session:
        for iteration in range(number_of_vacancies // 100 + 1):
            async with session.get(f'https://api.hh.ru/vacancies/',
                                   params=(
                                           ('text', f'{tracker.search_text}'),
                                           (('experience', f'{tracker.work_experience}') if tracker.work_experience != '' else ('', '')),
                                           ('excluded_text', tracker.exclude_from_search),
                                           ('per_page', '100'), ('page', f'{page}'),
                                           *(('area', area) for area in tracker.areas),
                                           *(('schedule', schedule) for schedule in tracker.work_schedule),
                                           *(('employment', employment) for employment in tracker.employment_type)
                                   ), headers=HEADERS) as vacancies:
                try:
                    vacancies_json = await vacancies.json()
                    for item in vacancies_json['items']:
                        id_of_vacancies.append(item['id'])
                    page += 1
                except KeyError:
                    page += 1

    while True:
        try:
            parser_id = await conn.execute(
                ParserData.insert().values(amount_of_vacancies=number_of_vacancies, date=today,
                                           tracker_id=tracker.id).returning(ParserData.c.id))
            parser_id = (await parser_id.fetchone())[0]
            break
        except RuntimeError:
            await asyncio.sleep(5)
    # Получаем все скиллы требуемые для вакансии и загружаем их куда нибудь
    skills = {}
    async with ClientSession() as session:
        for vac_id in id_of_vacancies:
            async with session.get(f'https://api.hh.ru/vacancies/{vac_id}', headers=HEADERS) as vacancy:
                try:
                    vacancy = await vacancy.json()
                    vacancy['key_skills']
                except KeyError as exc:
                    continue
                else:
                    for skill in vacancy['key_skills']:

                        if skill['name'] not in skills.keys():
                            skills[skill['name']] = 1
                        else:
                            skills[skill['name']] += 1

    for skill in skills:
        while True:
            try:
                await conn.execute(
                    SkillData.insert().values(parser_data_id=parser_id, name=skill, amount=skills[skill]))
                break
            except RuntimeError:
                await asyncio.sleep(5)

    await conn.execute(update(JobTracker).where(JobTracker.id == tracker.id).values(status_parser=True))
    while True:
        try:

            break
        except RuntimeError:
            await asyncio.sleep(5)
    return number_of_vacancies


async def get_all_trackers(conn):
    """
    ассинхроная функция для получения всех трекеров из бд
    """
    result = []
    async for row in conn.execute(select(JobTracker)):
        result.append(JobTracker(id=row[0], search_text=row[1], status_parser=row[2], exclude_from_search=row[3],
                                 modified_date=row[4], user_creator_id=row[5], hh_url=row[6],
                                 areas=row[7], employment_type=row[8], work_experience=row[9], work_schedule=row[10]))
    return result


async def update_all_areas(conn):
    """
    :param conn:
    """
    areas = []

    def unnest(nested_areas):
        for k, v in nested_areas.items():
            if k == 'id':
                hh_id = v
            if k == 'name':
                name = v
            if k == 'areas':
                areas.append((hh_id, name))
                for area in v:
                    unnest(area)

    r = requests.get(f'https://api.hh.ru/areas/')
    for item in r.json():
        unnest(item)

    for area in areas:
        while True:
            try:
                await conn.execute(Area.insert().values(hh_id=area[0], name=area[1]))
                break
            except RuntimeError:
                await asyncio.sleep(5)
            except UniqueViolation:
                break


async def get_tracker(conn, tracker_id: int):
    """
    ассинхроная функция для получения всех трекеров из бд
    """
    result = await conn.execute(select(JobTracker).where(JobTracker.id == tracker_id))
    query = await result.fetchone()
    print(query)
    tracker = JobTracker(id=query[0], search_text=query[1], status_parser=query[2], exclude_from_search=query[3],
                         modified_date=query[4], user_creator_id=query[5], hh_url=query[6],
                         areas=query[7], employment_type=query[8], work_experience=query[9], work_schedule=query[10])
    return tracker


async def main(tracker_id: int = None):
    global today, ParserData, SkillData, JobTracker, Area
    """
    Основная функция для запуска парсера
    :type tracker_id: id трекера который надо спарсить, если не указать, то будут парсится все трекеры из бд
    """

    info_logger = setup_logger('parser_info_logger', 'logs/parser_info_log.log', logging.INFO)

    error_logger = setup_logger('parser_error_logger', 'logs/parser_error_log.log', logging.ERROR)

    sqlalchemy_engine = sa.create_engine('postgresql://hhss_admin:coolpas123@db:5432/hhss')

    metadata = sa.MetaData(bind=True)

    metadata.reflect(sqlalchemy_engine)

    Base = automap_base(metadata=metadata)

    Base.prepare()

    ParserData = sa.Table('job_skills_parserdata', metadata,
                          autoload=True, autoload_with=sqlalchemy_engine)

    SkillData = sa.Table('job_skills_skilldata', metadata,
                         autoload=True, autoload_with=sqlalchemy_engine)

    Area = sa.Table('job_skills_area', metadata,
                    autoload=True, autoload_with=sqlalchemy_engine)

    JobTracker = Base.classes.job_skills_jobtracker
    dsn = 'dbname=hhss user=hhss_admin password=coolpas123 host=db'
    today = datetime.today()

    async def start_parsing(tracker: object):
        """
        ассинхроный запуск парсинга трекера и его логирование
        """
        try:
            start_time = datetime.now()
            number_of_vacancies = await get_vacancies(conn, tracker)
        except Exception:
            error_logger.exception(f'JobTracker({tracker.search_text},{tracker.id}) failed')
        else:
            info_logger.info(
                f'JobTracker({tracker.search_text},{tracker.id}) with {number_of_vacancies} vacancies, parsed for {datetime.now() - start_time}')

    async with create_engine(dsn=dsn) as engine:
        async with engine.acquire() as conn:
            if not tracker_id:
                await update_all_areas(conn)
                trackers = await get_all_trackers(conn)
                await asyncio.gather(*[asyncio.ensure_future(start_parsing(tracker)) for tracker in trackers])

            elif tracker_id and type(tracker_id) == int:
                try:
                    start_time = datetime.now()
                    tracker = await get_tracker(conn, tracker_id)
                    number_of_vacancies = await get_vacancies(conn, tracker)
                except Exception:
                    error_logger.exception(f'{tracker_id} failed')
                else:
                    info_logger.info(
                        f'JobTracker({tracker_id},{tracker.search_text}) with {number_of_vacancies} vacancies, parsed for {datetime.now() - start_time}')


def parse_one_tracker(tracker_id: int = None):
    asyncio.run(main(tracker_id=tracker_id))


if __name__ == "__main__":
    #asyncio.run(main())
    asyncio.run(main(tracker_id=17))