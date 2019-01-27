# https://calendar.google.com/calendar/ical/mozilla.com_tptb36ac7eijerilfnf6c1onfo%40group.calendar.google.com/public/basic.ics
import re
from datetime import datetime

import dateparser
import requests
import ics
from urlextract import URLExtract

import sessionize

FLAG_A = ord('🇦')
FLAG_Z = FLAG_A + 26
FLAG_OFFSET = FLAG_A - ord('A')
URL_EXTRACTOR = URLExtract()


def fetch_cal():
    url = 'https://calendar.google.com/calendar/ical/mozilla.com_tptb36ac7eijerilfnf6c1onfo%40group.calendar.google.com/public/basic.ics'
    return ics.Calendar(requests.get(url).text)


def convert_flags(s):
    ords = [ord(c) for c in s]
    return ''.join(chr(c - FLAG_OFFSET) if FLAG_A <= c <= FLAG_Z else chr(c) for c in ords)


def parse_event_url(evt):
    links = URL_EXTRACTOR.find_urls(evt.description)
    if links:
        return links[0]


def parse_date(raw_date, relative_to):
    s = {'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': relative_to.replace(tzinfo=None)}

    md = re.search(r'^(\w+) (\d+)\s*-\s*(\w+) (\d+)(.*)$', raw_date)
    if md:
        return (
            dateparser.parse(f'{md.group(1)} {md.group(2)}', settings=s).date(),
            dateparser.parse(f'{md.group(3)} {md.group(4)}', settings=s).date(),
            md.group(5),
        )
    md = re.search(r'^(\w+) (\d+)\s*-\s*(\d+)(.*)$', raw_date)
    if md:
        return (
            dateparser.parse(f'{md.group(1)} {md.group(2)}', settings=s).date(),
            dateparser.parse(f'{md.group(1)} {md.group(3)}', settings=s).date(),
            md.group(4),
        )
    md = re.search(r'^(\w+) (\d+)(.*)$', raw_date)
    if md:
        d = dateparser.parse(f'{md.group(1)} {md.group(2)}', settings=s).date()
        return (d, d, md.group(3))
    return (None, None, raw_date)


def parse_event_name(label, relative_to):
    label = convert_flags(label)
    md = re.search(r'^(.*) \((.*?)\)$', label)
    if not md:
        return {
            'Conference Name': label.strip(),
        }
    name, dates_and_location = md.group(1, 2)
    # Try to filter out the word CFP.
    name = name.replace('CFP', '')
    name = re.sub(r'(^| ):( |$)', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    # Parse dates.
    start_date, end_date, location = parse_date(dates_and_location, relative_to)
    # Clean up the location.
    location = location.lstrip(',').strip()
    evt = {
        'Conference Name': name,
    }
    if start_date:
        evt['Conference Start Date'] = start_date
    if end_date:
        evt['Conference End Date'] = end_date
    if location:
        evt['Location'] = location
    return evt


def parse_events(cal):
    # Skip anything that closed more than a year ago.
    now = datetime.utcnow()
    cutoff = now.replace(year=now.year-1, tzinfo=None)

    for evt in cal.events:
        if evt.begin.datetime.replace(tzinfo=None) < cutoff:
            continue
        data = parse_event_name(evt.name, evt.begin.datetime)
        if evt.location:
            data['Location'] = evt.location
        data['CFP End Date'] = evt.begin.datetime.replace(tzinfo=None)
        url = parse_event_url(evt)
        if url:
            data['Conference URL'] = data['CFP URL'] = url
        yield data


def scrape():
    for evt in parse_events(fetch_cal()):
        if evt is None or 'CFP URL' not in evt:
            continue
        if 'papercall.io' in evt['CFP URL']:
            continue
        if 'sessionize.com' in evt['CFP URL']:
            s = sessionize.parse_event(evt['CFP URL'])
            if s:
                evt.update(s)
        yield evt


if __name__ == '__main__':
    for e in scrape():
        print(e)
