import os
from datetime import datetime

import airtable
import dateparser


class AirtableModel(dict):
    class AirtablePropety:
        def __get__(_self, _instance, owner):
            if not hasattr(owner, '_db'):
                if not owner.table_name:
                    raise ValueError(f'{owner} does not define table_name')
                owner._db = airtable.Airtable(os.environ['AIRTABLE_BASE_KEY'], owner.table_name)
            return owner._db

    table_name = None
    db = AirtablePropety()

    def __init__(self, airtable_id=None, **fields):
        self.airtable_id = airtable_id
        super().__init__(fields)

    @classmethod
    def fetch(cls, **query):
        if len(query) != 1:
            raise ValueError(f'Invalid fetch query: {query}')
        key, value = list(query.items())[0]
        key = key.replace('_', ' ')
        record = cls.db.match(key, value)
        return cls(airtable_id=record.get('id'), **record.get('fields', {}))

    @classmethod
    def fetch_all(cls):
        for page in cls.db.get_iter():
            for record in page:
                yield cls(airtable_id=record.get('id'), **record.get('fields', {}))

    def save(self):
        if self.airtable_id:
            self.db.update(self.airtable_id, self)
        else:
            record = self.db.insert(self)
            self.airtable_id = record['id']


def datetime_lt(a, b):
    if isinstance(a, (str, bytes)):
        a = dateparser.parse(a)
    if isinstance(b, (str, bytes)):
        b = dateparser.parse(b)
    return a.replace(tzinfo=None) < b.replace(tzinfo=None)


class Conference(AirtableModel):
    table_name = 'Conferences'

    def __str__(self):
        label = self.get('Conference Name')
        if not label:
            label = self['CFP URL']
        return f'Conference: {label}'

    def save(self):
        # If we didn't have a CFP Start Date, just assume it's today.
        if 'CFP Start Date' not in self:
            if self.get('CFP End Date') and datetime_lt(self['CFP End Date'], datetime.now()):
                d = self['CFP End Date']
                if isinstance(d, (str, bytes)):
                    d = str(dateparser.parse(d).date())
                self['CFP Start Date'] = d
            else:
                self['CFP Start Date'] = str(datetime.utcnow().date())

        # Clear computed fields.
        end_date_only = self.pop('CFP End Date (Only)', None)

        # Handle the tags value.
        tags = self.pop('Tags', [])
        try:
            super().save()
        finally:
            # Restore it after the save
            self['Tags'] = tags
            self['CFP End Date (Only)'] = end_date_only
        # Update any new tags.
        for t in tags:
            tag = Tag.fetch(Tag=t)
            if self.airtable_id not in tag.get('Conference', []):
                tag['Tag'] = t
                tag.setdefault('Conference', [])
                tag['Conference'].append(self.airtable_id)
                tag.save()
        # Remove any old tags.
        for t in self.db.get(self.airtable_id)['fields'].get('Tags', []):
            if t not in tags:
                tag = Tag.fetch(Tag=t)
                if tag.get('Conferences'):
                    tag['Conferences'].delete(self.airtable_id)
                    tag.save()


class Tag(AirtableModel):
    table_name = 'Conference Tags'
