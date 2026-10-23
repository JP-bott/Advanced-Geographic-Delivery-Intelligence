"""SLA, lateness and Pareto helpers."""
import numpy as np
import pandas as pd
from src.delivery_metrics import safe_ratio

def sla_summary(df):
    done=df.loc[df.Delivered]
    late=done.loc[done.Late]
    return {'sla_rate':safe_ratio(done.On_Time.sum(),len(done)), 'late_count':len(late),
            'avg_delay':late.Delay_Days.mean(), 'median_days':done.Delivery_Days.median(),
            'p90_days':done.Delivery_Days.quantile(.9),'first_attempt':safe_ratio(done.First_Attempt.sum(),len(done))}

def pareto(df,group='Destination_Region'):
    late=df[df.Late].groupby(group).size().sort_values(ascending=False).rename('breaches').reset_index()
    late['cumulative_percent']=late.breaches.cumsum()/max(1,late.breaches.sum())*100
    return late
