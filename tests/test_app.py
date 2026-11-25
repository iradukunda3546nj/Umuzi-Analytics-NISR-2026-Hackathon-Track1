"""UI tests using Streamlit's AppTest on the real active snapshot."""
import pytest
from streamlit.testing.v1 import AppTest

from src.config import ROOT
from src.decisions.explain import PLAIN_CATEGORY
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


@pytest.mark.parametrize("view", ["home", "explore", "why", "ask", "evidence"])
def test_every_section_renders(view):
    at = run(view=view)
    labels = [b.label for b in at.button]
    assert {"Home", "Your district", "Why?", "Ask Umuzi", "Evidence"} <= set(labels)


def test_landing_page_explains_itself_and_leads_on():
    at = run(view="home")
    md = text(at)
    assert "Umuzi <span>Analytics</span>" in md and "umz-hook" in md
    assert "17</b><span>NISR surveys" in md                   # counted from the snapshot, not typed in
    at.button(key="cta_explore").click().run()
    assert at.session_state["view"] == "explore"


@pytest.mark.parametrize("season", ["A", "B"])
@pytest.mark.parametrize("crop", ["maize", "bean", "cassava"])
def test_district_page_renders_for_each_selection(season, crop):
    at = run(view="explore", season=season, crop=crop, district="Gakenke")
    md = text(at)
    assert "Gakenke (Northern)" in md and "umz-legs" in md and "umz-target-svg" in md


def test_values_next_to_the_benchmark_are_not_rounded_onto_it():
    # Gasabo cassava, Season A: 90.2% (not below) in 2024 and 89.6% (below) in 2026.
    at = run(view="explore", season="A", crop="cassava", district="Gasabo")
    md = text(at)
    assert "90.2%" in md and "89.6%" in md


def test_why_button_opens_the_explanation():
    at = run(view="explore", season="A", crop="maize", district="Ruhango")
    at.button(key="why_btn").click().run()
    assert at.session_state["view"] == "why"
    md = text(at)
    assert "Is it a pattern?" in md and "Seed and fertilizer?" in md and "Take action" in md


def test_why_page_and_assistant_state_the_same_finding():
    at = run(view="why", season="A", crop="maize", district="Ruhango")
    md = text(at)
    label = PLAIN_CATEGORY["Repeatedly below national, low input uptake"]
    assert label in md
    at.chat_input[0].set_value("Has it stayed below national?").run()
    assert not at.exception
    assert any(m.value.startswith(f"**{label}.**") for m in at.markdown)


def test_follow_up_offers_to_show_the_new_district_on_the_map():
    at = run(view="ask", season="A", crop="maize", district="Ruhango")
    at.chat_input[0].set_value("What about Nyamagabe?").run()
    labels = [b.label for b in at.button]
    assert "Show Nyamagabe, maize, Season A on the map" in labels
    at.button(key=[b.key for b in at.button if b.label.startswith("Show Nyamagabe")][0]).click().run()
    assert at.session_state["district"] == "Nyamagabe" and at.session_state["view"] == "explore"


def test_unrecognised_question_gets_a_short_reply_and_suggestions():
    at = run(view="ask")
    at.chat_input[0].set_value("what is the price of tea in London").run()
    md = text(at)
    assert "didn't catch that" in md
    assert any(b.key and b.key.startswith("sugg_") for b in at.button)


def test_brief_download_and_methods():
    at = run(view="why", season="B", crop="bean", district="Kamonyi")
    labels = [b.label for b in at.get("download_button")]
    assert "Download brief" in labels
    md = text(run(view="evidence"))
    assert "the rules were kept" in md                     # backtest decision shown in Data and methods
    assert "district analysis starts in 2018" in md


def test_non_default_benchmark_is_flagged():
    at = run(view="explore", gap=0.8)
    assert "non-default benchmark settings" in text(at)
