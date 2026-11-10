"""Aggregate counts from the bundled, fictional survey fixture."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANIES = ("Alder Works", "Birch Studio", "Cedar Group")
PERIODS = ("2026 Q1", "2026 Q2", "2026 Q3")
TOPICS = ("Role clarity", "Manager support", "Growth opportunities", "Workload")
TIERS = ("Benchmark", "Full")


def load_rows():
    with (ROOT / "examples" / "synthetic-responses.csv").open(encoding="utf-8", newline="") as source:
        return [
            {**row, "favorable": int(row["favorable"]), "responses": int(row["responses"])}
            for row in csv.DictReader(source)
        ]


def score(rows):
    favorable = sum(row["favorable"] for row in rows)
    total = sum(row["responses"] for row in rows)
    return {"favorable": favorable, "responses": total, "pct": round(100 * favorable / total, 1)}


def analyze(company, peers, start, end, tier):
    if company not in COMPANIES or tier not in TIERS:
        raise ValueError("Choose a listed company and report type.")
    if not isinstance(peers, list) or not peers or len(set(peers)) != len(peers) or any(p not in COMPANIES or p == company for p in peers):
        raise ValueError("Select one or more distinct peer companies, excluding the focus company.")
    if start not in PERIODS or end not in PERIODS or start > end:
        raise ValueError("Choose a valid quarter range.")
    selected = [r for r in load_rows() if start <= r["quarter"] <= end]
    focus = [r for r in selected if r["company"] == company]
    pool = [r for r in selected if r["company"] in peers]
    topics = []
    for topic in TOPICS:
        a = score([r for r in focus if r["topic"] == topic])
        b = score([r for r in pool if r["topic"] == topic])
        gap = round(100 * (a["favorable"] / a["responses"] - b["favorable"] / b["responses"]), 1)
        topics.append({"topic": topic, "focus": a, "peers": b, "gap": gap})
    trend = []
    for q in PERIODS:
        if start <= q <= end:
            trend.append({"quarter": q, "focus": score([r for r in focus if r["quarter"] == q]),
                          "peers": score([r for r in pool if r["quarter"] == q])})
    return {"company": company, "peers": peers, "start": start, "end": end, "tier": tier,
            "focus": score(focus), "pool": score(pool), "topics": topics, "trend": trend}


def finding(report):
    topic = max(report["topics"], key=lambda t: abs(t["gap"]))
    amount = abs(topic["gap"])
    if not amount:
        return "All four topics match the pooled peer result."
    direction = "above" if topic["gap"] > 0 else "below"
    verb = "are" if topic["topic"] == "Growth opportunities" else "is"
    return f"{topic['topic']} {verb} {amount:.1f} points {direction} peers."
