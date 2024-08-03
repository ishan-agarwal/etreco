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


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
