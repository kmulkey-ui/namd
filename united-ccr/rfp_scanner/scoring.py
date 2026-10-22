"""Eligibility, fit, proximity and priority for each opportunity."""
import re
from datetime import datetime, timezone

from .geo import haversine_miles

# SAM.gov set-aside codes -> certification needed to bid.
SET_ASIDE_CERT = {
    "SBA": "SB", "SBP": "SB",
    "8A": "8A", "8AN": "8A",
    "HZC": "HZ", "HZS": "HZ",
    "SDVOSBC": "SDVOSB", "SDVOSBS": "SDVOSB",
    "WOSB": "WOSB", "WOSBSS": "WOSB",
    "EDWOSB": "EDWOSB", "EDWOSBSS": "EDWOSB",
    "VSA": "VOSB", "VSS": "VOSB",
    "ISBEE": "ISBEE", "IEE": "ISBEE", "BICIV": "ISBEE",
}
# Holding one certification also satisfies these set-asides.
IMPLIES = {"EDWOSB": {"WOSB"}, "SDVOSB": {"VOSB"}, "8A": {"SB"}, "HZ": {"SB"}, "WOSB": {"SB"},
           "VOSB": {"SB"}}
CERT_ALIAS = {"HZC": "HZ", "HZS": "HZ", "HUBZONE": "HZ", "8AN": "8A", "SDVOSBC": "SDVOSB", "SDVOSBS": "SDVOSB",
              "WOSBSS": "WOSB", "EDWOSBSS": "EDWOSB", "VSA": "VOSB", "VSS": "VOSB"}
# Free-text set-aside descriptions (CSV imports, RSS) -> certification.
SET_ASIDE_TEXT = [
    (r"8\s*\(a\)", "8A"), (r"hubzone", "HZ"), (r"service[- ]disabled", "SDVOSB"),
    (r"economically disadvantaged wom", "EDWOSB"), (r"wom[ae]n[- ]owned|wosb", "WOSB"),
    (r"veteran[- ]owned", "VOSB"), (r"indian|isbee", "ISBEE"), (r"small business", "SB"),
]
EXCLUDED_TYPES = re.compile(r"award notice|justification|sale of surplus|intent to bundle|bundle", re.I)
EARLY_TYPES = re.compile(r"presolicitation|sources sought|request for information|\brfi\b|forecast", re.I)


def _held_certs(company):
    held = set()
    for c in company.get("certifications_held", []):
        c = CERT_ALIAS.get(c.upper(), c.upper())
        held.add(c)
    frontier = list(held)
    while frontier:
        for implied in IMPLIES.get(frontier.pop(), ()):
            if implied not in held:
                held.add(implied)
                frontier.append(implied)
    return held


def required_cert(opp):
    code = (opp.get("set_aside_code") or "").upper()
    if code and code != "NONE":
        return SET_ASIDE_CERT.get(code)
    text = (opp.get("set_aside") or "").lower()
    if not text or "none" in text or "full and open" in text or "unrestricted" in text:
        return None
    for pattern, cert in SET_ASIDE_TEXT:
        if re.search(pattern, text):
            return cert
    return None


def _contains(text, phrase):
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", text) is not None


def fit_score(opp, cfg):
    text = " ".join(filter(None, [opp.get("title"), opp.get("description")])).lower()
    naics = str(opp.get("naics") or "")
    psc = str(opp.get("psc") or "").upper()
    score, why = 0, []
    if naics in cfg["naics"]["primary"]:
        score += 45
        why.append("Primary NAICS " + naics)
    elif naics in cfg["naics"]["secondary"]:
        score += 30
        why.append("Secondary NAICS " + naics)
    if psc and any(psc.startswith(p) for p in cfg.get("psc_prefixes", [])):
        score += 15
        why.append("Facility service code " + psc)
    strong = [k for k in cfg["keywords"]["strong"] if _contains(text, k)]
    moderate = [k for k in cfg["keywords"]["moderate"] if _contains(text, k) and not any(k in s for s in strong)]
    score += (min(45, 15 + 15 * len(strong)) if strong else 0) + min(24, 8 * len(moderate))
    if strong:
        why.append("Matches: " + ", ".join(strong[:4]))
    elif moderate:
        why.append("Related: " + ", ".join(moderate[:4]))
    sectors = [k for k in cfg["company"].get("client_sectors", []) if _contains(text, k)]
    if sectors and score:
        score += 10
        why.append("Sector United CCR already serves: " + ", ".join(sectors[:2]))
    negative = [k for k in cfg["keywords"]["negative"] if _contains(text, k)]
    if negative:
        score -= 40
        why.append("Off-scope terms: " + ", ".join(negative[:3]))
    return max(0, min(100, score)), why


