"""Operational KPIs with consistent and explicit denominators."""
import pandas as pd

def safe_ratio(n,d):
    return float(n)/float(d)*100 if d else 0.0

def overview(df):
    delivered=df[df.Delivered]
    eligible=df[df.Eligible_Resolved]
    return dict(shipments=len(df),delivered=len(delivered),success_rate=safe_ratio(len(delivered),len(eligible)),
        on_time_rate=safe_ratio(delivered.On_Time.sum(),len(delivered)),
        avg_delivery_days=delivered.Delivery_Days.mean(),avg_cost=df.Shipping_Cost_PHP.mean(),
        failed_rate=safe_ratio(df.Delivery_Status.eq('Failed').sum(),len(eligible)),
        first_attempt_rate=safe_ratio(delivered.First_Attempt.sum(),len(delivered)))

def grouped_performance(df, group):
    if df.empty: return pd.DataFrame()
    f=df.groupby(group,dropna=False).agg(shipments=('Shipment_ID','size'),delivered=('Delivered','sum'),
      resolved=('Eligible_Resolved','sum'),on_time=('On_Time','sum'),first_attempt=('First_Attempt','sum'),
      avg_days=('Delivery_Days','mean'),avg_cost=('Shipping_Cost_PHP','mean'),total_cost=('Shipping_Cost_PHP','sum'),
      failed=('Delivery_Status',lambda x:(x=='Failed').sum()), late=('Late','sum')).reset_index()
    f['success_rate']=f.apply(lambda r:safe_ratio(r.delivered,r.resolved),axis=1)
    f['on_time_rate']=f.apply(lambda r:safe_ratio(r.on_time,r.delivered),axis=1)
    f['first_attempt_rate']=f.apply(lambda r:safe_ratio(r.first_attempt,r.delivered),axis=1)
    f['failed_rate']=f.apply(lambda r:safe_ratio(r.failed,r.resolved),axis=1)
    return f

def insights(df):
    if df.empty: return ['No shipments match the selected filters.']
    region=grouped_performance(df,'Destination_Region')
    largest=region.loc[region.shipments.idxmax()]
    p=region[region.delivered>=30]
    lines=[f"{largest.Destination_Region} handled {int(largest.shipments):,} shipments, the largest regional volume in this selection."]
    if not p.empty:
        worst=p.loc[p.on_time_rate.idxmin()]
        lines.append(f"{worst.Destination_Region} recorded {worst.on_time_rate:.1f}% on-time delivery across {int(worst.delivered):,} delivered shipments.")
    failures=df.loc[df.Delivery_Status.eq('Failed'),'Failure_Reason'].dropna()
    if not failures.empty:
        top=failures.value_counts()
        lines.append(f"{top.index[0]} was the most frequent recorded failure reason ({top.iloc[0]:,} shipments).")
    return lines
