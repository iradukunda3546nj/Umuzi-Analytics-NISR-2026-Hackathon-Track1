"""Umuzi Assistant on the ACTIVE snapshot: agreement with the map, follow-ups, limitations."""
import pytest

from src.assistant.umuzi import Selection, UmuziData, answer, parse
from src.config import DISTRICTS
from src.decisions.explain import PLAIN_CATEGORY, explain
from src.decisions.finding import POOLED_NOTE, pct
from src.services.snapshot_store import SnapshotStore

store = SnapshotStore()
pytestmark = pytest.mark.skipif(store.active_id() is None, reason="no active snapshot")


@pytest.fixture(scope="module")
def data():
    return UmuziData(*store.load())


@pytest.mark.parametrize("crop", ["maize", "bean", "irish_potato", "cassava", "paddy_rice", "soybean"])
@pytest.mark.parametrize("season", ["A", "B"])
def test_assistant_and_map_agree_for_every_district(data, crop, season):
    ev = data.evidence(crop, season).set_index("district")       # what the map colours
    for d in DISTRICTS:
        sel = Selection(d, crop, season)
        f = data.finding(sel)                                    # what the map panel prints
        a = answer(data, f"How is {d} doing?", sel)
        assert f.category == ev.loc[d, "category"]
        assert a.text.startswith(f"**{PLAIN_CATEGORY[f.category]}.**")
        assert f.headline in a.text
        for k, v in f.figures:
            assert f"{k}: {v}" in a.evidence


def test_example_conversation_follows_context(data):
    sel = Selection("Kicukiro", "bean", "B")
    a1 = answer(data, "Has Ruhango's maize yield stayed below national in Season A?", sel)
    assert (a1.selection.district, a1.selection.crop, a1.selection.season) == ("Ruhango", "maize", "A")
    assert "Ruhango's maize yield" in a1.text and "Season A" in a1.text
    a2 = answer(data, "What about Nyamagabe?", a1.selection)
    assert a2.selection.district == "Nyamagabe" and a2.selection.crop == "maize"
    assert "Nyamagabe's maize yield" in a2.text
    a3 = answer(data, "What should I verify about fertilizer access?", a2.selection)
    assert "Nyamagabe" in a3.text and "inorganic fertilizer" in a3.text
    assert POOLED_NOTE in a3.keep_in_mind                         # uptake is pooled across crops: said so
    assert "all crops, not maize alone" in a3.text
    assert any(line.startswith("- ") for line in a3.text.splitlines())   # concrete field checks


def test_cause_answer_matches_the_why_page_and_admits_the_limit(data):
    sel = Selection("Ruhango", "maize", "A")
    a = answer(data, "Why is Ruhango's maize yield low?", sel)
    e = explain(data.finding(sel))
    assert a.text.startswith(f"**{e.verdict_title}.**")          # same words as the Why page
    assert e.pattern_line in a.text
    assert "not why" in a.text and "field check" in a.text.lower()


def test_action_answer_lists_the_why_page_checks(data):
    sel = Selection("Gasabo", "cassava", "A")
    a = answer(data, "What should we check?", sel)
    for _, check in explain(data.finding(sel)).checks:
        assert check in a.text


def test_unrecognised_questions_get_a_short_reply_not_a_guess(data):
    sel = Selection("Ruhango", "maize", "A")
    for q in ["what is the weather tomorrow", "How is the president doing?", "asdfgh"]:
        a = answer(data, q, sel)
        assert a.text.startswith("Sorry, I didn't catch that"), q
        assert a.suggestions and a.selection == sel


def test_misspelled_district_is_recognised_and_said_so(data):
    a = answer(data, "How is Musanzi doing?", Selection("Ruhango", "maize", "A"))
    assert a.selection.district == "Musanze"
    assert "I read 'musanzi' as Musanze" in a.text


def test_greeting_and_best_districts(data):
    sel = Selection("Ruhango", "maize", "A")
    assert answer(data, "Muraho", sel).text.startswith("Muraho!")
    best = answer(data, "Which districts do best for beans?", sel)
    assert best.text.startswith("Highest bean yields") and best.text.count("\n- ") == 5


def test_list_and_target_answers_use_the_same_tables(data):
    sel = Selection("Ruhango", "maize", "A")
    ev = data.evidence("maize", "A")
    a = answer(data, "Which other districts are repeatedly below?", sel)
    n = int(ev["category"].str.startswith("Repeatedly below").sum())
    assert a.text.startswith(f"{n} districts")
    t = answer(data, "How far is Rwanda from the maize target?", sel)
    assert "2.06 t/ha" in t.text                                # PSTA 5 2025/26 maize target


def test_no_invented_answer_for_unpublished_crop(data):
    a = answer(data, "How is wheat in Nyagatare in season B?", Selection("Ruhango", "maize", "A"))
    if not data.has_crop("wheat", "B"):
        assert "publishes no district" in a.text


def test_percentages_keep_their_side_of_the_benchmark():
    assert pct(0.8957) == "89.6%" and pct(0.9023) == "90.2%"
    assert pct(0.8999) == "89.99%" and pct(0.90) == "90%"
    assert pct(0.71) == "71%" and pct(None) == "not reported"


def test_parse_recognises_districts_crops_and_seasons():
    sel = Selection("Ruhango", "maize", "A")
    s, intent, named = parse("Compare Musanze and Burera for irish potato in season b", sel)
    assert intent == "compare" and named == ["Musanze", "Burera"]
    assert s.crop == "irish_potato" and s.season == "B"
    s, intent, _ = parse("How are sweet potatoes doing?", sel)
    assert s.crop == "sweet_potato" and intent == "status"
