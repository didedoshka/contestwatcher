from bs4 import BeautifulSoup
import urllib.request
import datetime
import re

url = 'https://atcoder.jp/home'
host = 'https://atcoder.jp'


def get_html(url):
    response = urllib.request.urlopen(url)
    return response.read()


async def get_last():
    html = get_html(url)
    soup = BeautifulSoup(html, features='html.parser')
    table = soup.find('div', id='contest-table-recent')
    table = table.find('tbody')

    name = table.find_all('a')[1]

    return str(name)[:9] + host + str(name)[9:]


async def get_rating_change(url, user):
    html = get_html(f'{host}/users/{user}/history')
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
    html = get_html(f'{url}/submissions')

    soup = BeautifulSoup(html, features='html.parser')
    ul = soup.find('ul', class_='pagination pagination-sm mt-0 mb-1')
    a = ul.find_all('a')[-1]

    html = get_html(host + str(a)[9:str(a).find('>') - 1])
    soup = BeautifulSoup(html, features='html.parser')
    table = soup.find('table', class_='table table-bordered table-striped small th-center')
    tbody = table.find('tbody')
    tr = tbody.find_all('tr')[0]
    user = tr.find_all('a')[1]['href']
    html = get_html(f'{host}{user}/history')
    # html = get_html(f'{host}/users/NToneE/history')
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
        html = get_html(host + f'/users/{username}')
    except urllib.error.HTTPError:
        return False
    soup = BeautifulSoup(html, features='html.parser')
    a = soup.find('a', class_='username')
    return a.find('span').text


async def get_rating(username):
    html = get_html(host + f'/users/{username}')
    soup = BeautifulSoup(html, features='html.parser')
    div = soup.find('div', class_='col-md-9 col-sm-12')
    table = div.find('table', class_='dl-table')
    if table:
        trs = table.find_all_next('tr')
        for tr in trs:
            if tr.find('th', text='Rating'):
                return int(tr.find('span').text)
    return 0


def find_duration(url):
    html = get_html(url)
    soup = BeautifulSoup(html, features='html.parser')
    try:
        return soup.find('li', text=re.compile('Duration:*')).contents[0][10:]
    except AttributeError:
        return '0'


def parse_upcoming():
    html = get_html(url)
    soup = BeautifulSoup(html, features='html.parser')
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
        durations.append(find_duration(str(names[i])[9:str(names[i]).find('>') - 1]))

    table = []
    contest_type = 'ac'
    for i in range(len(times)):
        table.append([times[i], names[i], durations[i], contest_type])

    return table

