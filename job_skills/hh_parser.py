import asyncio
import re
import os
import time
import logging
from datetime import datetime
from sqlalchemy.sql import select, insert, update
import aiopg
import requests
import ujson
import sqlalchemy as sa
from sqlalchemy.ext.automap import automap_base
from aiohttp import ClientSession
from aiopg.sa import create_engine


def setup_logger(name: str, log_file: str, level: int):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s"))

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


async def get_vacancies(conn: object, search: str, tracker_id: int, excluded_from_search: str = 0) -> None:
    """
    ассинхронная функция для парсинга hh на вакансии и заполнения ими БД
    """
    r = requests.get(f'https://api.hh.ru/vacancies/', params={'text': f'{search}', 'per_page': '0'}, headers=HEADERS)
    number_of_vacancies = r.json()['found']
    page = 0
    id_of_vacancies = []
    # Получаем все id у вакансий
    async with ClientSession() as session:
        for iteration in range(number_of_vacancies // 100 + 1):
            async with session.get(f'https://api.hh.ru/vacancies/',
                                   params={'text': f'{search}', 'excluded_text': excluded_from_search, 'per_page': '100', 'page': f'{page}'}, headers=HEADERS) as vacancies:
                try:
                    vacancies_json = await vacancies.json()
                    for item in vacancies_json['items']:
                        id_of_vacancies.append(item['id'])
                    page += 1
                except KeyError:
                    page += 1

    while True:
        try:
            parser_id = await conn.execute(ParserData.insert().values(amount_of_vacancies=number_of_vacancies, date=today, tracker_id=tracker_id).returning(ParserData.c.id))
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
                await conn.execute(SkillData.insert().values(parser_data_id=parser_id, name=skill, amount=skills[skill]))
                break
            except RuntimeError:
                await asyncio.sleep(5)
    return number_of_vacancies


async def get_all_trackers(conn):
    """
    ассинхроная функция для получения всех трекеров из бд
    """
    result = []
    async for row in conn.execute(select(JobTracker.search_text, JobTracker.exclude_from_search, JobTracker.id)):
        result.append(row)
    return result


async def get_tracker(conn, tracker_id):
    """
    ассинхроная функция для получения всех трекеров из бд
    """
    result = await conn.execute(select(JobTracker).where(JobTracker.id == tracker_id))
    return await result.fetchone()


async def main(tracker_id: int = None):
    global today, ParserData, SkillData, JobTracker
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

    JobTracker = Base.classes.job_skills_jobtracker
    dsn = 'dbname=hhss user=hhss_admin password=coolpas123 host=db'
    today = datetime.today()

    async def start_parsing(tracker: list):
        print(tracker)
        try:
            start_time = datetime.now()
            number_of_vacancies = await get_vacancies(conn, tracker[0], tracker[2], tracker[1])
        except Exception:
            error_logger.exception(f'JobTracker({tracker[2]},{tracker[0]}) failed')
        else:
            info_logger.info(
                f'JobTracker({tracker[2]},{tracker[0]}) with {number_of_vacancies} vacancies, parsed for {datetime.now() - start_time}')

    async with create_engine(dsn=dsn) as engine:
        async with engine.acquire() as conn:
            if not tracker_id:
                trackers = await get_all_trackers(conn)
                await asyncio.gather(*[asyncio.ensure_future(start_parsing(tracker)) for tracker in trackers])

            elif tracker_id and type(tracker_id) == int:
                try:
                    start_time = datetime.now()
                    tracker = await get_tracker(conn, tracker_id)
                    number_of_vacancies = await get_vacancies(conn, tracker[1], tracker[0], tracker[3])
                except Exception:
                    error_logger.exception(f'{tracker_id} failed')
                else:
                    info_logger.info(f'JobTracker({tracker_id},{tracker[1]}) with {number_of_vacancies} vacancies, parsed for {datetime.now()-start_time}')


def parse_one_tracker(tracker_id: int = None):
    asyncio.run(main(tracker_id=tracker_id))

if __name__ == "__main__":
    asyncio.run(main())
