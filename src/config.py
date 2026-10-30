"""Central configuration for Umuzi Analytics.

Every path, canonical code list and analytical threshold lives here so that the
pipeline, the analytics layer, the app and the tests share one definition.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
QUARANTINE_DIR = DATA_DIR / "quarantine"
REGISTRY_PATH = DATA_DIR / "release_registry.json"
ACTIVE_POINTER = SNAPSHOT_DIR / "ACTIVE.json"
BOUNDARY_PATH = RAW_DIR / "boundaries" / "geoBoundaries-RWA-ADM2_simplified.geojson"

PRODUCT_NAME = "Umuzi Analytics"

# Province membership of the 30 districts (administrative structure as listed,
# in the same order, in every NISR SAS district table).
DISTRICT_PROVINCE: dict[str, str] = {
    "Nyarugenge": "Kigali City", "Gasabo": "Kigali City", "Kicukiro": "Kigali City",
    "Nyanza": "Southern", "Gisagara": "Southern", "Nyaruguru": "Southern", "Huye": "Southern",
    "Nyamagabe": "Southern", "Ruhango": "Southern", "Muhanga": "Southern", "Kamonyi": "Southern",
    "Karongi": "Western", "Rutsiro": "Western", "Rubavu": "Western", "Nyabihu": "Western",
    "Ngororero": "Western", "Rusizi": "Western", "Nyamasheke": "Western",
    "Rulindo": "Northern", "Gakenke": "Northern", "Musanze": "Northern", "Burera": "Northern",
    "Gicumbi": "Northern",
    "Rwamagana": "Eastern", "Nyagatare": "Eastern", "Gatsibo": "Eastern", "Kayonza": "Eastern",
    "Kirehe": "Eastern", "Ngoma": "Eastern", "Bugesera": "Eastern",
}
DISTRICTS: list[str] = list(DISTRICT_PROVINCE)

# Crop columns as printed in SAS tables -> canonical crop key. Group subtotal
# columns (Cereals, Tubers and Roots, ...) are deliberately excluded: yields of
# heterogeneous crop groups are not agronomically meaningful.
CROP_ALIASES: dict[str, str] = {
    "maize": "maize", "sorghum": "sorghum", "paddy rice": "paddy_rice", "rice": "paddy_rice",
    "wheat": "wheat", "cassava": "cassava", "sweet potato": "sweet_potato",
    "sweet potatoes": "sweet_potato", "irish potato": "irish_potato",
    "irish potatoes": "irish_potato", "yams & taro": "yams_taro",
    "cooking banana": "cooking_banana", "dessert banana": "dessert_banana",
    "banana for beer": "beer_banana", "bean": "bean", "beans": "bean",
    "bush bean": "bush_bean", "climbing bean": "climbing_bean", "pea": "pea", "peas": "pea",
    "groundnuts": "groundnut", "groundnut": "groundnut", "soybean": "soybean",
    "soybeans": "soybean", "vegetables": "vegetables", "fruits": "fruits",
}
CROP_LABELS: dict[str, str] = {
    "maize": "Maize", "sorghum": "Sorghum", "paddy_rice": "Paddy rice", "wheat": "Wheat",
    "cassava": "Cassava", "sweet_potato": "Sweet potato", "irish_potato": "Irish potato",
    "yams_taro": "Yams and taro", "cooking_banana": "Cooking banana",
    "dessert_banana": "Dessert banana", "beer_banana": "Banana for beer", "bean": "Bean (all)",
    "bush_bean": "Bush bean", "climbing_bean": "Climbing bean", "pea": "Pea",
    "groundnut": "Groundnut", "soybean": "Soybean", "vegetables": "Vegetables", "fruits": "Fruits",
}

# District-level SAS indicators (all crops pooled, Overall farmer column).
INPUT_LABELS: dict[str, str] = {
    "improved_seed_farmers_pct": "Farmers using improved seed (%)",
    "inorganic_fert_farmers_pct": "Farmers applying inorganic fertilizer (%)",
    "organic_fert_farmers_pct": "Farmers applying organic fertilizer (%)",
    "erosion_protection_farmers_pct": "Farmers protecting land against erosion (%)",
}

# Analytical thresholds. Each is documented in docs/methodology.md and
# exercised by the sensitivity analysis in scripts/run_analysis.py.
MIN_HARVESTED_HA = 500.0        # below this, a district-crop yield is flagged "thin coverage"
GAP_THRESHOLD = 0.90            # yield ratio below 0.90 of national = "below national"
MIN_MATCHED_SEASONS = 2         # seasons of the same type required for a persistence call