def due_datetime(value):
    """Deadline as a naive UTC datetime; a bare date means the end of that day."""
    d = datetime.fromisoformat(value)
    return d.replace(hour=23, minute=59) if len(value) == 10 else d


def time_score(days_left):
    if days_left is None:
        return 60
    if days_left < 3:
        return 20
    if days_left < 7:
        return 60
    if days_left <= 30:
        return 100
    return 85


def tier_for(miles, cfg):
    if miles is None:
        return "Location unconfirmed"
    for t in cfg["service_area"]["tiers"]:
        if miles <= t["max_miles"]:
            return t["name"]
    return cfg["service_area"]["tiers"][-1]["name"]


def evaluate(opp, cfg, geocoder, now=None):
    """Annotate opp in place with eligibility, flags, distance, and scores. Returns opp."""
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    company = cfg["company"]
    states = set(cfg["service_area"]["states"])
    held = _held_certs(company)
    licenses = set(company.get("licenses_held", []))
    text = " ".join(filter(None, [opp.get("title"), opp.get("description")])).lower()
    state = (opp.get("state") or "").upper() or None
    reasons, flags = [], []

    # Location and distance.
    point, precision = geocoder.locate(opp.get("city"), state, opp.get("zip"), opp.get("lat"), opp.get("lon"))
    miles = round(haversine_miles((company["hq"]["lat"], company["hq"]["lon"]), point)) if point else None
    opp["miles"] = miles
    opp["point"] = [round(point[0], 4), round(point[1], 4)] if point else None
    opp["geo_precision"] = precision
    if state and state not in states:
        reasons.append("Outside service area (%s)" % state)
    if not state:
        flags.append("Place of performance not stated; confirm it is in the service area")
    elif precision is None:
        flags.append("City not stated or not recognized; distance unknown")
    elif precision == "state":
        flags.append("Distance approximate (measured to the state's center)")

    # Notice type.
    ntype = opp.get("type") or ""
    if EXCLUDED_TYPES.search(ntype):
        reasons.append("Notice type is not biddable (%s)" % ntype)
    if EARLY_TYPES.search(ntype):
        flags.append("Early-stage notice: a capability response now can shape the set-aside and scope")

    # Set-aside.
    cert = required_cert(opp)
    if cert and cert not in held:
        reasons.append("Set-aside requires %s certification" % (opp.get("set_aside") or cert))
    elif cert:
        flags.append("Set-aside United CCR qualifies for: " + (opp.get("set_aside") or cert))

    # Deadline.
    days_left = None
    if opp.get("due"):
        due = due_datetime(opp["due"])
        days_left = round((due - now).total_seconds() / 86400, 1)
        if days_left < 0:
            reasons.append("Deadline passed")
        elif days_left < 3:
            flags.append("Due in under 3 days")
    opp["days_left"] = days_left

    # Requirement gates worth a human check.
    if state == "TX" and re.search(r"\bmold\b", text) and "TDLR-MOLD-REMEDIATION" not in licenses:
        flags.append("Texas mold remediation requires a TDLR-licensed remediation contractor")
    if opp.get("source") == "SAM.gov" and not company.get("sam_registered"):
        flags.append("Federal award requires an active SAM.gov registration (UEI); start it now, it takes weeks")
    if re.search(r"\bbond(s|ing|ed)?\b", text):
        flags.append("Bonding required; confirm bid/performance bond capacity")
    if re.search(r"mandatory (pre-?bid|pre-?proposal|site visit|walk)", text):
        flags.append("Mandatory pre-bid meeting or site visit")

    fit, why = fit_score(opp, cfg)
    sa = cfg["service_area"]
    proximity = 40 if miles is None else max(0, round(100 * (1 - miles / sa["proximity_zero_at_miles"])))
    w = cfg["scoring"]["weights"]
    priority = round(w["fit"] * fit + w["proximity"] * proximity + w["time"] * time_score(days_left))

    blocking = [f for f in flags if f.startswith(("Texas mold", "Place of performance", "Bonding", "Federal award"))]
    opp.update(
        fit=fit, fit_reasons=why, proximity=proximity, priority=priority,
        tier=tier_for(miles, cfg),
        status="ineligible" if reasons else ("check" if blocking else "eligible"),
        ineligible_reasons=reasons, flags=flags,
    )
    return opp
