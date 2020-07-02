import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
import json
import atcoder
import codeforces
import datetime
import sys

db = json.load(open("db.json", 'r'))
log = json.load(open("log.json", 'r'))

API_TOKEN = "1397545266:AAEU1ghXqUfpx04nr6NVwfJq7fcllC-ClEk"

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

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


async def add_log(string):
    d = {}
    d['time'] = datetime.datetime.now().isoformat()
    d['value'] = string
    log['log'].append(d)
    await save_log()


def sync_add_log(string):
    d = {}
    d['time'] = datetime.datetime.now().isoformat()
    d['value'] = string
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
    if db['id'].get(str(message.chat['id'])) == None:
        await add_log(f'person added to db ({str(message.chat["id"])})')
        db['id'][str(message.chat['id'])] = {"tz": 3,
                                             "status": 1,
                                             "notifications": [
                                                 15,
                                                 60,
                                                 1440
                                             ], "cf_handles": {},
                                             "ac_usernames": {}}
        save_json()


# start
@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    await add_person(message)
    await message.reply(start_message)


def load_json():
    for i in range(len(db['contests'])):
        db['contests'][i][0] = datetime.datetime.fromisoformat(db['contests'][i][0])


def get_upcoming():
    sync_add_log('upcoming was gotten')
    upcoming = []
    upcoming.extend(atcoder.parse_upcoming())
    upcoming.extend(codeforces.get_upcoming())

    upcoming.sort()

    for i in range(len(upcoming)):
        upcoming[i][0] = datetime.datetime.isoformat(upcoming[i][0])
    db['contests'] = upcoming
    json.dump(db, open('db.json', 'w'), indent=2)
    load_json()


def save_json():
    for i in range(len(db['contests'])):
        db['contests'][i][0] = datetime.datetime.isoformat(db['contests'][i][0])
    json.dump(db, open('db.json', 'w'), indent=2)
    load_json()


async def remove_cf_from_db(handles, message: types.Message):
    await add_log(f'cf users were removed ({str(message.chat["id"])})')
    handles_to_remove = []
    for handle in handles:
        handle = await codeforces.check_handle(handle)
        if not handle:
            continue
        if handle in db['id'][str(message.chat['id'])]['cf_handles']:
            handles_to_remove.append(handle)

    for handle in handles_to_remove:
        # print(handle)
        db['id'][str(message.chat['id'])]['cf_handles'].pop(handle)
    save_json()
    return handles_to_remove


async def remove_ac_from_db(usernames, message: types.Message):
    usernames_to_remove = []
    for username in usernames:
        username = await atcoder.check_username(username)
        if not username:
            continue
        if username in db['id'][str(message.chat['id'])]['ac_usernames']:
            usernames_to_remove.append(username)

    for username in usernames_to_remove:
        # print(username)
        db['id'][str(message.chat['id'])]['ac_usernames'].pop(username)
    save_json()
    await add_log(f'ac users were removed ({str(message.chat["id"])}) {usernames_to_remove}')
    return usernames_to_remove


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
    handles_to_add = []
    for handle in handles:
        handle = await codeforces.check_handle(handle)
        if not handle:
            continue
        if handle in db['id'][str(message.chat['id'])]['cf_handles']:
            continue
        else:
            handles_to_add.append(handle)
    for handle in handles_to_add:
        # print(handle)
        db['id'][str(message.chat['id'])]['cf_handles'][handle] = await codeforces.get_rating(handle)
    save_json()
    await add_log(f'cf users were added ({str(message.chat["id"])}) {handles_to_add}')
    return handles_to_add


