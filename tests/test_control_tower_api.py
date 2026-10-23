from fastapi.testclient import TestClient
from backend.main import app
client=TestClient(app)
def test_health_and_overview():
    assert client.get('/api/health').json()['shipments']==26000
    data=client.get('/api/overview').json()
    assert data['kpis']['shipments']==26000
    assert data['active']>=0

def test_filtered_reconciliation():
    response=client.get('/api/overview',params={'region':'NCR','service':'Standard'})
    assert response.status_code==200
    records=client.get('/api/shipments',params={'region':'NCR','service':'Standard','page_size':1}).json()
    assert records['total']==response.json()['kpis']['shipments']

def test_shipment_history_and_cutoff():
    data=client.get('/api/shipments',params={'page_size':1}).json()['items'][0]
    detail=client.get('/api/shipments/'+data['Shipment_ID']).json()
    assert detail['shipment']['Shipment_ID']==data['Shipment_ID']
    assert detail['events']==sorted(detail['events'],key=lambda x:x['Event_DateTime'])
    cutoff=client.get('/api/shipments',params={'cutoff':'2024-04-01','end':'2024-04-01','page_size':5}).json()
    assert all(x['Shipment_Date'][:10]<='2024-04-01' for x in cutoff['items'])

def test_geodata_and_api_contract():
    assert len(client.get('/api/hubs').json())==12
    assert len(client.get('/api/destinations').json())==24
    assert all(4<=x['Destination_Latitude']<=22 for x in client.get('/api/destinations').json())
    assert all(x['shipments']>0 for x in client.get('/api/routes').json())
    assert client.get('/api/geo/outline').json()['features']
    assert client.get('/api/shipments/invalid').status_code==404
    assert client.get('/api/overview',params={'cutoff':'2026-01-01'}).status_code==422
