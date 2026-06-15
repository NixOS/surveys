import polars as pl
import pytest

from nixos_survey_lib.aggregate import (
    counts_multi, counts_single, crosstab, crosstab_multi,
    upset_combinations,
)
from nixos_survey_lib.types import Bin, Combination, MultiChoice, Question, Ranking, SingleChoice


def _sc(values: list[str], qid: str = "country") -> SingleChoice:
    q = Question(id=qid, prompt=qid, type="single", choices=None, csv_columns=[])
    return SingleChoice(question=q, values=pl.Series(values))


def test_counts_single_basic():
    s = _sc(["Europe", "Europe", "Asia", "Europe"])
    bins = counts_single(s, bucket_min_percent=None, bucket_min_count=None)
    by_label = {b.label: b for b in bins}
    assert by_label["Europe"].count == 3
    assert by_label["Europe"].percent == 75.0
    assert by_label["Asia"].count == 1
    assert by_label["Asia"].percent == 25.0


def test_counts_single_respects_order():
    s = _sc(["Asia", "Europe", "Asia", "Europe"])
    bins = counts_single(s, order=["Europe", "Asia"], bucket_min_percent=None, bucket_min_count=None)
    assert [b.label for b in bins] == ["Europe", "Asia"]


def test_counts_single_exclude():
    s = _sc(["Europe", "Skipped", "Asia", "Skipped"])
    bins = counts_single(s, exclude=["Skipped"], bucket_min_percent=None, bucket_min_count=None)
    labels = {b.label for b in bins}
    assert "Skipped" not in labels
    by_label = {b.label: b for b in bins}
    assert by_label["Europe"].percent == 50.0


def test_counts_single_bucket_min_percent():
    s = _sc(["A"] * 95 + ["B"] * 3 + ["C"] * 2)
    bins = counts_single(s, bucket_min_percent=5.0)
    by_label = {b.label: b for b in bins}
    assert "A" in by_label
    assert "Other (combined)" in by_label
    assert by_label["Other (combined)"].count == 5


def test_counts_single_bucket_min_count():
    s = _sc(["A"] * 95 + ["B"] * 3 + ["C"] * 2)
    bins = counts_single(s, bucket_min_percent=None, bucket_min_count=4)
    by_label = {b.label: b for b in bins}
    assert "A" in by_label
    # B (3) and C (2) are both below count threshold of 4 → combined.
    assert "Other (combined)" in by_label
    assert by_label["Other (combined)"].count == 5
    assert "B" not in by_label
    assert "C" not in by_label


def test_counts_single_bucket_thresholds_or():
    # Thresholds: percent=2%, count=10. Total respondents = 107.
    # A (100, ~93.5%) is above both — kept.
    # B (5, ~4.7%) — above percent (2%), below count (10) → rare via count only.
    # C (2, ~1.9%) — below percent (2%), below count (10) → rare via both.
    # Both B and C end up bucketed because EITHER threshold fires (OR).
    s = _sc(["A"] * 100 + ["B"] * 5 + ["C"] * 2)
    bins = counts_single(s, bucket_min_percent=2.0, bucket_min_count=10)
    by_label = {b.label: b for b in bins}
    assert "A" in by_label
    assert "Other (combined)" in by_label
    assert by_label["Other (combined)"].count == 7


def test_counts_single_bucket_action_drop_removes_rare():
    # With bucket_action="drop", rare values vanish from the result instead of
    # being aggregated under "Other (combined)". Required for sensitive
    # categories where an aggregate bar would still leak counts via percent.
    s = _sc(["A"] * 95 + ["B"] * 3 + ["C"] * 2)
    bins = counts_single(s, bucket_min_percent=None, bucket_min_count=5, bucket_action="drop")
    by_label = {b.label: b for b in bins}
    assert "A" in by_label
    assert "Other (combined)" not in by_label
    assert "B" not in by_label
    assert "C" not in by_label
    # Percent is still computed against the original total (100), so the
    # remaining bar reflects 95/100 = 95%.
    assert by_label["A"].percent == 95.0


def test_counts_single_does_not_collide_with_literal_other():
    # The data contains a literal "Other" choice; the rare-bucket must not
    # collide with it.
    s = _sc(["Other"] * 50 + ["Linux"] * 50 + ["BSD"] * 2)
    bins = counts_single(s, bucket_min_percent=5.0)
    by_label = {b.label: b for b in bins}
    assert "Other" in by_label
    assert by_label["Other"].count == 50
    assert "Other (combined)" in by_label
    assert by_label["Other (combined)"].count == 2


