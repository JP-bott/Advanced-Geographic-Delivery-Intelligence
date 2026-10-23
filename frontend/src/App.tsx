import {useCallback,useEffect,useMemo,useState} from 'react'
import {BarChart3,ChevronLeft,ChevronRight,ChevronsUpDown,Clock3,Filter,LayoutDashboard,Map as MapIcon,MapPin,Menu,Package,PanelLeftClose,PanelRightClose,Route as RouteIcon,Search,Settings2,ShieldAlert,SlidersHorizontal,Truck,X,Info} from 'lucide-react'
import {Area,AreaChart,CartesianGrid,Cell,Pie,PieChart,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts'
import GeoMap from './components/GeoMap'
import {getJson,query,num,percentage,php,shortDate} from './api'
import type {Filters,Shipment,Hub,Region,Point,Route,Detail,Overview,Options,HubDetail,LayerFlags} from './types'

const pages=[{name:'Operations',icon:LayoutDashboard},{name:'Geographic Intelligence',icon:MapIcon},{name:'Courier Performance',icon:Truck},{name:'SLA Analytics',icon:ShieldAlert},{name:'Shipping Costs',icon:BarChart3},{name:'Shipment Explorer',icon:Package},{name:'Preferences',icon:Settings2}]
const defaultFilters:Filters={start:'2024-01-01',end:'2025-12-31',cutoff:'2025-12-31',region:'',courier:'',status:'',service:''}
const defaults:LayerFlags={hubs:true,destinations:true,flows:true,regions:false,risk:true,labels:true}
const palette:Record<string,string>={Completed:'#22c55e','On Track':'#22d3ee','At Risk':'#f59e0b',Delayed:'#f43f5e',Failed:'#f43f5e',Cancelled:'#8b9bae','Delivered':'#22c55e','In Transit':'#22d3ee','Returned':'#f43f5e'}
const navTooltip=(page:string)=>`Open ${page}`
const fmt=(x:string|null|undefined)=>x?new Date(x.slice(0,10)+'T00:00:00').toLocaleDateString('en-PH',{day:'2-digit',month:'short',year:'numeric'}):'—'
function Status({text}:{text:string}){return <span className="risk-tag" style={{color:palette[text]||'#cbd5e1'}}><span className="status-dot" style={{background:palette[text]||'#cbd5e1'}}/>{text}</span>}
function Stat({label,value,alert=false}:{label:string;value:string;alert?:boolean}){return <div className="metric-item"><span>{label}</span><strong className={alert?'alert':''}>{value}</strong></div>}
function MiniDonut({values}:{values:{name:string;count:number}[]}){
  const colors=['#22c55e','#f43f5e','#f59e0b','#22d3ee','#7c8da3']
  if(!values.length)return <p className="muted">No delivery outcomes for this selection.</p>
  return <div className="donut-wrap"><div className="donut-graphic"><ResponsiveContainer width="100%" height={148}><PieChart><Pie data={values} dataKey="count" innerRadius={48} outerRadius={65} paddingAngle={2} stroke="none">{values.map((v,i)=><Cell key={v.name} fill={palette[v.name]||colors[i%colors.length]}/>)}</Pie><Tooltip contentStyle={{background:'#111b29',border:'1px solid #344057',color:'#e8edf5'}}/></PieChart></ResponsiveContainer><div className="donut-center"><strong>{num(values.reduce((a,b)=>a+b.count,0))}</strong><small>SHIPMENTS</small></div></div><div className="legend-stack">{values.map((v,i)=><div key={v.name}><span className="legend-key" style={{background:palette[v.name]||colors[i%colors.length]}}/><span>{v.name}</span><b>{num(v.count)}</b></div>)}</div></div>
}
function InputSelect({label,value,options,onChange}:{label:string;value:string;options:{value:string;label:string}[];onChange:(s:string)=>void}){return <label className="field"><span>{label}</span><select aria-label={label} value={value} onChange={e=>onChange(e.target.value)}><option value="">All {label.toLowerCase()}</option>{options.map(v=><option key={v.value} value={v.value}>{v.label}</option>)}</select></label>}
function Trend({overview}:{overview:Overview}) {return <div className="spark-chart"><ResponsiveContainer width="100%" height={100}><AreaChart data={overview.sla_trend}><defs><linearGradient id="slaFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22d3ee" stopOpacity={.23}/><stop offset="100%" stopColor="#22d3ee" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#1b2838" vertical={false}/><XAxis dataKey="date" tick={{fontSize:9,fill:'#7a899d'}} tickFormatter={s=>s.slice(5,7)+'/'+s.slice(2,4)} interval="preserveStartEnd"/><YAxis domain={[0,100]} hide/><Tooltip contentStyle={{background:'#101722',border:'1px solid #2c3a4c'}} formatter={(v:number)=>percentage(v)}/><Area type="monotone" dataKey="rate" stroke="#22d3ee" fill="url(#slaFill)" strokeWidth={2}/></AreaChart></ResponsiveContainer></div>}
function Timeline({detail,overview,onFocusEvent}:{detail:Detail|null;overview:Overview|null;onFocusEvent:(hub:string|null)=>void}){
  if(detail){const e=detail.events;return <div className="timeline"><div className="timeline-header"><div><span className="section-eyebrow">SHIPMENT EVENT RECORD</span><strong>{detail.shipment.Shipment_ID} · {e.length} logged milestones</strong></div><span className="muted tiny">Click a milestone to inspect its hub</span></div><div className="timeline-scroll"><div className="event-track">{e.map((v,i)=><button key={v.Event_ID} className="event-node" onClick={()=>onFocusEvent(v.Hub_ID)} title={v.Event_Description}><span className={'event-pip '+(i===e.length-1?'end':'')}/><span className="event-name">{v.Event_Type}</span><span className="event-date">{v.Event_DateTime.slice(0,16).replace('T',' ')}</span></button>)}<div className="deadline-node"><span className="deadline-pip"/><span>SLA DEADLINE</span><strong>{shortDate(detail.shipment.Expected_Delivery_Date)}</strong></div></div></div></div>}
  return <div className="timeline"><div className="timeline-header"><div><span className="section-eyebrow">OPERATIONAL TIMELINE</span><strong>Shipment activity across the selected period</strong></div><span className="muted tiny">Daily received shipments · most recent intervals</span></div><div className="daily-bars">{(overview?.volume_trend||[]).map(x=><div className="daily-col" key={x.date} title={`${x.date}: ${num(x.count)} shipments`}><div style={{height:`${Math.max(5,100*x.count/Math.max(1,...(overview?.volume_trend||[]).map(a=>a.count)))}%`}}/><span>{x.date.slice(5)}</span></div>)}</div></div>
}
export default function App(){
 const [page,setPage]=useState('Geographic Intelligence')
 const [filters,setFilters]=useState<Filters>(defaultFilters)
 const [options,setOptions]=useState<Options|null>(null)
 const [shipments,setShipments]=useState<Shipment[]>([])
 const [total,setTotal]=useState(0)
 const [hubs,setHubs]=useState<Hub[]>([])
 const [regions,setRegions]=useState<Region[]>([])
 const [points,setPoints]=useState<Point[]>([])
 const [routes,setRoutes]=useState<Route[]>([])
 const [overview,setOverview]=useState<Overview|null>(null)
 const [outline,setOutline]=useState<GeoJSON.FeatureCollection|null>(null)
 const [admin,setAdmin]=useState<GeoJSON.FeatureCollection|null>(null)
 const [selectedId,setSelectedId]=useState<string|null>(null)
 const [selectedDetail,setSelectedDetail]=useState<Detail|null>(null)
 const [selectedHub,setSelectedHub]=useState<HubDetail|null>(null)
 const [selectedRoute,setSelectedRoute]=useState<Route|null>(null)
 const [selectedRegion,setSelectedRegion]=useState<Region|null>(null)
 const [layers,setLayers]=useState<LayerFlags>(defaults)
 const [search,setSearch]=useState('')
 const [deferredSearch,setDeferredSearch]=useState('')
 const [sort,setSort]=useState('risk')
 const [currentPage,setCurrentPage]=useState(1)
 const [busy,setBusy]=useState(false)
 const [error,setError]=useState('')
 const [leftOpen,setLeftOpen]=useState(true)
 const [rightOpen,setRightOpen]=useState(true)
 const [filtersOpen,setFiltersOpen]=useState(false)
 const [couriers,setCouriers]=useState<{Courier_ID:string;Courier_Name:string;on_time_rate:number;shipments:number}[]>([])
 const [metric,setMetric]=useState('on_time_rate')
 const [showRules,setShowRules]=useState(false)
 const params=useMemo(()=>query(filters),[filters])
 const update=(k:keyof Filters,v:string)=>{setFilters(f=>({...f,[k]:v}));setCurrentPage(1);setSelectedId(null)}
 useEffect(()=>{getJson<Options>('/api/filters').then(setOptions).catch(e=>setError(String(e)));getJson<GeoJSON.FeatureCollection>('/api/geo/outline').then(setOutline).catch(()=>{});getJson<GeoJSON.FeatureCollection>('/api/geo/regions').then(setAdmin).catch(()=>{})},[])
 useEffect(()=>{const timer=window.setTimeout(()=>setDeferredSearch(search),280);return ()=>clearTimeout(timer)},[search])
 useEffect(()=>{setCurrentPage(1)},[deferredSearch])
 useEffect(()=>{
   const controller=new AbortController();setBusy(true);setError('')
   Promise.all([
     getJson<Overview>(`/api/overview?${params}`,controller.signal),getJson<Hub[]>(`/api/hubs?${params}`,controller.signal),
     getJson<Point[]>(`/api/destinations?${params}`,controller.signal),getJson<Route[]>(`/api/routes?${params}`,controller.signal),
     getJson<Region[]>(`/api/regions?${params}`,controller.signal),getJson<{Courier_ID:string;Courier_Name:string;on_time_rate:number;shipments:number}[]>(`/api/courier-performance?${params}&minimum=20`,controller.signal),
   ]).then(([ov,hu,po,ro,re,co])=>{setOverview(ov);setHubs(hu);setPoints(po);setRoutes(ro);setRegions(re);setCouriers(co)}).catch(e=>{if(!controller.signal.aborted)setError(String(e))}).finally(()=>{if(!controller.signal.aborted)setBusy(false)})
   return ()=>controller.abort()
 },[params])
 useEffect(()=>{
   const controller=new AbortController()
   getJson<{items:Shipment[];total:number}>(`/api/shipments?${params}&${query({...defaultFilters,start:'',end:'',cutoff:'',region:'',courier:'',status:'',service:''},{search:deferredSearch,sort,page:currentPage,page_size:24})}`,controller.signal).then(v=>{setShipments(v.items);setTotal(v.total)}).catch(e=>{if(!controller.signal.aborted)setError(String(e))})
   return ()=>controller.abort()
 },[params,deferredSearch,sort,currentPage])
 useEffect(()=>{
   if(!selectedId){setSelectedDetail(null);return}
   const controller=new AbortController()
   getJson<Detail>(`/api/shipments/${encodeURIComponent(selectedId)}?cutoff=${filters.cutoff}`,controller.signal).then(d=>{setSelectedDetail(d);setRightOpen(true)}).catch(e=>{if(!controller.signal.aborted){setError(String(e));setSelectedDetail(null)}})
   return ()=>controller.abort()
 },[selectedId,filters.cutoff])
 const selectShipment=(id:string)=>{setSelectedId(id);setSelectedHub(null);setSelectedRoute(null);setSelectedRegion(null);setRightOpen(true)}
 const onHub=useCallback(async(id:string)=>{setSelectedId(null);setSelectedRoute(null);setSelectedRegion(null);setRightOpen(true);try{setSelectedHub(await getJson<HubDetail>(`/api/hubs/${id}?${params}`))}catch(e){setError(String(e))}},[params])
 const onRegion=useCallback((r:string)=>{update('region',r);setSelectedHub(null);setSelectedRoute(null);setRightOpen(true);setSelectedRegion(regions.find(x=>x.Destination_Region===r)||null)},[regions])
 const onRoute=useCallback((r:Route)=>{setSelectedId(null);setSelectedHub(null);setSelectedRegion(null);setSelectedRoute(r);setRightOpen(true)},[])
 const togglePanel=()=>{setFiltersOpen(v=>!v);setLeftOpen(true)}
 const hasActive=Object.entries(filters).some(([k,v])=>!['start','end','cutoff'].includes(k)&&v)
 const infoTitle=selectedDetail?'SHIPMENT INTELLIGENCE':selectedHub?'HUB INTELLIGENCE':selectedRoute?'CORRIDOR INTELLIGENCE':selectedRegion?'REGIONAL INTELLIGENCE':'PERFORMANCE INSIGHT'
 const riskTotals=overview?.at_risk||0
 const current=(selectedDetail?.shipment)||null
  return <div className="app-frame">
   <aside className="rail" aria-label="Main navigation"><div className="brand-mark" aria-label="NexRoute"><RouteIcon size={24}/><span>NX</span></div><nav>{pages.map(({name,icon:Icon},i)=><button className={'rail-button '+(page===name?'active':'')} aria-label={navTooltip(name)} title={name} key={name} onClick={()=>{setPage(name);if(name==='Preferences'){setFiltersOpen(true);setLeftOpen(true)}}}><Icon size={19}/></button>)}</nav><div className="rail-bottom"><span className="rail-status" title="Offline-capable historical analytics"/><span className="rail-version">v2</span></div></aside>
   <div className="workspace">
    <header className="topbar"><div className="top-title"><button className="hide-left" aria-label="Toggle monitoring panel" onClick={()=>setLeftOpen(v=>!v)}><Menu size={18}/></button><strong>Control Tower</strong><span className="crumb">/</span><span>{page}</span></div><div className="top-utilities"><span className="historic-pill"><Clock3 size={13}/> HISTORICAL SNAPSHOT · {filters.cutoff}</span><button title="Filter operational data" aria-label="Filter operational data" onClick={togglePanel}><Filter size={18}/></button><button title="Toggle detail panel" aria-label="Toggle details" onClick={()=>setRightOpen(v=>!v)}><PanelRightClose size={18}/></button><div className="avatar">NX</div></div></header>
    <div className={'body-grid '+(!leftOpen?'left-collapsed ':'')+(!rightOpen?'right-collapsed':'')}>
      {leftOpen&&<section className="left-panel" aria-label="Shipment monitoring panel">
        <div className="panel-head"><div><span className="section-eyebrow">NEXROUTE OPERATIONS</span><h2>Mission overview</h2></div><button className="icon-button" aria-label="Collapse monitoring panel" onClick={()=>setLeftOpen(false)}><PanelLeftClose size={17}/></button></div>
        <div className="summary-grid"><Stat label="IN TRANSIT" value={num(overview?.active)}/><Stat label="AT RISK" value={num(riskTotals)} alert/><Stat label="ON-TIME RATE" value={percentage(overview?.kpis.on_time_rate)}/><Stat label="DELAYED" value={num(overview?.delayed)} alert/><Stat label="FAILED / RETURNED" value={num(overview?.failed)} alert/><Stat label="SHIPMENTS" value={num(overview?.kpis.shipments)}/></div>
        <div className="panel-divider"/>
        <div className="compact-heading"><span>QUICK FILTERS</span><button onClick={()=>setFiltersOpen(v=>!v)} aria-expanded={filtersOpen}><SlidersHorizontal size={14}/> {filtersOpen?'Hide':'Edit'}</button></div>
        <div className="filter-summary">{filters.region||'All regions'} <span>/</span> {filters.status||'All statuses'} {hasActive&&<button onClick={()=>setFilters(defaultFilters)}>Clear</button>}</div>
        {filtersOpen&&<div className="filters-drawer">
          <div className="date-row"><label className="field"><span>START</span><input aria-label="Start date" type="date" min="2024-01-01" max={filters.cutoff} value={filters.start} onChange={e=>update('start',e.target.value)}/></label><label className="field"><span>END</span><input aria-label="End date" type="date" min={filters.start} max={filters.cutoff} value={filters.end} onChange={e=>update('end',e.target.value)}/></label></div>
          <InputSelect label="Region" value={filters.region} options={(options?.regions||[]).map(x=>({value:x,label:x}))} onChange={v=>update('region',v)}/>
          <InputSelect label="Courier" value={filters.courier} options={(options?.couriers||[]).map(x=>({value:x.Courier_ID,label:x.Courier_Name}))} onChange={v=>update('courier',v)}/>
          <InputSelect label="Status" value={filters.status} options={(options?.statuses||[]).map(x=>({value:x,label:x}))} onChange={v=>update('status',v)}/>
          <InputSelect label="Service" value={filters.service} options={(options?.services||[]).map(x=>({value:x,label:x}))} onChange={v=>update('service',v)}/>
          <label className="field"><span>AS-OF REPORTING DATE</span><input aria-label="Reporting cutoff" type="date" min="2024-01-01" max="2025-12-31" value={filters.cutoff} onChange={e=>{update('cutoff',e.target.value);setFilters(f=>({...f,cutoff:e.target.value,end:f.end>e.target.value?e.target.value:f.end}))}}/></label>
        </div>}
        <div className="panel-divider"/>
        <div className="compact-heading"><span>SHIPMENT MONITOR</span><small>{num(total)} RECORDS</small></div>
        <label className="search-box"><Search size={16}/><input placeholder="Search shipment ID" value={search} onChange={e=>setSearch(e.target.value)} aria-label="Search shipments"/>{search&&<button title="Clear search" onClick={()=>setSearch('')}><X size={13}/></button>}</label>
        <label className="sort-box"><ChevronsUpDown size={14}/><select value={sort} aria-label="Sort shipments" onChange={e=>{setSort(e.target.value);setCurrentPage(1)}}><option value="risk">Priority: risk first</option><option value="newest">Newest shipment first</option><option value="oldest">Oldest shipment first</option><option value="deadline">Earliest SLA deadline</option><option value="cost">Highest shipping cost</option></select></label>
        <div className="ship-list">{shipments.length===0&&<div className="empty-state">No matching shipments. Adjust the search or filters.</div>}{shipments.map(s=><button key={s.Shipment_ID} className={'shipment-card '+(selectedId===s.Shipment_ID?'selected':'')} onClick={()=>selectShipment(s.Shipment_ID)}><div className="ship-row"><span className="mono"><Package size={15}/> {s.Shipment_ID}</span><Status text={s.Risk}/></div><div className="ship-locations"><span>{s.Hub_Name}</span><RouteIcon size={15}/><strong>{s.Destination_City}</strong></div><div className="ship-row ship-meta"><span>{s.Courier_Name}</span><span>Due {shortDate(s.Expected_Delivery_Date)}</span></div><div className="card-bottom"><span className="status-line" style={{background:palette[s.Risk]}}/><span>{s.Service_Type} · {s.Delivery_Status}</span><ChevronRight size={14}/></div></button>)}</div>
        <div className="pagination"><button disabled={currentPage<=1} onClick={()=>setCurrentPage(v=>Math.max(1,v-1))} aria-label="Previous shipments"><ChevronLeft size={17}/></button><span>Page {currentPage} / {Math.max(1,Math.ceil(total/24))}</span><button disabled={currentPage*24>=total} onClick={()=>setCurrentPage(v=>v+1)} aria-label="Next shipments"><ChevronRight size={17}/></button></div>
      </section>}
      <main className="map-and-time" aria-label="Geographic operational workspace">
        <div className="map-topline"><div className="workspace-tabs"><strong>{page}</strong><span className="map-topline-sub">{selectedId||selectedHub?.hub.Hub_Name||selectedRoute?.Hub_Name||'Philippine delivery network'}</span></div><div className="map-topline-actions"><span className="tiny"><span className="live-dot"/> SYNTHETIC DATA</span><button title="Open filter controls" onClick={togglePanel}><SlidersHorizontal size={14}/> FILTERS</button><button title="Show risk rules" onClick={()=>setShowRules(true)}><Info size={14}/> RISK RULES</button></div></div>
        {page==='Preferences'&&<div className="display-overlay"><Settings2 size={20}/><h3>Display preferences</h3><p>Change the visible map layers using the map button at the right. Filter controls are available in the monitoring panel.</p><button onClick={()=>{setLayers(defaults);setPage('Geographic Intelligence')}}>Reset view and return to map</button></div>}
        <GeoMap hubs={hubs}points={points}routes={routes}regions={regions}outline={outline}admin={admin}selected={current}layers={layers}onLayers={setLayers}onHub={onHub}onRegion={onRegion}onRoute={onRoute}onPoint={onRegion}/>
        <Timeline detail={selectedDetail}overview={overview}onFocusEvent={v=>{if(v)onHub(v)}}/>
        <div className="map-footer"><span>PHILIPPINES / WGS84</span><span>{busy?'LOADING ANALYTICS…':`${num(overview?.kpis.shipments)} SHIPMENTS · ${num(hubs.reduce((a,b)=>a+(b.shipments||0),0))} HUB ASSIGNMENTS`}</span></div>
      </main>
      {rightOpen&&<aside className="right-panel" aria-label="Contextual detail panel"><div className="detail-title"><div><span className="section-eyebrow">CONTEXTUAL ANALYSIS</span><h2>{infoTitle}</h2></div><button aria-label="Close details" className="icon-button" onClick={()=>setRightOpen(false)}><X size={17}/></button></div>
        {selectedDetail&&<><div className="detail-highlight"><div className="detail-emblem"><Package size={21}/></div><div><span className="section-eyebrow">TRACKING NUMBER</span><h2 className="mono">{current?.Shipment_ID}</h2><Status text={current?.Risk||'On Track'}/></div></div><div className="detail-block"><div className="compact-heading"><span>SHIPMENT DETAIL</span><small>RECORDED DATA</small></div><div className="detail-grid">{[['ORIGIN HUB',current?.Hub_Name],['DESTINATION',current?.Destination_City],['COURIER',current?.Courier_Name],['SERVICE',current?.Service_Type],['DISPATCH',fmt(current?.Dispatch_Date)],['SLA DEADLINE',fmt(current?.Expected_Delivery_Date)],['DELIVERED',fmt(current?.Actual_Delivery_Date)],['SHIPMENT STATUS',current?.Delivery_Status],['ATTEMPTS',String(current?.Delivery_Attempts)],['GEODESIC DISTANCE',`${num(current?.Distance_KM,1)} km`],['MODELED COST',php(current?.Shipping_Cost_PHP)]].map(([k,v])=><div key={k}><span>{k}</span><strong>{v||'—'}</strong></div>)}</div></div><div className="detail-block"><div className="compact-heading"><span>RECORDED EVENT HISTORY</span><small>{selectedDetail.events.length} EVENTS</small></div><div className="detail-events">{selectedDetail.events.map(e=><div className="detail-event" key={e.Event_ID}><i/><div><strong>{e.Event_Type}</strong><small>{e.Event_DateTime.replace('T',' ').slice(0,16)}</small><p>{e.Event_Description}</p></div></div>)}</div></div></>}
        {selectedHub&&<><div className="detail-highlight"><div className="detail-emblem"><MapPin size={21}/></div><div><span className="section-eyebrow">DISTRIBUTION FACILITY</span><h2>{selectedHub.hub.Hub_Name}</h2><span className="muted">{selectedHub.hub.City}, {selectedHub.hub.Region}</span></div></div><div className="detail-block"><div className="compact-heading"><span>HUB PERFORMANCE</span></div><div className="detail-grid">{[['ASSIGNED',num(selectedHub.kpis.shipments)],['DELIVERED',num(selectedHub.kpis.delivered)],['ON TIME',percentage(selectedHub.kpis.on_time_rate)],['LATE',num(selectedHub.late)],['AVG DAYS',num(selectedHub.kpis.avg_delivery_days,1)],['COST/SHIPMENT',php(selectedHub.kpis.avg_cost)]].map(([a,b])=><div key={a}><span>{a}</span><strong>{b}</strong></div>)}</div></div><div className="detail-block"><div className="compact-heading"><span>TOP DESTINATION REGIONS</span></div>{selectedHub.top_destinations.map(r=><div className="rank-row" key={r.Destination_Region}><span>{r.Destination_Region}</span><b>{num(r.shipments)}</b></div>)}</div></>}
        {selectedRoute&&<><div className="detail-highlight"><div className="detail-emblem"><RouteIcon size={21}/></div><div><span className="section-eyebrow">AGGREGATED CORRIDOR</span><h2>{selectedRoute.Hub_Name} → {selectedRoute.Destination_City}</h2></div></div><div className="detail-block"><div className="detail-grid">{[['SHIPMENTS',num(selectedRoute.shipments)],['SLA COMPLIANCE',percentage(selectedRoute.on_time_rate)],['AVG DAYS',num(selectedRoute.avg_days,1)],['AVG COST',php(selectedRoute.avg_cost)],['LATE SHIPMENTS',num(selectedRoute.late)],['REGION',selectedRoute.Destination_Region]].map(([k,v])=><div key={k}><span>{k}</span><strong>{v}</strong></div>)}</div><p className="explain">The displayed connection is a geographic relationship, not a recorded road or GPS route.</p></div></>}
        {selectedRegion&&<><div className="detail-highlight"><div className="detail-emblem"><MapPin size={21}/></div><div><span className="section-eyebrow">REGIONAL PERFORMANCE</span><h2>{selectedRegion.Destination_Region}</h2></div></div><div className="detail-block"><div className="detail-grid">{[['SHIPMENTS',num(selectedRegion.shipments)],['DELIVERED',num(selectedRegion.delivered)],['ON-TIME',percentage(selectedRegion.on_time_rate)],['FAILURE RATE',percentage(selectedRegion.failed_rate)],['AVG COST',php(selectedRegion.avg_cost)],['AVG DAYS',num(selectedRegion.avg_days,1)]].map(([k,v])=><div key={k}><span>{k}</span><strong>{v}</strong></div>)}</div></div></>}
        {!selectedDetail&&!selectedHub&&!selectedRoute&&!selectedRegion&&<><div className="detail-block"><div className="compact-heading"><span>DELIVERY STATUS COMPOSITION</span></div><MiniDonut values={overview?.statuses||[]}/></div><div className="detail-block"><div className="compact-heading"><span>MONTHLY SLA PERFORMANCE</span><small>DELIVERED ONLY</small></div>{overview&&<Trend overview={overview}/>}</div><div className="detail-block"><div className="compact-heading"><span>REGIONAL OPERATIONS</span><select aria-label="Regional ranking metric" value={metric} onChange={e=>setMetric(e.target.value)}><option value="on_time_rate">On-time %</option><option value="shipments">Shipments</option><option value="avg_cost">Avg Cost</option><option value="failed_rate">Failed %</option></select></div>{regions.slice().sort((a,b)=>((metric==='shipments'?b[metric as 'shipments']:a[metric as 'on_time_rate']||0)-(metric==='shipments'?a[metric as 'shipments']:b[metric as 'on_time_rate']||0))).map(r=><button className="rank-row" key={r.Destination_Region} onClick={()=>onRegion(r.Destination_Region)}><span>{r.Destination_Region}</span><b>{metric==='shipments'?num(r.shipments):metric==='avg_cost'?php(r.avg_cost):percentage(metric==='failed_rate'?r.failed_rate:r.on_time_rate)}</b></button>)}</div><div className="detail-block"><div className="compact-heading"><span>COURIER ATTENTION</span><small>LOWEST ON-TIME</small></div>{couriers.slice(0,4).map(c=><button className="rank-row" key={c.Courier_ID} onClick={()=>update('courier',c.Courier_ID)}><span>{c.Courier_Name}</span><b>{percentage(c.on_time_rate)}</b></button>)}</div></>}
        <div className="right-footnote"><Info size={14}/><span>All shipments, status histories, hubs and costs are synthetic. Data as of {filters.cutoff}.</span></div>
      </aside>}
    </div>
   </div>
   {!leftOpen&&<button className="reopen left" onClick={()=>setLeftOpen(true)} title="Open shipment monitor" aria-label="Open shipment monitor"><ChevronRight size={19}/></button>}
   {!rightOpen&&<button className="reopen right" onClick={()=>setRightOpen(true)} title="Open details" aria-label="Open details"><ChevronLeft size={19}/></button>}
   {busy&&<div className="loading-indicator" role="status">Updating operational analytics…</div>}
   {error&&<div className="error-banner" role="alert">{error}<button onClick={()=>setError('')} aria-label="Dismiss error"><X size={15}/></button></div>}
   {showRules&&<div className="dialog-backdrop" onClick={()=>setShowRules(false)}><section className="dialog" role="dialog" aria-modal="true" aria-label="Delivery risk classification rules" onClick={e=>e.stopPropagation()}><button className="dialog-close" onClick={()=>setShowRules(false)} aria-label="Close dialog"><X size={19}/></button><h2>Delivery risk methodology</h2><p>Risk classifications use only recorded events up to the selected reporting cutoff. They do not imply live vehicle positions or a real-time shipping feed.</p><dl><dt>Completed</dt><dd>Delivered on or before the SLA deadline.</dd><dt>Delayed</dt><dd>Delivered after the SLA deadline, or still unresolved after its deadline at the selected cutoff.</dd><dt>At Risk</dt><dd>Unresolved and the SLA deadline is today or tomorrow relative to the selected historical cutoff.</dd><dt>On Track</dt><dd>Unresolved with more than one calendar day remaining.</dd><dt>Failed</dt><dd>Recorded failure or return-to-sender outcome.</dd><dt>Cancelled</dt><dd>Recorded cancellation.</dd></dl><p>Success rate denominator: Delivered + Failed + Returned. On-time denominator: delivered shipments only. Same-day and other SLA rules are calendar days.</p></section></div>}
 </div>
}
