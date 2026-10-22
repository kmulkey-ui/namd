"""Run a scan: pull every source, merge into the running store, score, and write outputs.

    python -m rfp_scanner.scan            (from the united-ccr/ directory)

Outputs:
    data/opportunities.json   the running store (kept between runs so older notices stay until their deadline)
    docs/index.html           the RFP Radar dashboard with the latest results embedded
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

from . import sources
from .geo import Geocoder
from .scoring import due_datetime, evaluate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STALE_WITHOUT_DUE_DAYS = 60


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def merge(store, fresh, now):
    by_id = {o["id"]: o for o in store}
    stamp = now.isoformat(timespec="minutes")
    for o in fresh:
        prev = by_id.get(o["id"])
        o["first_seen"] = prev.get("first_seen", stamp) if prev else stamp
        o["last_seen"] = stamp
        by_id[o["id"]] = o
    return list(by_id.values())


def prune(opps, now):
    keep = []
    for o in opps:
        if o.get("due"):
            if due_datetime(o["due"]) < now:
                continue
        elif datetime.fromisoformat(o.get("first_seen") or now.isoformat()) < now - timedelta(days=STALE_WITHOUT_DUE_DAYS):
            continue
        keep.append(o)
    return keep


def render_dashboard(payload, template_path, out_path):
    with open(template_path, encoding="utf-8") as f:
        body = f.read()
    data = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    body = body.replace("/*__RFP_DATA__*/null", data, 1)
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            "</head><body>" + body + "</body></html>")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


def apply_profile(cfg, profile):
    """Overlay what Cody entered in the company file (exported as portfolio/profile.json)."""
    o = (profile or {}).get("scanner") or {}
    company = cfg["company"]
    for key in ("certifications_held", "licenses_held", "sam_registered"):
        if key in o:
            company[key] = o[key]
    if o.get("service_states"):
        cfg["service_area"]["states"] = o["service_states"]
    if o.get("max_miles"):
        company["max_miles"] = o["max_miles"]
    return cfg


def run(config_path, now=None, extra=None, log=print):
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    cfg = load_json(config_path, None)
    profile = load_json(os.path.join(ROOT, "portfolio", "profile.json"), None)
    if profile:
        apply_profile(cfg, profile)
        log("Company file applied (exported %s)" % profile.get("exported_at", "?"))
    store_path = os.path.join(ROOT, "data", "opportunities.json")
    previous = load_json(store_path, None)
    first_run = previous is None
    src = cfg["sources"]

    fresh, ran = [], []
    sam = src.get("sam_gov", {})
    if sam.get("enabled"):
        # Primary codes every run; secondary codes rotate through whatever request budget is left.
        secondary = cfg["naics"]["secondary"]
        shift = now.toordinal() % len(secondary) if secondary else 0
        codes = cfg["naics"]["primary"] + secondary[shift:] + secondary[:shift]
        fresh += sources.fetch_sam(sam, codes, first_run, log)
        has_key = os.environ.get(sam.get("api_key_env", "SAM_API_KEY"))
        ran.append("SAM.gov" if has_key else "SAM.gov (skipped: no API key)")
    if src.get("rss_feeds"):
        fresh += sources.fetch_rss(src["rss_feeds"], log)
        ran.append("%d RSS feeds" % len(src["rss_feeds"]))
    imports = os.path.join(ROOT, src.get("csv_imports_dir", "imports"))
    if os.path.isdir(imports):
        fresh += sources.fetch_csv(imports, log)
        ran.append("CSV imports")
    fresh += extra or []

    opps = merge((previous or {}).get("opportunities", []), fresh, now)
    geocoder = Geocoder(os.path.join(ROOT, "data", "geo"))
    for o in opps:
        evaluate(o, cfg, geocoder, now)
    opps = [o for o in prune(opps, now) if o["fit"] >= cfg["scoring"]["min_fit_to_list"]]
    opps.sort(key=lambda o: (o["status"] == "ineligible", -o["priority"]))

    counts = {s: sum(o["status"] == s for o in opps) for s in ("eligible", "check", "ineligible")}
    payload = {
        "generated_at": now.isoformat(timespec="minutes") + "Z",
        "hq": cfg["company"]["hq"],
        "service_states": cfg["service_area"]["states"],
        "sources_run": ran,
        "counts": counts,
        "opportunities": opps,
    }
    os.makedirs(os.path.dirname(store_path), exist_ok=True)
    with open(store_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    render_dashboard(payload, os.path.join(ROOT, "rfp_scanner", "dashboard.html"),
                     os.path.join(ROOT, "docs", "index.html"))
    log("Listed %d opportunities: %s" % (len(opps), counts))
    return payload


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default=os.path.join(ROOT, "rfp_scanner", "config.json"))
    args = p.parse_args(argv)
    run(args.config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
