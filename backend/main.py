"""Analytics-backed, read-only FastAPI service for NexRoute's historic control tower.

Every endpoint uses a consistent historical reporting cutoff, date range and
filtered universe. No GPS positions or road paths are generated.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal
import json
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from src.database import read_shipments, read_table
from src.data_processing import prepare_shipments
from src.delivery_metrics import grouped_performance, overview

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = date(2025, 12, 31)
app = FastAPI(title="NexRoute Control Tower API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=False, allow_methods=["GET"], allow_headers=["*"])
TERMINAL = {"Delivered": "Delivered", "Failed Delivery": "Failed", "Returned to Sender": "Returned", "Order Cancelled": "Cancelled"}


class Filters(BaseModel):
    start: date = date(2024, 1, 1)
    end: date = CUTOFF
    cutoff: date = CUTOFF
    region: str | None = None
    courier: str | None = None
    status: str | None = None
    service: str | None = None


def args(start: date = date(2024, 1, 1), end: date = CUTOFF, cutoff: date = CUTOFF,
         region: str | None = None, courier: str | None = None,
         status: str | None = None, service: str | None = None) -> Filters:
    values = Filters(start=start, end=end, cutoff=cutoff, region=region, courier=courier, status=status, service=service)
    if values.start > values.end:
        raise HTTPException(422, "Start date must not be after end date")
    if values.cutoff > CUTOFF or values.cutoff < date(2024, 1, 1):
        raise HTTPException(422, "Reporting cutoff must be between 2024-01-01 and 2025-12-31")
    return values


@lru_cache(maxsize=1)
def sources():
    return read_shipments(), read_table("delivery_events"), read_table("hubs"), read_table("couriers")


@lru_cache(maxsize=16)
def snapshot(cutoff: date):
    """Reconstruct actual states from recorded events, not future final outcomes."""
    raw, events, *_ = sources()
    df = raw.copy()
    historical = events.loc[pd.to_datetime(events.Event_DateTime).dt.date.le(cutoff)]
    last = historical[historical.Event_Type.isin(TERMINAL)].drop_duplicates("Shipment_ID", keep="last")
    state = last.set_index("Shipment_ID").Event_Type.map(TERMINAL)
    df["Delivery_Status"] = df.Shipment_ID.map(state).fillna("In Transit")
    df.loc[~df.Delivery_Status.eq("Delivered"), "Actual_Delivery_Date"] = None
    return prepare_shipments(df)


def filtered(f: Filters) -> pd.DataFrame:
    df = snapshot(f.cutoff)
    date_end = min(f.end, f.cutoff)
    df = df.loc[df.Shipment_Date.dt.date.between(f.start, date_end)]
    for col, val in [("Destination_Region", f.region), ("Courier_ID", f.courier), ("Delivery_Status", f.status), ("Service_Type", f.service)]:
        if val:
            df = df.loc[df[col].eq(val)]
    return df.copy()


def jsonable(value):
    if isinstance(value, pd.DataFrame):
        return [jsonable(r) for r in value.to_dict(orient="records")]
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (pd.Timestamp, date)):
        return value.isoformat() if not pd.isna(value) else None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value) if np.isfinite(value) else None
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, (float,)) and (np.isnan(value) or not np.isfinite(value)):
        return None
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def risk(row, cutoff: date) -> str:
    status = row["Delivery_Status"]
    if status in ("Failed", "Returned"):
        return "Failed"
    if status == "Cancelled":
        return "Cancelled"
    if status == "Delivered":
        return "Completed" if row["On_Time"] else "Delayed"
    deadline = row["Expected_Delivery_Date"].date()
    if deadline < cutoff:
        return "Delayed"
    if deadline <= cutoff + pd.Timedelta(days=1):
        return "At Risk"
    return "On Track"


def row_detail(row, cutoff):
    d = row.to_dict() if isinstance(row, pd.Series) else dict(row)
    d["Risk"] = risk(d, cutoff)
    return jsonable(d)


@app.get("/api/health")
def health():
    try:
        count = len(sources()[0])
        return {"status": "ok", "shipments": count, "reporting_cutoff": str(CUTOFF)}
    except Exception as exc:
        raise HTTPException(503, f"Database not ready. Run python scripts/generate_data.py and python scripts/load_database.py. {exc}")


@app.get("/api/filters")
def filter_options():
    raw, _, hubs, couriers = sources()
    return {"regions": sorted(raw.Destination_Region.unique().tolist()),
            "statuses": ["Delivered", "Failed", "Returned", "In Transit", "Cancelled"],
            "services": sorted(raw.Service_Type.unique().tolist()),
            "couriers": jsonable(couriers[["Courier_ID", "Courier_Name"]].to_dict(orient="records")),
            "hubs": jsonable(hubs[["Hub_ID", "Hub_Name"]].to_dict(orient="records")),
            "cutoff": str(CUTOFF)}


@app.get("/api/overview")
def get_overview(start: date = date(2024, 1, 1), end: date = CUTOFF, cutoff: date = CUTOFF,
                 region: str | None = None, courier: str | None = None, status: str | None = None, service: str | None = None):
    f = args(start, end, cutoff, region, courier, status, service)
    df = filtered(f)
    k = overview(df)
    risks = df.apply(lambda row: risk(row, f.cutoff), axis=1) if len(df) else pd.Series([], dtype=str)
    by_status = df.Delivery_Status.value_counts()
    daily = df.groupby(df.Shipment_Date.dt.date).size().tail(40)
    completed = df[df.Delivered].groupby("Month").agg(on_time=("On_Time", "sum"), delivered=("Delivered", "sum"))
    completed["rate"] = 100 * completed.on_time / completed.delivered.where(completed.delivered.ne(0))
    return jsonable({"kpis": k, "active": int((df.Delivery_Status == "In Transit").sum()),
           "at_risk": int((risks == "At Risk").sum()), "delayed": int((risks == "Delayed").sum()),
           "failed": int((risks == "Failed").sum()), "statuses": [{"name": s, "count": int(n)} for s, n in by_status.items()],
           "volume_trend": [{"date": str(t), "count": int(n)} for t, n in daily.items()],
           "sla_trend": [{"date": str(t.date()), "rate": float(r.rate)} for t, r in completed.iterrows()]})


@app.get("/api/shipments")
def shipments(start: date = date(2024, 1, 1), end: date = CUTOFF, cutoff: date = CUTOFF,
             region: str | None = None, courier: str | None = None, status: str | None = None, service: str | None = None,
             search: str = "", sort: Literal["newest", "oldest", "deadline", "cost", "risk"] = "newest",
             page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)):
    f = args(start, end, cutoff, region, courier, status, service)
    df = filtered(f)
    if search:
        df = df.loc[df.Shipment_ID.str.contains(search.strip(), case=False, regex=False)]
    if sort == "risk":
        df = df.assign(_risk=df.apply(lambda row: {"Failed": 0, "Delayed": 1, "At Risk": 2, "On Track": 3, "Completed": 4, "Cancelled": 5}[risk(row, f.cutoff)], axis=1)).sort_values(["_risk", "Expected_Delivery_Date"])
    else:
        field = {"newest": "Shipment_Date", "oldest": "Shipment_Date", "deadline": "Expected_Delivery_Date", "cost": "Shipping_Cost_PHP"}[sort]
        df = df.sort_values(field, ascending=sort in ("oldest", "deadline"))
    total = len(df)
    result = df.iloc[(page-1)*page_size:page*page_size]
    fields = ["Shipment_ID", "Delivery_Status", "Shipment_Date", "Dispatch_Date", "Expected_Delivery_Date", "Actual_Delivery_Date", "Courier_ID", "Courier_Name", "Hub_Name", "Origin_Hub_ID", "Destination_Region", "Destination_City", "Service_Type", "Shipping_Cost_PHP", "Distance_KM", "Delivery_Attempts", "On_Time", "Origin_Latitude", "Origin_Longitude", "Destination_Latitude", "Destination_Longitude"]
    return {"total": total, "page": page, "page_size": page_size,
            "items": [row_detail(r, f.cutoff) for _, r in result[fields + ["Late"]].iterrows()]}


@app.get("/api/shipments/{shipment_id}")
def shipment_detail(shipment_id: str, cutoff: date = CUTOFF):
    f = args(cutoff=cutoff)
    df = snapshot(f.cutoff)
    selected = df.loc[df.Shipment_ID.eq(shipment_id)]
    if selected.empty or selected.iloc[0].Shipment_Date.date() > f.cutoff:
        raise HTTPException(404, "Shipment not present at this reporting cutoff")
    s = selected.iloc[0]
    events = sources()[1]
    e = events.loc[events.Shipment_ID.eq(shipment_id)].copy()
    e = e.loc[pd.to_datetime(e.Event_DateTime).dt.date.le(cutoff)].sort_values("Event_DateTime")
    ev = e.to_dict("records")
    return jsonable({"shipment": row_detail(s, f.cutoff), "events": ev,
       "milestones": {"recorded_event_count": len(ev), "terminal_event_recorded": s.Delivery_Status in ("Delivered", "Failed", "Returned", "Cancelled")},
       "notice": "Point-to-point line shows a geographic relationship, not a vehicle GPS trace or actual road route."})


@app.get("/api/hubs")
def hub_list(start: date = date(2024,1,1), end: date = CUTOFF, cutoff: date = CUTOFF, region: str | None = None,
             courier: str | None = None, status: str | None = None, service: str | None = None):
    df = filtered(args(start,end,cutoff,region,courier,status,service))
    hubs = sources()[2]
    summary = grouped_performance(df,"Origin_Hub_ID") if len(df) else pd.DataFrame()
    if len(summary):
        hubs = hubs.merge(summary,left_on="Hub_ID",right_on="Origin_Hub_ID",how="left")
    else:
        hubs = hubs.assign(shipments=0, delivered=0, late=0, avg_days=None, on_time_rate=None, avg_cost=None)
    return jsonable(hubs.fillna({"shipments": 0, "delivered":0,"late":0}).to_dict("records"))


@app.get("/api/hubs/{hub_id}")
def hub_detail(hub_id: str, start: date = date(2024,1,1), end: date = CUTOFF, cutoff: date = CUTOFF, region: str | None = None, courier: str | None = None, status: str | None = None, service: str | None = None):
    h = sources()[2]
    if hub_id not in set(h.Hub_ID):
        raise HTTPException(404,"Hub not found")
    df = filtered(args(start,end,cutoff,region,courier,status,service))
    part = df.loc[df.Origin_Hub_ID.eq(hub_id)]
    top = grouped_performance(part,"Destination_Region") if len(part) else pd.DataFrame()
    return jsonable({"hub": h.loc[h.Hub_ID.eq(hub_id)].iloc[0].to_dict(), "kpis": overview(part),
        "late": int(part.Late.sum()), "top_destinations": top.nlargest(5,"shipments").to_dict("records") if len(top) else []})


@app.get("/api/regions")
def regions(start: date = date(2024,1,1), end: date = CUTOFF, cutoff: date = CUTOFF, region: str | None = None, courier: str | None = None, status: str | None = None, service: str | None = None):
    df = filtered(args(start,end,cutoff,region,courier,status,service))
    if df.empty: return []
    g = grouped_performance(df,"Destination_Region")
    return jsonable(g.to_dict("records"))


@app.get("/api/destinations")
def destinations(start: date = date(2024,1,1), end: date = CUTOFF, cutoff: date = CUTOFF, region: str | None = None, courier: str | None = None, status: str | None = None, service: str | None = None):
    df = filtered(args(start,end,cutoff,region,courier,status,service))
    if df.empty: return []
    cols = ["Destination_Region", "Destination_Province", "Destination_City", "Destination_Latitude", "Destination_Longitude"]
    g = grouped_performance(df,cols)
    # Aggregated city centers only (24), not 26,000 individual point markers.
    return jsonable(g.to_dict("records"))


@app.get("/api/routes")
def routes(start: date = date(2024,1,1), end: date = CUTOFF, cutoff: date = CUTOFF, region: str | None = None, courier: str | None = None, status: str | None = None, service: str | None = None, limit: int = Query(80,ge=1,le=250)):
    df = filtered(args(start,end,cutoff,region,courier,status,service))
    if df.empty: return []
    group = ["Origin_Hub_ID", "Hub_Name", "Origin_Latitude", "Origin_Longitude", "Destination_Region", "Destination_City", "Destination_Latitude", "Destination_Longitude"]
    g = grouped_performance(df,group)
    return jsonable(g.nlargest(limit,"shipments").to_dict("records"))


@app.get("/api/courier-performance")
def courier_performance(start: date = date(2024,1,1), end: date = CUTOFF, cutoff: date = CUTOFF, region: str | None = None, courier: str | None = None, status: str | None = None, service: str | None = None, minimum: int = Query(20,ge=0)):
    df = filtered(args(start,end,cutoff,region,courier,status,service))
    if df.empty: return []
    g = grouped_performance(df,["Courier_ID", "Courier_Name", "Assigned_Region"])
    return jsonable(g[g.shipments.ge(minimum)].sort_values("on_time_rate").to_dict("records"))


@app.get("/api/sla-performance")
def sla_performance(start: date = date(2024,1,1), end: date = CUTOFF, cutoff: date = CUTOFF, region: str | None = None, courier: str | None = None, status: str | None = None, service: str | None = None):
    df = filtered(args(start,end,cutoff,region,courier,status,service))
    if df.empty: return []
    return jsonable(grouped_performance(df,["Destination_Region", "Service_Type"]).to_dict("records"))


@app.get("/api/geo/outline")
def boundary_outline():
    return json.loads((ROOT/"data/geo/philippines_outline.geojson").read_text())


@app.get("/api/geo/regions")
def boundary_regions():
    path = ROOT/"data/geo/philippines_adm1.geojson"
    if not path.exists():
        return {"type":"FeatureCollection","features":[],"available":False,
                "reason":"Validated administrative boundaries not bundled. Regional performance remains available as city aggregates."}
    return json.loads(path.read_text())
