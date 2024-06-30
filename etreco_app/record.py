# import pandas as pds
import os
from datetime import datetime
import mysql.connector


class Record:
    def __init__(self):
        self.db_config = {
            "user": os.environ.get("DB_USER"),
            "password": os.environ.get("DB_PASSWORD"),
            "host": os.environ.get("DB_HOST"),
            "port": os.environ.get("DB_PORT"),
            "database": os.environ.get("DB_NAME"),
        }
        self.columns = [
            "DateInserted",
            "Symbol",
            "CompanyName",
            "StockExchange",
            "TP",
        ]
        self.conn = mysql.connector.connect(**self.db_config)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS records (
            DateInserted DATETIME,
            Symbol VARCHAR(255),
            CompanyName VARCHAR(255),
            StockExchange VARCHAR(255),
            TP FLOAT,
            PRIMARY KEY (DateInserted, Symbol)
        )
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def add_row(self, Symbol, CompanyName, StockExchange, TP):
        DateInserted = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        insert_query = """
        INSERT INTO records (DateInserted, Symbol, CompanyName, StockExchange, TP)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            self.cursor.execute(
                insert_query, (DateInserted, Symbol, CompanyName, StockExchange, TP)
            )
            self.conn.commit()
        except mysql.connector.errors.IntegrityError:
            print(
                "Row with this DateInserted and Symbol already exists. Update the row if necessary."
            )

    def close_conn(self):
        self.cursor.close()
        self.conn.close()