def test_counts_single_empty():
    s = _sc([])
    bins = counts_single(s)
    assert bins == []


def _mc(choice_columns: dict[str, list[str]]) -> MultiChoice:
    q = Question(id="x", prompt="x", type="multiple", choices=list(choice_columns), csv_columns=[])
    return MultiChoice(question=q, choice_columns={k: pl.Series(v) for k, v in choice_columns.items()})


def test_counts_multi_basic():
    m = _mc({
        "Linux": ["Yes", "Yes", "Yes", "Yes"],
        "macOS": ["No", "Yes", "Yes", "No"],
        "Windows": ["No", "No", "No", "Yes"],
    })
    bins = counts_multi(m, bucket_min_percent=None, bucket_min_count=None)
    by_label = {b.label: b for b in bins}
    assert by_label["Linux"].count == 4
    assert by_label["Linux"].percent == 100.0
    assert by_label["macOS"].count == 2
    assert by_label["macOS"].percent == 50.0
    assert by_label["Windows"].count == 1
    assert by_label["Windows"].percent == 25.0


def test_counts_multi_sorted_by_percent_desc():
    m = _mc({
        "A": ["No", "Yes"],
        "B": ["Yes", "Yes"],
        "C": ["No", "No"],
    })
    bins = counts_multi(m, bucket_min_percent=None, bucket_min_count=None)
    assert [b.label for b in bins] == ["B", "A", "C"]


def test_counts_multi_bucket_min_percent():
    m = _mc({
        "A": ["Yes"] * 100,
        "B": ["Yes"] * 1 + ["No"] * 99,
        "C": ["Yes"] * 1 + ["No"] * 99,
    })
    bins = counts_multi(m, bucket_min_percent=5.0)
    labels = {b.label for b in bins}
    assert "A" in labels
    assert "Other (combined)" in labels
    assert "B" not in labels and "C" not in labels


def test_counts_multi_bucket_action_drop_removes_rare():
    m = _mc({
        "A": ["Yes"] * 100,
        "B": ["Yes"] * 4 + ["No"] * 96,
        "C": ["Yes"] * 2 + ["No"] * 98,
    })
    bins = counts_multi(m, bucket_min_percent=None, bucket_min_count=5, bucket_action="drop")
    labels = {b.label for b in bins}
    assert labels == {"A"}


def test_counts_multi_bucket_min_count():
    m = _mc({
        "A": ["Yes"] * 100,
        "B": ["Yes"] * 4 + ["No"] * 96,
        "C": ["Yes"] * 2 + ["No"] * 98,
    })
    bins = counts_multi(m, bucket_min_percent=None, bucket_min_count=5)
    labels = {b.label for b in bins}
    assert "A" in labels
    # B (4) and C (2) both below count threshold of 5.
    assert "Other (combined)" in labels
    assert "B" not in labels and "C" not in labels


def test_crosstab_global_normalize():
    x = _sc(["A", "A", "B", "B"], qid="x")
    y = _sc(["P", "Q", "P", "Q"], qid="y")
    ct = crosstab(x, y, normalize="global", x_order=["A", "B"], y_order=["P", "Q"])
    assert ct.cell_kind == "rate_pct"
    assert ct.cells == [[25.0, 25.0], [25.0, 25.0]]


def test_crosstab_x_normalize():
    x = _sc(["A", "A", "A", "B", "B"], qid="x")
    y = _sc(["P", "P", "Q", "P", "Q"], qid="y")
    ct = crosstab(x, y, normalize="x", x_order=["A", "B"], y_order=["P", "Q"])
    assert ct.cells[0][0] == pytest.approx(2 / 3 * 100, abs=0.01)
    assert ct.cells[0][1] == pytest.approx(1 / 3 * 100, abs=0.01)


def test_crosstab_y_normalize():
    x = _sc(["A", "A", "B"], qid="x")
    y = _sc(["P", "Q", "P"], qid="y")
    ct = crosstab(x, y, normalize="y", x_order=["A", "B"], y_order=["P", "Q"])
    assert ct.cells[0][0] == pytest.approx(50.0)
    assert ct.cells[1][0] == pytest.approx(50.0)


