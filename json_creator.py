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
    for file in files:
        if file == 'db.json':
            db = {'id': {}, 'contests': [], 'rating_changes': []}
            json.dump(db, open('db.json', 'w'), indent=2)
        if file == 'log.json':
            log = {'log': []}
            json.dump(log, open('log.json', 'w'), indent=2)
