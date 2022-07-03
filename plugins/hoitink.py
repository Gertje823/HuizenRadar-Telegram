"""
*hoitink* - hoitinkmakelaardij.nl

"""
from plugins import new_message, enable_check
import requests, sqlite3, re
from bs4 import BeautifulSoup
import cssutils, yaml


def check_hoitink(context):
    if enable_check.enable_check(__name__):
        return
    # load filters
    with open('config.yaml', 'r') as f:
        config = yaml.full_load(f)
    cookies = {
        'b1f695736752772a0874e17bd161669a': '050il03rrvuh8hoabnl9ahdc17',
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-NL,en;q=0.9,nl-NL;q=0.8,nl;q=0.7,en-US;q=0.6,de;q=0.5,ru;q=0.4,it;q=0.3',
        'Connection': 'keep-alive',
        # 'Cookie': 'b1f695736752772a0874e17bd161669a=050il03rrvuh8hoabnl9ahdc17',
        'DNT': '1',
        'Referer': 'https://www.hoitinkmakelaardij.nl/index.php/aanbod/203/search?option=com_realestatemanager&Itemid=203&task=search&searchtext=Almelo&submit=Zoeken&Houseid=on&Description=on&Title=on&Address=on&Country=on&Region=on&City=on&District=on&Zipcode=on&ownername=on&Area=on&Feature=on&Lot_size=on&Volume=on',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    params = {
        'submit': 'Zoeken',
        'Houseid': 'on',
        'Description': 'on',
        'Title': 'on',
        'Address': 'on',
        'Country': 'on',
        'Region': 'on',
        'City': 'on',
        'District': 'on',
        'Zipcode': 'on',
        'ownername': 'on',
        'Area': 'on',
        'Feature': 'on',
        'Lot_size': 'on',
        'Volume': 'on',
        'limit': '1200',
    }

    response = requests.get(f"https://www.hoitinkmakelaardij.nl/index.php/aanbod/203/search/12/12/{config['FILTERS']['Location']}", params=params,
                            cookies=cookies, headers=headers).content

    soup = BeautifulSoup(response, features="lxml")
    items = soup.findAll("div", {"class":"col-lg-4 col-md-4 col-sm-6 col-xs-12"})

    i = 0
    b = 0
    for item in items:
        conn = sqlite3.connect('huizenradar.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS hoitink(RAW PRIMARY KEY UNIQUE, Price, Address, Status, URL)''')
        # Convert HTML data to usable strings
        # Get Price
        status = item.findAll("div", {"class": "status"})
        status = status[0].get_text().strip()
        if "Verkocht" in status:
            # ignore sold
            continue
        else:
            # Get price
            price =  item.findAll("div", {"class":"price_hits"})
            price = price[0].get_text().strip()
            if re.search(r"(\d{1,}\.\d{1,})", price):
                price = re.search(r"(\d{1,}\.\d{1,})", price).group(1).replace(".","")
                if int(price) <= config['FILTERS']['Max_price']:
                    # Get address
                    address = item.findAll("div", {"class": "location"})
                    address = address[0].get_text().strip()
                    city = item.findAll("span", {"class": "city"})
                    city = city[0].get_text().strip()
                    address = address + ' ' + city
                    # get url
                    url = item.findAll("a")
                    url = url[0]['href']
                    # get img
                    img = item.findAll("img")
                    img = f"https://www.hoitinkmakelaardij.nl/{img[0]['src']}"
                    # get area
                    # area =  item.findAll("div", {"class":"land_area"})
                    #
                    # area = area[0]['text'].get_text().strip()
                    # # get living area
                    # living_area =  item.findAll("div", {"class":"area"})
                    # living_area = area[0].get_text().strip()

                    # compare with DB
                    try:
                        c.execute("INSERT INTO hoitink(RAW, Price, Address, Status, URL)VALUES (?,?,?,?,?)", (item.get_text().strip(), price, address, status, url))
                        conn.commit()

                        caption = f"Hoitink Makelaardij\n[{address}]({url})\n{price}"
                        try:
                            context.bot.send_photo(chat_id=config['TELEGRAM']['USERID'], caption=caption, photo=img, parse_mode="markdown")
                        except:
                            context.bot.send_message(chat_id=config['TELEGRAM']['USERID'], text=caption, parse_mode="markdown")
                    except sqlite3.IntegrityError:
                        # Already in DB no message
                        continue
                else:
                    # This house will be ignored because it does not match our filters
                    continue


