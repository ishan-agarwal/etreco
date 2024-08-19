import time
from datetime import datetime
import dateutil.parser
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

def get_date(date_str):
    if date_str.lower().endswith("hours ago"):
        return datetime.today().date()
    else:
        return dateutil.parser.parse(date_str).date()


def get_ticker(company_name):
    closest_match = process.extractOne(company_name, ALL_DICT.values())
    if closest_match:
        # Find the corresponding ticker by matching the closest company name
        matched_company = closest_match[0]
        matched_ticker = next(
            ticker for ticker, name in ALL_DICT.items() if name == matched_company
        )
        return matched_ticker
    else:
        return None


def get_close_price_on_date(symbol, date):
    try:
        params = {"ticker": symbol, "date": str(date)}
        response = requests.get(CLOSE_PRICE_ON_DATE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return round(data.get("close_price", 0), 2)
    except (requests.exceptions.RequestException, ValueError, KeyError):
        return 0


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
    pattern = re.compile(r"(\w+) (.*), target price Rs (.*)(\.)*:(.*)")
    for section in reco_sections:
        a_text = section.find("a").text.strip()
        match = pattern.match(a_text)
        if not match:
            continue
        side = match.group(1)
        company_name = match.group(2)
        target_price = match.group(3).replace(",", "")
        recommender = match.group(5)
        date_of_recommendation = get_date(section.find("time").text.strip())
        if side != "Buy":
            continue
        symbol = get_ticker(company_name)
        if symbol:
            symbol = symbol + ".NS" if symbol.isalpha() else symbol + ".BO"
        else:
            continue
        price_at_reco_date = get_close_price_on_date(symbol, date_of_recommendation)
        RECORDER.add_row(
            symbol,
            company_name,
            recommender.strip(),
            date_of_recommendation,
            TP=target_price,
            PriceAtRecoDate=price_at_reco_date,
        )


def main():
    reco_sections = scrape()
    parse(reco_sections)
    RECORDER.close_conn()


if __name__ == "__main__":
    main()
