"""UI smoke and state-propagation tests using Streamlit's AppTest (real active snapshot)."""
import pytest
from streamlit.testing.v1 import AppTest

from src.config import ROOT
from src.services.snapshot_store import SnapshotStore

pytestmark = pytest.mark.skipif(SnapshotStore().active_id() is None, reason="no active snapshot")
VIEWS = ["Overview", "Evidence Map", "Persistence", "Input Context", "Triage Matrix",
         "Compare Districts", "Evidence Brief", "Data and Methods"]


def run(view, **state):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
    at.session_state["view"] = view
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


@pytest.mark.parametrize("view", VIEWS)
@pytest.mark.parametrize("season", ["A", "B"])
def test_every_view_renders(view, season):
    run(view, season=season)


def test_filters_propagate_to_header_brief_and_exports():
    at = run("Evidence Brief", season="B", crop="bean", district="Kamonyi")
    md = " ".join(m.value for m in at.markdown)
    assert "Bean (all), Season B" in md                       # header scope
    assert "Kamonyi District" in md                            # brief title
    labels = [b.label for b in at.get("download_button")]
    assert "Download brief (Markdown)" in labels


def test_sensitivity_threshold_is_flagged():
    at = run("Evidence Map", gap=0.8)
    assert any("Non-default thresholds" in c.value for c in at.caption)
