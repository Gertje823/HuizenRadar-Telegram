"""
*Funda* - funda.nl
"""
from plugins import new_message, enable_check
import requests, sqlite3, re
from bs4 import BeautifulSoup
import cssutils, yaml


def check_funda(context):
    if enable_check.enable_check(__name__):
        return
    with open('config.yaml', 'r') as f:
        config = yaml.full_load(f)
    max_price = config['FILTERS']['Max_price']
    location = config['FILTERS']['Location']
    cookies = {

    }

    headers = {
        'authority': 'www.funda.nl',
        'accept': '*/*',
        'accept-language': 'en-NL,en;q=0.9,nl-NL;q=0.8,nl;q=0.7,en-US;q=0.6,de;q=0.5,ru;q=0.4,it;q=0.3',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'dnt': '1',
        'origin': 'https://www.funda.nl',
        'referer': f'https://www.funda.nl/koop/{location}/sorteer-datum-af/',
        'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    data = f'filter_location={location}&autocomplete-identifier={location}&filter_Straal=0&filter_ZoekType=koop&filter_ZoekType=koop&filter_WijkNaam=active&filter_KoopprijsVan=0&filter_KoopprijsVan=&filter_KoopprijsTot={max_price}&filter_KoopprijsTot=&filter_SoortObject=&filter_WoningSoort=active&filter_WoningType=active&filter_SoortAppartementId=active&filter_AppartementType=active&filter_SoortParkeergelegenheidId=active&filter_AutoCapaciteitParkeergelegenheid=&filter_IndBouwrijp=&filter_PublicatieDatum=&filter_WoonOppervlakte=&filter_WoonOppervlakte-range-min=&filter_WoonOppervlakte-range-max=&filter_PerceelOppervlakte=&filter_PerceelOppervlakte-range-min=&filter_PerceelOppervlakte-range-max=&filter_AantalKamers=&filter_AantalKamers-range-min=&filter_AantalKamers-range-max=&filter_AantalSlaapkamers=&filter_LiggingTuin=active&filter_Tuinoppervlakte=&filter_BouwPeriodeId=active&filter_Ligging=active&filter_BouwvormId=&filter_SoortGarage=active&filter_AutoCapaciteitGarage=&filter_AanwezigheidVan=active&filter_Toegankelijkheid=active&filter_Energielabel=active&filter_ZoekType=koop&filter_IndicatiePDF=active&filter_OpenHuizen=&filter_VeilingDatum=&filter_VirtueleOpenHuizen=&sort=sorteer-datum_Descending&search-map-type-control-top=default&pagination-page-number-next=2&'

    response = requests.post(f'https://www.funda.nl/koop/{location}/beschikbaar/sorteer-datum-af/', cookies=cookies, headers=headers, data=data)

    soup = BeautifulSoup(response.json()['content']['results'], features="lxml")
    items = soup.findAll("ol", {"class":"search-results"})
    for item in items:
        conn = sqlite3.connect('huizenradar.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS Funda(RAW PRIMARY KEY UNIQUE, Price, Address, Status, URL)''')
        # Convert HTML data to usable strings
        # Get Price
        try:
            price = item.findAll("span", {"class": "search-result-price"})
            price = price[0].get_text().strip()
            status = "Available"
        except IndexError:
            price = ''
            status = "Not Available"
        # Get Address & url
        url = item.findAll("a")
        url = "https://funda.nl" + url[0]['href']

        address = item.findAll("a")
        address = address[1].get_text().strip()
        img = item.findAll("img")[0]['src']
        try:
            c.execute("INSERT INTO Funda(RAW, Price, Address, Status, URL)VALUES (?,?,?,?,?)",
                      (item.get_text().strip(), price, address, status, url))
            conn.commit()

            caption = f"Funda\n[{address}]({url})\n{price}"
            try:
                context.bot.send_photo(chat_id=config['TELEGRAM']['USERID'], caption=caption, photo=img,
                                       parse_mode="markdown")
            except:
                context.bot.send_message(chat_id=config['TELEGRAM']['USERID'], text=caption, parse_mode="markdown")
        except sqlite3.IntegrityError:
            # Already in DB no message
            continue