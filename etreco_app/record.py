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
        self.columns = [
            "Symbol",
            "CompanyName",
            "TP",
        ]
        self.conn = mysql.connector.connect(**self.db_config)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS records (
            Symbol VARCHAR(255),
            CompanyName VARCHAR(255),
            TP FLOAT,
            PRIMARY KEY (Symbol)
        )
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def add_row(self, Symbol, CompanyName, TP):
        insert_query = """
            INSERT INTO records (Symbol, CompanyName, TP)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            TP = VALUES(TP)
            """
        try:
            self.cursor.execute(insert_query, (Symbol, CompanyName, TP))
            self.conn.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def close_conn(self):
        self.cursor.close()
        self.conn.close()
