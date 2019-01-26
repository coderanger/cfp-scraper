import itertools
from datetime import date, datetime, timedelta

import devopsdays
import papercall
import models
import sessionize
import linux_foundation
import seecfp
import lwn

def scrape_all():
    print('Scraping Papercall')
    yield from papercall.scrape()
    print('Scraping Devopsdays')
    yield from devopsdays.scrape()
    print('Scraping Sessionize')
    yield from sessionize.scrape()
    print('Scraping Linux Foundation')
    yield from linux_foundation.scrape()
    print('Scraping SeeCFP')
    yield from seecfp.scrape()
    print('Scraping LWN CFP Calendar')
    yield from lwn.scrape()


def sync_record(existing, fields):
    # Convert any needed fields:
    for key, value in fields.items():
        if isinstance(value, datetime):
            fields[key] = value.replace(microsecond=0, tzinfo=None).isoformat() + '.000Z'
        elif isinstance(value, date):
            fields[key] = value.isoformat()
    if not fields.get('Conference Start Date'):
        fields.pop('Conference Start Date', None)
    if not fields.get('Conference End Date'):
        fields.pop('Conference End Date', None)
    if not fields.get('Tags'):
        fields.pop('Tags', None)

    # No existing verison, create it.
    if existing is None:
        conf = models.Conference(**fields)
        print(f'Creating {conf}')
        conf.save()
        return conf
    else:
        # Check if a save is needed.
        do_update = False
        for key, value in fields.items():
            existing_value = existing.get(key)
            # Special case for tags, they need to be sorted to check.
            if key == 'Tags' and value and existing_value:
                if sorted(value) != sorted(existing_value):
                    print('{} {} {}'.format(key, repr(value), repr(existing_value)))
                    do_update = True
                    break
                else:
                    continue

            # Special case, none and '' are okay.
            if value == '' and existing_value is None:
                continue

            if value != existing_value:
                print('Field changed {}: was {} now {}'.format(key, repr(existing_value), repr(value)))
                do_update = True
                break
        if do_update:
            print(f'Updating {existing}')
            existing.update(fields)
            existing.save()
        return existing


def sync_all():
    # Fetch all the conferences into a local cache.
    conferences = {}
    for conf in models.Conference.fetch_all():
        conferences[conf['CFP URL']] = conf

    # Run the scrapes and syncs.
    for fields in scrape_all():
        # Try to filter out meetups
        if 'meetup' in fields.get('Conference Name', '').lower() or 'meetup' in fields.get('Conference URL', '').lower():
            continue
        if fields.get('Conference Start Date') and fields.get('Conference End Date') and fields['Conference End Date'] - fields['Conference Start Date'] > timedelta(days=14):
            continue

        conf = sync_record(conferences.get(fields['CFP URL']), fields)
        conferences[conf['CFP URL']] = conf


def main():
    sync_all()


if __name__ == '__main__':
    main()
