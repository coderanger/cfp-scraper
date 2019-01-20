import csv

import dateparser
import dateparser.search
import requests
from bs4 import BeautifulSoup

URL = 'https://www.papercall.io/events?open-cfps=true&page={page}'

def get(page):
    res = requests.get(URL.format(page=page))
    return BeautifulSoup(res.text, 'html.parser')


def maybe_int(s):
    try:
        return int(s)
    except ValueError:
        return 0


def num_pages():
    pagination = get(1).find(class_='pagination')
    return max(maybe_int(elm.string) for elm in pagination.find_all('a'))



# <div class="row event-list-detail">
#   <div class="col-md-10">
#     <div class="panel panel-default">
#       <div class="panel-heading">
#         <div class="row">
#           <h3 class="event__title col-md-11">
#             <a href="https://www.papercall.io/ibtechcon2019">Ignite Black Tech Conference - iBTechCon2019 - Atlanta, GA</a>
#           </h3>
#           <div class="col-md-1">
#             <div class="pull-right">
#                 <a href="http://ibtechcon.com/" target="_blank">
#                   <i class="fa fa-external-link" aria-hidden="true" data-toggle="tooltip" title="http://ibtechcon.com/"></i>
#                 </a>
#             </div>
#           </div>
#         </div>
#       </div>
#       <div class="panel-body ">
#         <div class="row">
#           <div class="col-md-1 hidden-sm hidden-xs">
#             <a href="https://www.papercall.io/ibtechcon2019" target="_blank">
#               <img width="90px" src="https://papercallio-production.s3.amazonaws.com/uploads/event/logo/1591/thumb_100_ibtechcon_squaremo.png" alt="Thumb 100 ibtechcon squaremo" />
#             </a>
#           </div>
#           <div class="col-md-11 col-sm-12">
#               <h4 class="hidden-xs">
#                 <a target="_blank" href="http://ibtechcon.com/">http://ibtechcon.com/</a>
#               </h4>
#               <h4>
#                 <strong>Event Dates:</strong> February 16, 2019, February 16, 2019
#               </h4>

#               <h4>
#                 <table>
#   <tbody>
#     <tr>
#       <td nowrap><strong> CFP closes at</strong>&nbsp;</td>
#       <td width="100%">January 27, 2019 23:01 UTC</td>
#     </tr>
#     <tr>
#       <td>&nbsp;</td>
#       <td style="font-size: 75%;"><time datetime="2019-01-27T23:01:00Z" data-local="time" data-format="%B %d, %Y %H:%M %Z">January 27, 2019 23:01 UTC</time> (Local)</td>
#     </tr>
#   </tbody>
# </table>

#               </h4>
#               <h4>
#                   <a href="/events?keywords=tags%3A+Blockchain">Blockchain</a>, <a href="/events?keywords=tags%3A+FinTech">Fintech</a>, <a href="/events?keywords=tags%3A+Healthcare+IT">Healthcare it</a>, <a href="/events?keywords=tags%3A+Energy">Energy</a>, <a href="/events?keywords=tags%3A+Entertainment">Entertainment</a>, <a href="/events?keywords=tags%3A+Artificial+Intelligence">Artificial intelligence</a>, <a href="/events?keywords=tags%3A+Virtual+Reality">Virtual reality</a>, <a href="/events?keywords=tags%3A+Gaming">Gaming</a>, <a href="/events?keywords=tags%3A+Cryptocurrency.+Cloud+Services">Cryptocurrency. cloud services</a>, <a href="/events?keywords=tags%3A+Cybersecurity">Cybersecurity</a>, <a href="/events?keywords=tags%3A+Machine+Learning">Machine learning</a>, <a href="/events?keywords=tags%3A+Big+Data">Big data</a>, <a href="/events?keywords=tags%3A+Data+Analytics">Data analytics</a>, <a href="/events?keywords=tags%3A+ERP+management">Erp management</a>, <a href="/events?keywords=tags%3A+Intermediate+Coding">Intermediate coding</a>, <a href="/events?keywords=tags%3A+Advanced+Coding">Advanced coding</a>, <a href="/events?keywords=tags%3A+BioTech">Biotech</a>, <a href="/events?keywords=tags%3A+Automation">Automation</a>, <a href="/events?keywords=tags%3A+Mechanical+engineering">Mechanical engineering</a>, <a href="/events?keywords=tags%3A+Advanced+Robotics">Advanced robotics</a>, <a href="/events?keywords=tags%3A+Unmanned+Systems+Demo">Unmanned systems demo</a>, <a href="/events?keywords=tags%3A+SAAS">Saas</a>, <a href="/events?keywords=tags%3A+CleanTech">Cleantech</a>, <a href="/events?keywords=tags%3A+System+Engineering">System engineering</a>, <a href="/events?keywords=tags%3A+Industry+Insight">Industry insight</a>
#               </h4>
#           </div>
#         </div>
#       </div>
#     </div>
#   </div>
def parse_page(root):
    for event in root.select('.event-list-detail'):
        title_line = event.select('.event__title a')[-1]
        title_parts = title_line.string.split(' - ', 1)
        if len(title_parts) == 1:
            title = title_parts[0]
            location = ''
        elif len(title_parts) == 2:
            title = title_parts[0]
            location = title_parts[1]
        try:
            url = event.select('.fa-external-link')[0]['title']
        except IndexError:
            url = ''
        start_date = end_date = None
        dates = event.find('strong').next_sibling.string.strip()
        if dates.strip():
            parsed_dates = [d for _, d in dateparser.search.search_dates(dates)]
            if parsed_dates:
                start_date = parsed_dates[0].date()
                end_date = parsed_dates[-1].date()
        cfp_close = event.select('tbody td')[1].string
        tags = [t.string for t in event.select('a[href^="/events?keywords=tags"]')]
        yield {
            'CFP URL': title_line['href'],
            'Conference Name': title,
            'Location': location,
            'Conference URL': url,
            'Conference Start Date': start_date,
            'Conference End Date': end_date,
            'CFP End Date': dateparser.parse(cfp_close),
            'Tags': tags,
        }


def parse_all():
    count = num_pages()
    for n in range(count):
        yield from parse_page(get(n+1))


def format_all(out):
    writer = csv.DictWriter(out, dialect='excel-tab', fieldnames=[
        'title', 'url', 'location', 'start_date', 'end_date',
        'cfp_open', 'cfp_close', 'cfp_url', 'tags',
    ])
    writer.writeheader()
    for event in parse_all():
        event['cfp_open'] = True
        writer.writerow(event)


def scrape():
    yield from parse_all()
