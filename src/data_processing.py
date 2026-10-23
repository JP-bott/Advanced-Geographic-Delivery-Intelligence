"""Parsing and feature engineering shared by dashboard and notebook."""
import pandas as pd
REPORTING_CUTOFF = pd.Timestamp('2025-12-31 23:59:59')

def prepare_shipments(frame: pd.DataFrame) -> pd.DataFrame:
    df=frame.copy()
    for c in ['Shipment_Date','Dispatch_Date','Expected_Delivery_Date','Actual_Delivery_Date']:
        df[c]=pd.to_datetime(df[c],errors='coerce')
    df['Delivered']=df.Delivery_Status.eq('Delivered')
    df['Resolved']=df.Delivery_Status.isin(['Delivered','Failed','Returned'])
    df['Eligible_Resolved']=df.Delivery_Status.isin(['Delivered','Failed','Returned'])
    df['Delivery_Days']=(df.Actual_Delivery_Date-df.Dispatch_Date).dt.total_seconds()/86400
    df['On_Time']=df.Delivered & (df.Actual_Delivery_Date.dt.normalize() <= df.Expected_Delivery_Date.dt.normalize())
    df['Late']=df.Delivered & ~df.On_Time
    df['Delay_Days']=((df.Actual_Delivery_Date.dt.normalize()-df.Expected_Delivery_Date.dt.normalize()).dt.days).clip(lower=0).where(df.Delivered)
    df['First_Attempt']=df.Delivered & df.Delivery_Attempts.eq(1)
    df['Month']=df.Shipment_Date.dt.to_period('M').dt.to_timestamp()
    df['Route']=df.Origin_Region+' → '+df.Destination_Region
    return df

def filter_shipments(df,date_range=None,regions=None,couriers=None,statuses=None,services=None):
    v=df
    if date_range and len(date_range)==2:
        start,end=[pd.Timestamp(x) for x in date_range]
        v=v.loc[v.Shipment_Date.dt.normalize().between(start,end)]
    for col,vals in [('Destination_Region',regions),('Courier_ID',couriers),('Delivery_Status',statuses),('Service_Type',services)]:
        if vals:
            v=v.loc[v[col].isin(vals)]
    return v.copy()
