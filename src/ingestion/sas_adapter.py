"""Source adapter for NISR Seasonal Agricultural Survey (SAS) Excel table releases.

NISR renumbers tables between releases (the district yield table is Table 13 in
2026 Season A but Table 10 in 2024 Season B), so tables are located by their
printed title and header labels, never by sheet number.

Output is a list of long-format canonical records:
    release_id, season_year, season, district, crop, metric, value, value_status,
    source_table
`value_status` separates an observed number from a cell NISR printed as 0 or
left blank, so that absence is never silently treated as a zero yield.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
import pandas as pd

from src.config import CROP_ALIASES, DISTRICTS


# Bump whenever parsing logic changes; the snapshot store re-processes an
# already-ingested raw file when its adapter version differs.
# 1.0 -> 1.1: national row labelled "Total" in input tables was being dropped.
ADAPTER_VERSION = "sas-adapter-1.1"


class SchemaError(ValueError):
    """Raised when a workbook does not contain a table the pipeline requires."""


@dataclass(frozen=True)
class TableSpec:
    metric: str
    title_pattern: str
    exclude_pattern: str | None = None
    kind: str = "crop_matrix"           # crop_matrix | district_column
    column_pattern: str | None = None   # for district_column tables
    required: bool = True


TABLE_SPECS: list[TableSpec] = [
    TableSpec("yield_kg_ha", r"average yield by crop type and district", r"large.scale"),
    TableSpec("harvested_ha", r"harvested area by crop type and district"),
    TableSpec("cultivated_ha", r"cultivated area by crop type and district"),
    TableSpec("production_t", r"crop production by crop type and district"),
    TableSpec("improved_seed_farmers_pct", r"use of seeds by farmer type per district",
              kind="district_column", column_pattern=r"farmers who used improved seed.*overall"),
    TableSpec("inorganic_fert_farmers_pct", r"use of inorganic fertili[sz]er by farmer type per district",
              kind="district_column", column_pattern=r"farmers who applied inorganic.*overall"),
    TableSpec("organic_fert_farmers_pct", r"use of organic fertili[sz]er by farmer type per district",
              kind="district_column", column_pattern=r"farmers who applied organic.*overall"),
    TableSpec("erosion_protection_farmers_pct", r"farmers who practiced agricultural practices",
              kind="district_column", column_pattern=r"protected land against erosion", required=False),
]

# "(?![a-z])" rather than "\b": titles such as "2024 Season A_Harvested" have no
# word boundary between the season letter and the underscore.
_SEASON_RE = re.compile(r"(20\d\d)\s*season\s*([abc])(?![a-z])|season\s*([abc])(?![a-z])\s*_?\s*(20\d\d)", re.I)
_DISTRICT_LOOKUP = {d.lower(): d for d in DISTRICTS}
# NISR labels the national row "National" in crop tables but "Total" in some
# input tables (e.g. 2026A inorganic fertilizer) and "S/Total" in production tables.
_NATIONAL_LABELS = {"national", "total", "rwanda", "s/total", "s/ total", "sub-total", "subtotal"}


@dataclass
class ParsedTable:
    sheet: str
    title: str
    rows: list[tuple]
    season_year: int | None = None
    season: str | None = None


@dataclass
class ParseResult:
    records: pd.DataFrame
    tables_used: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def _clean(v) -> str:
    return "" if v is None else re.sub(r"\s+", " ", str(v)).strip()


def _title_of(rows: list[tuple]) -> str:
    parts: list[str] = []
    for row in rows[:4]:
        parts += [_clean(v) for v in row if _clean(v)]
        if any(p.lower().startswith("district") for p in parts):
            break
    return " ".join(parts[:3])


def read_tables(path: Path) -> list[ParsedTable]:
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    out = []
    for ws in wb.worksheets:
        rows = [tuple(r) for r in ws.iter_rows(values_only=True)]
        title = _title_of(rows)
        m = _SEASON_RE.search(title)
        year = season = None
        if m:
            year = int(m.group(1) or m.group(4))
            season = (m.group(2) or m.group(3)).upper()
        out.append(ParsedTable(ws.title, title, rows, year, season))
    wb.close()
    return out


def _find_table(tables: list[ParsedTable], spec: TableSpec, year: int, season: str) -> ParsedTable | None:
    candidates = []
    for t in tables:
        low = t.title.lower()
        if not re.search(spec.title_pattern, low):
            continue
        if spec.exclude_pattern and re.search(spec.exclude_pattern, low):
            continue
        # Multi-season (annual) workbooks: the season tag must match. A table
        # without a season tag is only accepted if the workbook is single-season.
        if t.season_year is not None and (t.season_year, t.season) != (year, season):
            continue
        candidates.append(t)
    tagged = [t for t in candidates if t.season_year is not None]
    return (tagged or candidates or [None])[0]


def _district_rows(rows: list[tuple]) -> tuple[int, int, dict[str, int]]:
    """Return (district column index, first data row index, {district: row index})."""
    # Anchor the label column on a real district name; "Total" can also appear
    # as a column header above the data, so it must not set the anchor.
    col = None
    for row in rows:
        for j, v in enumerate(row):
            if _clean(v).lower() in _DISTRICT_LOOKUP:
                col = j
                break
        if col is not None:
            break
    if col is None:
        raise SchemaError("no district rows found")
    found: dict[str, int] = {}
    for i, row in enumerate(rows):
        key = _clean(row[col]).lower() if col < len(row) else ""
        if key in _DISTRICT_LOOKUP:
            found.setdefault(_DISTRICT_LOOKUP[key], i)
        elif key in _NATIONAL_LABELS and found:
            found.setdefault("National", i)
    first = min(found.values())
    return col, first, found


def _header_labels(rows: list[tuple], first_data: int, ncols: int) -> list[str]:
    header_rows = rows[max(0, first_data - 4):first_data]
    filled: list[list[str]] = []
    for row in header_rows:
        cells = [_clean(row[j]) if j < len(row) else "" for j in range(ncols)]
        # Forward-fill merged group headers to the right.
        last = ""
        ff = []
        for c in cells:
            last = c or last
            ff.append(last)
        filled.append(ff)
    return [" / ".join(dict.fromkeys(r[j] for r in filled if r[j])) for j in range(ncols)]


def _to_float(v) -> float | None:
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_crop_matrix(t: ParsedTable, metric: str) -> tuple[list[dict], list[str]]:
    col, first, found = _district_rows(t.rows)
    ncols = max(len(r) for r in t.rows)
    # Crop names sit on the last header row (the row holding "District").
    header = None
    for i in range(first - 1, max(-1, first - 5), -1):
        cells = [_clean(c) for c in t.rows[i]]
        if any(c.lower().startswith("district") for c in cells):
            header = cells
            break
    if header is None:
        raise SchemaError(f"{t.sheet}: no 'District' header row")
    header += [""] * (ncols - len(header))
    warnings = []
    recs = []
    crop_cols = {j: CROP_ALIASES[h.lower()] for j, h in enumerate(header) if h.lower() in CROP_ALIASES}
    if "maize" not in crop_cols.values():
        raise SchemaError(f"{t.sheet}: crop header not recognised")
    for district, i in found.items():
        row = t.rows[i]
        for j, crop in crop_cols.items():
            raw = row[j] if j < len(row) else None
            val = _to_float(raw)
            if val is None:
                status = "blank"
            elif val == 0:
                status = "reported_zero"
            elif val < 0:
                status = "invalid_negative"
                warnings.append(f"{t.sheet}: negative {metric} for {district}/{crop}")
            else:
                status = "observed"
            recs.append(dict(district=district, crop=crop, metric=metric,
                             value=val if status == "observed" else None, value_status=status))
    return recs, warnings


def _parse_district_column(t: ParsedTable, spec: TableSpec) -> tuple[list[dict], list[str]]:
    col, first, found = _district_rows(t.rows)
    ncols = max(len(r) for r in t.rows)
    labels = _header_labels(t.rows, first, ncols)
    target = None
    for j, lab in enumerate(labels):
        if j != col and re.search(spec.column_pattern, lab.lower()):
            target = j
            break
    if target is None:
        raise SchemaError(f"{t.sheet}: column /{spec.column_pattern}/ not found in {labels}")
    recs, warnings = [], []
    for district, i in found.items():
        row = t.rows[i]
        val = _to_float(row[target] if target < len(row) else None)
        status = "observed" if val is not None else "blank"
        if val is not None and not (0 <= val <= 100):
            status = "invalid_range"
            warnings.append(f"{t.sheet}: {spec.metric}={val} outside 0-100 for {district}")
        recs.append(dict(district=district, crop="all", metric=spec.metric,
                         value=val if status == "observed" else None, value_status=status))
    return recs, warnings


def parse_workbook(path: Path, release_id: str, season_year: int, season: str) -> ParseResult:
    """Parse one SAS workbook into canonical long records for one season."""
    tables = read_tables(Path(path))
    all_recs: list[dict] = []
    used: dict[str, str] = {}
    warnings: list[str] = []
    for spec in TABLE_SPECS:
        t = _find_table(tables, spec, season_year, season)
        if t is None:
            msg = f"table for '{spec.metric}' (/{spec.title_pattern}/) not found"
            if spec.required:
                raise SchemaError(f"{release_id}: {msg}")
            warnings.append(msg)
            continue
        if spec.kind == "crop_matrix":
            recs, w = _parse_crop_matrix(t, spec.metric)
        else:
            recs, w = _parse_district_column(t, spec)
        for r in recs:
            r["source_table"] = f"{t.sheet}: {t.title[:90]}"
        all_recs += recs
        warnings += w
        used[spec.metric] = t.sheet
    df = pd.DataFrame(all_recs)
    df.insert(0, "release_id", release_id)
    df.insert(1, "season_year", season_year)
    df.insert(2, "season", season)
    return ParseResult(df, used, warnings)
