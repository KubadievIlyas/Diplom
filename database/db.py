# database/db.py
import pymysql

class Database:
    def __init__(self, host="localhost", user="root", password="", db="coffee_shop", port=3306):
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            port=port,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

    def fetch_all(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def fetch_one(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def execute(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params or ())

    def insert_and_get_id(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.lastrowid

    def close(self):
        self.connection.close()
