"""UI tests using Streamlit's AppTest on the real active snapshot."""
import pytest
from streamlit.testing.v1 import AppTest

from src.config import ROOT
from src.services.snapshot_store import SnapshotStore

pytestmark = pytest.mark.skipif(SnapshotStore().active_id() is None, reason="no active snapshot")


def run(**state):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=300)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def text(at) -> str:
    return " ".join(m.value for m in at.markdown)


@pytest.mark.parametrize("season", ["A", "B"])
@pytest.mark.parametrize("crop", ["maize", "bean", "cassava"])
def test_overview_renders_for_each_selection(season, crop):
    at = run(season=season, crop=crop, district="Gakenke")
    md = text(at)
    assert "<div class='umz-card'>" in md and "Gakenke (Northern)" in md
    assert "umz-legend" in md


def test_map_panel_and_assistant_state_the_same_finding():
    at = run(season="A", crop="maize", district="Ruhango")
    card = next(m.value for m in at.markdown if "<div class='umz-card'>" in m.value)
    assert "Repeatedly below national" in card
    at.chat_input[0].set_value("Has it stayed below national?").run()
    assert not at.exception
    reply = [m.value for m in at.markdown if m.value.startswith("**Repeatedly below national")]
    assert reply, "assistant did not answer with the map's category"
    category = reply[-1].split(".**")[0].strip("*")
    assert category in card


def test_follow_up_offers_to_show_the_new_district_on_the_map():
    at = run(season="A", crop="maize", district="Ruhango")
    at.chat_input[0].set_value("What about Nyamagabe?").run()
    labels = [b.label for b in at.button]
    assert "Show Nyamagabe, maize, Season A on the map" in labels
    at.button(key=[b.key for b in at.button if b.label.startswith("Show Nyamagabe")][0]).click().run()
    assert at.session_state["district"] == "Nyamagabe"


def test_brief_download_and_methods_tab():
    at = run(season="B", crop="bean", district="Kamonyi")
    labels = [b.label for b in at.get("download_button")]
    assert "Download brief (Markdown)" in labels
    md = text(at)
    assert "the rules were kept" in md                     # backtest decision shown in Data and methods
    assert "district analysis starts in 2018" in md


def test_non_default_benchmark_is_flagged():
    at = run(gap=0.8)
    assert "non-default benchmark settings" in text(at)