def test_crosstab_excludes_values():
    x = _sc(["A", "B", "Skipped"], qid="x")
    y = _sc(["P", "Q", "P"], qid="y")
    ct = crosstab(x, y, normalize="global", x_exclude=["Skipped"],
                  x_order=["A", "B"], y_order=["P", "Q"])
    assert "Skipped" not in ct.x_labels


def test_crosstab_empty_returns_empty():
    x = _sc([], qid="x")
    y = _sc([], qid="y")
    ct = crosstab(x, y)
    assert ct.x_labels == []
    assert ct.y_labels == []
    assert ct.cells == []


def _mc_long() -> tuple[MultiChoice, SingleChoice]:
    m = _mc({
        "trait_A": ["Yes", "Yes", "No", "No"],
        "trait_B": ["Yes", "No", "Yes", "No"],
    })
    s = _sc(["Beginner", "Advanced", "Beginner", "Advanced"], qid="skill")
    return m, s


def test_crosstab_multi_rate():
    m, s = _mc_long()
    ct = crosstab_multi(m, s, denominator="rate", x_order=["Beginner", "Advanced"])
    assert ct.cell_kind == "rate_pct"
    # cells[xi][yi]: xi indexes x_labels (single values), yi indexes y_labels (traits)
    by_label = {(t, x): ct.cells[j][i] for i, t in enumerate(ct.y_labels) for j, x in enumerate(ct.x_labels)}
    assert by_label[("trait_A", "Beginner")] == pytest.approx(50.0)
    assert by_label[("trait_A", "Advanced")] == pytest.approx(50.0)


def test_crosstab_multi_composition():
    m, s = _mc_long()
    ct = crosstab_multi(m, s, denominator="composition", x_order=["Beginner", "Advanced"])
    assert ct.cell_kind == "composition_pct"
    # cells[xi][yi]: xi indexes x_labels (single values), yi indexes y_labels (traits)
    by_label = {(t, x): ct.cells[j][i] for i, t in enumerate(ct.y_labels) for j, x in enumerate(ct.x_labels)}
    assert by_label[("trait_A", "Beginner")] == pytest.approx(50.0)
    assert by_label[("trait_A", "Advanced")] == pytest.approx(50.0)


def test_crosstab_multi_lift():
    m, s = _mc_long()
    ct = crosstab_multi(m, s, denominator="lift", x_order=["Beginner", "Advanced"])
    assert ct.cell_kind == "lift"
    # cells[xi][yi]: xi indexes x_labels (single values), yi indexes y_labels (traits)
    by_label = {(t, x): ct.cells[j][i] for i, t in enumerate(ct.y_labels) for j, x in enumerate(ct.x_labels)}
    assert by_label[("trait_A", "Beginner")] == pytest.approx(1.0)


def _rk(rows: list[list[str | None]]) -> Ranking:
    n_positions = len(rows[0]) if rows else 0
    cols = [[r[i] for r in rows] for i in range(n_positions)]
    q = Question(id="x", prompt="x", type="ranking", choices=None, csv_columns=[])
    return Ranking(question=q, rank_columns=[pl.Series(c) for c in cols])



from nixos_survey_lib.aggregate import rank_distribution
from nixos_survey_lib.types import RankDistribution


def test_rank_distribution_per_position_basic():
    # 4 respondents, 3 positions.
    r = _rk([
        ["A", "B", "C"],
        ["A", "C", "B"],
        ["B", "A", "C"],
        ["C", "A", "B"],
    ])
    dist = rank_distribution(r, min_count=1)
    assert isinstance(dist, RankDistribution)
    assert dist.segment_labels == ["#1", "#2", "#3", "Unranked"]
    by = {it.label: it.percents for it in dist.items}
    # A: rank1 x2 (50%), rank2 x2 (50%), rank3 x0, unranked 0.
    assert by["A"] == [50.0, 50.0, 0.0, 0.0]
    # B: rank1 x1 (25%), rank2 x1 (25%), rank3 x2 (50%), unranked 0.
    assert by["B"] == [25.0, 25.0, 50.0, 0.0]
    # Sorted by average rank ascending: A avg=1.5 < B avg=2.25 = C avg=2.25 (tie -> label asc).
    assert dist.items[0].label == "A"
    assert dist.items[1].label == "B"
    assert dist.items[2].label == "C"


