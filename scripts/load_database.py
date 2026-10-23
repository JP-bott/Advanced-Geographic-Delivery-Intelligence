"""Load raw CSVs into a constrained, indexed SQLite database."""
from pathlib import Path
import sys
import sqlite3
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database'/'logistics_analytics.db'
def run():
    DB.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(DB) as con:
        con.execute('PRAGMA foreign_keys=ON')
        con.executescript((ROOT/'sql'/'01_create_tables.sql').read_text())
        for table in ['hubs','couriers','sla_rules','shipments','delivery_events']:
            frame=pd.read_csv(ROOT/'data'/'raw'/f'{table}.csv',keep_default_na=False)
            if table=='shipments':
                frame['Actual_Delivery_Date']=frame['Actual_Delivery_Date'].replace('',None)
            frame.to_sql(table,con,if_exists='append',index=False,chunksize=1500)
        con.executescript((ROOT/'sql'/'02_create_indexes.sql').read_text())
        fk=con.execute('PRAGMA foreign_key_check').fetchall()
        if fk:raise ValueError(f'Foreign key violations: {fk[:5]}')
        print(f'Database ready: {DB} ({con.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]:,} shipments)')
if __name__=='__main__':run()
