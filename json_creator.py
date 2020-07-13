import os
import asyncio
import json


def check():
    files = []
    if not os.path.exists('db.json'):
        files.append('db.json')
    if not os.path.exists('log.json'):
        files.append('log.json')
    if files:
        asyncio.run(create(files))


async def create(files):
    import codeforces
    import atcoder
    for file in files:
        if file == 'db.json':
            cf_name = await codeforces.get_last()
            ac_name = await atcoder.get_last()
            db = {'id': {}, 'contests': [], 'last_codeforces': {'name': cf_name, 'status': 1},
                  'last_atcoder': {'name': ac_name, 'status': 1}}
            json.dump(db, open('db.json', 'w'), indent=2)
        if file == 'log.json':
            log = {'log': []}
            json.dump(log, open('log.json', 'w'), indent=2)
