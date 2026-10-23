"""API tests operate on the included synthetic SQLite dataset."""
from datetime import date
from fastapi.testclient import TestClient
from backend.main import app,risk,snapshot,sources
client=TestClient(app)

def test_health_and_pagination():
    assert client.get('/api/health').json()['shipments']==26000
    r=client.get('/api/shipments',params={'page_size':12,'page':2})
    assert r.status_code==200
    body=r.json()
    assert body['total']==26000 and len(body['items'])==12 and body['page']==2
    assert len({x['Shipment_ID'] for x in body['items']})==12

def test_filtered_counts_reconcile():
    params={'region':'Central Luzon','status':'Delivered','service':'Standard'}
    total=client.get('/api/overview',params=params).json()['kpis']['shipments']
    assert total>0
    assert client.get('/api/shipments',params=params).json()['total']==total
    assert sum(r['shipments'] for r in client.get('/api/regions',params=params).json())==total
    assert sum(r['shipments'] for r in client.get('/api/destinations',params=params).json())==total

def test_selected_events_and_geography():
    record=client.get('/api/shipments',params={'page_size':1}).json()['items'][0]
    d=client.get('/api/shipments/'+record['Shipment_ID']).json()
    s=d['shipment']
    assert s['Shipment_ID']==record['Shipment_ID']
    assert 116<s['Destination_Longitude']<127
    assert 4<s['Destination_Latitude']<22
    assert all(a['Event_DateTime']<=b['Event_DateTime'] for a,b in zip(d['events'],d['events'][1:]))
    assert client.get('/api/shipments/no-such-id').status_code==404

def test_hub_aggregations():
    hubs=client.get('/api/hubs').json()
    assert len(hubs)==12
    assert sum(int(h['shipments']) for h in hubs)==26000
    for h in hubs[:2]:
        detail=client.get('/api/hubs/'+h['Hub_ID']).json()
        assert detail['kpis']['shipments']==h['shipments']

def test_historical_cutoff_does_not_leak_future_events():
    cutoff=date(2024,2,10)
    df=snapshot(cutoff)
    assert (df.loc[df.Delivered,'Actual_Delivery_Date'].dt.date<=cutoff).all()
    response=client.get('/api/shipments',params={'cutoff':str(cutoff),'page_size':50})
    assert response.status_code==200
    for s in response.json()['items']:
        assert s['Shipment_Date'][:10]<=str(cutoff)
        if s['Actual_Delivery_Date']:
            assert s['Actual_Delivery_Date'][:10]<=str(cutoff)
    first=response.json()['items'][0]
    events=client.get('/api/shipments/'+first['Shipment_ID'],params={'cutoff':str(cutoff)}).json()['events']
    assert all(e['Event_DateTime'][:10]<=str(cutoff) for e in events)

def test_risk_rules():
    from pandas import Timestamp
    base={'Delivery_Status':'In Transit','Expected_Delivery_Date':Timestamp('2024-05-12'),'On_Time':False}
    assert risk(base,date(2024,5,9))=='On Track'
    assert risk(base,date(2024,5,11))=='At Risk'
    assert risk(base,date(2024,5,13))=='Delayed'
    assert risk({**base,'Delivery_Status':'Failed'},date(2024,5,9))=='Failed'
    assert risk({**base,'Delivery_Status':'Delivered','On_Time':True},date(2024,5,13))=='Completed'

def test_api_empty_and_invalid_cases():
    assert client.get('/api/overview',params={'region':'No Such Region'}).json()['kpis']['shipments']==0
    assert client.get('/api/destinations',params={'region':'No Such Region'}).json()==[]
    assert client.get('/api/routes',params={'region':'No Such Region'}).json()==[]
    assert client.get('/api/shipments',params={'start':'2025-12-31','end':'2024-01-01'}).status_code==422
    assert client.get('/api/overview',params={'cutoff':'2026-01-01'}).status_code==422

