import asyncio


async def get_statistics(db):
    # 1: amount of users; 2: amount of unique cf_handles; 3: amount of unique ac_usernames
    stats = [len(db['id']), 0, 0]
    cf = set()
    ac = set()
    for user in db['id']:
        for handle in db['id'][user]['cf_handles']:
            cf.add(handle)
        for username in db['id'][user]['ac_usernames']:
            ac.add(username)

    stats[1] = len(cf)
    stats[2] = len(ac)
    return stats
