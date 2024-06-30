import time
import re
import json
import requests
import schedule
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from thefuzz import process

# from bsedata.bse import BSE

from record import Record

# b = BSE()
# b.updateScripCodes()

RECORDER = Record()
SCRAPE_URL = "https://economictimes.indiatimes.com/markets/stocks/recos"
NSE_DICT = pd.read_csv("etc/nse_list.csv").set_index("Symbol")["Company Name"].to_dict()
with open("etc/bse_list.json", "r") as file:
    BSE_DICT = json.load(file)
ALL_DICT = NSE_DICT | BSE_DICT
# SEARCH_CHOICES = ALL_DICT.values()
# FINAL_DATA = list()


def scrape():
    url = SCRAPE_URL
    pattern = re.compile(r"((Buy)|(Sell)) (.*), target price Rs (\d*)(\.)*:(.*)")
    response = requests.get(url)
    recommendations = {}  # Key=Stock Name, Value=Target Price
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        reco_sections = soup.find_all("div", class_="eachStory")
        for section in reco_sections:
            try:
                a_text = section.find("a").text.strip()
                match = pattern.match(a_text)
                print(a_text)
                if match.group(1) == "Buy":
                    # print(match.group(1), " ", match.group(4), "; TP : ", match.group(5))
                    recommendations[match.group(4)] = int(match.group(5))
            except AttributeError:
                print("AttributeError")
                continue
    else:
        print("Failed to retrieve the webpage")
    return recommendations


# def get_ltp(symbol):
#     print(symbol)
#     df = yf.Ticker(symbol + ".NS").history(period="1mo")
#     if df.shape[0] == 0:  # Not present in NSE
#         df = yf.Ticker(symbol + ".BO").history(period="1mo")  # Check BSE
#     return round(df["Close"].iloc[-1], 2)


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


def get_pct_change(recs):
    for company_name, tp in recs.items():
        symbol = get_symbol_of(company_name=company_name)
        if symbol == -1:
            continue
        print("getting ltp for ", company_name)
        RECORDER.add_row(
            symbol, company_name, "NSE" if symbol.isalpha() else "BSE", TP=tp
        )


def collect_recos():
    recs = scrape()
    get_pct_change(recs=recs)
    RECORDER.close_conn()


schedule.every().day.at("10:30").do(collect_recos)

while True:
    schedule.run_pending()
    time.sleep(1)
