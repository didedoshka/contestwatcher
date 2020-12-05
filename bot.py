import asyncio
import logging

from aiogram import Bot, Dispatcher, executor, types, exceptions
import re

import json
import atcoder
import codeforces
import datetime
import sys
import config
import json_creator
import time
import statistics

API_TOKEN = config.API_TOKEN
persons_to_remove = []

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

json_creator.check()

db = json.load(open("db.json", 'r'))
log = json.load(open("log.json", 'r'))

start_message = "Hi!\n" \
                "I'm @didedoshka CW Bot!\n" \
                "Notice that every value should be given in the replied message of your command!\n\n" \
                "List of commands:\n" \
                "/help - Get this list\n" \
                "/upcoming - Get the next scheduled contests\n" \
                "/usernames - Get the info about adding and removing usernames\n" \
                "/timezone - Change current timezone\n" \
                "/status - Change the way you get notifications (0 - off, 1 - on, 2 - silent)\n" \
                "/notifications - Change the time you get notifications"


async def add_log(string):
    d = {'time': datetime.datetime.now().isoformat(), 'value': string}
    log['log'].append(d)
    await save_log()


def sync_add_log(string):
    d = {'time': datetime.datetime.now().isoformat(), 'value': string}
    log['log'].append(d)
    sync_save_log()


async def save_log():
    if len(log['log']) == 500:
        log['log'] = []

    json.dump(log, open('log.json', 'w'), indent=2)


def sync_save_log():
    if len(log['log']) == 500:
        log['log'] = []

    json.dump(log, open('log.json', 'w'), indent=2)


# help
@dp.message_handler(commands=['help'])
async def send_welcome(message: types.Message):
    await message.reply(start_message)


async def add_person(message: types.Message):
    if db['id'].get(str(message.chat['id'])) is None:
        await add_log(f'person added to db ({str(message.chat["id"])})')
        db['id'][str(message.chat['id'])] = {"tz": "UTC+02:00",
                                             "status": 1,
                                             "notifications": [
                                                 15,
                                                 60,
                                                 1440
                                             ], "cf_handles": {},
                                             "ac_usernames": {}}
        save_json()


async def remove_person(user):
    if db['id'].get(user) is not None:
        await add_log(f'person added to "remove person" list ({user})')
        persons_to_remove.append(user)


async def remove_persons_from_db():
    for user in persons_to_remove:
        try:
            db['id'].pop(user)
            await add_log(f'person removed from db ({user})')
        except KeyError:
            await add_log(f'AHAHAHAHHAHAHAHAHA, cant remove person from db ({user})')
    save_json()
    persons_to_remove = []


# start
@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    await add_person(message)
    await message.reply(start_message)


def load_json():
    for i in range(len(db['contests'])):
        db['contests'][i][0] = datetime.datetime.fromisoformat(db['contests'][i][0])


async def get_upcoming():
    try:
        upcoming = []
        upcoming.extend(await atcoder.parse_upcoming())
        upcoming.extend(await codeforces.get_upcoming())

        upcoming.sort()

        for i in range(len(upcoming)):
            upcoming[i][0] = datetime.datetime.isoformat(upcoming[i][0])
        db['contests'] = upcoming
        json.dump(db, open('db.json', 'w'), indent=2)
        load_json()
        sync_add_log('upcoming was gotten')
    except Exception as e:
        sync_add_log(f'!upcoming wasn\'t gotten. {e}')
        raise e


def save_json():
    for i in range(len(db['contests'])):
        db['contests'][i][0] = datetime.datetime.isoformat(db['contests'][i][0])
    json.dump(db, open('db.json', 'w'), indent=2)
    load_json()


async def save_json_periodically(wait_for):
    while True:
        save_json()
        await asyncio.sleep(wait_for)


async def remove_cf_from_db(handles, message: types.Message):
    try:
        now = time.time()
        handles_to_remove = []
        not_existing_handles = []
        not_in_handle_list = []

        bad_one = ''
        left = [re.sub(r'[^A-Za-z0-9._-]', '', handle) for handle in handles]
        while bad_one is not None:
            bad_one, good_ones, left = await codeforces.check_handles(left)
            if bad_one is not None:
                not_existing_handles.append(bad_one)
            handles_to_remove.extend(good_ones)

        handles_to_remove_from_handles_to_remove = []

        for handle in handles_to_remove:
            if handle not in db['id'][str(message.chat['id'])]['cf_handles']:
                not_in_handle_list.append(handle)
                handles_to_remove_from_handles_to_remove.append(handle)

        for handle in handles_to_remove_from_handles_to_remove:
            handles_to_remove.remove(handle)

        for handle in handles_to_remove:
            db['id'][str(message.chat['id'])]['cf_handles'].pop(handle)

        save_json()
        await add_log(
            f'cf users were removed ({str(message.chat["id"])}) {handles_to_remove} in {time.time() - now:.3f}s')
        return handles_to_remove, not_existing_handles, not_in_handle_list
    except Exception as e:
        await add_log(f'During removing cf handles exception was raised. {e}')


