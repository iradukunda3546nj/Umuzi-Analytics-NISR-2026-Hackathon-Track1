"""Adapter rules for the 2018-2023 annual workbook layouts, on SYNTHETIC workbooks (not NISR data).

Each test builds the smallest workbook that reproduces one layout feature found
in the real files, so a regression in that rule fails here first.
"""
import openpyxl
import pytest

from src.config import DISTRICTS
from src.ingestion.sas_adapter import SchemaError, parse_workbook

MARKER = "SYNTHETIC TEST FIXTURE - not NISR data"
CROPS = ["Maize", "Cassava", "Beans", "Irish potatoes", "Paddy rice"]


def _row_table(wb, sheet, title, values, extra_rows=(), crops=CROPS):
    """2019-2023 layout: districts down, crops across, header row without 'District'."""
    ws = wb.create_sheet(sheet)
    ws.append(["List of Tables"])
    ws.append([None, sheet + ":", title])
    ws.append([None, None, *crops])
    for d in DISTRICTS:
        ws.append([None, d, *values(d)])
    ws.append([None, "National", *values("National")])
    for label, vals in extra_rows:
        ws.append([None, label, *vals])
    ws.append([None, MARKER])


def _annual(path, year, extra_national=(), crops=CROPS, yield_unit="(Kg/Ha)"):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    n = 10
    for s in "AB":
        y = (lambda d: [2000.0, 12000.0, 800.0, 9000.0, 4000.0][:len(crops)])
        a = (lambda d: [1000.0] * len(crops))
        pr = (lambda d: [2000.0, 12000.0, 800.0, 9000.0, 4000.0][:len(crops)])
        _row_table(wb, f"Table {n}", f"Season {s} {year}_Cultivated area by crop type per district (ha)", a, crops=crops); n += 1
        _row_table(wb, f"Table {n}", f"Season {s} {year}_Harvested area by crop type per district (ha)", a, crops=crops); n += 1
        _row_table(wb, f"Table {n}", f"Season {s} {year}_Average yield by crop type per district {yield_unit}", y,
                   crops=crops); n += 1
        _row_table(wb, f"Table {n}", f"Season {s} {year}_Crop production by crop type per district (MT)", pr,
                   extra_rows=extra_national, crops=crops); n += 1
        for metric, label in [("seeds", "Percentage of farmers who used improved seeds"),
                              ("inorganic fertilizer", "Percentage of farmers who used inorganic fertilizers"),
                              ("organic fertilizer", "Percentage of farmers who applied organic fertilizer")]:
            ws = wb.create_sheet(f"Table {n}"); n += 1
            ws.append([None, f"Table {n}:", f"Season {s} {year}_Use of {metric} by farmer type per district (%)"])
            ws.append([None, "District", label, None, None])
            ws.append([None, None, "Overall", "SSF", "LSF"])
            for d in DISTRICTS + ["National"]:
                ws.append([None, d, 40.0, 40.0, None])
    wb.save(path)
    return path


def test_previous_year_national_row_is_not_the_reference(tmp_path):
    # 2020-2022 production tables print "National 2019 A" after the current national row.
    p = _annual(tmp_path / "a.xlsx", 2020, extra_national=[("National 2019 A", [1.0, 1.0, 1.0, 1.0, 1.0])])
    r = parse_workbook(p, "SYN-2020A", 2020, "A").records
    nat = r[(r["district"] == "National") & (r["metric"] == "production_t") & (r["crop"] == "maize")]
    assert len(nat) == 1 and nat["value"].iloc[0] == 2000.0


def test_crop_printed_twice_is_dropped_not_guessed(tmp_path):
    crops = ["Maize", "Cassava", "Beans", "Beans", "Paddy rice"]
    p = _annual(tmp_path / "a.xlsx", 2021, crops=crops)
    res = parse_workbook(p, "SYN-2021A", 2021, "A")
    assert "bean" not in set(res.records["crop"])
    assert any("printed 2 times" in w for w in res.warnings)


def test_yield_table_must_state_kg_per_ha(tmp_path):
    p = _annual(tmp_path / "a.xlsx", 2019, yield_unit="(MT/Ha)")
    with pytest.raises(SchemaError, match="kg/ha"):
        parse_workbook(p, "SYN-2019A", 2019, "A")


def _transposed(wb, sheet, title, value, national_label):
    """2018 layout: crops down, districts across, national value in a total column."""
    ws = wb.create_sheet(sheet)
    ws.append([None])
    ws.append([title])
    ws.append(["Crop/District", *DISTRICTS, "East", national_label])
    for k, crop in enumerate(CROPS):
        ws.append([crop, *[value * (k + 1)] * len(DISTRICTS), 1.0, value * (k + 1)])
    ws.append([MARKER])


def _workbook_2018(path, harvested_b_title):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    _transposed(wb, "Appendix 1", "Appendix 1. Season A_Cultivated area by crop type by district (Ha)", 1000.0, "Total A")
    _transposed(wb, "Appendix 2", "Appendix 2. Season B_Cultivated area by crop type by district (Ha)", 1000.0, "Total 2018B")
    _transposed(wb, "Appendix 4", "Table 7.1: Season A_Harvested area by crop type by district(Ha)", 1000.0, "Grand Total")
    _transposed(wb, "Appendix 5", harvested_b_title, 1000.0, "2018 B Total")
    _transposed(wb, "Appendix 6", "Appendix 6: Season A_Production of main crops by District (MT)", 2000.0, "Grand Total")
    _transposed(wb, "Appendix 7", "Appendix 7: SeasonB_ Production of main crops by District (MT)", 2000.0, "2018 B Total")
    _transposed(wb, "Appendix 9", "Appendix 9: Season A_Yield of main crops by District (Kg/Ha)", 2000.0, "Overall Yield 2018 A")
    _transposed(wb, "Appendix 10", "Table 10b:Season B_Yield of main crops by District (Kg/Ha)", 2000.0, "Overall Yield")
    wb.save(path)
    return path


def test_transposed_2018_layout_reads_districts_and_national_column(tmp_path):
    p = _workbook_2018(tmp_path / "w.xlsx", "Appendix 5: Season B_Harvested area by crop type by district(Ha)")
    r = parse_workbook(p, "SYN-2018A", 2018, "A", inputs_comparable=False).records
    y = r[(r["metric"] == "yield_kg_ha") & (r["crop"] == "maize")].set_index("district")["value"]
    assert set(y.index) == set(DISTRICTS) | {"National"}
    assert y["National"] == 2000.0                    # the "East" province column is never read
    assert not (r["crop"] == "all").any()             # inputs skipped when not comparable


def test_untagged_sheet_in_annual_workbook_needs_an_explicit_override(tmp_path):
    p = _workbook_2018(tmp_path / "w.xlsx", "Appendix 5: Harvested area by crop type by district(Ha)")
    with pytest.raises(SchemaError, match="harvested_ha"):
        parse_workbook(p, "SYN-2018B", 2018, "B", inputs_comparable=False)
    r = parse_workbook(p, "SYN-2018B", 2018, "B", sheet_overrides={"harvested_ha": "Appendix 5"},
                       inputs_comparable=False)
    assert r.tables_used["harvested_ha"] == "Appendix 5"