async def add_ac_to_db(usernames, message: types.Message):
    usernames_to_add = []
    for username in usernames:
        username = await atcoder.check_username(username)
        if not username:
            continue
        if username in db['id'][str(message.chat['id'])]['ac_usernames']:
            continue
        else:
            usernames_to_add.append(username)
    for username in usernames_to_add:
        # print(username)
        db['id'][str(message.chat['id'])]['ac_usernames'][username] = await atcoder.get_rating(username)
    save_json()
    await add_log(f'ac users were added ({str(message.chat["id"])}) {usernames_to_add}')
    return usernames_to_add


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

    if (len(list_of_cf_handles) != 0):
        reply_message += 'Codeforces handles:\n'
        reply_message += f'<a><b>{", ".join(sorted(cf_handles, key=lambda a: a.lower()))}</b></a>\n\n'
    else:
        reply_message += 'You have no Codeforces handles\n\n'

    ac_usernames = db["id"][str(message.chat["id"])]["ac_usernames"]
    list_of_ac_usernames = []

    for ac_username in ac_usernames:
        list_of_ac_usernames.append(ac_username)

    if (len(list_of_ac_usernames) != 0):
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


async def send_cf_rating_changes():
    if db['last_codeforces']['status'] == 0:
        rating_changes_status, rating_changes = codeforces.get_rating_changes(
            int(db['last_codeforces']['name'][40:db['last_codeforces']['name'].find('>') - 1]))
        if not rating_changes_status:
            if not rating_changes:
                await add_log('contest happened to be unrated')
                db['last_codeforces']['status'] = 1
                save_json()
            else:
                await add_log('rating changes aren\'t out yet')
            return
        db['last_codeforces']['status'] = 1

        for user in db['id']:
            message = 'Rating changes for ' + db['last_codeforces']['name'] + ' are out:\n\n'
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
                await add_log(f'rating changes were sent to ({user})')
                if db['id'][user]['status'] == 2:
                    await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True,
                                           disable_notification=True)
                elif db['id'][user]['status'] == 1:
                    await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True)
                else:
                    pass

        save_json()


async def send_ac_rating_changes():
    if db['last_atcoder']['status'] == 0 and db['last_atcoder']['name'] == await atcoder.get_last():
        if await atcoder.are_rating_changes_out(await get_atcoder_url(db['last_atcoder']['name'])):
            db['last_atcoder']['status'] = 1
            for user in db['id']:
                message = 'Rating changes for ' + db['last_atcoder']['name'] + ' are out:\n\n'
                changes = []
                for username in db['id'][user]['ac_usernames']:
                    new_rating = await atcoder.get_rating_change(await get_atcoder_url(db['last_atcoder']['name']),
                                                                 username)
                    if new_rating:
                        changes.append([new_rating - db['id'][user]['ac_usernames'][username],
                                        db['id'][user]['ac_usernames'][username], new_rating, username])
                        db['id'][user]['ac_usernames'][username] = new_rating

                if len(changes) != 0:
                    changes.sort(reverse=True)
                    for change in changes:
                        message += f'<a><b>{change[3]}</b></a>\n{change[1]} -> {change[2]} ({"+" if change[0] > 0 else ""}{change[0]})\n\n'

                    await add_log(f'rating changes were sent to ({user})')
                    if db['id'][user]['status'] == 2:
                        await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True,
                                               disable_notification=True)
                    elif db['id'][user]['status'] == 1:
                        await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True)
                    else:
                        pass
            save_json()


async def get_atcoder_url(name):
    return name[9:name.find('>') - 1]


async def send_rating_changes(wait_for):
    while True:
        await asyncio.sleep(wait_for)
        await send_cf_rating_changes()
        await send_ac_rating_changes()


# get changes from server
async def get_changes(wait_for):
    while True:
        await asyncio.sleep(wait_for)
        get_upcoming()
        await add_log('changes were gotten')


