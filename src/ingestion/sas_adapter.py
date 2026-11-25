"""Source adapter for NISR Seasonal Agricultural Survey (SAS) Excel table releases.

NISR renumbers tables between releases (the district yield table is Table 13 in
2026 Season A but Table 10 in 2024 Season B), so tables are located by their
printed title and header labels, never by sheet number.

The same adapter reads the annual workbooks from 2018 to 2023. Their layouts
differ from the current releases in four ways, each handled explicitly:
- 2018 prints districts as columns and crops as rows (transposed matrix), with
  the national value in a "Grand Total" / "Overall Yield" column;
- 2018 Season B harvested area has no season in its title; the release entry in
  data/sources.json names the sheet (validated by production = yield x area);
- 2019 nests the farmer share as "Percentage of Farmers / Overall / Improved";
- 2018 reports input use per plot (or without a stated basis), not per farmer, so those tables are not
  comparable and the release entry marks inputs as unavailable.

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
# 1.1 -> 1.2: historical (2018-2023) title variants, transposed tables, unit check.
ADAPTER_VERSION = "sas-adapter-1.2"


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


_BY_DISTRICT = r"(?:and|per|by) district"
TABLE_SPECS: list[TableSpec] = [
    # "Large scale", "CIP crops", "detailed ..." and "Season C site" tables are
    # sub-populations of the same survey and must never stand in for the district total.
    TableSpec("yield_kg_ha", rf"average yield by crop type {_BY_DISTRICT}|yield of main crops by district",
              r"large.scale|cip crops|detailed|site"),
    TableSpec("harvested_ha", rf"harvested area by crop type {_BY_DISTRICT}"),
    TableSpec("cultivated_ha", rf"cultivated area by crop type {_BY_DISTRICT}"),
    TableSpec("production_t", rf"crop production by crop type {_BY_DISTRICT}|production of main crops by district"),
    TableSpec("improved_seed_farmers_pct",
              r"use of (?:improved )?seeds? by farmer (?:type|categories) per district",
              kind="district_column",
              column_pattern=r"farmers who used improved.*overall|percentage of farmers / overall / improved"),
    TableSpec("inorganic_fert_farmers_pct",
              r"use of inorganic fertili[sz]er by farmer (?:type|categories) per district",
              kind="district_column",
              column_pattern=r"farmers who (?:applied|used) inorganic.*overall|percentage of farmers / overall / yes"),
    TableSpec("organic_fert_farmers_pct",
              r"use of organic fertili[sz]er by farmer (?:type|categories) per district",
              kind="district_column",
              column_pattern=r"farmers who (?:applied|used) organic.*overall|percentage of farmers / overall / yes"),
    TableSpec("erosion_protection_farmers_pct", r"farmers who practiced agricultural practices",
              kind="district_column", column_pattern=r"protected land against erosion", required=False),
]
INPUT_METRICS = [s.metric for s in TABLE_SPECS if s.kind == "district_column"]

# "(?![a-z])" rather than "\b": titles such as "2024 Season A_Harvested" have no
# word boundary between the season letter and the underscore. 2018 titles carry
# the season without a year ("Season A_Yield", "SeasonB_ Production").
_SEASON_RE = re.compile(r"(20\d\d)\s*season\s*([abc])(?![a-z])|season\s*([abc])(?![a-z])\s*_?\s*(20\d\d)", re.I)
_SEASON_ONLY_RE = re.compile(r"season\s*([abc])(?![a-z])", re.I)
_DISTRICT_LOOKUP = {d.lower(): d for d in DISTRICTS}
# NISR labels the national row "National" in crop tables but "Total" in some
# input tables (e.g. 2026A inorganic fertilizer) and "S/Total" in production tables.
_NATIONAL_LABELS = {"national", "total", "rwanda", "s/total", "s/ total", "sub-total", "subtotal"}
# 2018 transposed tables put the national value in a column: "Total A",
# "Grand Total", "2018 B Total", "Overall Yield 2018 A", "Overall Yield".
_NATIONAL_COLUMN_RE = re.compile(r"^(?:grand total|total\b.*|20\d\d ?[ab] total|overall yield.*|national)$", re.I)


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
        elif (m := _SEASON_ONLY_RE.search(title)):
            season = m.group(1).upper()
        out.append(ParsedTable(ws.title.strip(), title, rows, year, season))
    wb.close()
    return out


def _find_table(tables: list[ParsedTable], spec: TableSpec, year: int, season: str,
                override: str | None = None) -> ParsedTable | None:
    if override is not None:
        named = [t for t in tables if t.sheet == override.strip()]
        if not named:
            raise SchemaError(f"override sheet '{override}' for {spec.metric} not in workbook")
        return named[0]
    candidates = []
    for t in tables:
        low = t.title.lower()
        if not re.search(spec.title_pattern, low):
            continue
        if spec.exclude_pattern and re.search(spec.exclude_pattern, low):
            continue
        # Multi-season (annual) workbooks: any season or year tag must match.
        if t.season is not None and t.season != season:
            continue
        if t.season_year is not None and t.season_year != year:
            continue
        candidates.append(t)
    full = [t for t in candidates if t.season_year is not None]
    season_only = [t for t in candidates if t.season is not None]
    if full or season_only:
        return (full or season_only)[0]
    # An untagged table is only safe when no table of this kind in the workbook
    # carries a season tag (a single-season release); otherwise the season of the
    # untagged one is a guess and the release entry must name the sheet.
    tagged_elsewhere = any(t.season is not None for t in tables
                           if re.search(spec.title_pattern, t.title.lower()))
    if candidates and tagged_elsewhere:
        return None
    return candidates[0] if candidates else None


_NATIONAL_YEAR_RE = re.compile(r"^national(?: level)?(?:\s+(20\d\d)\s*[abc]?)?$")


def _is_national(label: str, year: int | None) -> bool:
    """True for the national row of *this* release. Annual workbooks from 2020 to
    2022 also print the previous year's national value ("National 2019 A") for
    comparison; that row must never be read as the current national reference."""
    if label in _NATIONAL_LABELS:
        return True
    m = _NATIONAL_YEAR_RE.match(label)
    return bool(m) and (m.group(1) is None or year is None or int(m.group(1)) == year)


def _district_rows(rows: list[tuple], year: int | None = None) -> tuple[int, int, dict[str, int]]:
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
        elif found and _is_national(key, year):
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


def _status(val: float | None) -> str:
    if val is None:
        return "blank"
    if val == 0:
        return "reported_zero"
    if val < 0:
        return "invalid_negative"
    return "observed"


def _unambiguous(positions: dict[int, str], sheet: str) -> tuple[dict[int, str], list[str]]:
    """Drop crops printed twice in one table. 2021 Season A production prints two
    different "Bush bean" columns (one includes small red bean); choosing either
    would be a guess, so the crop is left unreported for that table."""
    counts = pd.Series(list(positions.values())).value_counts()
    dup = set(counts[counts > 1].index)
    warnings = [f"{sheet}: '{c}' printed {counts[c]} times with different values; not used" for c in sorted(dup)]
    return {k: v for k, v in positions.items() if v not in dup}, warnings


def _transposed_header(rows: list[tuple]) -> int | None:
    """Index of a row that holds district names as column headers (2018 layout)."""
    for i, row in enumerate(rows[:12]):
        if sum(_clean(v).lower() in _DISTRICT_LOOKUP for v in row) >= 20:
            return i
    return None


def _parse_transposed_matrix(t: ParsedTable, metric: str, hdr: int) -> tuple[list[dict], list[str]]:
    header = [_clean(v) for v in t.rows[hdr]]
    cols: dict[int, str] = {}
    for j, h in enumerate(header):
        if h.lower() in _DISTRICT_LOOKUP:
            cols[j] = _DISTRICT_LOOKUP[h.lower()]
        elif _NATIONAL_COLUMN_RE.match(h) and "National" not in cols.values():
            cols[j] = "National"
    if "National" not in cols.values():
        raise SchemaError(f"{t.sheet}: no national column in transposed table")
    crop_rows, warnings = _unambiguous({i: CROP_ALIASES[_clean(row[0]).lower()]
                                        for i, row in enumerate(t.rows) if i > hdr and row
                                        and _clean(row[0]).lower() in CROP_ALIASES}, t.sheet)
    recs, seen = [], set(crop_rows.values())
    for i, crop in crop_rows.items():
        row = t.rows[i]
        for j, district in cols.items():
            val = _to_float(row[j] if j < len(row) else None)
            status = _status(val)
            if status == "invalid_negative":
                warnings.append(f"{t.sheet}: negative {metric} for {district}/{crop}")
            recs.append(dict(district=district, crop=crop, metric=metric,
                             value=val if status == "observed" else None, value_status=status))
    if "maize" not in seen:
        raise SchemaError(f"{t.sheet}: crop rows not recognised")
    return recs, warnings


def _parse_crop_matrix(t: ParsedTable, metric: str, year: int | None = None) -> tuple[list[dict], list[str]]:
    hdr = _transposed_header(t.rows)
    if hdr is not None:
        return _parse_transposed_matrix(t, metric, hdr)
    col, first, found = _district_rows(t.rows, year)
    ncols = max(len(r) for r in t.rows)
    # Crop names sit on the nearest header row above the data that names at least
    # two known crops; "District" may be on that row, below it, or missing (2020-2023).
    header = None
    for i in range(first - 1, max(-1, first - 6), -1):
        cells = [_clean(c) for c in t.rows[i]]
        if sum(c.lower() in CROP_ALIASES for c in cells) >= 2:
            header = cells
            break
    if header is None:
        raise SchemaError(f"{t.sheet}: no crop header row above the district rows")
    header += [""] * (ncols - len(header))
    recs = []
    crop_cols, warnings = _unambiguous({j: CROP_ALIASES[h.lower()] for j, h in enumerate(header)
                                        if h.lower() in CROP_ALIASES}, t.sheet)
    if "maize" not in crop_cols.values():
        raise SchemaError(f"{t.sheet}: crop header not recognised")
    for district, i in found.items():
        row = t.rows[i]
        for j, crop in crop_cols.items():
            val = _to_float(row[j] if j < len(row) else None)
            status = _status(val)
            if status == "invalid_negative":
                warnings.append(f"{t.sheet}: negative {metric} for {district}/{crop}")
            recs.append(dict(district=district, crop=crop, metric=metric,
                             value=val if status == "observed" else None, value_status=status))
    return recs, warnings


def _parse_district_column(t: ParsedTable, spec: TableSpec, year: int | None = None) -> tuple[list[dict], list[str]]:
    col, first, found = _district_rows(t.rows, year)
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


def parse_workbook(path: Path, release_id: str, season_year: int, season: str,
                   sheet_overrides: dict[str, str] | None = None,
                   inputs_comparable: bool = True) -> ParseResult:
    """Parse one SAS workbook into canonical long records for one season.

    `sheet_overrides` names the sheet for a metric whose title carries no season
    (documented per release in data/sources.json). `inputs_comparable=False` skips
    the input-use tables of a release that reports them on a different basis.
    """
    tables = read_tables(Path(path))
    overrides = sheet_overrides or {}
    all_recs: list[dict] = []
    used: dict[str, str] = {}
    warnings: list[str] = []
    for spec in TABLE_SPECS:
        if spec.kind == "district_column" and not inputs_comparable:
            if spec.required:
                warnings.append(f"{spec.metric}: not published per farmer in this release; not used")
            continue
        t = _find_table(tables, spec, season_year, season, overrides.get(spec.metric))
        if t is None:
            msg = f"table for '{spec.metric}' (/{spec.title_pattern}/) not found"
            if spec.required:
                raise SchemaError(f"{release_id}: {msg}")
            warnings.append(msg)
            continue
        if spec.metric == "yield_kg_ha" and "kg/ha" not in t.title.lower().replace(" ", ""):
            raise SchemaError(f"{release_id}: yield table '{t.title[:80]}' does not state kg/ha")
        if spec.kind == "crop_matrix":
            recs, w = _parse_crop_matrix(t, spec.metric, season_year)
        else:
            recs, w = _parse_district_column(t, spec, season_year)
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