def test_rank_distribution_sorted_by_avg_rank_not_top_share():
    # P is always ranked #2 (avg rank 2.0, top-band share 0%).
    # Q is ranked #1 by one respondent but #3 by the other three
    #   (avg rank 2.5, top-band share 25%).
    # Old sort (top-band desc) would put Q first.
    # New sort (avg rank asc) must put P first because 2.0 < 2.5.
    r = _rk([
        ["Q", "P", None],  # Q@1, P@2
        ["X", "P", "Q"],   # X@1, P@2, Q@3
        ["X", "P", "Q"],   # X@1, P@2, Q@3
        ["X", "P", "Q"],   # X@1, P@2, Q@3
    ])
    dist = rank_distribution(r, min_count=1)
    labels = [it.label for it in dist.items]
    p_idx = labels.index("P")
    q_idx = labels.index("Q")
    assert p_idx < q_idx, (
        f"P (avg rank 2.0) should sort before Q (avg rank 2.5), "
        f"but got order {labels}"
    )


def test_rank_distribution_unranked_share():
    # 2 respondents; choice D only appears for one of them, never for the other.
    r = _rk([
        ["A", "D"],
        ["A", "B"],
    ])
    dist = rank_distribution(r, min_count=1)
    by = {it.label: it.percents for it in dist.items}
    # D: rank2 x1 (50%), unranked = 100 - 50 = 50%.
    assert by["D"] == [0.0, 50.0, 50.0]
    assert dist.segment_labels == ["#1", "#2", "Unranked"]


def test_rank_distribution_suppresses_below_min_count():
    # A ranked by 5 respondents, B by only 2.
    rows = [["A", "B"]] * 2 + [["A", "C"]] * 3
    r = _rk(rows)
    dist = rank_distribution(r, min_count=5)
    labels = {it.label for it in dist.items}
    assert "A" in labels
    # B (2) and C (3) both below min_count=5 -> suppressed.
    assert "B" not in labels
    assert "C" not in labels


def test_rank_distribution_bands_collapse_tail_to_unranked():
    # 1 respondent ranking 4 positions; bands (1,2),(3,3); position 4 folds to unranked.
    r = _rk([
        ["A", "B", "C", "D"],
    ])
    dist = rank_distribution(r, bands=[(1, 2), (3, 3)], min_count=1)
    assert dist.segment_labels == ["1-2", "3", "Unranked"]
    by = {it.label: it.percents for it in dist.items}
    # A pos1 -> band "1-2" (100%); B pos2 -> band "1-2" (100%);
    # C pos3 -> band "3" (100%); D pos4 -> past last band -> unranked (100%).
    assert by["A"] == [100.0, 0.0, 0.0]
    assert by["C"] == [0.0, 100.0, 0.0]
    assert by["D"] == [0.0, 0.0, 100.0]


from nixos_survey_lib.aggregate import sankey_funnel


def _stable() -> SingleChoice:
    values = (
        ["I had no issues."] * 30
        + ["I had minor issues."] * 20
        + ["I had moderate issues."] * 10
        + ["I had severe issues but figured it out after some time."] * 8
        + ["I had severe issues and could not make the upgrade."] * 6
        + ["I have not upgraded."] * 12
        + ["I did not know there was a new stable release."] * 7
        + ["Skipped"] * 3
    )
    return _sc(values, qid="stable_upgrade")


def test_sankey_funnel_excludes_skipped():
    nodes, links = sankey_funnel(_stable())
    # No node or link mentions "Skipped".
    assert "Skipped" not in nodes
    for l in links:
        assert l["source"] != "Skipped" and l["target"] != "Skipped"


def test_sankey_funnel_stage_a_b_counts():
    nodes, links = sankey_funnel(_stable())
    by = {(l["source"], l["target"]): l["value"] for l in links}
    # Knew = everyone except didn't-know and Skipped = 30+20+10+8+6+12 = 86
    assert by[("All", "Knew")] == 86
    assert by[("All", "Didn't know")] == 7


def test_sankey_funnel_stage_c_counts():
    nodes, links = sankey_funnel(_stable())
    by = {(l["source"], l["target"]): l["value"] for l in links}
    # Upgraded = all severities = 30+20+10+8+6 = 74
    assert by[("Knew", "Upgraded")] == 74
    assert by[("Knew", "Did not upgrade")] == 12