async def remove_ac_from_db(usernames, message: types.Message):
    try:
        now = time.time()
        usernames_to_remove = []
        not_existing_usernames = []
        not_in_username_list = []
        users = []

        for username in usernames:
            users.append((username, dp.loop.create_task(atcoder.check_username(username.lstrip(' ')))))

        for inputted, username in users:
            ac_username = await username
            if not ac_username:
                not_existing_usernames.append(inputted.lstrip(' '))
                continue
            if ac_username in db['id'][str(message.chat['id'])]['ac_usernames']:
                usernames_to_remove.append(ac_username)
                continue
            else:
                not_in_username_list.append(ac_username)

        for username in usernames_to_remove:
            if username in db['id'][str(message.chat['id'])]['ac_usernames']:
                db['id'][str(message.chat['id'])]['ac_usernames'].pop(username)

        save_json()
        await add_log(
            f'ac users were removed ({str(message.chat["id"])}) {usernames_to_remove} in {time.time() - now:.3f}s')
        return usernames_to_remove, not_existing_usernames, not_in_username_list
    except Exception as e:
        await add_log(f'During removing ac usernames exception was raised. {e}')


@dp.message_handler(commands=['remove_ac'])
async def remove_ac(message: types.Message):
    await add_person(message)
    await message.reply('Send me ac usernames you want to remove.\n'
                        'You can send a list of them.\n'
                        'Separate them with commas, please',
                        reply_markup=types.ForceReply.create(selective=True), reply=True)


@dp.message_handler(commands=['remove_cf'])
async def remove_cf(message: types.Message):
    await add_person(message)
    await message.reply('Send me cf handles you want to remove.\n'
                        'You can send a list of them.\n'
                        'Separate them with commas, please',
                        reply_markup=types.ForceReply.create(selective=True), reply=True)


async def add_cf_to_db(handles, message: types.Message):
    try:
        now = time.time()
        handles_to_add = []
        not_existing_handles = []
        already_added_handles = []

        bad_one = ''
        left = [re.sub(r'[^A-Za-z0-9._-]', '', handle) for handle in handles]
        while bad_one is not None:
            bad_one, good_ones, left = await codeforces.check_handles(left)
            if bad_one is not None:
                not_existing_handles.append(bad_one)
            handles_to_add.extend(good_ones)

        handles_to_remove_from_handles_to_add = []

        for handle in handles_to_add:
            if handle in db['id'][str(message.chat['id'])]['cf_handles']:
                already_added_handles.append(handle)
                handles_to_remove_from_handles_to_add.append(handle)

        for handle in handles_to_remove_from_handles_to_add:
            handles_to_add.remove(handle)

        handles_to_add_with_ratings = await codeforces.get_multiple_ratings(handles_to_add)

        handles_to_add = []

        for handle, rating in handles_to_add_with_ratings:
            db['id'][str(message.chat['id'])]['cf_handles'][handle] = rating
            handles_to_add.append(handle)

        save_json()
        await add_log(
            f'cf users were added ({str(message.chat["id"])}) {handles_to_add} in {time.time() - now:.3f}s')
        return handles_to_add, not_existing_handles, already_added_handles
    except Exception as e:
        await add_log(f'During adding cf handles exception was raised. {e}')


async def add_ac_to_db(usernames, message: types.Message):
    try:
        now = time.time()
        usernames_to_add = []
        not_existing_usernames = []
        already_added_usernames = []
        users = []

        for username in usernames:
            users.append((username, dp.loop.create_task(atcoder.check_username(username.lstrip(' ')))))

        for inputted, username in users:
            ac_username = await username
            if not ac_username:
                not_existing_usernames.append(inputted.lstrip(' '))
                continue
            if ac_username in db['id'][str(message.chat['id'])]['ac_usernames']:
                already_added_usernames.append(ac_username)
                continue
            else:
                usernames_to_add.append(ac_username)
        ratings = []
        for username in usernames_to_add:
            ratings.append((username, dp.loop.create_task(atcoder.get_rating(username))))

        for username, rating in ratings:
            db['id'][str(message.chat['id'])]['ac_usernames'][username] = await rating
        save_json()
        await add_log(
            f'ac users were added ({str(message.chat["id"])}) {usernames_to_add} in {time.time() - now:.3f}s')
        return usernames_to_add, not_existing_usernames, already_added_usernames
    except Exception as e:
        await add_log(f'During removing ac usernames exception was raised. {e}')


