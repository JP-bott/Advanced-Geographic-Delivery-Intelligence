"""Optional fetch of authoritative-source-credited Philippine ADM1 geometries.

Requires internet at download time. Offline-only users can use the bundled
Natural Earth country outline and city aggregates without any tiles or keys.
"""
import argparse
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
API = 'https://www.geoboundaries.org/api/current/gbOpen/PHL/ADM1/'
MAPPING = {
    'national capital region':'NCR',
    'ncr':'NCR',
    'calabarzon':'CALABARZON',
    'central luzon':'Central Luzon',
    'central visayas':'Central Visayas',
    'western visayas':'Western Visayas',
    'davao region':'Davao Region',
}

def normalize(name):
    val = name.lower().strip()
    for token, canonical in MAPPING.items():
        if token in val:
            return canonical
    return name

def main(optional=False):
    dest = ROOT/'data/geo/philippines_adm1.geojson'
    if dest.exists():
        print('Existing local polygons:', dest)
        return
    try:
        with urlopen(API, timeout=20) as response:
            meta=json.load(response)
        source=meta['simplifiedGeometryGeoJSON']
        with urlopen(source, timeout=35) as response:
            geo=json.load(response)
        if geo['type']!='FeatureCollection' or not 12<=len(geo['features'])<=30:
            raise ValueError('Not a plausible Philippine ADM1 boundary collection')
        # This dataset includes provinces not modeled in the shipment data.
        # Preserve them for a real geographic outline without guessing polygons.
        for feature in geo['features']:
            p=feature.setdefault('properties', {})
            name=p.get('shapeName') or p.get('NAME_1') or p.get('name','')
            p['region']=normalize(name)
            if feature['geometry']['type'] not in ('Polygon','MultiPolygon'):
                raise ValueError('Unexpected boundary geometry type')
        dest.write_text(json.dumps(geo,separators=(',',':')), encoding='utf-8')
        print('Saved region polygons from',source,'to',dest)
    except Exception as exc:
        if optional:
            print('Optional boundary download skipped:',exc)
        else:
            raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--optional',action='store_true');a=p.parse_args();main(a.optional)
