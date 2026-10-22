"""Opportunity sources. Each returns a list of normalized opportunity dicts:

id, source, title, agency, number, type, posted, due, naics, psc, set_aside_code,
set_aside, city, state, zip, lat, lon, url, description, contact
"""
import csv
import glob
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

USER_AGENT = "UnitedCCR-RFP-Scanner/1.0"
SAM_URL = "https://api.sam.gov/opportunities/v2/search"


def _blank(**kw):
    o = dict.fromkeys(["id", "source", "title", "agency", "number", "type", "posted", "due", "naics", "psc",
                       "set_aside_code", "set_aside", "city", "state", "zip", "lat", "lon", "url",
                       "description", "contact"])
    o.update(kw)
    return o


def _stable_id(*parts):
    return hashlib.sha1("|".join(str(p or "") for p in parts).encode()).hexdigest()[:16]


_DATE_FORMATS = ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %I:%M %p",
                 "%m/%d/%Y %H:%M", "%m/%d/%Y", "%m/%d/%y", "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                 "%B %d, %Y", "%b %d, %Y"]


def parse_date(value):
    """Parse the date formats seen on procurement sites into an ISO string (UTC when zoned)."""
    if not value:
        return None
    s = str(value).strip()
    s = re.sub(r"\s+(CST|CDT|EST|EDT|MST|MDT|PST|PDT|CT|ET)$", "", s)
    s = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", s)
    for fmt in _DATE_FORMATS:
        try:
            d = datetime.strptime(s, fmt)
        except ValueError:
            continue
        if d.tzinfo:
            d = d.astimezone(timezone.utc).replace(tzinfo=None)
        if not any(c in fmt for c in "HI"):
            return d.date().isoformat()  # date only: treated as end of that day
        return d.isoformat(timespec="minutes")
    return None


