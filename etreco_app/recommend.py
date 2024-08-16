import time
from datetime import datetime
import re
import json
import requests
import schedule
from bs4 import BeautifulSoup

import pandas as pd
from thefuzz import process


from record import Record


time.sleep(20)  # wait for mysql container to be up
RECORDER = Record()

SCRAPE_URL = "https://economictimes.indiatimes.com/markets/stocks/recos"
LAST_CLOSE_PRICE_URL = "http://192.168.0.125:5000/last_close_price"

NSE_DICT = pd.read_csv("etc/nse_list.csv").set_index("Symbol")["Company Name"].to_dict()
with open("etc/bse_list.json", "r") as file:
    BSE_DICT = json.load(file)
ALL_DICT = NSE_DICT | BSE_DICT


def get_symbol_of(company_name):
    match = process.extract(company_name, NSE_DICT.values(), limit=1)[0][0]
    if match.split(" ")[0] == company_name.split(" ")[0]:
        found = match
    else:
        match = process.extract(company_name, BSE_DICT.values(), limit=1)[0][0]
        if match.split(" ")[0] == company_name.split(" ")[0]:
            found = match
            print("not found on nse, but found on bse - ", company_name)
        else:
            print(company_name, " not found in records")
            return -1  # Not Found
    print("found - ", found)
    for symbol, name in ALL_DICT.items():
        if name == found:
            return symbol


def get_last_close_price(symbol):
    try:
        params = {"ticker": symbol}
        response = requests.get(LAST_CLOSE_PRICE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return round(data.get(symbol, 0), 2)
    except (requests.exceptions.RequestException, ValueError, KeyError):
        return 0


def get_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%b %d, %Y, %I:%M %p %Z")
    except ValueError:
        date_obj = datetime.strptime(date_str, "%b %d, %Y")
    return date_obj.date()


def main():
    url = SCRAPE_URL
    pattern = re.compile(r"((Buy)|(Sell)) (.*), target price Rs (\d*)(\.)*:(.*)")
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        reco_sections = soup.find_all("div", class_="eachStory")
        for section in reco_sections:
            try:
                a_text = section.find("a").text.strip()
                match = pattern.match(a_text)
                side = match.group(1)
                company_name = match.group(4)
                target_price = match.group(5)
                recommender = match.group(7)
                time_text = section.find("time").text.strip()
                if side != "Buy":
                    continue
                symbol = get_symbol_of(company_name)
                if symbol == -1:
                    continue
                else:
                    symbol = symbol + ".NS" if symbol.isalpha() else symbol + ".BO"
                ltp = get_last_close_price(symbol)
                RECORDER.add_row(
                    symbol,
                    company_name,
                    recommender.strip(),
                    get_date(time_text),
                    TP=target_price,
                    LTP=ltp,
                )
            except:
                print("Error in Main Function")
                continue
    else:
        print("Failed to retrieve the webpage")
    return


main()

RECORDER.close_conn()
