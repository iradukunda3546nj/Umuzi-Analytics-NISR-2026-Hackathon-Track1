"""Decision-rule tests on hand-built SYNTHETIC records (not NISR data)."""
import numpy as np
import pandas as pd

from src.analytics.indicators import (CATEGORY_DIP, CATEGORY_INSUFFICIENT, CATEGORY_NOT_BELOW,
                                      CATEGORY_REPEATED_INPUTS_OK, CATEGORY_REPEATED_LOW_INPUT,
                                      Params, evidence_table)
from src.config import DISTRICTS


def synthetic_records(ratios: dict, areas: dict | None = None, seed=None, fert=None,
                      national_inputs=(40.0, 60.0)):
    """ratios: {district: [ratio per release]} for maize, Season A; others at 1.0."""
    n = len(next(iter(ratios.values()), [1, 1, 1]))
    rels = [(f"SYN-{y}A", y) for y in range(2027 - n, 2027)]
    rows = []
    for k, (rid, y) in enumerate(rels):
        def add(d, crop, metric, v):
            rows.append(dict(release_id=rid, season_year=y, season="A", district=d, crop=crop,
                             metric=metric, value=v,
                             value_status="observed" if v is not None and not pd.isna(v) else "blank",
                             source_table="synthetic"))
        add("National", "maize", "yield_kg_ha", 2000.0)
        add("National", "maize", "harvested_ha", 100000.0)
        add("National", "all", "improved_seed_farmers_pct", national_inputs[0])
        add("National", "all", "inorganic_fert_farmers_pct", national_inputs[1])
        for d in DISTRICTS:
            r = ratios.get(d, [1.0] * n)[k]
            add(d, "maize", "yield_kg_ha", None if r is None else 2000.0 * r)
            add(d, "maize", "harvested_ha", (areas or {}).get(d, [3000] * n)[k])
            add(d, "all", "improved_seed_farmers_pct", (seed or {}).get(d, 45.0))
            add(d, "all", "inorganic_fert_farmers_pct", (fert or {}).get(d, 70.0))
    return pd.DataFrame(rows)


def cat(ev, d):
    return ev.set_index("district").loc[d, "category"]


def test_categories():
    rec = synthetic_records(
        ratios={"Ruhango": [0.7, 0.7, 0.7], "Gicumbi": [0.7, 0.8, 0.75], "Huye": [1.0, 1.1, 0.7],
                "Nyanza": [None, None, 0.6], "Rubavu": [0.7, 0.7, 0.7]},
        areas={"Rubavu": [3000, 3000, 100]},
        seed={"Ruhango": 20.0, "Gicumbi": 50.0}, fert={"Ruhango": 30.0, "Gicumbi": 30.0})
    ev = evidence_table(rec, "maize", "A")
    assert cat(ev, "Ruhango") == CATEGORY_REPEATED_LOW_INPUT
    assert cat(ev, "Gicumbi") == CATEGORY_REPEATED_INPUTS_OK      # seed above national
    assert cat(ev, "Huye") == CATEGORY_DIP
    assert cat(ev, "Nyanza") == CATEGORY_INSUFFICIENT               # only one season observed
    assert cat(ev, "Rubavu") == CATEGORY_INSUFFICIENT               # latest season thin coverage
    assert cat(ev, "Musanze") == CATEGORY_NOT_BELOW


def test_unknown_national_input_never_counts_as_not_low():
    rec = synthetic_records(ratios={"Ruhango": [0.7, 0.7, 0.7]}, seed={"Ruhango": 20.0},
                            fert={"Ruhango": 30.0}, national_inputs=(np.nan, 60.0))
    ev = evidence_table(rec, "maize", "A")
    assert cat(ev, "Ruhango") == CATEGORY_INSUFFICIENT


def test_threshold_parameters_change_classification():
    rec = synthetic_records(ratios={"Ruhango": [0.85, 0.85, 0.85]})
    assert cat(evidence_table(rec, "maize", "A"), "Ruhango").startswith("Repeatedly below")
    assert cat(evidence_table(rec, "maize", "A", Params(gap_threshold=0.8)), "Ruhango") == CATEGORY_NOT_BELOW


def test_ratio_is_same_release_district_over_national():
    rec = synthetic_records(ratios={"Ruhango": [0.5, 0.6, 0.65]})
    ev = evidence_table(rec, "maize", "A").set_index("district")
    assert abs(ev.loc["Ruhango", "latest_ratio"] - 0.65) < 1e-9
    assert abs(ev.loc["Ruhango", "ratio_SYN-2024A"] - 0.5) < 1e-9


def test_two_of_last_three_is_repeated_one_good_season_does_not_clear_it():
    rec = synthetic_records(ratios={"Ruhango": [0.7, 1.0, 0.7], "Huye": [1.0, 0.7, 0.95]},
                            seed={"Ruhango": 20.0}, fert={"Ruhango": 30.0})
    ev = evidence_table(rec, "maize", "A").set_index("district")
    assert ev.loc["Ruhango", "category"] == CATEGORY_REPEATED_LOW_INPUT
    assert ev.loc["Ruhango", "below_in_window"] == 2
    assert ev.loc["Huye", "category"] == CATEGORY_NOT_BELOW          # latest season decides "below now"


def test_only_the_last_three_surveys_count():
    # Behind in all of the first five surveys but only the latest of the last three.
    rec = synthetic_records(ratios={"Ruhango": [0.6, 0.6, 0.6, 0.6, 1.0, 1.0, 0.7],
                                    "Gicumbi": [1.0, 1.0, 1.0, 1.0, 0.8, 1.0, 0.8]})
    ev = evidence_table(rec, "maize", "A").set_index("district")
    assert ev.loc["Ruhango", "category"] == CATEGORY_DIP
    assert ev.loc["Gicumbi", "category"].startswith("Repeatedly below")
    assert ev.loc["Ruhango", "window_releases"] == "SYN-2024A,SYN-2025A,SYN-2026A"


def test_thin_coverage_is_a_gap_not_a_value():
    rec = synthetic_records(ratios={"Ruhango": [0.7, 0.7, 0.7]}, areas={"Ruhango": [3000, 100, 3000]})
    ev = evidence_table(rec, "maize", "A").set_index("district")
    assert ev.loc["Ruhango", "reliable_in_window"] == 2 and ev.loc["Ruhango", "below_in_window"] == 2
    assert ev.loc["Ruhango", "category"].startswith("Repeatedly below")
    rec = synthetic_records(ratios={"Ruhango": [0.7, 0.7, 0.7]}, areas={"Ruhango": [100, 100, 3000]})
    assert evidence_table(rec, "maize", "A").set_index("district").loc["Ruhango", "category"] == CATEGORY_INSUFFICIENT
