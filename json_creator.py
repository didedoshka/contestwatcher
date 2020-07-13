import os

import json


async def check():
    if not os.path.exists('db.json'):
        await create(['db.json'])
    if not os.path.exists('log.json'):
        await create(['log.json'])


async def create(files):
    import codeforces
    import atcoder
    for file in files:
        if file == 'db.json':
            cf_name = await codeforces.get_last()
            ac_name = await atcoder.get_last()
            db = {'contest': [], 'id': {}, 'contests': [], 'last_codeforces': {'name': cf_name, 'status': 1},
                  'last_atcoder': {'name': ac_name, 'status': 1}}
            json.dump(db, open('db.json', 'w'), indent=2)
        if file == 'log.json':
            log = {'log': []}
            json.dump(log, open('log.json', 'w'), indent=2)
