import pandas as pd
import os
from datetime import datetime

class Record:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.columns = [
            "DateInserted",
            "Symbol",
            "CompanyName",
            "StockExchange",
            "TP",
            "LTP",
        ]

        if os.path.exists(self.csv_file):
            self.df = pd.read_csv(self.csv_file)
        else:
            self.df = pd.DataFrame(columns=self.columns)

        # Ensure the combination of DateInserted and Symbol is unique
        self.df.set_index(["DateInserted", "Symbol"], inplace=True, drop=False)

    def add_row(self, Symbol, CompanyName, StockExchange, TP, LTP):
        DateInserted = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        new_row = pd.DataFrame(
            {
                "DateInserted": [DateInserted],
                "Symbol": [Symbol],
                "CompanyName": [CompanyName],
                "StockExchange": [StockExchange],
                "TP": [TP],
                "LTP": [LTP],
            }
        )
        new_row.set_index(["DateInserted", "Symbol"], inplace=True, drop=False)

        if (DateInserted, Symbol) not in self.df.index:
            self.df = pd.concat([self.df, new_row])
        else:
            print(
                "Row with this DateInserted and Symbol already exists. Update the row if necessary."
            )

    def save_to_csv(self):
        self.df.to_csv(self.csv_file, index=False)
