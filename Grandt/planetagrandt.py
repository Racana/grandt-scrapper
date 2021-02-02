import requests
import locale
import csv
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

locale.setlocale(locale.LC_ALL, 'es_ES.utf8')

def parse_date(date):
    parsed_date = datetime.strptime(date, '%A, %d de %B de %Y')
    return parsed_date

def obtain_links(url, links, dates, validate):
    while True:
        validate_links = validate.links.tolist()
        validate_dates = validate.dates.tolist()

        r = requests.get(url)
        if r.status_code != 200:
            break

        soup = BeautifulSoup(r.text, 'html.parser') 
        estadisticas = soup.find_all('a', text='Ver Estadísticas')
        date_header = soup.find_all('h2', {'class':'date-header'})

        [links.append(x['href']) for x in estadisticas] 
        [dates.append(parse_date(date.text)) for date in date_header]
        
        if any(l in validate_links for l in links):
            break #if we get to last stored page we stop

        if any(t < datetime(2015, 2, 1) for t in dates):
            break #we get data until 2015

        url = soup.find('a', {'class':'blog-pager-older-link'})['href']

    if len(links) != len(dates):
        print('something happen, link and dates dont have the same lenght')

    df = pd.DataFrame({'dates':dates, 'links': links})
    df.sort_values(by=['dates'], inplace=True)

    df = df.merge(validate, how='left', indicator=True).query('_merge == "left_only"').drop(['_merge'], axis=1)

    return df