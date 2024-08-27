import time
from datetime import datetime
import dateutil.parser
import schedule
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from thefuzz import process
import argparse

from setup_logger import setup_logger
from record import Record


def get_date(date_str):
    if date_str.lower().endswith("hours ago"):
        return datetime.today().date()
    else:
        return dateutil.parser.parse(date_str).date()


def get_ticker(company_name):
    closest_match = process.extractOne(company_name, NSE_DICT.values())
    if closest_match:
        matched_company = closest_match[0]
        matched_ticker = next(
            ticker for ticker, name in NSE_DICT.items() if name == matched_company
        )
        if re.split(r'[ .]+', matched_company)[0] == re.split(r'[ .]+', company_name)[0]:       # First word should match
            LOGGER.info(f"Closest match for {company_name} found : {matched_ticker}")
            return matched_ticker
        else:
            LOGGER.info(f"Not a match for {company_name} - {matched_company}")
            return None
    else:
        LOGGER.error(f"No closest match ticker found for company name : {company_name}")
        return None


def get_close_price_on_date(symbol, date):
    try:
        params = {"ticker": symbol, "date": str(date)}
        response = requests.get(CLOSE_PRICE_ON_DATE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        lcp = round(data.get("close_price", 0), 2)
        LOGGER.info(f"Last close price for {symbol} on date {date} is {lcp}")
        return lcp
    except (requests.exceptions.RequestException, ValueError, KeyError):
        LOGGER.error(f"Failed to get last close price for {symbol} on date {date}")
        return -1


def scrape(old):
    if not old:
        LOGGER.info("Scraping data from URL "+ SCRAPE_URL)
        response = requests.get(SCRAPE_URL)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            reco_sections = soup.find_all("div", class_="eachStory")
            LOGGER.info("Found " + str(len(reco_sections))+ " reco sections")
            return reco_sections
        else:
            LOGGER.error("Failed scraping URL")
    if old:
        # Load from local HTML file
        LOGGER.info("Scraping data from file ")
        with open("etc/old_data.html","r") as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, "html.parser")
        reco_sections = soup.find_all("div", class_="eachStory")
        return reco_sections


def parse(reco_sections):
    pattern = re.compile(r"(\w+) (.*), target price Rs (.*)(\.)*:(.*)")
    for section in reco_sections:
        a_text = section.find("a").text.strip()
        LOGGER.info(f"a_text in reco section is {a_text}")
        match = pattern.match(a_text)
        if not match:
            LOGGER.info("Could match regex pattern on a_text")
            continue
        side = match.group(1)
        company_name = match.group(2)
        target_price = match.group(3).replace(",", "")
        recommender = match.group(5).strip()
        date_of_recommendation = get_date(section.find("time").text.strip())
        LOGGER.info(f"Parsed a_text, side:{side}, company_name:{company_name}, target_prce:{target_price}, recommender:{recommender}, date_of_recommendation:{date_of_recommendation}")
        if side != "Buy":
            LOGGER.info("Side not \"Buy\", ignoring reco")
            continue
        symbol = get_ticker(company_name)
        if symbol:
            symbol = symbol + ".NS" if symbol.isalpha() else symbol + ".BO"
        else:
            continue
        price_at_reco_date = get_close_price_on_date(symbol, date_of_recommendation)
        LOGGER.info(f"Adding row, symbol:{symbol}, company_name:{company_name}, recommender:{recommender}, date_of_recommendation:{date_of_recommendation}, target_prce:{target_price}, price_at_reco_date:{price_at_reco_date}")
        RECORDER.add_row(
            symbol,
            company_name,
            recommender,
            date_of_recommendation,
            TP=target_price,
            PriceAtRecoDate=price_at_reco_date,
        )


def main():
    LOGGER.info("Start of RUN")
    reco_sections = scrape(args.old)
    parse(reco_sections)
    LOGGER.info("End of RUN")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", action="store_true", help="Scrape now")
    parser.add_argument("--old", action="store_true", help="Scrape old data")
    args = parser.parse_args()
    
    LOGGER = setup_logger()

    LOGGER.info("Sleeping for 10 seconds to let MySQL get ready")
    time.sleep(10)  # wait for mysql container to be up

    LOGGER.info("Initializing MySQL connection")
    RECORDER = Record()

    SCRAPE_URL = "https://economictimes.indiatimes.com/markets/stocks/recos"
    CLOSE_PRICE_ON_DATE_URL = "http://192.168.0.125:5000/close_price_on_date"

    LOGGER.info("Building ALL_DICT , dictionary of tickers to company names from NSE, BSE")
    NSE_DICT = pd.read_csv("etc/nse_list.csv").set_index("Symbol")["Company Name"].to_dict()
    
    if args.now:
        LOGGER.info("Running Now")
        main()
    else:
        LOGGER.info("Setting main function on a schedule to run daily on 06:10 UTC")
        schedule.every().day.at("06:10").do(main)
        while True:
            schedule.run_pending()
            time.sleep(1)        # sleep for 1 hour