# check changes in db
async def check_changes(wait_for):
    while True:
        await asyncio.sleep(wait_for)
        upcoming = db['contests']
        for contest in upcoming:
            if int((contest[0] - datetime.datetime.utcnow()) / datetime.timedelta(minutes=1)) == 0:
                if contest[3] == 'cf':
                    db['last_codeforces']['name'] = contest[1]
                    db['last_codeforces']['status'] = 0
                else:
                    db['last_atcoder']['name'] = contest[1]
                    db['last_atcoder']['status'] = 0
        for user in db['id']:
            if db['id'][user]['status'] == 0:
                continue
            for notification in db['id'][user]['notifications']:
                for contest in upcoming:
                    # print(((contest[0] - datetime.datetime.utcnow())) / datetime.timedelta(minutes=1))
                    if (int((contest[0] - datetime.datetime.utcnow()) / datetime.timedelta(
                            minutes=1)) == notification):
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
                        if db['id'][user]['status'] == 1:
                            await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True)
                        else:
                            await bot.send_message(user, message, parse_mode='HTML', disable_web_page_preview=True,
                                                   disable_notification=True)
        # print('I checked and sent everybody a notification')


@dp.message_handler(commands=['logs'])
async def send_logs(message: types.Message):
    if (str(message.chat['id']) != "818537853"):
        await message.reply('You\'re not an administrator here')
        await add_log(f'he tried to get logs ({message.chat["id"]})')
        return
    amount = int(message.text.split()[1])
    await add_log(f'{amount} logs were sent')
    reply_message = ''
    if amount > len(log['log']):
        amount = 0
    for one_log in log['log'][-amount:]:
        reply_message += f'{one_log["time"]} : {one_log["value"]}\n'
    await message.reply(reply_message)


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

    for i in upcoming_contests:
        reply_message += i[1]
        if i[2] != '0':
            reply_message += f' ({i[2]})'
        reply_message += '\nStart Time: '
        reply_message += (i[0] + datetime.timedelta(hours=tz)).strftime('%d.%m.%Y %H:%M')
        reply_message += ' <a><b>('
        mins = int(float(str((i[0] - datetime.datetime.utcnow()) / datetime.timedelta(minutes=1))))
        if mins < 1440:
            reply_message += '%dh %dm' % divmod(mins, 60)
        else:
            reply_message += '%dd %dh' % divmod(mins / 60, 24)
        reply_message += ')</b></a>\n\n'

    await new_message.edit_text(reply_message, parse_mode='HTML', disable_web_page_preview=True)

    # print(reply_message)


@dp.message_handler(commands=['timezone'])
async def change_timezone(message: types.Message):
    await add_log(f'timezone was changed ({str(message.chat["id"])})')
    await add_person(message)
    await message.reply('Send me new timezone', reply_markup=types.ForceReply.create(selective=True), reply=True)


