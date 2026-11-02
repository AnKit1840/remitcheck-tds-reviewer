import json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from remitcheck.core import FACT_KEYS
from remitcheck.llm import OpenRouterReader
from remitcheck.pipeline import ESCALATE, READY, run_case
from remitcheck.core import load_yaml
from remitcheck.verify import locate

CONTRACT = "Customer may access the Acme platform online for internal use. It gets no right to copy the platform. Fee: USD 10,000."
INVOICE = "Invoice 1. Total USD 10,000."
INTAKE = dict(payee="Acme", amount=10000, currency="USD", fx_rate="88", payee_country="US", payee_type="company",
              remittance_date="2026-11-15", credit_date="2026-10-31", ytd_taxable_inr=0, trc_from="2026-01-01",
              trc_to="2026-12-31", treaty_form_filed=True, beneficial_owner_declared=True, no_pe_declared=True,
              alt_details_furnished=True, payee_income_band="up_to_1cr")


def good():
    f = {k: {"value": "silent", "quote": ""} for k in FACT_KEYS}
    f["software_access_only"] = {"value": "yes", "quote": "may access the Acme platform online"}
    f["copyright_rights_granted"] = {"value": "no", "quote": "no right to copy the platform"}
    return {"facts": f, "proposed_category": "BUSINESS_PROFITS_NO_PE", "citations": ["KONY_DHC"], "reasoning": "x",
            "contract_amount": {"value": "10000", "quote": "USD 10,000"}, "invoice_amount": {"value": "10000", "quote": "USD 10,000"}}


class Fixed:
    def __init__(self, o, error=None):
        self.o, self.error = o, error

    def read(self, *_):
        return {"output": self.o, "error": self.error, "meta": {"reader": "fixed"}}


def run(o, as_of="2026-11-03", rules=None, **intake):
    return run_case(CONTRACT, INVOICE, {**INTAKE, **intake}, Fixed(o), as_of, rules=rules)


def codes(t):
    return [e["code"] for e in t["escalations"]]


def test_clean_output_reaches_ca_not_approval():
    t = run(good())
    assert t["status"] == READY and t["tax"]["tds_inr"] == "0" and "Not tax advice" in t["disclaimer"]


def test_invented_quote_blocked():
    o = good(); o["facts"]["software_access_only"]["quote"] = "payment is for a plain subscription only"
    assert "UNVERIFIED_QUOTE" in codes(run(o))


def test_invented_citation_blocked():
    o = good(); o["citations"] = ["SC_FAKE_2030"]
    assert "UNKNOWN_CITATION" in codes(run(o))


def test_model_and_table_must_agree():
    o = good(); o["proposed_category"] = "ROYALTY"
    assert "TWO_KEY_DISAGREEMENT" in codes(run(o))


def test_malformed_output_blocked():
    assert "READER_FAILED" in codes(run({"facts": {}}))
    assert "READER_FAILED" in codes(run(None))


def test_amount_conflict_blocked():
    assert "AMOUNT_CONFLICT" in codes(run(good(), amount=12000))


def test_stale_rules_fail_closed():
    assert "RULE_PACK_STALE" in codes(run(good(), as_of="2027-04-01"))


def test_date_before_coverage():
    assert "NO_RULE_FOR_DATE" in codes(run(good(), remittance_date="2022-01-10", credit_date="2022-01-10"))


def test_other_country_out_of_scope():
    assert "OUT_OF_SCOPE_PAYEE" in codes(run(good(), payee_country="DE"))


def test_rate_change_is_data_only():
    rules = load_yaml("rules.yaml")
    rules["rates"]["treaty_royalty_pct"]["value"] = "12"
    o = good(); o["facts"]["copyright_rights_granted"] = {"value": "yes", "quote": "no right to copy the platform"}
    o["proposed_category"] = "ROYALTY"
    assert run(o, rules=rules)["tax"]["effective_rate_pct"] == "12"


def test_whitespace_tolerant_but_exact():
    assert locate("may  access\nthe Acme", CONTRACT)
    assert not locate("may access an Acme", CONTRACT)


def test_openrouter_client_parses_and_retries():
    calls = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            calls.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            if len(calls) == 1:
                self.send_response(429); self.end_headers(); return
            body = json.dumps({"model": "served/x", "choices": [{"message": {"content": "```json\n" + json.dumps(good()) + "\n```"}}]}).encode()
            self.send_response(200); self.end_headers(); self.wfile.write(body)

        def log_message(self, *_):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        r = OpenRouterReader(model="m", key="k", base_url=f"http://127.0.0.1:{srv.server_port}", pause=0)
        t = run_case(CONTRACT, INVOICE, INTAKE, r, "2026-11-03")
    finally:
        srv.shutdown()
        srv.server_close()
    assert t["status"] == READY and t["reader"]["served_model"] == "served/x" and len(calls) == 2
    assert "untrusted" in calls[0]["messages"][0]["content"]
