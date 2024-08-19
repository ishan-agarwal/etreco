# import pandas as pds
import os
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
        self.conn = mysql.connector.connect(**self.db_config)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS recos (
            Symbol VARCHAR(255),
            CompanyName VARCHAR(255),
            Recommender VARCHAR(255),
            DateOfRecommendation DATE,
            TP FLOAT,
            PriceAtRecoDate FLOAT,
            PRIMARY KEY (CompanyName, TP)
        )
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def add_row(self, Symbol, CompanyName, Recommender, Date, TP, PriceAtRecoDate):
        insert_query = """
            INSERT INTO recos (Symbol, CompanyName, Recommender, DateOfRecommendation, TP, PriceAtRecoDate)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
        try:
            self.cursor.execute(
                insert_query,
                (Symbol, CompanyName, Recommender, Date, TP, PriceAtRecoDate),
            )
            self.conn.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def close_conn(self):
        self.cursor.close()
        self.conn.close()