@dp.message_handler(commands=['add_cf'])
async def add_cf(message: types.Message):
    await add_person(message)
    await message.reply('Send me cf handles you want to add.\n'
                        'You can send a list of them.\n'
                        'Separate them with commas, please',
                        reply_markup=types.ForceReply.create(selective=True), reply=True)


@dp.message_handler(commands=['add_ac'])
async def add_ac(message: types.Message):
    await add_person(message)
    await message.reply('Send me ac usernames you want to add.\n'
                        'You can send a list of them.\n'
                        'Separate them with commas, please',
                        reply_markup=types.ForceReply.create(selective=True), reply=True)


@dp.message_handler(commands=['usernames'])
async def usernames_help(message: types.Message):
    await add_log(f'/usernames was used ({str(message.chat["id"])})')
    await add_person(message)
    reply_message = 'Usernames help:\n' \
                    '/add_cf for adding Codeforces handles\n' \
                    '/remove_cf for removing Codeforces handles\n' \
                    '/add_ac for adding AtCoder usernames\n' \
                    '/remove_ac for removing AtCoder usernames\n\n'

    cf_handles = db["id"][str(message.chat["id"])]["cf_handles"]
    list_of_cf_handles = []

    for cf_handle in cf_handles:
        list_of_cf_handles.append(cf_handle)

    if len(list_of_cf_handles) != 0:
        reply_message += 'Codeforces handles:\n'
        reply_message += f'<a><b>{", ".join(sorted(cf_handles, key=lambda a: a.lower()))}</b></a>\n\n'
    else:
        reply_message += 'You have no Codeforces handles\n\n'

    ac_usernames = db["id"][str(message.chat["id"])]["ac_usernames"]
    list_of_ac_usernames = []

    for ac_username in ac_usernames:
        list_of_ac_usernames.append(ac_username)

    if len(list_of_ac_usernames) != 0:
        reply_message += 'AtCoder usernames:\n'
        reply_message += f'<a><b>{", ".join(sorted(ac_usernames, key=lambda a: a.lower()))}</b></a>'
    else:
        reply_message += 'You have no AtCoder usernames'

    await message.reply(reply_message, parse_mode='HTML')


# its notifications help
@dp.message_handler(commands=['notifications'])
async def notifications_help(message: types.Message):
    await add_log(f'/notifications was used ({str(message.chat["id"])})')
    await add_person(message)
    reply_message = 'Notification help:\nUse /add_notification and /remove_notification\n' \
                    'Notice you can add or remove only one notification per command\n' \
                    'Enter just the number between 1 and 1440\n' \
                    'You can restore your notification settings to default using /clear_notifications\n\n' \
                    'Current notifications:\n'
    for i in db['id'][str(message.chat['id'])]['notifications']:
        if i // 1440 == 1:
            reply_message += '1d, '
        elif i // 60 != 0:
            reply_message += (f'{i // 60}h {i % 60}m, ' if (i % 60 != 0) else f'{i // 60}h, ')
        else:
            reply_message += f'{i}m, '
    await message.reply(reply_message[:-2], reply=True)


@dp.message_handler(commands=['clear_notifications'])
async def clear_notifications(message: types.Message):
    await add_log(f'notifications were cleared ({str(message.chat["id"])})')
    await add_person(message)
    db['id'][str(message.chat['id'])]['notifications'] = [15, 60, 1440]
    save_json()
    await message.reply('Your notification settings have been restored')


@dp.message_handler(commands=['add_notification'])
async def add_notification(message: types.Message):
    await add_log(f'notification was added ({str(message.chat["id"])})')
    await add_person(message)
    await message.reply('Send me amount of minutes before the contest you want to be notified',
                        reply_markup=types.ForceReply.create(selective=True), reply=True)


@dp.message_handler(commands=['remove_notification'])
async def remove_notification(message: types.Message):
    await add_log(f'notification was removed ({str(message.chat["id"])})')
    await add_person(message)
    await message.reply('Send me amount of minutes before the contest you don\'t want to be notified anymore',
                        reply_markup=types.ForceReply.create(selective=True), reply=True)


