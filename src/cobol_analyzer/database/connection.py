import psycopg2
from psycopg2 import sql

def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname="cobol_analysis_db",
            user="cobana_admin",
            password="Kanami1001!",
            host="172.16.0.13",
            port="5432"
        )
        print("Connected to the database")
        return conn
    except Exception as e:
        print(f"Error: {e}")

