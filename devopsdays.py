import re

import dateparser
import requests
from bs4 import BeautifulSoup

def get(url):
    res = requests.get(url)
    return BeautifulSoup(res.text, 'html.parser')


def parse_events():
    root = get('https://www.devopsdays.org/events/')
    for elm in root.select('.col-md-12 .row')[1].find_all('a'):
        yield elm['href']


def parse_open_cfps():
    root = get('https://www.devopsdays.org/speaking/')
    for row in root.select('table.sortable tbody tr'):
        yield {
            'Location': row.find('a').string,
            'Conference URL': 'https://www.devopsdays.org' + row.find('a')['href'],
            'CFP End Date': dateparser.parse(row.find_all('td')[1].string.strip()),
            'Conference Start Date': dateparser.parse(row.find_all('td')[2].string.strip()).date(),
        }


def parse_event(url):
    root = get(url+'welcome/')

    cfp_nav = None
    for nav in root.select('.nav-link'):
        nav_text = str(nav.string).lower()
        if 'propose' in nav_text or 'cfp' in nav_text:
            cfp_nav = nav
            break
    if cfp_nav is None:
        propose_elm = root.find('strong', string='Propose')
        if propose_elm:
            cfp_nav = propose_elm.parent.next_sibling.find('a')
    if cfp_nav is None:
        return None
    cfp_url = cfp_nav['href']
    if cfp_url.startswith('/'):
        cfp_url = f'https://www.devopsdays.org{cfp_url}'


    dates_elm = root.find('strong', string='Dates')
    if dates_elm:
        dates = dates_elm.parent.next_sibling.string.split('-')
        event_end = dateparser.parse(dates[-1]).date()
    else:
        dates = root.select('.welcome-page-date')[0].contents[0]
        # Looks like "April 9 - 10, 2019"
        md = re.match(r'^(\S+) ([ 0-9-]+), (\d+)$', dates)
        if md:
            month, days, year = md.group(1, 2, 3)
            if '-' in days:
                start_day, end_day = days.split('-')
            else:
                start_day = end_day = days
            event_end = dateparser.parse(f'{month} {end_day}, {year}').date()
            if int(start_day) > int(end_day):
                event_end = event_end.replace(month=event_end.month+1)
        else:
            raise ValueError(f'Unable to find end date in {url}')

    name_parts = root.select('.welcome-page')[0].string.split()
    name_parts[0] = name_parts[0].capitalize()
    name = ' '.join(name_parts)

    return {
        'Conference Name': name,
        'CFP URL': cfp_url,
        'Conference End Date': event_end,
        'Tags': ['devops', 'devopsdays'],
    }


def scrape():
    for data in parse_open_cfps():
        evt_data = parse_event(data['Conference URL'])
        if evt_data is None:
            continue
        data.update(evt_data)
        # Papercall is already handled.
        if 'papercall.io' in data['CFP URL']:
            continue
        yield data

if __name__ == '__main__':
    # print(parse_event('https://www.devopsdays.org/events/2019-indianapolis/'))
    # for d in parse_open_cfps():
        # print(d)
    for d in scrape():
        print(d)