def test_sankey_funnel_stage_d_severity():
    nodes, links = sankey_funnel(_stable())
    by = {(l["source"], l["target"]): l["value"] for l in links}
    assert by[("Upgraded", "No issues")] == 30
    assert by[("Upgraded", "Minor")] == 20
    assert by[("Upgraded", "Moderate")] == 10
    assert by[("Upgraded", "Severe (resolved)")] == 8
    assert by[("Upgraded", "Severe (stuck)")] == 6


def test_sankey_funnel_nodes_in_stage_order():
    nodes, links = sankey_funnel(_stable())
    assert nodes == [
        "All", "Knew", "Didn't know", "Upgraded", "Did not upgrade",
        "No issues", "Minor", "Moderate", "Severe (resolved)", "Severe (stuck)",
    ]


def test_sankey_funnel_drops_sub_min_count_links_and_orphan_nodes():
    # Severe (stuck) has only 2 respondents → its link drops; with no other
    # link touching it, the node is omitted too.
    values = (
        ["I had no issues."] * 30
        + ["I had severe issues and could not make the upgrade."] * 2
        + ["I have not upgraded."] * 12
        + ["I did not know there was a new stable release."] * 7
    )
    nodes, links = sankey_funnel(_sc(values, qid="stable_upgrade"))
    by = {(l["source"], l["target"]): l["value"] for l in links}
    assert ("Upgraded", "Severe (stuck)") not in by
    assert "Severe (stuck)" not in nodes
    # Upgraded total counts only surviving severity respondents? No — the
    # Knew->Upgraded value reflects ALL upgraded respondents (32), since the
    # respondent existed even though their leaf link is suppressed.
    assert by[("Knew", "Upgraded")] == 32


from nixos_survey_lib.aggregate import sankey_links


def test_sankey_links_basic_cooccurrence():
    x = _sc(["3 to 4 years"] * 6 + ["1 to 2 years"] * 6, qid="years_using_nix")
    y = _sc(["No issues"] * 6 + ["Minor"] * 6, qid="outcome")
    nodes, links = sankey_links(x, y, min_count=5)
    by = {(l["source"], l["target"]): l["value"] for l in links}
    assert by[("3 to 4 years", "No issues")] == 6
    assert by[("1 to 2 years", "Minor")] == 6


def test_sankey_links_drops_sub_min_count():
    # The (1 to 2 years, Minor) pair has only 2 → dropped; that y-node has no
    # other link → omitted.
    x = _sc(["3 to 4 years"] * 6 + ["1 to 2 years"] * 2, qid="years_using_nix")
    y = _sc(["No issues"] * 6 + ["Minor"] * 2, qid="outcome")
    nodes, links = sankey_links(x, y, min_count=5)
    by = {(l["source"], l["target"]): l["value"] for l in links}
    assert ("1 to 2 years", "Minor") not in by
    assert "Minor" not in nodes
    assert "1 to 2 years" not in nodes
    assert "No issues" in nodes
    assert "3 to 4 years" in nodes


def test_sankey_links_excludes_either_side():
    x = _sc(["3 to 4 years"] * 6 + ["I don't use Nix"] * 6, qid="years_using_nix")
    y = _sc(["No issues"] * 6 + ["No issues"] * 6, qid="outcome")
    nodes, links = sankey_links(x, y, exclude=["I don't use Nix"], min_count=5)
    by = {(l["source"], l["target"]): l["value"] for l in links}
    assert by[("3 to 4 years", "No issues")] == 6
    assert "I don't use Nix" not in nodes


def test_sankey_links_x_band_groups_values():
    x = _sc(["7 to 8 years"] * 3 + ["9 to 10 years"] * 3, qid="years_using_nix")
    y = _sc(["No issues"] * 6, qid="outcome")
    band = {"7 to 8 years": "7-10y", "9 to 10 years": "7-10y"}
    nodes, links = sankey_links(x, y, x_band=band, min_count=5)
    by = {(l["source"], l["target"]): l["value"] for l in links}
    assert by[("7-10y", "No issues")] == 6
    assert "7 to 8 years" not in nodes


def test_sankey_links_y_map_groups_values():
    x = _sc(["3 to 4 years"] * 6, qid="years_using_nix")
    y = _sc(["I had moderate issues."] * 3
            + ["I had severe issues and could not make the upgrade."] * 3,
            qid="outcome")
    ymap = {
        "I had moderate issues.": "Problems",
        "I had severe issues and could not make the upgrade.": "Problems",
    }
    nodes, links = sankey_links(x, y, y_map=ymap, min_count=5)
    by = {(l["source"], l["target"]): l["value"] for l in links}
    assert by[("3 to 4 years", "Problems")] == 6


