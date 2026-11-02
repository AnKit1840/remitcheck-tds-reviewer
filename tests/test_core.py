from decimal import Decimal
import copy
import pytest
from remitcheck.core import (BP, FIS, ROYALTY, compute_tax, decide, load_yaml, regime_for, route_forms, sensitivity, TaxResult)
from datetime import date

RULES = load_yaml("rules.yaml")
REG = regime_for(date(2026, 11, 15), RULES)
BASE = dict(amount=100000, currency="USD", fx_rate="88", remittance_date="2026-11-15", trc_from="2026-01-01",
            trc_to="2026-12-31", treaty_form_filed=True, beneficial_owner_declared=True, no_pe_declared=True,
            pan=False, alt_details_furnished=True, payee_income_band="up_to_1cr", ytd_taxable_inr=0)


def tax(cat, net=False, **kw):
    return compute_tax(cat, {**BASE, **kw}, RULES, REG, net)


def test_treaty_rate_has_no_cess():
    assert tax(ROYALTY).tds_inr == Decimal("1320000")


def test_act_rate_loads_cess_without_trc():
    r = tax(ROYALTY, trc_to=None)
    assert r.effective_rate_pct == Decimal("20.8") and r.tds_inr == Decimal("1830400")


def test_surcharge_band():
    assert tax(FIS, trc_to=None, payee_income_band="above_10cr").effective_rate_pct == Decimal("21.84")


def test_unknown_band_escalates():
    assert tax(FIS, trc_to=None, payee_income_band="unknown") == "SURCHARGE_BAND_UNKNOWN"
    assert tax(FIS, trc_to=None, payee_income_band="status") == "SURCHARGE_BAND_UNKNOWN"


def test_gross_up_matches_published_example():
    r = tax(FIS, True, amount=900000, currency="INR", fx_rate="1")
    assert r.gross_inr == Decimal("1058824") and r.tds_inr == Decimal("158824")


def test_no_pan_floor():
    assert tax(ROYALTY, alt_details_furnished=False).effective_rate_pct == Decimal("20")


def test_nil_rate_needs_documents():
    assert tax(BP, no_pe_declared=False) == "TREATY_DOCS_MISSING_FOR_NIL_RATE"


def test_trc_must_cover_date():
    assert tax(ROYALTY, trc_to="2026-06-30").basis == "act"


def test_fx_never_guessed():
    assert tax(ROYALTY, fx_rate=None) == "FX_RATE_MISSING"


@pytest.mark.parametrize("gross,ytd,part", [(500000, 0, "Part A"), (500001, 0, "Part C"), (300000, 200001, "Part C")])
def test_threshold(gross, ytd, part):
    r = TaxResult(Decimal(gross), Decimal(1), Decimal(15), "treaty")
    assert part in route_forms(r, {"ytd_taxable_inr": ytd}, RULES, REG)["route"]


def test_regime_dates():
    assert regime_for(date(2026, 3, 31), RULES)["declaration_form"] == "Form 15CA"
    assert regime_for(date(2026, 4, 1), RULES)["declaration_form"] == "Form 145"
    assert regime_for(date(2023, 3, 31), RULES) is None


def test_label_does_not_matter_order():
    assert decide({"software_access_only": "yes", "copyright_rights_granted": "yes"}).category == ROYALTY


def test_silent_knowhow_escalates():
    assert decide({"technical_service": "yes", "knowhow_transfer": "silent"}).code == "MISSING_MAKE_AVAILABLE_FACT"


def test_sensitivity_reports_flip():
    flips = sensitivity({"software_access_only": "yes"})
    assert {"fact": "copyright_rights_granted", "from": "silent", "to": "yes", "outcome": ROYALTY} in flips
