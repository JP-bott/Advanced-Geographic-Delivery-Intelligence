"""Geographic analysis of actual city-point coordinates, not road distances."""
import numpy as np
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
from pyproj import Geod
WGS84=Geod(ellps='WGS84')

def geodesic_km(lat1,lon1,lat2,lon2):
    _,_,meters=WGS84.inv(float(lon1),float(lat1),float(lon2),float(lat2))
    return abs(meters)/1000

def destination_points(df):
    cities=df.groupby(['Destination_Region','Destination_Province','Destination_City','Destination_Latitude','Destination_Longitude'],as_index=False).agg(shipments=('Shipment_ID','size'),delivered=('Delivered','sum'),on_time=('On_Time','sum'),cost=('Shipping_Cost_PHP','mean'))
    cities['on_time_rate']=np.where(cities.delivered>0, cities.on_time/cities.delivered*100,0)
    return gpd.GeoDataFrame(cities,geometry=gpd.points_from_xy(cities.Destination_Longitude,cities.Destination_Latitude),crs='EPSG:4326')

def route_flows(df):
    return df.groupby(['Hub_Name','Origin_Latitude','Origin_Longitude','Destination_City','Destination_Latitude','Destination_Longitude'],as_index=False).size().rename(columns={'size':'shipments'}).sort_values('shipments',ascending=False)
