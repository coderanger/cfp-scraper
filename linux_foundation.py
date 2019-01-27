import re
from urllib.parse import urljoin

import dateparser
import pytz
import requests
from bs4 import BeautifulSoup

def get(url):
    res = requests.get(url)
    return BeautifulSoup(res.text, 'html.parser')


def parse_date(raw_date):
    md = re.search(r'^(\w+) (\d+), (\d+)$', raw_date)
    if md:
        d = dateparser.parse(raw_date).date()
        return (d, d)
    md = re.search(r'^(\w+) (\d+) - (\d+), (\d+)$', raw_date)
    if md:
        return (
            dateparser.parse(f'{md.group(1)} {md.group(2)}, {md.group(4)}').date(),
            dateparser.parse(f'{md.group(1)} {md.group(3)}, {md.group(4)}').date(),
        )
    md = re.search(r'^(\w+) (\d+) - (\w+) (\d+), (\d+)$', raw_date)
    if md:
        return (
            dateparser.parse(f'{md.group(1)} {md.group(2)}, {md.group(5)}').date(),
            dateparser.parse(f'{md.group(3)} {md.group(4)}, {md.group(5)}').date(),
        )
    raise ValueError(f'Unable to parse {raw_date}')


def parse_events_page():
    root = get('https://events.linuxfoundation.org/')

    for elm in root.select('.single-event-wrap'):
        raw_date, location = [e.string for e in elm.find_all('h3')]
        start_date, end_date = parse_date(raw_date)
        yield {
            'Conference URL': elm.find('span', string=re.compile(r'(?i:(learn more)|(view the website))')).parent['href'],
            'Conference Start Date': start_date,
            'Conference End Date': end_date,
            'Location': location,
        }


def fetch_smapply_json():
    has_next = True
    page = 1
    # Ten page limit to deal with errors I guess?
    while has_next and page < 10:
        data = requests.get(f'https://linuxfoundation.smapply.io/prog/ds/?page={page}&base_query=all').json()
        has_next = data['has_next']
        page += 1
        yield from data['results']


def parse_smapply_json():
    for data in fetch_smapply_json():
        yield {
            'Conference Name': data['name'],
            'CFP Start Date': dateparser.parse(data['startdate']).astimezone(pytz.utc).date(),
            'CFP End Date': dateparser.parse(data['deadline']).astimezone(pytz.utc),
            'CFP URL': 'https://linuxfoundation.smapply.io{}'.format(data['listing_url']),
        }


def possible_cfp_links(evt):
    evt_page = get(evt['Conference URL'])
    for elm in evt_page.find_all('a'):
        if elm.has_attr('href') and ('cfp' in elm['href'] or 'program' in elm['href']):
            yield urljoin(evt['Conference URL'], elm['href'])


def correlate_event(evt, json_data):
    for url in possible_cfp_links(evt):
        page = requests.get(url).text
        for d in json_data:
            if d['CFP URL'].rstrip('/') in page:
                out = {}
                out.update(evt)
                out.update(d)
                return out


def scrape():
    smapply_json = list(parse_smapply_json())

    for evt in parse_events_page():
        out = correlate_event(evt, smapply_json)
        if out is not None:
            yield out


if __name__ == '__main__':
    for d in scrape():
        # print(d)
        pass
