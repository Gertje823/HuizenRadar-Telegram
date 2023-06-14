"""
*teamsanders* - Get items from teamsanders.nl
Usage: /teamsanders
"""
from plugins import new_message, enable_check
import requests, sqlite3, re, yaml
from bs4 import BeautifulSoup

def teamsanders(context):
    if enable_check.enable_check(__name__):
        return
    with open('config.yaml', 'r') as f:
        config = yaml.full_load(f)
    max_price = config['FILTERS']['Max_price']
    location = config['FILTERS']['Location']
    cookies = {
        'gmb_r_state': '4c9040a27c81f122ffb321a9b9f2c71c',
    }

    headers = {
        'authority': 'teamsanders.nl',
        'accept': '*/*',
        'accept-language': 'en-NL,en;q=0.9,nl-NL;q=0.8,nl;q=0.7,en-US;q=0.6,de;q=0.5,ru;q=0.4,it;q=0.3',
        # 'cookie': 'gmb_r_state=4c9040a27c81f122ffb321a9b9f2c71c',
        'dnt': '1',
        'if-modified-since': 'Sun, 26 Jun 2022 11:01:11 GMT',
        'referer': 'https://teamsanders.nl/woningen/bestaandebouw',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    data = {
        '__live': '1',
        '__infinite': 'item',
        'plaats': location,
        'wonenType':'koop',
        'koopprijs[min]': '',
        'koopprijs[max]': str(max_price),
        'status': 'beschikbaar',
        'orderby': 'datumInvoer:desc',
    }

    response = requests.post('https://teamsanders.nl/woningen/page/1/', cookies=cookies, headers=headers,
                             data=data).json()
    for item in response['items']:
        conn = sqlite3.connect('huizenradar.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS Teamsanders(RAW PRIMARY KEY UNIQUE, Price, Address, Status, URL)''')
        # Convert HTML data to usable strings
        soup = BeautifulSoup(item, features="lxml")
        price = soup.findAll("div", {"class": "card__price"})
        price = price[0].get_text().strip()
        address = soup.findAll("div", {"class": "card__adress"})
        address = address[0].get_text().strip()
        try:
            status = soup.findAll("div", {"class": "item-status"})
            status = status[0].get_text().strip()
        except IndexError:
            status = ''
        url = soup.findAll("a", {"class": "card__overlay"})
        url = url[0]['href']

        imgs = soup.findAll('div', {'class':'card__slide'})
        img = imgs[0].find('img')['data-flickity-lazyload']

        data = soup.findAll("div", {"class": "card__listing-item u-flex u-align-center u-gap-10"})
        area = data[0].get_text().strip()
        Living_space = data[1].get_text().strip()
        Bed_rooms = data[2].get_text().strip()

        # compare with DB

        params = (item, price, address, status, url)
        try:
            c.execute("INSERT INTO Teamsanders(RAW, Price, Address, Status, URL)VALUES (?,?,?,?,?)", params)
            conn.commit()

            caption = f"[{address}]({url})\n{price}\nWoonoppervlakte: {area}, Kamers: {Living_space}\nSlaapkamers: {Bed_rooms}"
            try:
                context.bot.send_photo(chat_id=19441944, caption=caption, photo=img, parse_mode="markdown")
            except:
                context.bot.send_message(chat_id=19441944, text=caption, parse_mode="markdown")
        except sqlite3.IntegrityError:
            # Already in DB no message
            continue