async def send_cf_rating_changes(contest: str):
    rating_changes_status, rating_changes = await codeforces.get_rating_changes(
        int(await codeforces.get_id(contest)))
    if not rating_changes_status:
        if not rating_changes:
            await add_log('contest happened to be unrated')
            return 1
        else:
            await add_log('rating changes aren\'t out yet')
        return

    for user in db['id']:
        message = 'Rating changes for ' + contest + ' are out:\n\n'
        changes = []
        for handle in db['id'][user]['cf_handles']:
            # print(handle)
            for cf_user in rating_changes:
                # print(cf_user['handle'])
                if cf_user['handle'] == handle:
                    changes.append([cf_user['newRating'] - cf_user['oldRating'], cf_user['oldRating'],
                                    cf_user['newRating'], handle])
                    db['id'][user]['cf_handles'][handle] = cf_user['newRating']
                    break
        changes.sort(reverse=True)
        if len(changes) != 0:
            for change in changes:
                message += f'<a><b>{change[3]}</b></a>\n{change[1]} -> {change[2]} ({"+" if change[0] > 0 else ""}{change[0]})\n\n'

            try:
                if db['id'][user]['status'] == 2:
                    await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True,
                                           disable_notification=True)
                    await add_log(f'rating changes were sent to ({user})')
                elif db['id'][user]['status'] == 1:
                    await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True)
                    await add_log(f'rating changes were sent to ({user})')
                else:
                    pass
            except Exception as e:
                await remove_person(user)
                await bot.send_message(config.ADMIN, f"{e}")

    return 1


async def send_ac_rating_changes(contest):
    if contest == await atcoder.get_last():
        if await atcoder.are_rating_changes_out(await atcoder.get_url(contest)):
            for user in db['id']:
                message = 'Rating changes for ' + contest + ' are out:\n\n'
                changes = []
                for username in db['id'][user]['ac_usernames']:
                    new_rating = await atcoder.get_rating_change(await atcoder.get_url(contest),
                                                                 username)
                    if new_rating:
                        changes.append([new_rating - db['id'][user]['ac_usernames'][username],
                                        db['id'][user]['ac_usernames'][username], new_rating, username])
                        db['id'][user]['ac_usernames'][username] = new_rating

                if len(changes) != 0:
                    changes.sort(reverse=True)
                    for change in changes:
                        message += f'<a><b>{change[3]}</b></a>\n{change[1]} -> {change[2]} ({"+" if change[0] > 0 else ""}{change[0]})\n\n'
                    try:
                        if db['id'][user]['status'] == 2:
                            await add_log(f'rating changes were sent to ({user})')
                            await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True,
                                                   disable_notification=True)
                        elif db['id'][user]['status'] == 1:
                            await add_log(f'rating changes were sent to ({user})')
                            await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            pass
                    except Exception as e:
                        await remove_person(user)
                        await bot.send_message(config.ADMIN, f"{e}\n{user}")
            return 1
        else:
            await add_log(f"Rating changes for {contest} aren\'t out yet")


async def send_rating_changes(wait_for):
    while True:
        contests_to_delete = []
        for contest, t in db["rating_changes"]:
            if t == 'ac':
                delete = await send_ac_rating_changes(contest)
            else:
                delete = await send_cf_rating_changes(contest)

            if delete:
                contests_to_delete.append([contest, t])

        for contest in contests_to_delete:
            db["rating_changes"].remove(contest)

        save_json()

        await asyncio.sleep(wait_for)


# get changes from server
async def get_changes(wait_for):
    while True:
        await asyncio.sleep(wait_for)
        try:
            await get_upcoming()
        finally:
            pass


# check changes in db
async def check_changes(wait_for):
    while True:
        await asyncio.sleep(wait_for)
        await remove_persons_from_db()
        upcoming = db['contests']
        for contest in upcoming:
            if int((contest[0] - datetime.datetime.utcnow()) / datetime.timedelta(minutes=1)) <= 0:
                if contest[3] == 'cf':
                    if [contest[1], 'cf'] not in db["rating_changes"]:
                        db['rating_changes'].append([contest[1], 'cf'])
                        await bot.send_message(config.ADMIN,
                                               f"new contest is added to rating_changes watching list: {contest[1]}")
                        await add_log(f"new contest is added to rating_changes watching list: {contest[1]}")
                else:
                    if [contest[1], 'ac'] not in db["rating_changes"]:
                        db['rating_changes'].append([contest[1], 'ac'])
                        await bot.send_message(config.ADMIN,
                                               f"new contest is added to rating_changes watching list: {contest[1]}")
                        await add_log(f"new contest is added to rating_changes watching list: {contest[1]}")

                try:
                    await get_upcoming()
                except Exception as e:
                    await add_log(f"upcoming wasn\'t gotten: {e}")
        for user in db['id']:
            if db['id'][user]['status'] == 0:
                continue
            for notification in db['id'][user]['notifications']:
                for contest in upcoming:
                    # print(((contest[0] - datetime.datetime.utcnow())) / datetime.timedelta(minutes=1))
                    if (int((contest[0] - datetime.datetime.utcnow()) / datetime.timedelta(
                            minutes=1)) == notification - 1):
                        message = ''
                        message += contest[1]
                        message += (f' ({contest[2]}) starts in ' if contest[2] != '0' else ' starts in ')

                        if notification // 1440 == 1:
                            message += '1 day'
                        elif notification // 60 != 0:
                            if notification % 60 == 0:
                                if notification // 60 != 1:
                                    message += f'{notification // 60} hours'
                                else:
                                    message += '1 hour'
                            else:
                                if notification // 60 != 1:
                                    message += f'{notification // 60} hours '
                                else:
                                    message += '1 hour '
                                if notification % 60 != 1:
                                    message += f'{notification % 60} minutes'
                                else:
                                    message += '1 minute'
                        else:
                            if notification == 1:
                                message += f'{notification} minute'
                            else:
                                message += f'{notification} minutes'

                        await add_log(f'notification was sent to {user}')
                        try:
                            if db['id'][user]['status'] == 1:
                                await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True)
                            else:
                                await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True,
                                                       disable_notification=True)
                        except Exception as e:
                            await remove_person(user)
                            await add_log(f"during sending changes an exception occurred{e}")
        # print('I checked and sent everybody a notification')


