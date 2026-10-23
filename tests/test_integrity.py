"""Data contract and KPI reconciliation tests."""
import sqlite3
import pandas as pd
import pytest
from src.database import DB_PATH, read_shipments,read_table
from src.data_processing import prepare_shipments,filter_shipments
from src.delivery_metrics import overview,grouped_performance
from src.geospatial_analysis import geodesic_km,destination_points
from src.sla_analysis import sla_summary

@pytest.fixture(scope='module')
def data():return prepare_shipments(read_shipments())

def test_volume_and_primary_keys(data):
    assert len(data)==26000
    assert data.Shipment_ID.is_unique and data.Order_ID.is_unique
    assert read_table('couriers').Courier_ID.is_unique

def test_foreign_keys():
    with sqlite3.connect(DB_PATH) as con:
        assert con.execute('PRAGMA foreign_key_check').fetchall()==[]

def test_geography(data):
    assert data.Destination_Latitude.between(4,22).all()
    assert data.Destination_Longitude.between(116,127).all()
    assert len(destination_points(data))==24
    assert geodesic_km(14.5995,120.9842,10.3157,123.8854)>500

def test_dates(data):
    assert (data.Dispatch_Date>=data.Shipment_Date).all()
    assert (data.Expected_Delivery_Date>=data.Dispatch_Date).all()
    delivered=data[data.Delivered]
    assert delivered.Actual_Delivery_Date.notna().all()
    assert (~data[data.Delivery_Status!='Delivered'].Actual_Delivery_Date.notna()).all()
    assert delivered.Delivery_Days.ge(0).all()

def test_sla_joins(data):
    with sqlite3.connect(DB_PATH) as con:
        q='''SELECT COUNT(*) FROM shipments s JOIN hubs h ON h.Hub_ID=s.Origin_Hub_ID
        JOIN sla_rules r ON r.SLA_ID=s.SLA_ID WHERE
        s.Service_Type<>r.Service_Type OR h.Region<>r.Origin_Region OR
        s.Destination_Region<>r.Destination_Region OR
        date(s.Dispatch_Date, printf('+%d days',r.SLA_Days))<>s.Expected_Delivery_Date'''
        assert con.execute(q).fetchone()[0]==0

def test_kpi_reconciliation(data):
    k=overview(data)
    assert k['delivered']==data.Delivered.sum()
    assert abs(k['success_rate']-data.Delivered.sum()/data.Eligible_Resolved.sum()*100)<1e-10
    assert abs(k['on_time_rate']-data.On_Time.sum()/data.Delivered.sum()*100)<1e-10
    assert k['failed_rate']>0
    assert abs(sla_summary(data)['sla_rate']-k['on_time_rate'])<1e-8

def test_regions_reconcile(data):
    region=grouped_performance(data,'Destination_Region')
    assert region.shipments.sum()==len(data)
    assert region.delivered.sum()==data.Delivered.sum()

def test_event_timeline():
    events=read_table('delivery_events')
    assert events.Event_ID.is_unique
    dts=pd.to_datetime(events.Event_DateTime)
    assert dts.max()<=pd.Timestamp('2025-12-31 23:59:59')
    for _,g in events.assign(ts=dts).groupby('Shipment_ID',sort=False):
        assert g.ts.is_monotonic_increasing
    assert events.Shipment_ID.nunique()==26000

def test_terminal_events(data):
    events=read_table('delivery_events')
    last=events.drop_duplicates('Shipment_ID',keep='last').set_index('Shipment_ID').Event_Type
    mapping={'Delivered':'Delivered','Failed':'Failed Delivery','Returned':'Returned to Sender','Cancelled':'Order Cancelled'}
    for status,event_type in mapping.items():
        ids=data.loc[data.Delivery_Status==status,'Shipment_ID']
        assert last.reindex(ids).eq(event_type).all()

def test_filtering(data):
    f=filter_shipments(data,regions=['NCR'],statuses=['Delivered'],services=['Standard'])
    assert not f.empty
    assert f.Destination_Region.eq('NCR').all() and f.Delivery_Status.eq('Delivered').all()
    assert f.Service_Type.eq('Standard').all()
