import json
import os
import unittest
from datetime import datetime

from rfp_scanner import scoring, sources
from rfp_scanner.geo import Geocoder

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "..", "config.json")))
NOW = datetime(2026, 10, 22, 12, 0)
GEO = Geocoder()


def sam(**kw):
    rec = {
        "noticeId": "abc123", "title": "Roof Replacement, Building 12", "solicitationNumber": "W9126G26R0001",
        "fullParentPathName": "DEPT OF DEFENSE.DEPT OF THE ARMY", "postedDate": "2026-10-20",
        "type": "Combined Synopsis/Solicitation", "typeOfSetAside": "SBA",
        "typeOfSetAsideDescription": "Total Small Business Set-Aside (FAR 19.5)",
        "responseDeadLine": "2026-11-12T14:00:00-06:00", "naicsCode": "238160", "classificationCode": "Z2JZ",
        "placeOfPerformance": {"city": {"name": "Houston"}, "state": {"code": "TX"}, "zip": "77002"},
        "uiLink": "https://sam.gov/opp/abc123/view",
        "pointOfContact": [{"fullName": "Pat Buyer", "email": "pat@example.gov"}],
    }
    rec.update(kw)
    return scoring.evaluate(sources.sam_record_to_opp(rec), CFG, GEO, NOW)


class ScoringTests(unittest.TestCase):
    def test_houston_roofing_small_business_is_top_tier(self):
        o = sam()
        self.assertEqual(o["due"], "2026-11-12T20:00")
        self.assertTrue(o["tier"].startswith("Home turf"))
        self.assertLess(o["miles"], 30)
        self.assertGreaterEqual(o["fit"], 80)
        self.assertNotEqual(o["status"], "ineligible")
        self.assertTrue(any("SAM.gov registration" in f for f in o["flags"]))

    def test_set_aside_without_certification_is_ineligible(self):
        o = sam(typeOfSetAside="8A", typeOfSetAsideDescription="8(a) Set-Aside (FAR 19.8)")
        self.assertEqual(o["status"], "ineligible")
        self.assertTrue(any("8(a)" in r for r in o["ineligible_reasons"]))

    def test_out_of_area_is_ineligible_not_dropped(self):
        o = sam(placeOfPerformance={"city": {"name": "Denver"}, "state": {"code": "CO"}})
        self.assertEqual(o["status"], "ineligible")
        self.assertIn("Outside service area (CO)", o["ineligible_reasons"])

    def test_nearer_job_outranks_identical_farther_job(self):
        near = sam()
        far = sam(placeOfPerformance={"city": {"name": "El Paso"}, "state": {"code": "TX"}})
        self.assertGreater(near["priority"], far["priority"])
        self.assertEqual(far["status"], near["status"])

    def test_texas_mold_needs_license(self):
        o = sam(title="Mold Remediation at Clinic", naicsCode="562910")
        self.assertTrue(any(f.startswith("Texas mold") for f in o["flags"]))
        self.assertEqual(o["status"], "check")

    def test_passed_deadline_and_award_notice(self):
        self.assertIn("Deadline passed", sam(responseDeadLine="2026-10-01T10:00:00-05:00")["ineligible_reasons"])
        self.assertEqual(sam(type="Award Notice")["status"], "ineligible")

    def test_off_scope_scores_low(self):
        o = sam(title="Laboratory equipment purchase", naicsCode="334516", classificationCode="6640")
        self.assertLess(o["fit"], CFG["scoring"]["min_fit_to_list"])


class ProfileTests(unittest.TestCase):
    def test_company_file_unlocks_set_aside_and_license(self):
        from rfp_scanner.scan import apply_profile
        cfg = json.loads(json.dumps(CFG))
        apply_profile(cfg, {"scanner": {"certifications_held": ["SB", "TX-HUB", "WOSB"], "sam_registered": True,
                                        "licenses_held": ["TDLR-MOLD-REMEDIATION"], "max_miles": 300}})
        rec = sources.sam_record_to_opp({"noticeId": "x", "title": "Mold Remediation, Clinic", "naicsCode": "562910",
                                         "type": "Solicitation", "typeOfSetAside": "WOSB", "responseDeadLine": "2026-11-20",
                                         "placeOfPerformance": {"city": {"name": "El Paso"}, "state": {"code": "TX"}}})
        o = scoring.evaluate(rec, cfg, GEO, NOW)
        self.assertEqual(o["status"], "eligible")
        self.assertFalse(any(f.startswith(("Texas mold", "Federal award")) for f in o["flags"]))
        self.assertTrue(any("travel limit" in f for f in o["flags"]))


class SourceTests(unittest.TestCase):
    def test_parse_dates(self):
        self.assertEqual(sources.parse_date("12/08/2026"), "2026-12-08")
        self.assertEqual(sources.parse_date("2026-11-12T14:00:00-05:00"), "2026-11-12T19:00")
        self.assertEqual(sources.parse_date("November 3, 2026"), "2026-11-03")
        self.assertIsNone(sources.parse_date("TBD"))

    def test_rss_feed(self):
        xml = b"""<rss><channel><item><title>Custodial Services for City Hall</title>
        <link>https://example.gov/bids/1</link><pubDate>Mon, 19 Oct 2026 09:00:00 -0500</pubDate>
        <description>&lt;p&gt;Closing Date: 11/20/2026 2:00 PM&lt;/p&gt;</description></item></channel></rss>"""
        feed = {"name": "City of Tomball", "url": "https://example.gov/rss", "city": "Tomball", "state": "TX"}
        [o] = sources.parse_feed(xml, feed)
        self.assertEqual(o["due"], "2026-11-20")
        o = scoring.evaluate(o, CFG, GEO, NOW)
        self.assertTrue(o["tier"].startswith("Home turf"))
        self.assertGreaterEqual(o["fit"], CFG["scoring"]["min_fit_to_list"])

    def test_csv_import(self):
        path = os.path.join(HERE, "..", "..", "imports", "web-research-leads-2026-10-22.csv")
        rows = sources.parse_csv_file(path)
        self.assertTrue(rows)
        self.assertTrue(all(r["title"] for r in rows))
        region2 = [r for r in rows if "Region 2" in (r["agency"] or "")][0]
        self.assertEqual(region2["due"], "2026-12-08")
        self.assertEqual(region2["city"], "Corpus Christi")


if __name__ == "__main__":
    unittest.main()
