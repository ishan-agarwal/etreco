from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)


@app.route("/price_data", methods=["GET"])
def get_price_data():
    # Get ticker,duration,interval from query parameters
    ticker = request.args.get("ticker")
    duration = request.args.get("duration")
    interval = request.args.get("interval")
    
    if not ticker or not duration:
        return (
            jsonify({"error": "Please provide both ticker and duration parameters"}),
            400,
        )

    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=duration,interval=interval,auto_adjust=False, back_adjust=False)

        price_data = []
        for index, row in data.iterrows():
            entry = {
                "created_at": index.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"],
            }
            price_data.append(entry)

        return jsonify(price_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/last_close_price", methods=["GET"])
def get_last_close_price():
    # Get ticker,duration,interval from query parameters
    ticker = request.args.get("ticker")    
    if not ticker:
        return (
            jsonify({"error": "Please provide both ticker and duration parameters"}),
            400,
        )
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="5d",interval="1d",auto_adjust=False, back_adjust=False)
        last_close=dict()
        last_close[ticker] = data.iloc[-1]["Close"]
        return jsonify(last_close)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/close_price_on_date", methods=["GET"])
def get_close_price_on_date():
    # Get ticker and date from query parameters
    ticker = request.args.get("ticker")
    date_str = request.args.get("date")
    
    if not ticker or not date_str:
        return (
            jsonify({"error": "Please provide both ticker and date parameters"}),
            400,
        )

    try:
        # Convert the date string to a datetime object
        target_date = datetime.strptime(date_str, "%Y-%m-%d")

        # Fetch the stock data for the period surrounding the target date
        start_date = (target_date - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = (target_date + timedelta(days=5)).strftime("%Y-%m-%d")

        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date, interval="1d", auto_adjust=False, back_adjust=False)

        # Find the closest previous trading day if the target date is not a trading day
        closest_date = None
        for index in reversed(data.index):
            if index.date() <= target_date.date():
                closest_date = index.date()
                break

        if closest_date is None:
            return jsonify({"error": "No trading data available for the specified date or nearby dates"}), 404

        close_price = data.loc[str(closest_date)]["Close"]
        result = {
            "ticker": ticker,
            "date": closest_date.strftime("%Y-%m-%d"),
            "close_price": close_price
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