def test_sankey_links_node_order_x_then_y():
    x = _sc(["1 to 2 years"] * 6 + ["3 to 4 years"] * 6, qid="years_using_nix")
    y = _sc(["No issues"] * 6 + ["Minor"] * 6, qid="outcome")
    nodes, links = sankey_links(
        x, y, x_band={"1 to 2 years": "1-2y", "3 to 4 years": "3-4y"}, min_count=5
    )
    # x-nodes precede y-nodes.
    assert nodes.index("1-2y") < nodes.index("No issues")
    assert nodes.index("3-4y") < nodes.index("No issues")


def test_sankey_links_raises_on_x_y_collision():
    # x and y share a node name "Shared" → must raise ValueError.
    x = _sc(["Shared"] * 6, qid="x")
    y = _sc(["Shared"] * 6, qid="y")
    import pytest
    with pytest.raises(ValueError, match="collide"):
        sankey_links(x, y, min_count=1)


def test_sankey_links_x_band_resolves_collision():
    # After renaming via x_band the collision disappears → no error, link produced.
    x = _sc(["Shared"] * 6, qid="x")
    y = _sc(["Shared"] * 6, qid="y")
    nodes, links = sankey_links(x, y, x_band={"Shared": "Shared (x side)"}, min_count=1)
    assert "Shared (x side)" in nodes
    assert "Shared" in nodes
    assert links[0]["source"] == "Shared (x side)"
    assert links[0]["target"] == "Shared"


def test_sankey_funnel_as_percent_root_links_sum_to_100():
    # _stable() has 93 non-Skipped respondents: knew=86, didnt_know=7.
    # As percent of 93: Knew≈92.5, Didn't know≈7.5 → sum ≈ 100.
    nodes, links = sankey_funnel(_stable(), as_percent=True)
    by = {(l["source"], l["target"]): l["value"] for l in links}
    root_sum = by[("All", "Knew")] + by[("All", "Didn't know")]
    assert abs(root_sum - 100.0) <= 0.2, f"root-stage out-links sum {root_sum}, expected ~100"
    # All values are floats ≤ 100, not raw counts (max raw count was 86).
    for l in links:
        assert isinstance(l["value"], float)
        assert l["value"] <= 100.0


def test_sankey_funnel_as_percent_sub5_suppressed():
    # Severe (stuck) has count=2; should be suppressed even in percent mode.
    values = (
        ["I had no issues."] * 30
        + ["I had severe issues and could not make the upgrade."] * 2
        + ["I have not upgraded."] * 12
        + ["I did not know there was a new stable release."] * 7
    )
    nodes, links = sankey_funnel(_sc(values, qid="stable_upgrade"), as_percent=True)
    by = {(l["source"], l["target"]): l["value"] for l in links}
    assert ("Upgraded", "Severe (stuck)") not in by
    assert "Severe (stuck)" not in nodes


def test_sankey_links_as_percent_values_are_percent():
    # 12 rows total (no exclusions): 6 → (A, X), 6 → (B, Y).
    # Each link is 6/12*100 = 50.0.
    x = _sc(["A"] * 6 + ["B"] * 6, qid="q1")
    y = _sc(["X"] * 6 + ["Y"] * 6, qid="q2")
    nodes, links = sankey_links(x, y, min_count=5, as_percent=True)
    by = {(l["source"], l["target"]): l["value"] for l in links}
    assert by[("A", "X")] == 50.0
    assert by[("B", "Y")] == 50.0
    total_pct = sum(l["value"] for l in links)
    assert abs(total_pct - 100.0) <= 0.2


def test_sankey_links_as_percent_sub5_suppressed():
    # (B, Y) has count=2, below min_count=5 → suppressed before percent conversion.
    x = _sc(["A"] * 6 + ["B"] * 2, qid="q1")
    y = _sc(["X"] * 6 + ["Y"] * 2, qid="q2")
    nodes, links = sankey_links(x, y, min_count=5, as_percent=True)
    by = {(l["source"], l["target"]): l["value"] for l in links}
    assert ("B", "Y") not in by
    # (A, X) is 6/8*100 = 75.0 (total rows = 8).
    assert by[("A", "X")] == 75.0


