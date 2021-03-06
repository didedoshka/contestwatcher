from bs4 import BeautifulSoup
import urllib.request
import datetime
import re
import aiohttp
import asyncio
import time

url = 'https://atcoder.jp/home'
host = 'https://atcoder.jp'


async def get_url(a):
    return a[9:a.find('>') - 1]


async def get_html(url):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
        async with session.get(url) as response:
            if response.status == 404:
                raise Exception('404. Not found')
            html = await response.text()
            return html


async def get_last():
    html = await get_html(url)
    soup = BeautifulSoup(html, features='html.parser')
    table = soup.find('div', id='contest-table-recent')
    table = table.find('tbody')

    name = table.find_all('a')[1]

    return str(name)[:9] + host + str(name)[9:]


async def get_rating_change(url, user):
    html = await get_html(f'{host}/users/{user}/history')
    soup = BeautifulSoup(html, features='html.parser')
    table = soup.find('table', id='history')
    if table is None:
        return False
    td = table.find('a', href=f'{url[18:]}')
    if td is None:
        return False

    tc = table.find_all('tr', 'text-center')[-1]
    td = tc.find_all('td')[4].text
    if td == '-':
        return False

    return int(td)


async def are_rating_changes_out(url):
    html = await get_html(f'{url}/submissions')

    soup = BeautifulSoup(html, features='html.parser')
    ul = soup.find('ul', class_='pagination pagination-sm mt-0 mb-1')
    a = ul.find_all('a')[-1]

    html = await get_html(host + await get_url(str(a)))
    soup = BeautifulSoup(html, features='html.parser')
    table = soup.find('table', class_='table table-bordered table-striped small th-center')
    tbody = table.find('tbody')
    tr = tbody.find_all('tr')[0]
    user = tr.find_all('a')[1]['href']
    html = await get_html(f'{host}{user}/history')
    soup = BeautifulSoup(html, features='html.parser')
    table = soup.find('table', id='history')
    if table is None:
        return False
    td = table.find('a', href=f'{url[18:]}')
    if td is None:
        return False
    return True


async def check_username(username):
    try:
        html = await get_html(host + f'/users/{username}')
        soup = BeautifulSoup(html, features='html.parser')
        a = soup.find('a', class_='username')
        return a.find('span').text
    except Exception as e:
        return False


async def get_rating(username):
    html = await get_html(host + f'/users/{username}')
    soup = BeautifulSoup(html, features='html.parser')
    div = soup.find('div', class_='col-md-9 col-sm-12')
    table = div.find('table', class_='dl-table')
    if table:
        trs = table.find_all_next('tr')
        for tr in trs:
            if tr.find('th', text='Rating'):
                return int(tr.find('span').text)
    return 0


async def find_duration(url):
    html = await get_html(url)
    soup = BeautifulSoup(html, features='html.parser')
    try:
        return soup.find('li', text=re.compile('Duration:*')).contents[0][10:]
    except AttributeError:
        return '0'


async def parse_upcoming():
    html = await get_html(url)
    soup = BeautifulSoup(html, features='html.parser')
    try:
        table = soup.find('div', id='contest-table-upcoming')
        table = table.find('tbody')
        time = table.find_all('time')
        times = []
        for i in time:
            times.append(i.contents[0][:-5])

        # time = table.find('time')
        # print(time.contents)

        times = list(map(datetime.datetime.fromisoformat, times))
        for i in range(len(times)):
            times[i] -= datetime.timedelta(0, 0, 0, 0, 0, 9)

        names = table.find_all('a')[1::2]
        durations = []

        for i in range(len(names)):
            names[i] = str(names[i])[:9] + host + str(names[i])[9:]
            durations.append(await find_duration(await get_url(names[i])))

        table = []
        contest_type = 'ac'
        for i in range(len(times)):
            table.append([times[i], names[i], durations[i], contest_type])

        return table
    except:
        print("AtCoder has no contests for now. Sad(")
        return []


async def main():
    b = await parse_upcoming()
    print(b)


if __name__ == '__main__':
    now = time.time()
    asyncio.run(main())
    print(time.time() - now)
