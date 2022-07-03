"""
*marcel-kon* - marcel-kon.nl

"""
# To do filter price
from plugins import new_message, enable_check
import requests, sqlite3, re
from bs4 import BeautifulSoup
import cssutils, yaml

def check_marcel_kon(context):
    if enable_check.enable_check(__name__):
        return
    with open('config.yaml', 'r') as f:
        config = yaml.full_load(f)
    cookies = {
        'display': 'list',
    }

    headers = {
        'authority': 'www.marcel-kon.nl',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-NL,en;q=0.9,nl-NL;q=0.8,nl;q=0.7,en-US;q=0.6,de;q=0.5,ru;q=0.4,it;q=0.3',
        'cache-control': 'max-age=0',
        # 'cookie': 'display=list',
        'dnt': '1',
        'origin': 'https://www.marcel-kon.nl',
        'referer': 'https://www.marcel-kon.nl/woningen/',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    }

    data = {
        'plaats': config['FILTERS']['Location'],
        'type': '',
        'eigendomsoort': '',
        'koopprijs': '',
    }

    response = requests.post('https://www.marcel-kon.nl/woningen/', cookies=cookies, headers=headers, data=data).content
    soup = BeautifulSoup(response, features="lxml")
    items = soup.findAll("div", {"class":"blk-4 blk-md-6 blk-sm-12 gutter-sm"})
    i = 0
    b = 0
    for item in items:
        conn = sqlite3.connect('huizenradar.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS marcel_kon(RAW PRIMARY KEY UNIQUE, Price, Address, Status, URL)''')
        # Convert HTML data to usable strings
        # Get Price
        try:
            price =  item.findAll("div", {"class":"items__loop-item-price"})
            price = price[0].get_text().strip()
            status = "Available"
        except IndexError:
            price = ''
            status = item.findAll("div", {"class": "items__loop-item-status"})
            status = status[0].get_text().strip()

        # Get Address & url
        url =  item.findAll("a")
        url = url[0]['href']
        address =  item.findAll("p", {"class":"size-3"})
        address =  address[1].get_text().strip()

        img = item.findAll("img")[0]['src']
        try:
            c.execute("INSERT INTO marcel_kon(RAW, Price, Address, Status, URL)VALUES (?,?,?,?,?)",
                      (item.get_text().strip(), price, address, status, url))
            conn.commit()

            caption = f"Marcel Kon\n[{address}]({url})\n{price}"
            try:
                context.bot.send_photo(chat_id=config['TELEGRAM']['USERID'], caption=caption, photo=img, parse_mode="markdown")
            except:
                context.bot.send_message(chat_id=config['TELEGRAM']['USERID'], text=caption, parse_mode="markdown")
        except sqlite3.IntegrityError:
            # Already in DB no message
            continue


