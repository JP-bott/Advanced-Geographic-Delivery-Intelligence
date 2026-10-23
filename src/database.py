"""Database access. Raw CSVs are authoritative; SQLite is reproducible."""
from pathlib import Path
import sqlite3
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'database' / 'logistics_analytics.db'

def connect(path=DB_PATH):
    connection = sqlite3.connect(path)
    connection.execute('PRAGMA foreign_keys=ON')
    return connection

def read_shipments(path=DB_PATH):
    with connect(path) as con:
        return pd.read_sql_query('''SELECT s.*,c.Courier_Name,c.Courier_Type,c.Vehicle_Type,
            c.Assigned_Region,h.Hub_Name,h.Region AS Origin_Region,h.Latitude AS Origin_Latitude,
            h.Longitude AS Origin_Longitude FROM shipments s
            JOIN couriers c ON s.Courier_ID=c.Courier_ID
            JOIN hubs h ON s.Origin_Hub_ID=h.Hub_ID''', con)

def read_table(table, path=DB_PATH):
    allowed={'shipments','couriers','hubs','delivery_events','sla_rules'}
    if table not in allowed:
        raise ValueError('Unknown table')
    with connect(path) as con:
        return pd.read_sql_query(f'SELECT * FROM {table}',con)
