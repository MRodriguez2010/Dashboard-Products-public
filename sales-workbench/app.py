"""A fictional sales pipeline showing open value and probability-weighted value by stage."""
from pathlib import Path
import csv
from collections import defaultdict
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from html import escape

app=FastAPI(title="Sales Pipeline")
def read_pipeline():
    groups=defaultdict(lambda: {"deals":0,"open_value":0,"weighted_value":0})
    with Path(__file__).with_name("opportunities.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            value,probability=int(row["value"]),int(row["probability_pct"])
            if value<0 or not 0<=probability<=100:raise ValueError("Invalid opportunity")
            stage=groups[row["stage"]]
            stage["deals"]+=1;stage["open_value"]+=value;stage["weighted_value"]+=value*probability/100
    return [{"stage":k,**v} for k,v in groups.items()]

@app.get("/api/pipeline")
def pipeline():
    return read_pipeline()

@app.get("/",response_class=HTMLResponse)
def home():
    rows="".join(f"<tr><th>{escape(r['stage'])}</th><td>{r['deals']}</td><td>{r['open_value']:,}</td><td>{r['weighted_value']:,.0f}</td></tr>" for r in read_pipeline())
    return f"""<!doctype html><title>Sales pipeline</title><style>body{{font:18px system-ui;margin:8vh auto;max-width:55rem}}th,td{{padding:.8rem;text-align:left;border-bottom:1px solid #ccc}}</style>
    <h1>Sales pipeline</h1><p>Fictional opportunities. Weighted value is open value multiplied by the stated probability.</p>
    <table><tr><th>Stage</th><th>Deals</th><th>Open value ($)</th><th>Weighted value ($)</th></tr>{rows}</table>"""
