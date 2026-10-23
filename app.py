"""NexRoute | Logistics Intelligence — six-view synthetic logistics control tower."""
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.database import read_shipments,read_table,DB_PATH
from src.data_processing import prepare_shipments,filter_shipments
from src.delivery_metrics import overview,grouped_performance,insights,safe_ratio
from src.sla_analysis import sla_summary,pareto
from src.geospatial_analysis import destination_points,route_flows
from src.visualizations import themed,area_line,horizontal_bar,geo_base,COLORS,empty_chart

st.set_page_config(page_title='NexRoute | Logistics Intelligence',page_icon='◈',layout='wide',initial_sidebar_state='expanded')
CSS='''<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=Inter:wght@400;500;600;700;800&display=swap');
:root {color-scheme:dark} .stApp {background:#0B1420;color:#E8EEF5;font-family:Inter,Arial,sans-serif}
[data-testid="stSidebar"] {background:#101D2B;border-right:1px solid #29394B}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#C3CFDA}
.block-container {padding-top:1.4rem;padding-bottom:3rem;max-width:1600px}
h1,h2,h3{letter-spacing:-.03em} h1{font-size:2.0rem!important;font-weight:750!important}
h3{font-size:1.02rem!important;color:#E8EEF5}
[data-testid="stMetric"] {background:#172738;border:1px solid #29394B;border-radius:5px;padding:15px 17px;min-height:112px}
[data-testid="stMetricLabel"] {color:#95A7B8;font-size:.76rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em}
[data-testid="stMetricValue"] {color:#EDF4FC;font-family:'IBM Plex Mono',monospace;font-size:1.58rem;font-weight:600}
[data-testid="stVerticalBlockBorderWrapper"]>div {border-color:#29394B}
[data-testid="stDataFrame"]{border:1px solid #29394B;border-radius:5px}
div[data-testid="stPlotlyChart"] {border:1px solid #29394B;background:#111F2E;border-radius:5px;padding:5px 7px}
section[data-testid="stSidebar"] button {border-color:#29394B}
hr {border-color:#29394B}
.nr-eyebrow {color:#2DD4BF;letter-spacing:.16em;font-size:11px;font-weight:800;text-transform:uppercase;margin:8px 0}
.nr-subtitle {color:#95A7B8;margin:-8px 0 22px;line-height:1.6;font-size:13px}
.nr-brand {color:#EDF4FC;font-size:19px;font-weight:800;letter-spacing:-.02em;margin:14px 0 2px}
.nr-brand b {color:#2DD4BF}
.nr-rule {height:1px;background:#29394B;margin:18px 0}
.nr-note {color:#95A7B8;font-size:12px;padding:8px 0;line-height:1.6}
.nr-callout {border-left:3px solid #2DD4BF;background:#112631;padding:14px 16px;font-size:13px;color:#C7D7E4;margin:10px 0}
div.stButton>button[kind="primary"]{background:#4C9AFF;color:#0B1420;border-radius:4px}
</style>'''
st.markdown(CSS,unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load():
    if not DB_PATH.exists():
        st.error('Database missing. Run `python scripts/generate_data.py` followed by `python scripts/load_database.py`.')
        st.stop()
    return prepare_shipments(read_shipments()),read_table('hubs'),read_table('delivery_events')

def plot(fig,key=None):
    st.plotly_chart(fig,use_container_width=True,config={'displaylogo':False,'toImageButtonOptions':{'format':'png'}},key=key)

def section(title,subtitle):
    st.markdown('<div class="nr-eyebrow">NEXROUTE / OPERATIONS INTELLIGENCE</div>',unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="nr-subtitle">{subtitle}</div>',unsafe_allow_html=True)

def fmt(v,unit='',dec=1):
    return '—' if pd.isna(v) else f'{v:,.{dec}f}{unit}'

def cards(items):
    # cards: [(label,value), ...]
    for start in range(0,len(items),4):
        cols=st.columns(4,gap='small')
        for col,(label,value) in zip(cols,items[start:start+4]):
            col.metric(label,value)

def dashboard(df):
    section('Operations Overview','Delivery throughput, fulfillment outcomes and service reliability. All figures are simulated.')
    k=overview(df)
    cards([('Total shipments',f'{k["shipments"]:,}'),('Delivered',f'{k["delivered"]:,}'),
       ('Delivery success',fmt(k['success_rate'],'%')),('On-time delivery',fmt(k['on_time_rate'],'%')),
       ('Avg delivery days',fmt(k['avg_delivery_days'],' d')),('Avg shipping cost',f'₱{fmt(k["avg_cost"])}'),
       ('Failed delivery',fmt(k['failed_rate'],'%')),('First-attempt success',fmt(k['first_attempt_rate'],'%'))])
    gran=st.segmented_control('Shipment trend aggregation',['Daily','Weekly','Monthly'],default='Monthly')
    frequency={'Daily':'D','Weekly':'W','Monthly':'MS'}[gran]
    trend=df.set_index('Shipment_Date').resample(frequency).size().rename('Shipments').reset_index()
    trend['7-period average']=trend['Shipments'].rolling(7,min_periods=1).mean()
    a,b=st.columns([1.75,1],gap='medium')
    with a:plot(area_line(trend,'Shipment_Date','Shipments','Shipment volume · 2024–2025','7-period average'))
    with b:
        by=df.Delivery_Status.value_counts().reindex(['Delivered','Failed','Returned','In Transit','Cancelled'],fill_value=0).reset_index()
        by.columns=['Status','Count']
        fig=px.bar(by,x='Count',y='Status',color='Status',orientation='h',color_discrete_sequence=COLORS)
        plot(themed(fig))
    a,b=st.columns(2,gap='medium')
    with a:
        done=df[df.Delivered].copy()
        monthly=done.groupby('Month').agg(on_time=('On_Time','sum'),delivered=('Shipment_ID','size')).reset_index()
        monthly['On-time %']=np.where(monthly.delivered>0,monthly.on_time/monthly.delivered*100,0)
        plot(area_line(monthly,'Month','On-time %','On-time delivery · monthly'))
    with b:
        monthregion=done.pivot_table(index='Destination_Region',columns='Month',values='On_Time',aggfunc='mean')*100
        if not monthregion.empty:
            monthregion.columns=monthregion.columns.strftime('%b %y')
            fig=px.imshow(monthregion,aspect='auto',color_continuous_scale=['#7D2437','#E6AE58','#2DD4BF'],labels=dict(color='On-time %'))
            plot(themed(fig))
        else:plot(empty_chart())
    if df.Month.nunique()>=2:
        months=sorted(df.Month.dropna().unique())
        first_month,last_month=months[0],months[-1]
        baseline=df.loc[df.Month.eq(first_month)].On_Time.sum()
        current=df.loc[df.Month.eq(last_month)].On_Time.sum()
        groups=sorted(df.Service_Type.unique())
        contributions=[]
        for service in groups:
            start=df.loc[df.Month.eq(first_month)&df.Service_Type.eq(service)].On_Time.sum()
            end=df.loc[df.Month.eq(last_month)&df.Service_Type.eq(service)].On_Time.sum()
            contributions.append(int(end-start))
        wf=go.Figure(go.Waterfall(x=['First selected month']+groups+['Last selected month'],
              measure=['absolute']+['relative']*len(groups)+['total'],
              y=[int(baseline)]+contributions+[0],
              connector=dict(line=dict(color='#61768A')),
              increasing=dict(marker=dict(color=COLORS[1])),decreasing=dict(marker=dict(color=COLORS[3])),
              totals=dict(marker=dict(color=COLORS[0]))))
        plot(themed(wf,325))
        st.caption('Waterfall compares counts of on-time deliveries in the first and last selected shipment months; contributions by service type exactly reconcile their difference. These counts are not percentages.')
    st.markdown('#### Operational signals')
    for line in insights(df):st.markdown(f'<div class="nr-callout">{line}</div>',unsafe_allow_html=True)
    st.caption('KPI denominators: success = delivered / (delivered + failed + returned); on-time and first attempt = on-time or first-attempt delivered / delivered; failed = failed / resolved. Cancelled and in-transit parcels are excluded from resolved rates.')

def geography(df,hubs):
    section('Geographic Delivery Analysis','Shipment concentration, facility locations and aggregated corridors across the Philippines.')
    points=destination_points(df) if not df.empty else pd.DataFrame()
    if points.empty:st.info('No geographic data for these filters.');return
    a,b,c=st.columns(3)
    a.metric('Active destination cities',f'{len(points):,}')
    b.metric('Covered regions',f'{df.Destination_Region.nunique():,}')
    c.metric('Geodesic mean',f'{df.Distance_KM.mean():,.1f} km')
    mode=st.radio('Map layer',['Destination volume','On-time performance','Origin hub flows'],horizontal=True)
    fig=geo_base(mode,530)
    if mode!='Origin hub flows':
        size=np.sqrt(points.shipments.clip(lower=1))
        if mode=='Destination volume':
            color=points.shipments;scale='Blues';label='Shipments'
        else:color=points.on_time_rate;scale='Viridis';label='On-time %'
        fig.add_trace(go.Scattergeo(lon=points.Destination_Longitude,lat=points.Destination_Latitude,
          text=points.Destination_City+' · '+points.Destination_Province+'<br>Shipments: '+points.shipments.astype(str)+'<br>On-time: '+points.on_time_rate.round(1).astype(str)+'%',
          hoverinfo='text',mode='markers',name='Cities',marker=dict(size=(size/size.max()*25+6).tolist(),color=color,
          colorscale=scale,showscale=True,colorbar=dict(title=label),line=dict(color='#0B1420',width=.9),opacity=.85)))
    else:
        flows=route_flows(df).head(35)
        for r in flows.itertuples(index=False):
            fig.add_trace(go.Scattergeo(lon=[r.Origin_Longitude,r.Destination_Longitude],lat=[r.Origin_Latitude,r.Destination_Latitude],
              mode='lines',hovertext=f'{r.Hub_Name} → {r.Destination_City}: {r.shipments} parcels',hoverinfo='text',showlegend=False,
              line=dict(width=1.0+5*r.shipments/max(flows.shipments.max(),1),color='rgba(76,154,255,.53)')))
    active=df.groupby('Origin_Hub_ID').size()
    active_hubs=hubs[hubs.Hub_ID.isin(active.index)].copy()
    active_hubs['volume']=active_hubs.Hub_ID.map(active)
    fig.add_trace(go.Scattergeo(lon=active_hubs.Longitude,lat=active_hubs.Latitude,mode='markers',name='Hubs',
      text=active_hubs.Hub_Name+' · '+active_hubs.volume.astype(str)+' shipments',hoverinfo='text',
      marker=dict(size=9,symbol='diamond',color='#2DD4BF',line=dict(color='#0B1420',width=1))))
    plot(fig)
    st.caption('Dots use representative city-center coordinates, not recipient addresses. Lines indicate aggregated origin–destination connections, not actual road or air routes. Straight-line distance uses WGS84 and is not driving distance. No unsupported choropleth boundaries are fabricated.')
    a,b=st.columns(2)
    with a:
        by=grouped_performance(df,'Destination_Region').sort_values('shipments',ascending=False)
        plot(horizontal_bar(by,'Destination_Region','shipments',title='Shipment volume by region'))
    with b:
        plot(horizontal_bar(by,'Destination_Region','avg_cost',color=COLORS[1],title='Average simulated cost · PHP'))
    st.dataframe(by[['Destination_Region','shipments','success_rate','on_time_rate','avg_days','avg_cost']].round(2),hide_index=True,use_container_width=True)

def couriers(df):
    section('Courier Performance','Compare workload, delivery quality and last-mile operational efficiency.')
    g=grouped_performance(df,['Courier_ID','Courier_Name','Assigned_Region','Vehicle_Type'])
    if g.empty:st.info('No courier records for these filters.');return
    minimum=st.slider('Minimum delivered parcels for ranking',10,500,75,step=5)
    eligible=g[g.delivered>=minimum]
    metric=st.selectbox('Rank courier by',['on_time_rate','success_rate','first_attempt_rate','avg_days'])
    a,b=st.columns(2)
    with a:
        best=eligible.nlargest(14,metric) if metric!='avg_days' else eligible.nsmallest(14,metric)
        plot(horizontal_bar(best,'Courier_Name',metric,title=f'Courier ranking · {metric.replace("_"," ")}'))
    with b:
        fig=px.scatter(eligible,x='delivered',y='avg_days',color='on_time_rate',size='shipments',
            hover_name='Courier_Name',color_continuous_scale='Teal',labels={'delivered':'Delivered parcels','avg_days':'Mean transit days'})
        plot(themed(fig))
    selected=st.multiselect('Compare up to five couriers',g.Courier_ID.tolist(),default=g.Courier_ID.head(3).tolist(),max_selections=5,
         format_func=lambda cid:g.set_index('Courier_ID').loc[cid,'Courier_Name'])
    cmp=g[g.Courier_ID.isin(selected)]
    if not cmp.empty:
        metrics=['on_time_rate','success_rate','first_attempt_rate']
        long=cmp.melt(id_vars='Courier_Name',value_vars=metrics,var_name='KPI',value_name='Percent')
        fig=px.bar(long,x='Courier_Name',y='Percent',color='KPI',barmode='group',color_discrete_sequence=COLORS)
        plot(themed(fig))
    done=df.loc[df.Delivered]
    if not done.empty:
        fig=px.box(done,x='Vehicle_Type',y='Delivery_Days',color='Vehicle_Type',points=False,color_discrete_sequence=COLORS)
        plot(themed(fig))
    st.dataframe(g.sort_values('on_time_rate').round(2),hide_index=True,use_container_width=True)

def sla(df):
    section('SLA & Delay Analytics','Quantify late deliveries, service-level exposure and recurring exceptions.')
    k=sla_summary(df)
    cards([('SLA compliance',fmt(k['sla_rate'],'%')),('Late deliveries',f'{k["late_count"]:,}'),
           ('Mean days late',fmt(k['avg_delay'],' d')),('Median delivery days',fmt(k['median_days'],' d')),
           ('P90 delivery days',fmt(k['p90_days'],' d')),('First-attempt success',fmt(k['first_attempt'],'%'))])
    done=df.loc[df.Delivered]
    a,b=st.columns(2)
    with a:
        late=done[done.Late]
        if not late.empty:
            plot(themed(px.histogram(late,x='Delay_Days',nbins=12,title='Late arrival · delay days',color_discrete_sequence=[COLORS[3]])))
        else:plot(empty_chart())
    with b:
        if not done.empty:
            heat=done.pivot_table(index='Destination_Region',columns='Service_Type',values='On_Time',aggfunc='mean')*100
            plot(themed(px.imshow(heat,aspect='auto',color_continuous_scale=['#B33F4A','#E6AE58','#2DD4BF'],title='SLA compliance · region × service')))
        else:plot(empty_chart())
    a,b=st.columns(2)
    with a:
        if not done.empty:plot(themed(px.box(done,x='Service_Type',y='Delivery_Days',color='Service_Type',points=False,title='Delivery time by service',color_discrete_sequence=COLORS)))
    with b:
        failures=df[df.Delivery_Status.isin(['Failed','Returned'])].Failure_Reason.value_counts().reset_index()
        failures.columns=['Failure reason','Count']
        plot(horizontal_bar(failures,'Failure reason','Count',color=COLORS[3],title='Recorded failure reasons'))
    a,b=st.columns(2)
    with a:
        monthly=done.groupby('Month').agg(mean_delay=('Delay_Days','mean'),median_delay=('Delay_Days','median')).reset_index()
        plot(area_line(monthly,'Month','mean_delay','Delay trend · all delivered, including on-time'))
    with b:
        p=pareto(df)
        if not p.empty:
            fig=go.Figure([go.Bar(x=p.Destination_Region,y=p.breaches,name='Breach count',marker_color=COLORS[3]),
                go.Scatter(x=p.Destination_Region,y=p.cumulative_percent,name='Cumulative %',yaxis='y2',line=dict(color=COLORS[1]))])
            fig.update_layout(yaxis2=dict(overlaying='y',side='right',range=[0,105],title='Cumulative %'))
            plot(themed(fig))
        else:plot(empty_chart())
    st.caption('SLA = actual delivered date ≤ promised date. On-time denominator includes delivered parcels only. Delay days are positive integer calendar days past the promised date; unresolved or returned parcels are not classified as late delivered.')

def costs(df):
    section('Shipping Cost Analysis','Synthetic cost economics by month, network region, distance and vehicle mix.')
    delivered=df[df.Delivered]
    cards([('Total shipping cost',f'₱{df.Shipping_Cost_PHP.sum():,.0f}'),
          ('Cost / shipment',f'₱{fmt(df.Shipping_Cost_PHP.mean())}'),
          ('Cost / delivered',f'₱{fmt(delivered.Shipping_Cost_PHP.mean())}'),
          ('Cost / geodesic km',f'₱{fmt(df.Shipping_Cost_PHP.sum()/df.Distance_KM.sum() if df.Distance_KM.sum() else np.nan,dec=2)}')])
    a,b=st.columns(2)
    with a:
        trend=df.groupby('Month',as_index=False).Shipping_Cost_PHP.sum()
        plot(area_line(trend,'Month','Shipping_Cost_PHP','Aggregate shipping cost · PHP'))
    with b:
        by=grouped_performance(df,'Destination_Region')
        plot(horizontal_bar(by,'Destination_Region','avg_cost',title='Mean shipping cost · region'))
    a,b=st.columns(2)
    with a:
        sample=df.sample(min(5000,len(df)),random_state=42) if not df.empty else df
        if not sample.empty:
            fig=px.scatter(sample,x='Distance_KM',y='Shipping_Cost_PHP',color='Service_Type',
                opacity=.43,hover_data=['Package_Weight_KG'],color_discrete_sequence=COLORS)
            plot(themed(fig))
        else:plot(empty_chart())
    with b:
        if not df.empty:
            fig=px.box(df,x='Vehicle_Type',y='Shipping_Cost_PHP',color='Vehicle_Type',points=False,color_discrete_sequence=COLORS)
            plot(themed(fig))
        else:plot(empty_chart())
    g=grouped_performance(df,'Destination_Region')
    if not g.empty:
        fig=px.scatter(g,x='avg_cost',y='success_rate',size='shipments',hover_name='Destination_Region',color='on_time_rate',
            labels={'avg_cost':'Average simulated cost (PHP)','success_rate':'Resolved delivery success (%)'},color_continuous_scale='Viridis')
        plot(themed(fig))
    route=grouped_performance(df,'Route').nlargest(12,'avg_cost')
    plot(horizontal_bar(route,'Route','avg_cost',title='Highest-cost origin–destination region pairs'))
    st.caption('Amounts are synthetic model costs, not market rates. Cost depends on WGS84 distance, weight, service type, vehicle and modeled inter-island factors. Cost/km is an aggregate ratio of total cost to summed geodesic distance, not a driving-mileage benchmark. Associations do not prove causality.')

def explorer(df,events):
    section('Shipment Explorer','Search records, export the filtered set and inspect genuine simulated event history.')
    needle=st.text_input('Shipment ID contains',placeholder='NR000142').upper().strip()
    found=df[df.Shipment_ID.str.contains(needle,regex=False)] if needle else df
    view_cols=['Shipment_ID','Courier_Name','Hub_Name','Destination_City','Service_Type','Shipment_Date','Expected_Delivery_Date',
               'Actual_Delivery_Date','Delivery_Status','Delivery_Days','On_Time','Shipping_Cost_PHP']
    st.caption(f'{len(found):,} matching shipment records')
    st.dataframe(found[view_cols].round(2),hide_index=True,use_container_width=True,height=400)
    st.download_button('Export filtered shipments · CSV',data=found.drop(columns=['Month']).to_csv(index=False).encode('utf-8'),
          file_name='nexroute_shipments_export.csv',mime='text/csv')
    if not found.empty:
        selected=st.selectbox('Inspect shipment timeline',found.Shipment_ID.head(1000).tolist())
        detail=events[events.Shipment_ID.eq(selected)].sort_values('Event_DateTime')
        if not detail.empty:
            for evt in detail.itertuples(index=False):
                st.markdown(f'<div class="nr-callout"><b>{evt.Event_Type}</b> &nbsp; <code>{evt.Event_DateTime}</code><div class="nr-note">{evt.Event_Description}</div></div>',unsafe_allow_html=True)
    st.caption('Dates are expressed in local Philippine time without explicit timezone offsets in the synthetic dataset. Only recorded events are shown.')

frame,hubs,events=load()
with st.sidebar:
    st.markdown('<div class="nr-brand">◈ <b>NEX</b>ROUTE</div><div class="nr-note">LOGISTICS INTELLIGENCE<br>CONTROL TOWER / V1.0</div>',unsafe_allow_html=True)
    st.markdown('<div class="nr-rule"></div>',unsafe_allow_html=True)
    page=st.radio('WORKSPACES',['Operations Overview','Geographic Delivery Analysis','Courier Performance','SLA & Delay Analytics','Shipping Cost Analysis','Shipment Explorer'],label_visibility='visible')
    st.markdown('<div class="nr-rule"></div>',unsafe_allow_html=True)
    st.markdown('<div class="nr-eyebrow">GLOBAL FILTERS</div>',unsafe_allow_html=True)
    period=st.date_input('Shipment dates',(date(2024,1,1),date(2025,12,31)),min_value=date(2024,1,1),max_value=date(2025,12,31))
    regions=st.multiselect('Destination region',sorted(frame.Destination_Region.unique()))
    services=st.multiselect('Service type',sorted(frame.Service_Type.unique()))
    statuses=st.multiselect('Delivery status',sorted(frame.Delivery_Status.unique()))
    courier_ids=st.multiselect('Courier',sorted(frame.Courier_ID.unique()),format_func=lambda x:frame.set_index('Courier_ID').loc[x,'Courier_Name'])
    st.markdown('<div class="nr-rule"></div>',unsafe_allow_html=True)
    st.markdown('<div class="nr-note">DATA WINDOW: 2024–2025<br>REPORTING CUTOFF: 31 DEC 2025<br><br>Fictional company and synthetic transactions. No customer location tracking.</div>',unsafe_allow_html=True)

df=filter_shipments(frame,date_range=period if len(period)==2 else None,regions=regions,services=services,statuses=statuses,couriers=courier_ids)
st.caption(f'OPERATIONS / {page.upper()} &nbsp; | &nbsp; {len(df):,} selected shipments')
if page=='Operations Overview':dashboard(df)
elif page=='Geographic Delivery Analysis':geography(df,hubs)
elif page=='Courier Performance':couriers(df)
elif page=='SLA & Delay Analytics':sla(df)
elif page=='Shipping Cost Analysis':costs(df)
else:explorer(df,events)
