"""Reproducible synthetic Philippine logistics data. All operations are fictional.

Calendar-day SLAs begin at dispatch; distances are WGS84 straight-line geodesics,
not road routes. The reporting cutoff is 2025-12-31 23:59:59.
"""
from __future__ import annotations
import argparse
from datetime import date,datetime,timedelta
from pathlib import Path
import csv
import numpy as np
from pyproj import Geod

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data'/'raw'
SEED=20261107
CUTOFF=date(2025,12,31)
GEOD=Geod(ellps='WGS84')
# Region, province, city, representative city-center latitude/longitude, relative volume.
CITIES=[
 ('NCR','Metro Manila','Quezon City',14.6760,121.0437,18),
 ('NCR','Metro Manila','Manila',14.5995,120.9842,11),
 ('NCR','Metro Manila','Pasig',14.5764,121.0851,10),
 ('NCR','Metro Manila','Taguig',14.5176,121.0509,10),
 ('NCR','Metro Manila','Makati',14.5547,121.0244,7),
 ('NCR','Metro Manila','Caloocan',14.6507,120.9668,6),
 ('Central Luzon','Bulacan','Malolos',14.8433,120.8114,6),
 ('Central Luzon','Bulacan','Meycauayan',14.7360,120.9600,5),
 ('Central Luzon','Pampanga','San Fernando',15.0285,120.6898,5),
 ('Central Luzon','Pampanga','Angeles',15.1450,120.5887,4),
 ('CALABARZON','Cavite','Bacoor',14.4624,120.9645,6),
 ('CALABARZON','Cavite','Dasmariñas',14.3294,120.9367,5),
 ('CALABARZON','Laguna','Santa Rosa',14.3122,121.1114,6),
 ('CALABARZON','Laguna','Calamba',14.2117,121.1653,5),
 ('CALABARZON','Rizal','Antipolo',14.6255,121.1245,6),
 ('CALABARZON','Rizal','Cainta',14.5786,121.1222,4),
 ('CALABARZON','Batangas','Batangas City',13.7565,121.0583,4),
 ('CALABARZON','Batangas','Lipa',13.9411,121.1622,4),
 ('Central Visayas','Cebu','Cebu City',10.3157,123.8854,7),
 ('Central Visayas','Cebu','Mandaue',10.3236,123.9225,4),
 ('Central Visayas','Cebu','Lapu-Lapu City',10.3103,123.9494,3),
 ('Western Visayas','Iloilo','Iloilo City',10.7202,122.5621,5),
 ('Western Visayas','Iloilo','Pavia',10.7758,122.5453,2),
 ('Davao Region','Davao del Sur','Davao City',7.0731,125.6128,7),
]
HUBS=[
 ('H01','Quezon City Hub','NCR','Metro Manila','Quezon City',14.6760,121.0437,'Primary Hub'),
 ('H02','Pasig Distribution Center','NCR','Metro Manila','Pasig',14.5764,121.0851,'Sorting Hub'),
 ('H03','Manila Central Hub','NCR','Metro Manila','Manila',14.5995,120.9842,'Primary Hub'),
 ('H04','Bulacan Sorting Facility','Central Luzon','Bulacan','Malolos',14.8433,120.8114,'Sorting Hub'),
 ('H05','Pampanga Regional Hub','Central Luzon','Pampanga','San Fernando',15.0285,120.6898,'Regional Hub'),
 ('H06','Cavite Delivery Hub','CALABARZON','Cavite','Dasmariñas',14.3294,120.9367,'Delivery Hub'),
 ('H07','Laguna Delivery Hub','CALABARZON','Laguna','Calamba',14.2117,121.1653,'Delivery Hub'),
 ('H08','Rizal Delivery Hub','CALABARZON','Rizal','Antipolo',14.6255,121.1245,'Delivery Hub'),
 ('H09','Batangas Regional Hub','CALABARZON','Batangas','Batangas City',13.7565,121.0583,'Regional Hub'),
 ('H10','Cebu Distribution Center','Central Visayas','Cebu','Cebu City',10.3157,123.8854,'Regional Hub'),
 ('H11','Iloilo Regional Hub','Western Visayas','Iloilo','Iloilo City',10.7202,122.5621,'Regional Hub'),
 ('H12','Davao Regional Hub','Davao Region','Davao del Sur','Davao City',7.0731,125.6128,'Regional Hub'),
]
SERVICES=['Same Day','Express','Standard','Economy']
SERVICE_FACTOR={'Same Day':1.85,'Express':1.55,'Standard':1.0,'Economy':.78}
SERVICE_SPEED={'Same Day':0,'Express':1,'Standard':2,'Economy':4}
VEHICLE_FACTOR={'Motorcycle':.88,'Van':1.,'Light Truck':1.19,'Delivery Truck':1.37}
FAILURES=['Recipient unavailable','Incorrect address','Delivery refused','Weather disruption','Damaged parcel','Access restriction']

def km(a,b,c,d):
    return round(abs(GEOD.inv(b,a,d,c)[2])/1000,2)

