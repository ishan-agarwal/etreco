import time
from datetime import datetime
import re
import json
import requests
from bs4 import BeautifulSoup

import pandas as pd
from thefuzz import process


from record import Record


time.sleep(20)  # wait for mysql container to be up
RECORDER = Record()

SCRAPE_URL = "https://economictimes.indiatimes.com/markets/stocks/recos"
CLOSE_PRICE_ON_DATE_URL = "http://192.168.0.125:5000/close_price_on_date"

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


def get_close_price_on_date(symbol, date):
    try:
        params = {"ticker": symbol, "date": str(date)}
        response = requests.get(CLOSE_PRICE_ON_DATE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return round(data.get("close_price", 0), 2)
    except (requests.exceptions.RequestException, ValueError, KeyError):
        return 0


def get_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%b %d, %Y, %I:%M %p %Z")
    except ValueError:
        date_obj = datetime.strptime(date_str, "%b %d, %Y")
    return date_obj.date()


def scrape():
    response = requests.get(SCRAPE_URL)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        reco_sections = soup.find_all("div", class_="eachStory")
        return reco_sections
    else:
        print("Failed to retrieve the webpage")
    
    # Load from local HTML file     
    # with open("etc/old_data.html","r") as file:
    #     html_content = file.read()
    # soup = BeautifulSoup(html_content, "html.parser")
    # reco_sections = soup.find_all("div", class_="eachStory")
    # return reco_sections

def parse(reco_sections):
    pattern = re.compile(r"((Buy)|(Sell)) (.*), target price Rs (\d*)(\.)*:(.*)")
    for section in reco_sections:
        try:
            a_text = section.find("a").text.strip()
            match = pattern.match(a_text)
            side = match.group(1)
            company_name = match.group(4)
            target_price = match.group(5)
            recommender = match.group(7)
            date_of_recommendation = get_date(section.find("time").text.strip())
            if side != "Buy":
                continue
            symbol = get_symbol_of(company_name)
            if symbol == -1:
                continue
            else:
                symbol = symbol + ".NS" if symbol.isalpha() else symbol + ".BO"
            price_at_reco_date = get_close_price_on_date(symbol, date_of_recommendation)
            RECORDER.add_row(
                symbol,
                company_name,
                recommender.strip(),
                date_of_recommendation,
                TP=target_price,
                PriceAtRecoDate=price_at_reco_date,
            )
        except:
            print("Error in Main Function")
            continue

def main():
    reco_sections = scrape()
    parse(reco_sections)

main()

RECORDER.close_conn()
