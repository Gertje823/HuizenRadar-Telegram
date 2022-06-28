"""
*weusthuis* - weusthuismakelaardij.nl

"""
from plugins import new_message, enable_check
import requests, sqlite3, re
from bs4 import BeautifulSoup
import cssutils, yaml

def check_weusthuis(context):
    if enable_check.enable_check(__name__):
        return
    # load filters
    with open('config.yaml', 'r') as f:
        config = yaml.full_load(f)

    cookies = {
        'CRAFT_CSRF_TOKEN': 'd536a7fd9df9f1dcf7c26db1f3e25a2a003181e5d8689d4ce6a5cd930c82aa75a%3A2%3A%7Bi%3A0%3Bs%3A16%3A%22CRAFT_CSRF_TOKEN%22%3Bi%3A1%3Bs%3A40%3A%22tbR-K9pS7isM3vdRJvSr31qkYwWvbs12O1dtv7KN%22%3B%7D',
    }

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-NL,en;q=0.9,nl-NL;q=0.8,nl;q=0.7,en-US;q=0.6,de;q=0.5,ru;q=0.4,it;q=0.3',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Referer': 'https://www.weusthuismakelaardij.nl/aanbod/woningen/p2?highestPrice=1000000&type=sale&price%5B%5D=0&price%5B%5D=250000&query=Almelo&sort=newest&pageAmount=10',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    params = {
        'highestPrice': '1000000',
        'type': 'sale',
        'price[]': [
            '0',
            f"{config['FILTERS']['Max_price']}",
        ],
        'query': config['FILTERS']['Location'],
        'sort': 'newest',
        'pageAmount': '10',
        'isPartial': '1',
    }

    response = requests.get('https://www.weusthuismakelaardij.nl/aanbod/woningen/p2', params=params, cookies=cookies,
                            headers=headers).content
    soup = BeautifulSoup(response, features="lxml")
    items = soup.findAll("div", {"class":"md:w-1/2 lg:w-3/5 xl:w-2/3 px-15"})
    #print(item)
    i = 0
    b = 0
    for item in items:
        conn = sqlite3.connect('huizenradar.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS weusthuis(RAW PRIMARY KEY UNIQUE, Price, Address, Status, URL)''')
        # Convert HTML data to usable strings
        # Get Price
        price =  soup.findAll("p", {"class":"font-ubuntu text-2xl xl:text-3xl text-green leading-none mb-15"})
        price = price[i].get_text().strip()

        # Get Address & url
        address =  soup.findAll("a", {"class":"font-ubuntu font-bold text-grey text-2xl md:text-3xl leading-none mb-15 transition hover:no-underline hover:text-green"})
        url = address[i]['href']
        address =  address[i].get_text().strip()

        # rooms = soup.findAll("div", {"class": "lg:w-1/2"})
        # #print(rooms)
        # data = []
        # c=0
        # for a in rooms:
        #     if c == 3:
        #         break
        #     print(a.get_text().strip())
        #     data.append(a.get_text().strip())
        #     b+=1
        #     c+=1
        # print(data)

        # page does not contain status
        status = ''
        div_style = soup.findAll("div", {"class": "block image pt-2/3 bg-grey-lighter mb-25 md:mb-0 transition hover:shadow-lg"})[i]['style']
        style = cssutils.parseStyle(div_style)
        img = style['background-image']
        img = img.replace('url(', '').replace(')', '')
        print(img)
        # compare with DB
        print(item.get_text().strip())
        params = (price, address, status, url)
        try:
            c.execute("INSERT INTO weusthuis(RAW, Price, Address, Status, URL)VALUES (?,?,?,?,?)", (item.get_text().strip(), price, address, status, url))
            conn.commit()

            caption = f"[{address}]({url})\n{price}"
            try:
                context.bot.send_photo(chat_id=config['TELEGRAM']['USERID'], caption=caption, photo=img, parse_mode="markdown")
            except:
                context.bot.send_message(chat_id=config['TELEGRAM']['USERID'], text=caption, parse_mode="markdown")
        except sqlite3.IntegrityError:
            # Already in DB no message
            continue
        i += 1


