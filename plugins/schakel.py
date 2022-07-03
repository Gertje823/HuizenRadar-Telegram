"""
*schakel* - schakel.nl

"""
from plugins import new_message, enable_check
import requests, sqlite3, re, yaml
from bs4 import BeautifulSoup

def check_schakel(context):
    if enable_check.enable_check(__name__):
        return
    # load filters
    with open('config.yaml', 'r') as f:
        config = yaml.full_load(f)
    cookies = {
        'display': 'list',
        'cookielawinfo-checkbox-necessary': 'yes',
        'cookielawinfo-checkbox-functional': 'yes',
        'cookielawinfo-checkbox-analytics': 'yes',
        'cookielawinfo-checkbox-advertisement': 'yes',
        'cookielawinfo-checkbox-others': 'yes',
        'cookielawinfo-checkbox-performance': 'yes',
        'CookieLawInfoConsent': 'eyJuZWNlc3NhcnkiOnRydWUsImZ1bmN0aW9uYWwiOnRydWUsInBlcmZvcm1hbmNlIjp0cnVlLCJhbmFseXRpY3MiOnRydWUsImFkdmVydGlzZW1lbnQiOnRydWUsIm90aGVycyI6dHJ1ZX0=',
        'viewed_cookie_policy': 'yes',
    }

    headers = {
        'authority': 'www.schakel.nl',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-NL,en;q=0.9,nl-NL;q=0.8,nl;q=0.7,en-US;q=0.6,de;q=0.5,ru;q=0.4,it;q=0.3',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'dnt': '1',
        'origin': 'https://www.schakel.nl',
        'referer': 'https://www.schakel.nl/woningen/bestaandebouw/',
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
        'plaats': f"{config['FILTERS']['Location']}",
        'adres': '',
        'koopofhuur': 'koop',
        'soortWoonhuis': '',
        'aantalSlaapkamers': '',
        'prijsMin': '',
        'prijsMax': f"{config['FILTERS']['Max_price']}",
        'typeWoonhuis': '',
        'bouwvorm': '',
        'perceelOppervlakte': '',
        'orderby': 'datumInvoer:desc',
    }

    response = requests.post('https://www.schakel.nl/woningen/bestaandebouw/page/1/', cookies=cookies, headers=headers,
                             data=data).json()
    for item in response['items']:
        conn = sqlite3.connect('huizenradar.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS Schakel(RAW PRIMARY KEY UNIQUE, Price, Address, Status, URL)''')
        # Convert HTML data to usable strings
        soup = BeautifulSoup(item, features="lxml")
        price =  soup.findAll("span", {"class":"prijs"})
        price = price[0].get_text().strip()
        address =  soup.findAll("h4")
        address =  address[0].get_text().strip()
        try:
            status = soup.findAll("div", {"class": "item-status"})
            status = status[0].get_text().strip()
        except IndexError:
            status = ''
        url = soup.findAll("a", {"class": "overlay"})
        url = url[0]['href']

        imgs = [i.get('srcset') for i in soup.find_all('img', srcset=True)]
        try:
            img = re.match(r"(https:\/\/(.*?)-390x260.jpg)", imgs[0]).group(2)
            img = img + '.jpg'
            #print(img)
        except IndexError:
            print(imgs)
            img = ''

        data = soup.findAll("div", {"class": "item-data"})
        area = data[0].get_text().strip()
        Living_space = data[1].get_text().strip()
        Bed_rooms = data[2].get_text().strip()

        # compare with DB

        params = (item, price, address, status, url)
        try:
            c.execute("INSERT INTO Schakel(RAW, Price, Address, Status, URL)VALUES (?,?,?,?,?)", params)
            conn.commit()

            caption = f"Schakel\n[{address}]({url})\n{price}\nArea: {area} Living space: {Living_space}\nBedrooms: {Bed_rooms}"
            try:
                context.bot.send_photo(chat_id=19441944, caption=caption, photo=img, parse_mode="markdown")
            except:
                context.bot.send_message(chat_id=19441944, text=caption, parse_mode="markdown")
        except sqlite3.IntegrityError:
            # Already in DB no message
            continue