@dp.message_handler(commands=['logs'])
async def send_logs(message: types.Message):
    if str(message.chat['id']) != str(config.ADMIN):
        await message.reply('You\'re not an administrator here')
        await add_log(f'he tried to get logs ({message.chat["id"]})')
        return
    amount = int(message.text.split()[1])
    reply_message = ''
    if amount > len(log['log']):
        amount = 0
    for one_log in log['log'][-amount:]:
        reply_message += f'{datetime.datetime.fromisoformat(one_log["time"]).strftime("%H.%M.%S")}: {one_log["value"]}\n'
    await message.reply(reply_message, parse_mode='HTML')


@dp.message_handler(commands=['stats'])
async def send_stats(message: types.Message):
    if str(message.chat['id']) != str(config.ADMIN):
        await message.reply('You\'re not an administrator here')
        await add_log(f'he tried to get statistics ({message.chat["id"]})')
        return
    stats = await statistics.get_statistics(db)

    reply_message = f'Bot users: {stats[0]}\nCF Handles: {stats[1]}\nAC Usernames: {stats[2]}'

    await message.reply(reply_message, parse_mode='HTML')


@dp.message_handler(commands=['message'])
async def send_message(message: types.Message):
    if str(message.chat['id']) != str(config.ADMIN):
        await message.reply('You\'re not an administrator here')
        await add_log(f'he tried to get logs ({message.chat["id"]})')
        return
    args = message.text.split()[1:]
    if args[0] == "1":
        await bot.send_message(args[1], ' '.join(args[2:]))
        await add_log(f"message was sent to {args[1]}\n{' '.join(args[2:])}")
    else:
        for user in db['id']:
            await bot.send_message(user, ' '.join(args[1:]))
            await add_log(f"message was sent to {user}\n{' '.join(args[1:])}")


@dp.message_handler(commands=['refresh'])
async def refresh(message: types.Message):
    if str(message.chat['id']) != str(config.ADMIN):
        await message.reply('You\'re not an administrator here')
        await add_log(f'he tried to refresh ({message.chat["id"]})')
        return
    new_message = await message.reply('<a><b>Processing...</b></a>', parse_mode='HTML')
    now = time.time()
    try:
        await get_upcoming()
        await new_message.edit_text(f'<a><b>Done in {"%.3f" % (time.time() - now)}s</b></a>', parse_mode='HTML')
    except Exception as e:
        await new_message.edit_text(f'Something happened. {e}', parse_mode='HTML')


@dp.message_handler(commands=['status'])
async def change_status(message: types.Message):
    await add_log(f'status was changed ({str(message.chat["id"])})')
    await add_person(message)
    await message.reply(
        f'Your current status = {db["id"][str(message.chat["id"])]["status"]}\nSend me your new status if you want',
        reply_markup=types.ForceReply.create(selective=True), reply=True)


@dp.message_handler(commands=['upcoming'])
async def send_upcoming(message: types.Message):
    await add_log(f'upcoming list was sent ({str(message.chat["id"])})')
    await add_person(message)
    new_message = await message.reply('<a><b>Processing...</b></a>', parse_mode='HTML')

    upcoming_contests = db['contests']
    reply_message = ''

    tz = db['id'][str(message.chat['id'])]['tz']

    for i in upcoming_contests[:min(5, len(upcoming_contests))]:
        reply_message += i[1]
        if i[2] != '0':
            reply_message += f' ({i[2]})'
        reply_message += '\nStart Time: '
        reply_message += (i[0] + await get_timezone(tz)).strftime('%d.%m.%Y %H:%M')
        reply_message += ' <a><b>('
        mins = int(float(str((i[0] - datetime.datetime.utcnow()) / datetime.timedelta(minutes=1))))
        if mins < 1440:
            reply_message += '%dh %dm' % divmod(mins, 60)
        else:
            reply_message += '%dd %dh' % divmod(mins / 60, 24)
        reply_message += ')</b></a>\n\n'

    await new_message.edit_text(reply_message, parse_mode='HTML', disable_web_page_preview=True)

    # print(reply_message)


