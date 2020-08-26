import asyncio
import time
from typing import List

from asyncio.exceptions import TimeoutError

import aiohttp
import requests
import json
import datetime

lock = asyncio.Lock()


async def get(url):
    async with lock:
        await asyncio.sleep(0.2)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(url) as response:
                return await response.text()


async def check_handles(handles: List):
    if len(handles) == 0:
        return None, [], []
    try:
        a = await get(f'https://codeforces.com/api/user.info?handles={";".join(handles)}')
    except TimeoutError:
        raise TimeoutError('Timeout Error: check_handles()')
    result = json.loads(a)
    if result['status'] == 'FAILED':
        bad_one = result['comment'][26:result['comment'].find('not') - 1]
        bad_index = handles.index(bad_one)
        good_ones = handles[:bad_index]
        left = handles[bad_index + 1:]
        return bad_one, good_ones, left
    else:
        return None, handles, []


async def get_multiple_ratings(handles: List):
    try:
        a = await get(f'https://codeforces.com/api/user.info?handles={";".join(handles)}')
    except TimeoutError:
        raise TimeoutError('Timeout Error: get_multiple_ratings()')
    result = json.loads(a)
    if result['status'] != 'FAILED':
        users = []
        for user in result['result']:
            users.append((user['handle'], user.get('rating', 0)))
        return users
    return []


async def get_rating_changes(id):
    try:
        a = await get(f'https://codeforces.com/api/contest.ratingChanges?contestId={id}')
    except TimeoutError:
        raise TimeoutError('Timeout Error: get_rating_changes()')
    result = json.loads(a)
    if result['status'] == 'FAILED':
        if result['comment'] == 'contestId: Rating changes are unavailable for this contest':
            return False, False
        return False, True
    elif len(result['result']) == 0:
        return False, True
    else:
        return True, result['result']


async def get_upcoming():
    import bot
    try:
        a = await get('https://codeforces.com/api/contest.list')
    except TimeoutError:
        raise TimeoutError('Timeout Error: get_upcoming()')
    all_codeforces_contests = json.loads(a)
    codeforces_contests = []
    times = []
    names = []
    durations = []
    for i in all_codeforces_contests['result']:
        if i['id'] == int(bot.db['last_codeforces']['name'][40:bot.db['last_codeforces']['name'].find('>') - 1]):
            break
        codeforces_contests.append(i)
        times.append(datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=i['startTimeSeconds']))
        names.append(f"<a href=\"https://codeforces.com/contest/{i['id']}\">{i['name']}</a>")
        durations.append(str(i['durationSeconds'] // 60) + ' minutes')

    table = []
    contest_type = 'cf'
    for i in range(len(times)):
        table.append([times[i], names[i], durations[i], contest_type])

    return table


if __name__ == '__main__':
    print(asyncio.run(get('https://codeforces.com/api/contest.list')))
