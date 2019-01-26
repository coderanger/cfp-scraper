import re
from datetime import date, datetime, time

import dateparser
import pytz
import requests
from bs4 import BeautifulSoup

import sessionize

def get(url):
    res = requests.get(url)
    return BeautifulSoup(res.text, 'html.parser')


def parse_page(root):
    for evt_elm in root.select('.CalMEvent a'):
        col_index = len(evt_elm.find_parent('td').find_previous_siblings('td'))
        date_row = evt_elm.find_parent('tr').find_previous_sibling(lambda elm: elm.name == 'tr' and elm.select('.CalMDate'))
        day = date_row.find_all('td')[col_index].text
        yield {
            'short_name' : evt_elm.text,
            'url': evt_elm['href'],
            'name': evt_elm['title'],
            'day': day
        }


def find_pages():
    start = date.today()
    for i in range(12):
        new_month = start.month + i
        new_year = start.year
        if new_month > 12:
            new_month -= 12
            new_year += 1
        yield f'https://lwn.net/Calendar/Monthly/cfp/{new_year}-{new_month:02d}/', date(new_year, new_month, 1)


def parse_pages():
    for url, base_date in find_pages():
        for evt in parse_page(get(url)):
            evt['date'] = base_date.replace(day=int(evt['day']))
            yield evt


def format_page(raw_evt):
    md = re.search(r'^([^(]+) \(([^)]+)\)$', raw_evt['name'])
    name, location = md.group(1, 2)
    return {
        'Conference Name': name,
        'Conference URL': raw_evt['url'],
        'Location': location,
        'CFP URL': raw_evt['url'],
        'CFP End Date': datetime.combine(raw_evt['date'], time()),
    }

def scrape():
    for raw_evt in parse_pages():
        evt = format_page(raw_evt)
        if evt is None:
            continue
        if 'papercall.io' in evt['CFP URL']:
            continue
        if 'events.linuxfoundation.org' in evt['CFP URL']:
            continue
        if 'sessionize.com' in evt['CFP URL']:
            s = sessionize.parse_event(evt['CFP URL'])
            if s:
                evt.update(s)
        yield evt

if __name__ == '__main__':
    for e in scrape():
        print(e)