@dp.message_handler()
async def main(message: types.Message):
    await add_person(message)
    # print(message.text)
    if message.reply_to_message is not None:
        if message.reply_to_message.text[-20:] == 'Send me new timezone':
            try:
                int(message.text)
                if (int(message.text) > 12) or (int(message.text) < -12):
                    raise ValueError
            except ValueError:
                await message.answer("Not a valid timezone. Send me new timezone",
                                     reply_markup=types.ForceReply.create(selective=True), reply=True)
                return
            db['id'][str(message.chat['id'])]["tz"] = int(message.text)
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
            db['id'][str(message.chat['id'])]["notifications"].append(int(message.text))
            db['id'][str(message.chat['id'])]["notifications"].sort()
            save_json()
            await message.answer("Notifications were edited successfully")

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
                    "It wasn\'t in the list. Send me amount of minutes before the contest you don\'t want to be notified anymore",
                    reply_markup=types.ForceReply.create(selective=True), reply=True)
                return
            db['id'][str(message.chat['id'])]["notifications"].remove(int(message.text))
            save_json()
            await message.answer("Notifications were edited successfully")
        elif message.reply_to_message.text[-98:] == 'Send me cf handles you want to add.\n' \
                                                    'You can send a list of them.\n' \
                                                    'Separate them with commas, please':
            new_message = await message.reply('<a><b>Processing...</b></a>', parse_mode='HTML')
            added_handles = await add_cf_to_db(str(message.text).split(','), message)
            if len(added_handles) == 0:
                await new_message.delete()
                await message.reply('No handles were added.\n\nSend me cf handles you want to add.\n'
                                    'You can send a list of them.\n'
                                    'Separate them with commas, please',
                                    reply_markup=types.ForceReply.create(selective=True))
                return
            elif len(added_handles) == 1:
                reply_message = f'1 handle was added:\n<a><b>{added_handles[0]}</b></a>'
            else:
                reply_message = f'{len(added_handles)} handles were added:\n<a><b>{", ".join(sorted(added_handles))}</b></a>'
            await new_message.edit_text(reply_message, parse_mode='HTML')

        elif message.reply_to_message.text[-101:] == 'Send me cf handles you want to remove.\n' \
                                                     'You can send a list of them.\n' \
                                                     'Separate them with commas, please':
            new_message = await message.reply('<a><b>Processing...</b></a>', parse_mode='HTML')
            removed_handles = await remove_cf_from_db(str(message.text).split(','), message)
            if len(removed_handles) == 0:
                await new_message.delete()
                await message.reply('No handles were removed.\n\nSend me cf handles you want to remove.\n'
                                    'You can send a list of them.\n'
                                    'Separate them with commas, please',
                                    reply_markup=types.ForceReply.create(selective=True))
                return
            elif len(removed_handles) == 1:
                reply_message = f'1 handle was removed:\n<a><b>{removed_handles[0]}</b></a>'
            else:
                reply_message = f'{len(removed_handles)} handles were removed:\n<a><b>{", ".join(sorted(removed_handles))}</b></a>'
            await new_message.edit_text(reply_message, parse_mode='HTML')

        elif message.reply_to_message.text[-100:] == 'Send me ac usernames you want to add.\n' \
                                                     'You can send a list of them.\n' \
                                                     'Separate them with commas, please':
            new_message = await message.reply('<a><b>Processing...</b></a>', parse_mode='HTML')
            added_usernames = await add_ac_to_db(str(message.text).split(','), message)
            if len(added_usernames) == 0:
                await new_message.delete()
                await message.reply('No usernames were added.\n\nSend me ac usernames you want to add.\n'
                                    'You can send a list of them.\n'
                                    'Separate them with commas, please',
                                    reply_markup=types.ForceReply.create(selective=True))
                return
            elif len(added_usernames) == 1:
                reply_message = f'1 username was added:\n<a><b>{added_usernames[0]}</b></a>'
            else:
                reply_message = f'{len(added_usernames)} usernames were added:\n<a><b>{", ".join(sorted(added_usernames))}</b></a>'
            await new_message.edit_text(reply_message, parse_mode='HTML')

        elif message.reply_to_message.text[-103:] == 'Send me ac usernames you want to remove.\n' \
                                                     'You can send a list of them.\n' \
                                                     'Separate them with commas, please':
            new_message = await message.reply('<a><b>Processing...</b></a>', parse_mode='HTML')
            removed_usernames = await remove_ac_from_db(str(message.text).split(','), message)
            if len(removed_usernames) == 0:
                await new_message.delete()
                await message.reply('No usernames were removed.\n\nSend me ac usernames you want to remove.\n'
                                    'You can send a list of them.\n'
                                    'Separate them with commas, please',
                                    reply_markup=types.ForceReply.create(selective=True))
                return
            elif len(removed_usernames) == 1:
                reply_message = f'1 username was removed:\n<a><b>{removed_usernames[0]}</b></a>'
            else:
                reply_message = f'{len(removed_usernames)} usernames were removed:\n<a><b>{", ".join(sorted(removed_usernames))}</b></a>'
            await new_message.edit_text(reply_message, parse_mode='HTML')

    else:
        await message.answer(start_message)


async def send_message(message):
    for i in db['id']:
        await bot.send_message(i, message)


if __name__ == '__main__':
    load_json()
    dp.loop.create_task(get_changes(6000))
    dp.loop.create_task(send_rating_changes(300))
    dp.loop.create_task(check_changes(60))
    executor.start_polling(dp, skip_updates=True)
