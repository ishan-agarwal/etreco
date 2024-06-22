import os
import re
import json
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from fuzzywuzzy import process
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bsedata.bse import BSE

b = BSE()
b.updateScripCodes()

NSE_DICT = pd.read_csv("nse_list.csv").set_index('Symbol')['Company Name'].to_dict()
with open("bse_list.json", 'r') as file:
    BSE_DICT = json.load(file)
ALL_DICT = NSE_DICT | BSE_DICT

SCRAPE_URL = "https://economictimes.indiatimes.com/markets/stocks/recos"

SEARCH_CHOICES = ALL_DICT.values()

SENDER_EMAIL = os.getenv("ETRECO_SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("ETRECO_SENDER_PWD")
RECEIVER_EMAIL = os.getenv("ETRECO_RECEIVER_EMAIL")

SMTP_URL = 'smtp.gmail.com'
SMTP_PORT = 587

FINAL_DATA = list()


def scrape():
    url = SCRAPE_URL
    pattern = re.compile(r"((Buy)|(Sell)) (.*), target price Rs (.*):(.*)")
    response = requests.get(url)
    recommendations = {} # Key=Stock Name, Value=Target Price
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        reco_sections = soup.find_all("div", class_="eachStory")
        for section in reco_sections:
            try:
                a_text = section.find("a").text.strip()
                match = pattern.match(a_text)
                if match.group(1) == "Buy":
                    # print(match.group(1), " ", match.group(4), "; TP : ", match.group(5))
                    recommendations[match.group(4)] = int(match.group(5))
            except AttributeError:
                continue
    else:
        print("Failed to retrieve the webpage")
    return recommendations

def get_ltp(symbol):
    df = yf.Ticker(symbol+".NS").history(period="1mo")
    if df.shape[0] == 0: # Not present in NSE
        df = yf.Ticker(symbol+".BO").history(period="1mo") # Check BSE
    return df['Close'].iloc[-1]

def get_symbol_of(company_name):
    match = process.extract(company_name, SEARCH_CHOICES, limit=1)[0]
    for symbol, name in ALL_DICT.items():
        if name == match[0]:
            return symbol
    
def get_pct_change(recs):
    pct_changes = {} # Key=Stock Symbol, Value=Possible Pct Change
    for company_name, tp in recs.items():
        symbol = get_symbol_of(company_name=company_name)
        ltp = get_ltp(symbol=symbol)
        pct_change = ((tp - ltp) / ltp) * 100
        pct_changes[company_name] = pct_change
        FINAL_DATA.append(tuple(["BUY", company_name, symbol, tp, pct_change]))
        print("Buy ", company_name, "\t\tLTP:",ltp,"\t\tTP:",tp, "\t\tupside:", pct_change)
    return pct_changes

def send_email():
    columns = ["Action", "Company Name", "Symbol", "Target Price", "Possible Pct Change"]
    df = pd.DataFrame(FINAL_DATA, columns=columns)

    # Convert DataFrame to HTML
    html_table = df.to_html(index=False)

    # Email setup

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "ET Stock Recommendations"

    # Attach the HTML table to the email body
    body = f"""
    <html>
    <body>
        <p>Dear recipient,</p>
        <p>Please find below the latest stock recommendations:</p>
        {html_table}
        <p>Best regards,<br>Your Name</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    # Sending the email
    try:
        server = smtplib.SMTP(SMTP_URL, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")


def main():
    recs = scrape()
    print(get_pct_change(recs=recs))
    # send_email()

main()


# Buy Godrej Consumer Products, target price Rs 1650:  ICICI Securities
# Buy Bajaj Consumer Care, target price Rs 300:  ICICI Securities
# Buy PDS, target price Rs 780:  JM Financial
# Buy SBI Cards and Payment Services, target price Rs 855:  Anand Rathi
# Buy Andhra Sugars, target price Rs 140:  Axis Securities
# Buy Hindustan Petroleum Corporation, target price Rs 600:  Motilal Oswal
# Buy Indian Oil Corporation, target price Rs 195:  Motilal Oswal
# Buy GMR Airports Infrastructure, target price Rs 112:  Anand Rathi
# Buy Varun Beverages, target price Rs 1900:  Anand Rathi
# Buy Hindustan Zinc, target price Rs 890:  Anand Rathi
# Buy Trent, target price Rs 5500:  Motilal Oswal
# Buy Mankind Pharma, target price Rs 2650:  Motilal Oswal
# Sell GAIL (India), target price Rs 170:  Prabhudas Lilladher
# Buy Mold-Tek Packaging, target price Rs 957:  Geojit
# Buy India Shelter Finance Corporation, target price Rs 800:  ICICI Securities
# Buy Tata Motors, target price Rs 1200:  JM Financial