def sla_days(service,origin,dest):
    if service=='Same Day': return 0
    base=SERVICE_SPEED[service]
    if origin==dest: return base
    if {origin,dest}.issubset({'NCR','Central Luzon','CALABARZON'}): return base+1
    return base+3

def write_csv(name,cols,rows):
    RAW.mkdir(parents=True,exist_ok=True)
    with (RAW/name).open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(cols);writer.writerows(rows)

def run(n=26000):
    rng=np.random.default_rng(SEED)
    regions=sorted({h[2] for h in HUBS})
    hub_region={h[0]:h[2] for h in HUBS}
    hubs_by_region={r:[h for h in HUBS if h[2]==r] for r in regions}
    courier_rows=[]
    first=['Alex','Jamie','Morgan','Taylor','Casey','Jordan','Riley','Avery','Sam','Drew','Kai','Robin']
    last=['Santos','Reyes','Cruz','Garcia','Mendoza','Ramos','Bautista','Flores','Navarro','Villanueva']
    all_couriers={r:[] for r in regions}
    for i in range(60):
        region=regions[i%len(regions)]
        vehicle=rng.choice(['Motorcycle','Van','Light Truck','Delivery Truck'],p=[.55,.31,.11,.03])
        cid=f'C{i+1:03}'
        courier_rows.append((cid,f'{first[i%len(first)]} {last[(i//len(first))%len(last)]} {i+1:02}',
                            'In-House' if i%4 else 'Partner',region,'Active',vehicle,'2023-01-01'))
        all_couriers[region].append((cid,vehicle))
    courier_by_id={c[0]:c for c in courier_rows}
    write_csv('couriers.csv',['Courier_ID','Courier_Name','Courier_Type','Assigned_Region','Employment_Status','Vehicle_Type','Start_Date'],courier_rows)
    write_csv('hubs.csv',['Hub_ID','Hub_Name','Region','Province','City','Latitude','Longitude','Hub_Type'],HUBS)
    rules=[];lookup={}
    for origin in regions:
        for dest in regions:
            for service in SERVICES:
                if service=='Same Day' and origin!=dest: continue
                sid=f'SLA{len(rules)+1:04}'
                days=sla_days(service,origin,dest)
                rules.append((sid,service,origin,dest,days))
                lookup[(service,origin,dest)]=(sid,days)
    write_csv('sla_rules.csv',['SLA_ID','Service_Type','Origin_Region','Destination_Region','SLA_Days'],rules)
    dates=np.arange(np.datetime64('2024-01-01'),np.datetime64('2026-01-01'))
    # Add seasonal promotional peaks (11.11, 12.12, holiday shipping); weekend slightly lower.
    weights=[]
    for ds in dates:
        d=date.fromisoformat(str(ds))
        mult=1.0 if d.weekday()<5 else .72
        if d.month in (11,12):mult*=1.28
        if d.month in (6,7):mult*=1.08
        if (d.month,d.day) in [(11,11),(12,12),(9,9)]:mult*=2.4
        weights.append(mult)
    weights=np.asarray(weights);weights/=weights.sum()
    weighted_cities=np.asarray([x[5] for x in CITIES],dtype=float)
    weighted_cities/=weighted_cities.sum()
    shipments=[];events=[]
    event_i=0
    def add_event(ship,when,event,hub,detail):
        nonlocal event_i
        event_i+=1
        events.append((f'EV{event_i:07}',ship,when.isoformat(timespec='seconds'),event,hub or '',detail))
    generated_dates=rng.choice(dates,size=n,p=weights)
    for i in range(n):
        shipment_id=f'NR{i+1:06}'
        city=CITIES[int(rng.choice(len(CITIES),p=weighted_cities))]
        dest_reg,province,city_name,lat,lon,_=city
        # Most flows begin in-region. Remote destinations commonly connect through Metro Manila.
        origin_reg=dest_reg if rng.random()<.76 else ('NCR' if rng.random()<.72 else regions[int(rng.integers(len(regions)))])
        hub=hubs_by_region[origin_reg][int(rng.integers(len(hubs_by_region[origin_reg])))]
        distance=km(hub[5],hub[6],lat,lon)
        service=str(rng.choice(SERVICES if origin_reg==dest_reg else SERVICES[1:],p=[.06,.20,.52,.22] if origin_reg==dest_reg else [.24,.54,.22]))
        rule_id,sla=lookup[(service,origin_reg,dest_reg)]
        # Destination-aligned courier assignment captures last-mile operations.
        cid,vehicle=all_couriers[dest_reg][int(rng.integers(len(all_couriers[dest_reg])))]
        dt=date.fromisoformat(str(generated_dates[i]))
        dispatch= min(dt+timedelta(days=int(rng.choice([0,1,2],p=[.64,.34,.02]))),CUTOFF)
        expected=dispatch+timedelta(days=sla)
        weight=round(float(np.clip(rng.lognormal(mean=.1,sigma=.83),.08,24)),2)
        interisland=origin_reg in {'Central Visayas','Western Visayas','Davao Region'} or dest_reg in {'Central Visayas','Western Visayas','Davao Region'}
        cost=(49+distance*(.85 if interisland else .57)+weight*18)*SERVICE_FACTOR[service]*VEHICLE_FACTOR[vehicle]
        cost=round(max(35,cost*float(rng.uniform(.92,1.08))),2)
        fee=round(cost*float(rng.uniform(1.16,1.32)),2)
        # Synthetic route-level operational friction and peak-season congestion.
        peak=(dt.month in (11,12))
        remote=dest_reg in ('Central Visayas','Western Visayas','Davao Region')
        base_failure=.045+(.017 if remote else 0)+(.012 if peak else 0)
        courier_risk=((int(cid[1:])%10)-4.5)*.004
        failure_prob=max(.018,base_failure+courier_risk)
        choice=float(rng.random())
        status='Delivered';actual=None;failure='';attempts=1
        if choice<.011: status='Cancelled';attempts=0
        elif choice<.011+failure_prob*.78:status='Failed';attempts=int(rng.choice([1,2,3],p=[.55,.38,.07]))
        elif choice<.011+failure_prob:status='Returned';attempts=int(rng.choice([1,2,3],p=[.4,.4,.2]))
        late_chance=.085+(.07 if remote else 0)+(.055 if peak else 0)+max(0,courier_risk)*3
        if status=='Delivered' or status in ('Failed','Returned'):
            delay=int(rng.choice([0,1,2,3,4,5],p=[.86,.065,.035,.02,.012,.008])) if rng.random()<late_chance else 0
            # Delivery variation around SLA; economy is generally slower than express.
            early=int(rng.integers(0,max(1,min(3,sla+1)))) if sla else 0
            duration=max(0,sla-early+delay)
            outcome=dispatch+timedelta(days=duration)
            if outcome>CUTOFF:
                status='In Transit';attempts=0
            elif status=='Delivered':
                actual=outcome
                attempts=int(rng.choice([1,2,3],p=[.88,.105,.015]))
            else:
                failure=str(rng.choice(FAILURES,p=[.33,.23,.16,.13,.08,.07]))
        if status=='Cancelled':failure='';actual=None
        shipment_row=(shipment_id,f'ORD{i+1:06}',f'CUS{int(rng.integers(1,5300)):05}',cid,hub[0],dest_reg,province,city_name,
          lat,lon,dt.isoformat(),dispatch.isoformat(),expected.isoformat(),actual.isoformat() if actual else '',
          status,attempts,failure,weight,cost,fee,service,distance,rule_id)
        shipments.append(shipment_row)
        order_time=datetime.combine(dt,datetime.min.time())+timedelta(hours=7)
        dispatch_time=datetime.combine(dispatch,datetime.min.time())+timedelta(hours=11)
        add_event(shipment_id,order_time,'Order Received',hub[0],'Shipment registered')
        if status=='Cancelled':
            add_event(shipment_id,order_time+timedelta(hours=1),'Order Cancelled',hub[0],'Cancelled before delivery')
            continue
        if dispatch_time>order_time+timedelta(minutes=60):
            add_event(shipment_id,order_time+timedelta(minutes=60),'Package Picked Up',hub[0],'Parcel accepted at origin')
        add_event(shipment_id,dispatch_time,'Dispatched',hub[0],'Released for delivery')
        if status=='In Transit':
            if dispatch<CUTOFF:
                add_event(shipment_id,dispatch_time+timedelta(hours=1),'Arrived at Hub',hub[0],'Pending onward movement at reporting cutoff')
            continue
        when=datetime.combine(outcome,datetime.min.time())+timedelta(hours=16)
        if when <= dispatch_time:when=dispatch_time+timedelta(hours=1)
        add_event(shipment_id,when-timedelta(minutes=40),'Out for Delivery',hub[0],'Courier began final-mile delivery')
        if attempts>1:
            add_event(shipment_id,when-timedelta(minutes=25),'Delivery Attempted',hub[0],'Earlier delivery attempt was unsuccessful')
        event_name={'Delivered':'Delivered','Failed':'Failed Delivery','Returned':'Returned to Sender'}[status]
        add_event(shipment_id,when,event_name,hub[0],failure or 'Shipment delivered to recipient')
    write_csv('shipments.csv',['Shipment_ID','Order_ID','Customer_ID','Courier_ID','Origin_Hub_ID','Destination_Region','Destination_Province',
         'Destination_City','Destination_Latitude','Destination_Longitude','Shipment_Date','Dispatch_Date','Expected_Delivery_Date',
         'Actual_Delivery_Date','Delivery_Status','Delivery_Attempts','Failure_Reason','Package_Weight_KG','Shipping_Cost_PHP',
         'Delivery_Fee_PHP','Service_Type','Distance_KM','SLA_ID'],shipments)
    write_csv('delivery_events.csv',['Event_ID','Shipment_ID','Event_DateTime','Event_Type','Hub_ID','Event_Description'],events)
    print(f'Generated {len(shipments):,} shipments, {len(events):,} tracking events, {len(rules)} SLA rules with seed {SEED}')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--shipments',type=int,default=26000)
    run(parser.parse_args().shipments)
