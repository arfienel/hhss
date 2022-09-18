import asyncio
import re
import time
from datetime import datetime
from sqlalchemy.sql import select, insert, update
import aiopg
import requests
import ujson
import sqlalchemy as sa
from sqlalchemy.ext.automap import automap_base
from aiohttp import ClientSession
from aiopg.sa import create_engine


sqlalchemy_engine = sa.create_engine('postgresql://hhss_admin:coolpas123@localhost:5432/hhss')

metadata = sa.MetaData(bind=True)

metadata.reflect(sqlalchemy_engine)

Base = automap_base(metadata=metadata)

Base.prepare()


ParserData = sa.Table('job_skills_parserdata', metadata,
                      autoload=True, autoload_with=sqlalchemy_engine)

SkillData = sa.Table('job_skills_skilldata', metadata,
                     autoload=True, autoload_with=sqlalchemy_engine)

JobTracker = Base.classes.job_skills_jobtracker


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

    parser_id = await conn.execute(ParserData.insert().values(amount_of_vacancies=number_of_vacancies, date=today, tracker_id=tracker_id, error_log='').returning(ParserData.c.id))
    parser_id = (await parser_id.fetchone())[0]
    # Получаем все скиллы требуемые для вакансии и загружаем их куда нибудь
    skills = {}
    async with ClientSession() as session:
        for vac_id in id_of_vacancies:
            async with session.get(f'https://api.hh.ru/vacancies/{vac_id}', headers=HEADERS) as vacancy:
                try:
                    vacancy = await vacancy.json()
                    vacancy['key_skills']
                except KeyError:
                    continue
                else:
                    for skill in vacancy['key_skills']:
                        if skill['name'] not in skills.keys():
                            skills.setdefault(skill['name'], 1)
                        else:
                            skills[skill['name']] += 1

    for skill in skills:
        await conn.execute(SkillData.insert().values(parser_data_id=parser_id, tracker_id=tracker_id, name=skill, amount=skills[skill]))


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
    global today
    """
    Основная функция для запуска парсера
    :type tracker_id: id трекера который надо спарсить, если не указать, то будут парсится все трекеры из бд
    """
    dsn = 'dbname=hhss user=hhss_admin password=coolpas123 host=localhost'
    today = datetime.today()
    async with create_engine(dsn=dsn) as engine:
        async with engine.acquire() as conn:
            if not tracker_id:
                trackers = await get_all_trackers(conn)
                for tracker in trackers:
                    await get_vacancies(conn, tracker[0], tracker[2], tracker[1])
            elif tracker_id and type(tracker_id) == int:
                tracker = await get_tracker(conn, tracker_id)
                await get_vacancies(conn, tracker[1], tracker[0], tracker[3])


def parse_one_tracker(tracker_id: int = None):
    asyncio.run(main(tracker_id=tracker_id))


if __name__ == "__main__":
    asyncio.run(main())