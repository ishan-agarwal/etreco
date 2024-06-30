from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)


@app.route("/price_data", methods=["GET"])
def get_price_data():
    # Get ticker and duration from query parameters
    ticker = request.args.get("ticker")
    duration = request.args.get("duration")

    if not ticker or not duration:
        return (
            jsonify({"error": "Please provide both ticker and duration parameters"}),
            400,
        )

    try:
        # Fetch data using yfinance
        stock = yf.Ticker(ticker)
        data = stock.history(period=duration)

        # Convert data to the desired JSON structure
        price_data = []
        for index, row in data.iterrows():
            entry = {
                "created_at": index.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"],
                # Add more fields if necessary
            }
            price_data.append(entry)

        return jsonify(price_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0")