def _get_json(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


# ---------------------------------------------------------------- SAM.gov

def sam_record_to_opp(r):
    pop = r.get("placeOfPerformance") or {}
    office = r.get("officeAddress") or {}
    city = (pop.get("city") or {}).get("name") or office.get("city")
    state = (pop.get("state") or {}).get("code") or office.get("state")
    zip_code = pop.get("zip") or office.get("zipcode")
    contacts = r.get("pointOfContact") or []
    contact = None
    if contacts:
        c = contacts[0]
        contact = ", ".join(x for x in [c.get("fullName"), c.get("email"), c.get("phone")] if x)
    agency = (r.get("fullParentPathName") or "").replace(".", " / ")
    return _blank(
        id="sam-" + (r.get("noticeId") or _stable_id(r.get("title"), r.get("solicitationNumber"))),
        source="SAM.gov",
        title=(r.get("title") or "").strip(),
        agency=agency,
        number=r.get("solicitationNumber"),
        type=r.get("type") or r.get("baseType"),
        posted=parse_date(r.get("postedDate")),
        due=parse_date(r.get("responseDeadLine")),
        naics=r.get("naicsCode"),
        psc=r.get("classificationCode"),
        set_aside_code=r.get("typeOfSetAside") or None,
        set_aside=r.get("typeOfSetAsideDescription") or None,
        city=city, state=state, zip=zip_code,
        url=r.get("uiLink"),
        description=None,
        contact=contact,
    )


def fetch_sam(cfg, naics_codes, first_run, log=print):
    key = os.environ.get(cfg.get("api_key_env", "SAM_API_KEY"))
    if not key:
        log("SAM.gov: skipped (no API key in $%s)" % cfg.get("api_key_env", "SAM_API_KEY"))
        return []
    days = cfg["first_run_lookback_days"] if first_run else cfg["lookback_days"]
    today = datetime.now()
    params_base = {
        "api_key": key,
        "postedFrom": (today - timedelta(days=days)).strftime("%m/%d/%Y"),
        "postedTo": today.strftime("%m/%d/%Y"),
        "ptype": cfg.get("notice_types", "o,k,p,r"),
        "limit": 1000,
    }
    out, requests = [], 0
    for code in naics_codes:
        if requests >= cfg.get("max_requests_per_run", 9):
            log("SAM.gov: request budget reached, remaining NAICS codes deferred")
            break
        params = dict(params_base, ncode=code)
        try:
            data = _get_json(SAM_URL + "?" + urllib.parse.urlencode(params))
        except Exception as e:  # keep the run alive; one bad call should not lose the others
            log("SAM.gov NAICS %s: %s" % (code, e))
            requests += 1
            continue
        requests += 1
        recs = data.get("opportunitiesData") or []
        log("SAM.gov NAICS %s: %d notices" % (code, len(recs)))
        out.extend(sam_record_to_opp(r) for r in recs)
    return out


# ---------------------------------------------------------------- RSS / Atom bid feeds

_DUE_HINT = re.compile(
    r"(?:clos(?:es|ing)|due|deadline|opening|submittal|responses?)(?:\s+(?:date|by|on))?[^0-9A-Za-z]{0,20}"
    r"(\d{1,2}/\d{1,2}/\d{2,4}|[A-Z][a-z]+ \d{1,2}, \d{4})", re.I)


def parse_feed(xml_text, feed):
    root = ET.fromstring(xml_text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item") or root.findall(".//a:entry", ns)
    out = []
    for it in items:
        def t(tag):
            el = it.find(tag)
            if el is None:
                el = it.find("a:" + tag, ns)
            return (el.text or "").strip() if el is not None and el.text else ""
        link = t("link")
        if not link:
            el = it.find("a:link", ns)
            link = el.get("href") if el is not None else ""
        title = t("title")
        desc = re.sub(r"<[^>]+>", " ", t("description") or t("summary") or t("content"))
        desc = re.sub(r"\s+", " ", desc).strip()
        m = _DUE_HINT.search(desc) or _DUE_HINT.search(title)
        out.append(_blank(
            id="rss-" + _stable_id(feed["url"], link, title),
            source=feed.get("name") or "RSS",
            title=title,
            agency=feed.get("agency"),
            type="Bid posting",
            posted=parse_date(t("pubDate") or t("published") or t("updated")),
            due=parse_date(m.group(1)) if m else None,
            city=feed.get("city"), state=feed.get("state"), zip=feed.get("zip"),
            lat=feed.get("lat"), lon=feed.get("lon"),
            url=link,
            description=desc[:1500],
        ))
    return out


def fetch_rss(feeds, log=print):
    out = []
    for feed in feeds:
        try:
            req = urllib.request.Request(feed["url"], headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                items = parse_feed(r.read(), feed)
            log("%s: %d items" % (feed.get("name"), len(items)))
            out.extend(items)
        except Exception as e:
            log("%s: %s" % (feed.get("name"), e))
    return out


# ---------------------------------------------------------------- CSV exports (ESBD, BidNet, co-ops, manual)

CSV_ALIASES = {
    "title": ["title", "solicitation title", "solicitation name", "bid title", "project name", "name", "description"],
    "number": ["solicitation id", "solicitation number", "solicitation #", "bid number", "bid #", "number", "rfp number"],
    "agency": ["agency", "agency name", "issuing agency", "organization", "entity", "buyer"],
    "due": ["due date", "response due date", "closing date", "close date", "bid due", "deadline", "due"],
    "posted": ["posted date", "post date", "posting date", "issue date", "posted"],
    "city": ["city", "place of performance city", "location city"],
    "state": ["state", "place of performance state", "location state"],
    "zip": ["zip", "zip code", "postal code"],
    "url": ["url", "link", "solicitation url", "web link"],
    "naics": ["naics", "naics code"],
    "type": ["type", "notice type", "solicitation type"],
    "set_aside": ["set aside", "set-aside", "set aside type"],
    "description": ["details", "summary", "scope", "notes"],
}


def _norm(h):
    return re.sub(r"\s+", " ", (h or "").strip().lower())


def parse_csv_file(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = {_norm(h): h for h in reader.fieldnames or []}
        mapping = {}
        for field, aliases in CSV_ALIASES.items():
            for a in aliases:
                if a in cols and cols[a] not in mapping.values():
                    mapping[field] = cols[a]
                    break
        out = []
        name = os.path.splitext(os.path.basename(path))[0]
        for row in reader:
            v = {k: (row.get(src) or "").strip() for k, src in mapping.items()}
            if not v.get("title"):
                continue
            out.append(_blank(
                id="csv-" + _stable_id(name, v.get("number"), v.get("title")),
                source="Import: " + name,
                title=v.get("title"), number=v.get("number") or None, agency=v.get("agency") or None,
                due=parse_date(v.get("due")), posted=parse_date(v.get("posted")),
                city=v.get("city") or None, state=(v.get("state") or "").upper()[:2] or None, zip=v.get("zip") or None,
                url=v.get("url") or None, naics=v.get("naics") or None, type=v.get("type") or "Imported",
                set_aside=v.get("set_aside") or None, description=v.get("description") or None,
            ))
        return out


def fetch_csv(directory, log=print):
    out = []
    for path in sorted(glob.glob(os.path.join(directory, "*.csv"))):
        try:
            rows = parse_csv_file(path)
            log("%s: %d rows" % (os.path.basename(path), len(rows)))
            out.extend(rows)
        except Exception as e:
            log("%s: %s" % (path, e))
    return out
