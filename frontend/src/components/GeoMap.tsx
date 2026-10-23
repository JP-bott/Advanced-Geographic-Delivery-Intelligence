import {useEffect,useMemo,useRef,useState} from 'react'
import maplibregl,{type Map as MaplibreMap,type GeoJSONSource} from 'maplibre-gl'
import {Crosshair,LocateFixed,Minus,Plus,Layers3,MapPinned} from 'lucide-react'
import type {Shipment,Hub,Point,Route,LayerFlags,Region} from '../types'
import {num} from '../api'

type Props={hubs:Hub[];points:Point[];routes:Route[];regions:Region[];outline:GeoJSON.FeatureCollection|null;admin:GeoJSON.FeatureCollection|null;selected:Shipment|null;layers:LayerFlags;onLayers:(x:LayerFlags)=>void;onHub:(id:string)=>void;onRegion:(name:string)=>void;onRoute:(route:Route)=>void;onPoint:(name:string)=>void;onMapReady?:()=>void}
const center:[number,number]=[122.5,12.3]
const clean=(value:number|null|undefined)=>Number.isFinite(value)?Number(value):0
const collection=(features:any[]):GeoJSON.FeatureCollection=>({type:'FeatureCollection',features})
const property=(record:Record<string,any>,geometry:any):GeoJSON.Feature=>({type:'Feature',properties:record,geometry} as GeoJSON.Feature)
function line(from:[number,number],to:[number,number]){
  // A visual geographic connection only: no routing claim.
  const dx=to[0]-from[0],dy=to[1]-from[1]
  const bow=Math.min(.4,Math.hypot(dx,dy)*.065)
  return Array.from({length:20},(_,i)=>{const t=i/19;return [from[0]+dx*t-bow*Math.sin(Math.PI*t)*(dy===0?0:dy/Math.abs(dy)),from[1]+dy*t+bow*Math.sin(Math.PI*t)*(dx===0?1:dx/Math.abs(dx))]})
}
const bg:any={version:8,sources:{},layers:[{id:'base',type:'background',paint:{'background-color':'#09111b'}}]}
export default function GeoMap({hubs,points,routes,regions,outline,admin,selected,layers,onLayers,onHub,onRegion,onRoute,onPoint,onMapReady}:Props){
  const mount=useRef<HTMLDivElement>(null)
  const map=useRef<MaplibreMap|null>(null)
  const popup=useRef<maplibregl.Popup|null>(null)
  const refs=useRef({onHub,onRegion,onRoute,onPoint,routes,regions})
  const [ready,setReady]=useState(false)
  const [layerPanel,setLayerPanel]=useState(false)
  
  refs.current={onHub,onRegion,onRoute,onPoint,routes,regions}
  const regionLookup=useMemo(()=>new Map(regions.map(r=>[r.Destination_Region,r])),[regions])

  useEffect(()=>{
    if(!mount.current||map.current)return
    const m=new maplibregl.Map({container:mount.current,style:bg,center,zoom:5.2,minZoom:3.5,maxZoom:16,attributionControl:false,renderWorldCopies:false})
    map.current=m
    m.addControl(new maplibregl.AttributionControl({compact:true}), 'bottom-right')
    m.on('load',()=>{
      const empty=collection([])
      m.addSource('country',{type:'geojson',data:empty})
      m.addLayer({id:'geo-land',type:'fill',source:'country',paint:{'fill-color':'#142638','fill-opacity':.9}})
      m.addLayer({id:'country-line',type:'line',source:'country',paint:{'line-color':'#395269','line-width':1}})
      m.addSource('admin',{type:'geojson',data:empty})
      m.addLayer({id:'admin-fill',type:'fill',source:'admin',paint:{'fill-color':['interpolate',['linear'],['coalesce',['get','metric'],0],0,'#183042',50,'#215066',100,'#277c88'],'fill-opacity':.55}})
      m.addLayer({id:'admin-line',type:'line',source:'admin',paint:{'line-color':'#47718b','line-opacity':.5,'line-width':.9}})
      m.addSource('flows',{type:'geojson',data:empty})
      m.addLayer({id:'routes',type:'line',source:'flows',paint:{'line-color':['interpolate',['linear'],['coalesce',['get','on_time_rate'],0],0,'#f43f5e',75,'#f59e0b',95,'#22d3ee'],'line-opacity':.52,'line-width':['interpolate',['linear'],['coalesce',['get','shipments'],1],0,1,100,2,600,5]}})
      m.addSource('hubs',{type:'geojson',data:empty})
      m.addLayer({id:'hubs-outer',type:'circle',source:'hubs',paint:{'circle-color':'#030812','circle-radius':['interpolate',['linear'],['coalesce',['get','shipments'],0],0,9,5000,20],'circle-stroke-color':['interpolate',['linear'],['coalesce',['get','on_time_rate'],0],0,'#f43f5e',80,'#f59e0b',95,'#22d3ee'],'circle-stroke-width':2}})
      m.addLayer({id:'hubs-core',type:'circle',source:'hubs',paint:{'circle-radius':4,'circle-color':'#a78bfa'}})
      m.addSource('destinations',{type:'geojson',data:empty,cluster:true,clusterRadius:42,clusterMaxZoom:9})
      m.addLayer({id:'destination-clusters',type:'circle',source:'destinations',filter:['has','point_count'],paint:{'circle-color':'#133b58','circle-radius':20,'circle-stroke-color':'#22d3ee','circle-stroke-width':1.5}})
      m.addLayer({id:'cluster-count',type:'symbol',source:'destinations',filter:['has','point_count'],layout:{'text-field':['get','point_count_abbreviated'],'text-size':11},paint:{'text-color':'#e8edf5'}})
      m.addLayer({id:'destinations',type:'circle',source:'destinations',filter:['!',['has','point_count']],paint:{'circle-radius':['interpolate',['linear'],['coalesce',['get','shipments'],0],0,5,4500,14],'circle-color':['interpolate',['linear'],['coalesce',['get','on_time_rate'],0],0,'#f43f5e',82,'#f59e0b',96,'#22d3ee'],'circle-opacity':.92,'circle-stroke-color':'#0a1420','circle-stroke-width':1.5}})
      m.addLayer({id:'destination-labels',type:'symbol',source:'destinations',filter:['!',['has','point_count']],layout:{'text-field':['get','name'],'text-size':10,'text-offset':[0,1.4],'text-allow-overlap':false},paint:{'text-color':'#afbdcb','text-halo-color':'#0a1420','text-halo-width':1}})
      m.addSource('risk',{type:'geojson',data:empty})
      m.addLayer({id:'risk-halos',type:'circle',source:'risk',paint:{'circle-radius':19,'circle-color':'#f43f5e','circle-opacity':.13,'circle-stroke-width':1,'circle-stroke-color':'#f43f5e','circle-stroke-opacity':.45}})
      m.addSource('focus',{type:'geojson',data:empty})
      m.addLayer({id:'focus-route',type:'line',source:'focus',filter:['==',['geometry-type'],'LineString'],paint:{'line-color':'#a78bfa','line-width':3,'line-dasharray':[2,1]}})
      m.addLayer({id:'focus-start',type:'circle',source:'focus',filter:['==',['get','role'],'origin'],paint:{'circle-color':'#8b5cf6','circle-radius':10,'circle-stroke-color':'#e9d5ff','circle-stroke-width':2}})
      m.addLayer({id:'focus-end',type:'circle',source:'focus',filter:['==',['get','role'],'destination'],paint:{'circle-color':'#22d3ee','circle-radius':10,'circle-stroke-color':'#d1fafc','circle-stroke-width':2}})
      for(const layer of ['hubs-outer','destinations','destination-clusters','routes','admin-fill']) {
        m.on('mouseenter',layer,()=>{m.getCanvas().style.cursor='pointer'})
        m.on('mouseleave',layer,()=>{m.getCanvas().style.cursor=''})
      }
      m.on('click','hubs-outer',e=>{const id=e.features?.[0]?.properties?.Hub_ID;if(id)refs.current.onHub(id)})
      m.on('click','destinations',e=>{const region=e.features?.[0]?.properties?.region;if(region)refs.current.onPoint(region)})
      m.on('click','destination-clusters',e=>{const feature=e.features?.[0];if(!feature)return;const id=feature.properties?.cluster_id;const source=m.getSource('destinations') as GeoJSONSource;source.getClusterExpansionZoom(id).then(z=>m.easeTo({center:(feature.geometry as GeoJSON.Point).coordinates as [number,number],zoom:z}))})
      m.on('click','routes',e=>{const ix=Number(e.features?.[0]?.properties?.index);const route=refs.current.routes[ix];if(route)refs.current.onRoute(route)})
      m.on('click','admin-fill',e=>{const region=e.features?.[0]?.properties?.region;if(region)refs.current.onRegion(region)})
      m.on('mousemove',e=>{
        const hit=m.queryRenderedFeatures(e.point,{layers:['hubs-outer','destinations','routes','admin-fill']}).at(0)
        popup.current?.remove();popup.current=null
        if(!hit)return
        const p=hit.properties||{}
        const content=p.Hub_Name?`${p.Hub_Name} · ${num(p.shipments)} shipments`:(p.name?`${p.name} · ${num(p.shipments)} shipments`:p.route?`${p.route} · ${num(p.shipments)} parcels`:p.region||'')
        if(content)popup.current=new maplibregl.Popup({closeButton:false,closeOnClick:true,offset:12,className:'nex-map-popup'}).setLngLat(e.lngLat).setText(content).addTo(m)
      })
      setReady(true);onMapReady?.()
    })
    return ()=>{popup.current?.remove();m.remove();map.current=null;setReady(false)}
  },[])
  useEffect(()=>{
    const m=map.current;if(!m||!ready)return
    function set(id:string,geo:GeoJSON.FeatureCollection){(m.getSource(id) as GeoJSONSource)?.setData(geo)}
    set('country',outline||collection([]))
    const sourceFeatures=(admin?.features||[]).map(f=>{
      const props=f.properties||{}
      const name=String(props.shapeName||props.NAME_1||props.name||'')
      const metric=regionLookup.get(name)
      return {...f,properties:{...props,region:name,metric:clean(metric?.on_time_rate)}} as GeoJSON.Feature
    })
    set('admin',collection(sourceFeatures))
    set('hubs',collection(hubs.map(h=>property({...h}, {type:'Point',coordinates:[h.Longitude,h.Latitude]}))))
    set('destinations',collection(points.map(p=>property({...p,name:p.Destination_City,region:p.Destination_Region}, {type:'Point',coordinates:[p.Destination_Longitude,p.Destination_Latitude]}))))
    set('risk',collection(points.filter(p=>p.shipments>=60&&(p.failed_rate>=9||p.on_time_rate<80)).map(p=>property({name:p.Destination_City}, {type:'Point',coordinates:[p.Destination_Longitude,p.Destination_Latitude]}))))
    set('flows',collection(routes.map((r,i)=>property({...r,index:i,route:`${r.Hub_Name} → ${r.Destination_City}`},{type:'LineString',coordinates:line([r.Origin_Longitude,r.Origin_Latitude],[r.Destination_Longitude,r.Destination_Latitude])}))))
    const visibility:Record<string,boolean>={'hubs-outer':layers.hubs,'hubs-core':layers.hubs,'destination-clusters':layers.destinations,'cluster-count':layers.destinations,'destinations':layers.destinations,'destination-labels':layers.destinations&&layers.labels,'routes':layers.flows,'risk-halos':layers.risk,'admin-fill':layers.regions&&sourceFeatures.length>0,'admin-line':layers.regions&&sourceFeatures.length>0}
    for(const [id,show] of Object.entries(visibility)) m.setLayoutProperty(id,'visibility',show?'visible':'none')
  },[hubs,points,routes,admin,outline,layers,ready,regionLookup])
  useEffect(()=>{
    const m=map.current;if(!m||!ready)return
    const s=m.getSource('focus') as GeoJSONSource
    if(!selected){s.setData(collection([]));return}
    const a:[number,number]=[selected.Origin_Longitude,selected.Origin_Latitude]
    const b:[number,number]=[selected.Destination_Longitude,selected.Destination_Latitude]
    s.setData(collection([property({role:'origin'},{type:'Point',coordinates:a}),property({role:'destination'},{type:'Point',coordinates:b}),property({role:'connection'},{type:'LineString',coordinates:line(a,b)})]))
    const extent=new maplibregl.LngLatBounds(a,b)
    m.fitBounds(extent,{padding:75,maxZoom:9,duration:650})
  },[selected,ready])
  const change=(k:keyof LayerFlags)=>onLayers({...layers,[k]:!layers[k]})
  const fit=()=>map.current?.fitBounds([[116.2,4.5],[127,20.9]],{padding:35,duration:550})
  return <div className="map-shell">
    <div ref={mount} className="geo-map" role="application" aria-label="Interactive Philippine geographic logistics map"/>
    <div className="map-chip"><span className="live-dot"/> HISTORICAL GEOGRAPHIC VIEW <span className="chip-separator">/</span> WGS84 · PHILIPPINES</div>
    <div className="map-controls">
      <button title="Zoom in" aria-label="Zoom in" onClick={()=>map.current?.zoomIn()}><Plus size={17}/></button>
      <button title="Zoom out" aria-label="Zoom out" onClick={()=>map.current?.zoomOut()}><Minus size={17}/></button>
      <button title="Fit Philippines" aria-label="Fit Philippines" onClick={fit}><LocateFixed size={17}/></button>
      <button title="Reset map" aria-label="Reset map" onClick={()=>map.current?.flyTo({center,zoom:5.2})}><Crosshair size={17}/></button>
      <button title="Toggle map layers" aria-label="Toggle map layers" aria-expanded={layerPanel} onClick={()=>setLayerPanel(v=>!v)}><Layers3 size={17}/></button>
    </div>
    {layerPanel&&<div className="layer-flyout"><div className="flyout-title">MAP DISPLAY <button onClick={()=>setLayerPanel(false)}>×</button></div>{(Object.keys(layers) as (keyof LayerFlags)[]).map(k=><label key={k} className="toggle-line"><span>{k==='regions'?'Regional boundaries':k==='risk'?'Delivery risk':k[0].toUpperCase()+k.slice(1)}</span><input type="checkbox" checked={layers[k]} disabled={k==='regions'&&!admin?.features.length} onChange={()=>change(k)}/></label>)}{!admin?.features.length&&<small>Region polygons unavailable. City-level metrics remain active.</small>}</div>}
    <div className="map-bottom-note"><MapPinned size={13}/> OFFLINE VECTOR OUTLINE · GEOGRAPHIC FLOWS ARE NOT DRIVING ROUTES</div>
  </div>
}
