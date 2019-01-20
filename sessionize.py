import dateparser
import requests
from bs4 import BeautifulSoup


def get(url):
    res = requests.get(url)
    return BeautifulSoup(res.text, 'html.parser')


def find_navy_section(root, label):
    for elm in root.select('.text-navy'):
        if elm.contents[-1].strip().startswith(label):
            return elm.find_parent(lambda e: e.has_attr('class') and 'col-' in ' '.join(e['class'])).find('h2')


def parse_event(url):
    root = get(url)

    data = {
        'Conference Name': root.select('.ibox-title h4')[0].string,
        'CFP URL': url,
    }

    elm = find_navy_section(root, 'location')
    if elm:
         data['Location'] = elm.select('.block')[-1].string

    elm = find_navy_section(root, 'website')
    if elm:
        data['Conference URL'] = elm.find('a')['href']

    elm = find_navy_section(root, 'event date')
    if elm:
        data['Conference Start Date'] = data['Conference End Date'] = dateparser.parse(elm.string).date()

    elm = find_navy_section(root, 'event starts')
    if elm:
        data['Conference Start Date'] = dateparser.parse(elm.string).date()

    elm = find_navy_section(root, 'event ends')
    if elm:
        data['Conference End Date'] = dateparser.parse(elm.string).date()

    # Find the UTC version of the CFP end date.
    elm = root.select('.js-closedate')[0]
    if not elm:
        raise ValueError(f'js-closedate not found in {url}')
    utc_cfp_end_date = dateparser.parse(elm['data-date']).replace(tzinfo=None)
    data['CFP End Date'] = utc_cfp_end_date

    elm = find_navy_section(root, 'CfS closes at')
    if not elm:
        raise ValueError(f'CfS closes at not found in {url}')
    time = elm.parent.select('.text-navy')[0].string[13:]
    parsed = dateparser.parse(f'{elm.string} {time}')
    utc_offset = parsed - utc_cfp_end_date


    elm = find_navy_section(root, 'CfS opens at')
    if elm:
        time = elm.parent.select('.text-navy')[0].string[13:]
        date = elm.string
        parsed = dateparser.parse(f'{date} {time}')
        data['CFP Start Date'] = (parsed - utc_offset).date()

    return data

if __name__ == '__main__':
    print(parse_event('https://sessionize.com/mixit19'))
    print(parse_event('https://sessionize.com/blockchain-saturday-Utah-v2'))