async def get_timezone(utctimezoneformat):
    if utctimezoneformat[0:3] != "UTC":
        raise ValueError("Timezone format is wrong")
    hours = int(utctimezoneformat[3:6])
    minutes = int(utctimezoneformat[3] + utctimezoneformat[7:9])
    if abs(hours) > 24 or abs(minutes) > 60:
        raise ValueError("Either hours or minutes numbers are too big")
    return datetime.timedelta(hours=hours, minutes=minutes)


@dp.message_handler(commands=['timezone'])
async def change_timezone(message: types.Message):
    await add_log(f'timezone was changed ({str(message.chat["id"])})')
    await add_person(message)
    await message.reply('Send me new timezone in format UTC±hh:mm',
                        reply_markup=types.ForceReply.create(selective=True), reply=True)


@dp.message_handler()
async def main(message: types.Message):
    await add_person(message)
    # print(message.text)
    if message.reply_to_message is not None:
        if message.reply_to_message.text[-40:] == 'Send me new timezone in format UTC±hh:mm':
            try:
                await get_timezone(message.text)
            except Exception as e:
                await message.answer("Not a valid timezone. Send me new timezone in format UTC±hh:mm",
                                     reply_markup=types.ForceReply.create(selective=True), reply=True)
                await add_log(f"During timezone changing exception was caught. {message.from_user}\n{e}")
                return
            db['id'][str(message.chat['id'])]["tz"] = message.text
            save_json()
            await message.answer("Timezone was edited successfully")
        elif message.reply_to_message.text[-35:] == 'Send me your new status if you want':
            try:
                if message.text != '1' and message.text != '2' and message.text != '0':
                    raise ValueError
            except ValueError:
                await message.answer("Not a valid status. Send me your new status if you want",
                                     reply_markup=types.ForceReply.create(selective=True), reply=True)
                return
            db['id'][str(message.chat['id'])]['status'] = int(message.text)
            save_json()
            await message.answer("Status was edited successfully")
        elif message.reply_to_message.text[-68:] == \
                'Send me amount of minutes before the contest you want to be notified':
            try:
                int(message.text)
                if int(message.text) < 1 or int(message.text) > 1440:
                    raise ValueError
            except ValueError:
                await message.answer(
                    "Not a valid amount of minutes. Send me amount of minutes before the contest you want to be notified",
                    reply_markup=types.ForceReply.create(selective=True), reply=True)
                return
            if int(message.text) not in db['id'][str(message.chat['id'])]["notifications"]:
                db['id'][str(message.chat['id'])]["notifications"].append(int(message.text))
                db['id'][str(message.chat['id'])]["notifications"].sort()
                save_json()
                await message.answer("Notifications were edited successfully")
            else:
                await message.answer(
                    "It\'s already in the list. \nSend me amount of minutes before the contest you want to be notified",
                    reply_markup=types.ForceReply.create(selective=True), reply=True)

        elif message.reply_to_message.text[-82:] == \
                'Send me amount of minutes before the contest you don\'t want to be notified anymore':
            try:
                int(message.text)
                if int(message.text) < 1 or int(message.text) > 1440:
                    raise ValueError
            except ValueError:
                await message.answer(
                    "Not a valid amount of minutes. Send me amount of minutes before the contest you don\'t want to be notified anymore",
                    reply_markup=types.ForceReply.create(selective=True), reply=True)
                return

            try:
                if int(message.text) not in db['id'][str(message.chat['id'])]["notifications"]:
                    raise ValueError
            except ValueError:
                await message.answer(
                    "It wasn\'t in the list. Send me amount of minutes before the contest you don\'t want to be "
                    "notified anymore",
                    reply_markup=types.ForceReply.create(selective=True), reply=True)
                return
            db['id'][str(message.chat['id'])]["notifications"].remove(int(message.text))
            save_json()
            await message.answer("Notifications were edited successfully")
        elif message.reply_to_message.text[-98:] == 'Send me cf handles you want to add.\n' \
                                                    'You can send a list of them.\n' \
                                                    'Separate them with commas, please':
            new_message = await message.reply('<a><b>Processing...</b></a>', parse_mode='HTML')
            added_handles, not_existing_handles, already_added_handles = await add_cf_to_db(
                str(message.text).split(','), message)
            # added and non-existing handles output
            added_and_non_existing = ''
            if len(already_added_handles) == 0:
                pass
            elif len(already_added_handles) == 1:
                added_and_non_existing += f'1 handle is already in your handle list:\n<a><b>{already_added_handles[0]}</b></a>\n'
            else:
                added_and_non_existing += f'{len(already_added_handles)} handles are already in your handle ' \
                                          f'list:\n<a><b>' \
                                          f'{", ".join(sorted(already_added_handles, key=lambda a: a.lower()))}</b></a>\n'

            if len(not_existing_handles) == 0:
                pass
            elif len(not_existing_handles) == 1:
                added_and_non_existing += f'1 handle doesn\'t exist:\n<a><b>{not_existing_handles[0]}</b></a>\n'
            else:
                added_and_non_existing += f'{len(not_existing_handles)} handles don\'t exist:\n' \
                                          f'<a><b>{", ".join(sorted(not_existing_handles, key=lambda a: a.lower()))}</b></a>\n'

            if len(added_handles) == 0:
                await new_message.delete()
                message_text = f'{added_and_non_existing}\nNo handles were added.'

                await message.reply(f'{message_text}\n\n'
                                    f'Send me cf handles you want to add.\n'
                                    'You can send a list of them.\n'
                                    'Separate them with commas, please',
                                    reply_markup=types.ForceReply.create(selective=True), parse_mode='HTML')
                return
            elif len(added_handles) == 1:
                reply_message = f'{added_and_non_existing}\n1 handle was added:\n<a><b>{added_handles[0]}</b></a>'

            else:
                reply_message = f'{added_and_non_existing}\n' \
                                f'{len(added_handles)} handles were added:\n<a><b>' \
                                f'{", ".join(sorted(added_handles, key=lambda a: a.lower()))}</b></a>'
            await new_message.edit_text(reply_message, parse_mode='HTML')

        elif message.reply_to_message.text[-101:] == 'Send me cf handles you want to remove.\n' \
                                                     'You can send a list of them.\n' \
                                                     'Separate them with commas, please':

            new_message = await message.reply('<a><b>Processing...</b></a>', parse_mode='HTML')
            try:
                removed_handles, not_existing_handles, not_added_handles = await remove_cf_from_db(
                    str(message.text).split(','), message)
                # not added and non-existing handles output
                not_added_and_non_existing = ''
                if len(not_added_handles) == 0:
                    pass
                elif len(not_added_handles) == 1:
                    not_added_and_non_existing += f'1 handle wasn\'t in your handle list:\n<a><b>{not_added_handles[0]}</b></a>\n'
                else:
                    not_added_and_non_existing += f'{len(not_added_handles)} handles weren\'t in your handle list:\n<a><b>' \
                                                  f'{", ".join(sorted(not_added_handles, key=lambda a: a.lower()))}</b></a>\n'

                if len(not_existing_handles) == 0:
                    pass
                elif len(not_existing_handles) == 1:
                    not_added_and_non_existing += f'1 handle doesn\'t exist:\n<a><b>{not_existing_handles[0]}</b></a>\n'
                else:
                    not_added_and_non_existing += f'{len(not_existing_handles)} handles don\'t exist:\n' \
                                                  f'<a><b>{", ".join(sorted(not_existing_handles, key=lambda a: a.lower()))}</b></a>\n'

                if len(removed_handles) == 0:
                    await new_message.delete()
                    message_text = f'{not_added_and_non_existing}\nNo handles were removed.'

                    await message.reply(f'{message_text}\n\n'
                                        f'Send me cf handles you want to remove.\n'
                                        'You can send a list of them.\n'
                                        'Separate them with commas, please',
                                        reply_markup=types.ForceReply.create(selective=True), parse_mode='HTML')
                    return
                elif len(removed_handles) == 1:
                    reply_message = f'{not_added_and_non_existing}\n1 handle was removed:\n<a><b>{removed_handles[0]}</b></a>'

                else:
                    reply_message = f'{not_added_and_non_existing}\n' \
                                    f'{len(removed_handles)} handles were removed:\n<a><b>' \
                                    f'{", ".join(sorted(removed_handles, key=lambda a: a.lower()))}</b></a>'
                await new_message.edit_text(reply_message, parse_mode='HTML')
            except Exception as e:
                await new_message.edit_text('Something happened. Try later', parse_mode='HTML')

        elif message.reply_to_message.text[-100:] == 'Send me ac usernames you want to add.\n' \
                                                     'You can send a list of them.\n' \
                                                     'Separate them with commas, please':
            new_message = await message.reply('<a><b>Processing...</b></a>', parse_mode='HTML')
            added_usernames, not_existing_usernames, already_added_usernames = await add_ac_to_db(
                str(message.text).split(','), message)
            # added and non-existing usernames output
            added_and_non_existing = ''
            if len(already_added_usernames) == 0:
                pass
            elif len(already_added_usernames) == 1:
                added_and_non_existing += f'1 username is already in your username list:\n<a><b>{already_added_usernames[0]}</b></a>\n'
            else:
                added_and_non_existing += f'{len(already_added_usernames)} usernames are already in your username list:\n<a><b>' \
                                          f'{", ".join(sorted(already_added_usernames, key=lambda a: a.lower()))}</b></a>\n'

            if len(not_existing_usernames) == 0:
                pass
            elif len(not_existing_usernames) == 1:
                added_and_non_existing += f'1 username doesn\'t exist:\n<a><b>{not_existing_usernames[0]}</b></a>\n'
            else:
                added_and_non_existing += f'{len(not_existing_usernames)} usernames don\'t exist:\n' \
                                          f'<a><b>{", ".join(sorted(not_existing_usernames, key=lambda a: a.lower()))}</b></a>\n'

            if len(added_usernames) == 0:
                await new_message.delete()
                message_text = f'{added_and_non_existing}\nNo usernames were added.'

                await message.reply(f'{message_text}\n\n'
                                    f'Send me ac usernames you want to add.\n'
                                    'You can send a list of them.\n'
                                    'Separate them with commas, please',
                                    reply_markup=types.ForceReply.create(selective=True), parse_mode='HTML')
                return
            elif len(added_usernames) == 1:
                reply_message = f'{added_and_non_existing}\n1 username was added:\n<a><b>{added_usernames[0]}</b></a>'

            else:
                reply_message = f'{added_and_non_existing}\n' \
                                f'{len(added_usernames)} usernames were added:\n<a><b>' \
                                f'{", ".join(sorted(added_usernames, key=lambda a: a.lower()))}</b></a>'
            await new_message.edit_text(reply_message, parse_mode='HTML')

        elif message.reply_to_message.text[-103:] == 'Send me ac usernames you want to remove.\n' \
                                                     'You can send a list of them.\n' \
                                                     'Separate them with commas, please':
            new_message = await message.reply('<a><b>Processing...</b></a>', parse_mode='HTML')
            removed_usernames, not_existing_usernames, not_added_usernames = await remove_ac_from_db(
                str(message.text).split(','), message)
            # not added and non-existing usernames output
            not_added_and_non_existing = ''
            if len(not_added_usernames) == 0:
                pass
            elif len(not_added_usernames) == 1:
                not_added_and_non_existing += f'1 username wasn\'t in your username list:\n<a><b>{not_added_usernames[0]}</b></a>\n'
            else:
                not_added_and_non_existing += f'{len(not_added_usernames)} usernames weren\'t in your username list:\n<a><b>' \
                                              f'{", ".join(sorted(not_added_usernames, key=lambda a: a.lower()))}</b></a>\n'

            if len(not_existing_usernames) == 0:
                pass
            elif len(not_existing_usernames) == 1:
                not_added_and_non_existing += f'1 username doesn\'t exist:\n<a><b>{not_existing_usernames[0]}</b></a>\n'
            else:
                not_added_and_non_existing += f'{len(not_existing_usernames)} usernames don\'t exist:\n' \
                                              f'<a><b>{", ".join(sorted(not_existing_usernames, key=lambda a: a.lower()))}</b></a>\n'

            if len(removed_usernames) == 0:
                await new_message.delete()
                message_text = f'{not_added_and_non_existing}\nNo usernames were removed.'

                await message.reply(f'{message_text}\n\n'
                                    f'Send me ac usernames you want to remove.\n'
                                    'You can send a list of them.\n'
                                    'Separate them with commas, please',
                                    reply_markup=types.ForceReply.create(selective=True), parse_mode='HTML')
                return
            elif len(removed_usernames) == 1:
                reply_message = f'{not_added_and_non_existing}\n1 username was removed:\n<a><b>{removed_usernames[0]}</b></a>'

            else:
                reply_message = f'{not_added_and_non_existing}\n' \
                                f'{len(removed_usernames)} usernames were removed:\n<a><b>' \
                                f'{", ".join(sorted(removed_usernames, key=lambda a: a.lower()))}</b></a>'
            await new_message.edit_text(reply_message, parse_mode='HTML')


async def send_message(message):
    for i in db['id']:
        await bot.send_message(i, message)


async def try_getting_upcoming():
    try:
        await get_upcoming()
    except Exception as e:
        print(e)


if __name__ == '__main__':
    load_json()
    dp.loop.create_task(try_getting_upcoming())
    dp.loop.create_task(get_changes(6000))
    dp.loop.create_task(send_rating_changes(300))
    dp.loop.create_task(check_changes(60))
    dp.loop.create_task(save_json_periodically(60 * 30))
    executor.start_polling(dp, skip_updates=True)