def test_upset_combinations_exclusive_membership_sizes():
    # 6 respondents over sets A, B, C:
    #   r0: A only
    #   r1: A only
    #   r2: A & B
    #   r3: B only
    #   r4: A & B & C
    #   r5: (none selected)
    m = _mc({
        "A": ["Yes", "Yes", "Yes", "No",  "Yes", "No"],
        "B": ["No",  "No",  "Yes", "Yes", "Yes", "No"],
        "C": ["No",  "No",  "No",  "No",  "Yes", "No"],
    })
    combos, set_totals, dropped = upset_combinations(
        m, min_size=1, max_combos=20,
    )

    # Exclusive memberships and their sizes:
    #   (A,)      -> 2   (r0, r1)
    #   (A, B)    -> 1   (r2)
    #   (B,)      -> 1   (r3)
    #   (A, B, C) -> 1   (r4)
    # The empty membership (r5) is never a combination.
    by_members = {c.members: c.size for c in combos}
    assert by_members == {
        ("A",): 2,
        ("A", "B"): 1,
        ("B",): 1,
        ("A", "B", "C"): 1,
    }
    # Sorted by size desc; (A,) with size 2 is first.
    assert combos[0].members == ("A",)
    assert combos[0].size == 2
    # Per-set totals follow choice_columns order A, B, C.
    # A: r0, r1, r2, r4 = 4 Yes; B: r2, r3, r4 = 3 Yes; C: r4 = 1 Yes.
    assert set_totals == [("A", 4), ("B", 3), ("C", 1)]
    assert dropped == 0


def test_upset_combinations_members_in_set_order_not_selection_order():
    # Even though respondent "selected" via columns, members must be ordered
    # by the set order (choice_columns key order), here A, B, C.
    m = _mc({
        "A": ["Yes"],
        "B": ["Yes"],
        "C": ["Yes"],
    })
    combos, _set_totals, _dropped = upset_combinations(m, min_size=1, max_combos=20)
    assert len(combos) == 1
    assert combos[0].members == ("A", "B", "C")
    assert combos[0].size == 1


def test_upset_combinations_drops_below_min_size():
    # Sizes: (A,)=6, (B,)=3, (A,B)=2.  min_size=5 keeps only (A,).
    # 2 non-empty combinations are dropped -> dropped == 2.
    m = _mc({
        "A": ["Yes"] * 6 + ["No"] * 3 + ["Yes"] * 2,
        "B": ["No"] * 6 + ["Yes"] * 3 + ["Yes"] * 2,
    })
    combos, _set_totals, dropped = upset_combinations(m, min_size=5, max_combos=20)
    assert [c.members for c in combos] == [("A",)]
    assert combos[0].size == 6
    assert dropped == 2


def test_upset_combinations_cap_counts_dropped():
    # Three distinct combinations all above the floor, but max_combos=2 keeps
    # the two largest and reports the third as dropped.
    #   (A,)      size 5
    #   (B,)      size 6
    #   (A, B)    size 7
    m = _mc({
        "A": ["Yes"] * 5 + ["No"] * 6 + ["Yes"] * 7,
        "B": ["No"] * 5 + ["Yes"] * 6 + ["Yes"] * 7,
    })
    combos, _set_totals, dropped = upset_combinations(m, min_size=5, max_combos=2)
    # Largest two by size: (A,B)=7, (B,)=6.
    assert [c.members for c in combos] == [("A", "B"), ("B",)]
    assert dropped == 1


def test_upset_combinations_default_min_size_is_five():
    # Defaults: min_size=5, max_combos=20. (A,) size 4 is below the default
    # floor and must be dropped without passing min_size explicitly.
    m = _mc({"A": ["Yes"] * 4 + ["No"] * 1})
    combos, _set_totals, dropped = upset_combinations(m)
    assert combos == []
    assert dropped == 1


def test_upset_combinations_set_totals_full_order():
    # set_totals always lists every set in choice order, even sets that never
    # appear in any kept combination.
    m = _mc({
        "A": ["Yes"] * 6,
        "B": ["No"] * 6,
        "C": ["No"] * 6,
    })
    _combos, set_totals, _dropped = upset_combinations(m, min_size=5, max_combos=20)
    assert set_totals == [("A", 6), ("B", 0), ("C", 0)]
