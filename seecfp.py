import dateparser
import pytz
import requests

import sessionize

URL = '''
https://airtable.com/v0.3/view/viw1YoXQzG3f7Ty7D/readSharedViewData?stringifiedObjectParams=%7B%7D&requestId=reqcNhwt4DFJWjr0u&accessPolicy=%7B%22allowedAction
s%22%3A%5B%7B%22modelClassName%22%3A%22view%22%2C%22modelIdSelector%22%3A%22viw1YoXQzG3f7Ty7D%22%2C%22action%22%3A%22readSharedViewData%22%7D%2C%7B%22modelClas
sName%22%3A%22view%22%2C%22modelIdSelector%22%3A%22viw1YoXQzG3f7Ty7D%22%2C%22action%22%3A%22getMetadataForPrinting%22%7D%2C%7B%22modelClassName%22%3A%22row%22%
2C%22modelIdSelector%22%3A%22rows+*%5BdisplayedInView%3Dviw1YoXQzG3f7Ty7D%5D%22%2C%22action%22%3A%22createBoxDocumentSession%22%7D%2C%7B%22modelClassName%22%3A
%22row%22%2C%22modelIdSelector%22%3A%22rows+*%5BdisplayedInView%3Dviw1YoXQzG3f7Ty7D%5D%22%2C%22action%22%3A%22createDocumentPreviewSession%22%7D%2C%7B%22modelC
lassName%22%3A%22view%22%2C%22modelIdSelector%22%3A%22viw1YoXQzG3f7Ty7D%22%2C%22action%22%3A%22downloadCsv%22%7D%2C%7B%22modelClassName%22%3A%22view%22%2C%22mo
delIdSelector%22%3A%22viw1YoXQzG3f7Ty7D%22%2C%22action%22%3A%22downloadICal%22%7D%2C%7B%22modelClassName%22%3A%22row%22%2C%22modelIdSelector%22%3A%22rows+*%5Bd
isplayedInView%3Dviw1YoXQzG3f7Ty7D%5D%22%2C%22action%22%3A%22downloadAttachment%22%7D%5D%2C%22shareId%22%3A%22shrBMFY4CSpSRGmAs%22%2C%22applicationId%22%3A%22a
ppl4CwxGoKNDk2ek%22%2C%22sessionId%22%3A%22sestt1hvhA5QXmrdz%22%2C%22generationNumber%22%3A0%2C%22signature%22%3A%22562e2ea38b121c78fada55b507c41695cb9991bfe74
e1231c9be2406c3e589ee%22%7D
'''.replace('\n', '')
HEADERS = {'x-airtable-application-id': 'appl4CwxGoKNDk2ek', 'X-Requested-With': 'XMLHttpRequest', 'x-time-zone': 'UTC', 'x-user-locale': 'en'}

def get_data():
    r = requests.get(URL, headers=HEADERS)
    if r.status_code != 200:
        raise requests.HTTPError(f'Error retreiving Airtable data {r.status_code}: {r.text}')
    return r.json()['data']


def convert_columns(data):
    col_map = {}
    for d in data['columns']:
        col_map[d['id']] = d['name']

    for d in data['rows']:
        row_data = {}
        for k, v in d['cellValuesByColumnId'].items():
            k = col_map[k]
            if k == 'Country':
                v = v[0]['foreignRowDisplayName']
            row_data[k] = v
        yield row_data

def format_data(row):
    # {'Link to the call for paper': 'http://www.jbcnconf.com/2019/', 'Submission Deadline': '2019-04-01T00:00:00.000Z', 'Country': [{'foreignRowId': 'recIhNTuv0pD1lSSN', 'foreignRowDisplayName': 'Spain'}], 'City': 'Barcelona', 'Conference Start': '2019-05-27T00:00:00.000Z', 'Conference End': '2019-05-29T00:00:00.000Z', 'Name': 'JBCNConf-2019', 'Continent': {'valuesByForeignRowId': {'recIhNTuv0pD1lSSN': ['Europe']}, 'foreignRowIdOrder': ['recIhNTuv0pD1lSSN']}, 'Days left': 69, 'When': 'May'}
    location = row['Country']
    if 'City' in row:
        location = '{}, {}'.format(row['City'], row['Country'])
    return {
        'CFP URL': row['Link to the call for paper'],
        'Conference URL': row['Link to the call for paper'], # Shrug, I guess I'll just use it for both.
        'CFP End Date': dateparser.parse(row['Submission Deadline']).astimezone(pytz.utc).replace(tzinfo=None),
        'Location': location,
        'Conference Start Date': dateparser.parse(row['Conference Start']).date(),
        'Conference End Date': dateparser.parse(row['Conference End']).date(),
        'Conference Name': row['Name']
    }


def scrape():
    for raw_row in convert_columns(get_data()):
        row = format_data(raw_row)
        if row is None:
            continue
        if 'papercall.io' in row['CFP URL']:
            continue
        if 'sessionize.com' in row['CFP URL']:
            s = sessionize.parse_event(row['CFP URL'])
            if s:
                row.update(s)
        yield row


if __name__ == '__main__':
    for row in scrape():
        print(row)


# 'Country': [{'foreignRowId': 'recOUw0MItMcZxNQe', 'foreignRowDisplayName': 'Slovakia'}]
