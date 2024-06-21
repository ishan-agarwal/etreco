import os
import requests
import re
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from fuzzywuzzy import process
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SCRAPE_URL = "https://economictimes.indiatimes.com/markets/stocks/recos"
NSE_DF = pd.read_csv("nse_list.csv")
SEARCH_CHOICES = NSE_DF['Company Name']
SENDER_EMAIL = os.getenv("ETRECO_SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("ETRECO_SENDER_PWD")
RECEIVER_EMAIL = os.getenv("ETRECO_RECEIVER_EMAIL")
SMTP_URL = 'smtp.gmail.com'
SMTP_PORT = 587

FINAL_DATA = list()

# Example Data
# FINAL_DATA = [
#     ('BUY', 'Godrej Consumer Products', 'GODREJCP', 1650, 18.45364570434647),
#     ('BUY', 'Bajaj Consumer Care', 'BAJAJCON', 300, 13.860629835622287),
#     ('BUY', 'PDS', 'PDSL', 780, 48.968685326453006),
#     ('BUY', 'SBI Cards and Payment Services', 'SBICARD', 855, 17.388622044255037),
#     ('BUY', 'Andhra Sugars', 'ANDHRSUGAR', 140, 11.758604415791599),
#     ('BUY', 'Hindustan Petroleum Corporation', 'HINDPETRO', 600, 11.877682949271625),
#     ('BUY', 'Indian Oil Corporation', 'IOC', 195, 14.463488671853902),
#     ('BUY', 'GMR Airports Infrastructure', 'GMRINFRA', 112, 19.25042821927231),
#     ('BUY', 'Varun Beverages', 'VBL', 1900, 15.90666463321641),
#     ('BUY', 'Hindustan Zinc', 'HINDZINC', 890, 34.461394043286184),
#     ('BUY', 'Trent', 'TRENT', 5500, 4.85078218273935),
#     ('BUY', 'Mankind Pharma', 'MANKIND', 2650, 18.271886302781),
#     ('BUY', 'Mold-Tek Packaging', 'MOLDTKPAC', 957, 18.97806042734855),
#     ('BUY', 'India Shelter Finance Corporation', 'INDIASHLTR', 800, 14.351061737812989),
#     ('BUY', 'Tata Motors', 'TATAMOTORS', 1200, 20.797258959984063)
# ]


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
                    print(match.group(1), " ", match.group(4), "; TP : ", match.group(5))
                    recommendations[match.group(4)] = int(match.group(5))
            except AttributeError:
                continue
    else:
        print("Failed to retrieve the webpage")
    return recommendations

def get_ltp(symbol):
    return yf.Ticker(symbol+".NS").history(period="1d")['Close'].iloc[-1]

def get_symbol_of(company_name):
    matches = process.extract(company_name, SEARCH_CHOICES, limit=1)
    for match in matches:
        row_index = NSE_DF[NSE_DF['Company Name'] == match[0]].index[0]
        return NSE_DF.iloc[row_index]["Symbol"]
    
def get_pct_change(recs):
    pct_changes = {} # Key=Stock Symbol, Value=Possible Pct Change
    for company_name, tp in recs.items():
        symbol = get_symbol_of(company_name=company_name)
        ltp = get_ltp(symbol=symbol)
        pct_change = ((tp - ltp) / ltp) * 100
        pct_changes[symbol] = pct_change
        FINAL_DATA.append(tuple(["BUY", company_name, symbol, tp, pct_change]))
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