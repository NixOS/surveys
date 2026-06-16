# community/2025/process.py
"""Compose the NixOS Community Survey 2025 results page.

Reads:
  argv[1] — path to the raw CSV (gitignored; supplied via pkgs.requireFile in Nix builds)
  argv[2] — path to write results-2025.json to

Year-specific knowledge lives in this file: which questions go in which
sections, label orders for ordinal data, references to commentary.md.

Generic logic lives in nixos_survey_lib.
"""
import sys
from pathlib import Path

from nixos_survey_lib.aggregate import (
    counts_multi,
    counts_single,
    crosstab,
    crosstab_multi,
    rank_distribution,
    sankey_funnel,
    sankey_links,
    upset_combinations,
)
from nixos_survey_lib.loader import (
    load_commentary,
    load_responses,
    load_schema,
)
from nixos_survey_lib.normalize import (
    extract_first_semver,
    normalize_yes_no,
)
from nixos_survey_lib.page import write_page
from nixos_survey_lib.render_echarts import (
    heatmap,
    horizontal_bar,
    likert_bar,
    line_chart,
    lollipop,
    rank_distribution_bar,
    sankey,
    upset,
)
from nixos_survey_lib.types import Page, Row, Section


# --- Ordinal orderings used by multiple rows ------------------------------

AGE_ORDER = [
    "Under 18", "18-24", "25-34", "35-44", "45-54", "55-64", "65 or older",
    "Prefer not to say", "Skipped",
]

YEARS_PROGRAMMING_ORDER = [
    "I have never programmed", "Less than 1 year", "1 to 4 years",
    "5 to 9 years", "10 to 14 years", "15 to 19 years", "20 to 24 years",
    "25 to 29 years", "30 to 34 years", "35 to 39 years", "40 to 44 years",
    "45 to 49 years", "More than 50 years", "Prefer not to say", "Skipped",
]

YEARS_USING_NIX_ORDER = [
    "I don't use Nix", "Less than 1 year", "1 to 2 years", "3 to 4 years",
    "5 to 6 years", "7 to 8 years", "9 to 10 years", "11 or more years",
    "Prefer not to say", "Skipped",
]

SKILL_ORDER = [
    "I have never used Nix", "Beginner", "Intermediate", "Advanced",
    "Prefer not to say", "Skipped",
]

STABLE_UPGRADE_ORDER = [
    "I did not know there was a new stable release.",
    "I have not upgraded.",
    "I had no issues.",
    "I had minor issues.",
    "I had moderate issues.",
    "I had severe issues but figured it out after some time.",
    "I had severe issues and could not make the upgrade.",
    "Skipped",
]

HELP_FREQUENCY_ORDER = [
    "Always", "Often", "Sometimes", "Rarely", "Never", "Skipped",
]

# Phase 3 Sankey staging. Straight apostrophes throughout to match CSV values.
YEARS_USING_NIX_BAND = {
    "Less than 1 year": "<1y",
    "1 to 2 years": "1-2y",
    "3 to 4 years": "3-4y",
    "5 to 6 years": "5-6y",
    "7 to 8 years": "7-10y",
    "9 to 10 years": "7-10y",
    "11 or more years": "11y+",
}

STABLE_UPGRADE_OUTCOME_MAP = {
    "I had no issues.": "No issues",
    "I had minor issues.": "Minor",
    "I had moderate issues.": "Problems",
    "I had severe issues but figured it out after some time.": "Problems",
    "I had severe issues and could not make the upgrade.": "Problems",
    "I have not upgraded.": "Did not upgrade",
}

STABLE_UPGRADE_CROSS_EXCLUDE = [
    "I don't use Nix",
    "Prefer not to say",
    "Skipped",
    "I did not know there was a new stable release.",
]


def main(csv_path: str, out_path: str) -> None:
    here = Path(__file__).resolve().parent
    schema = load_schema(here / "survey.yaml")
    r = load_responses(Path(csv_path), schema=schema)
    cm = load_commentary(here / "commentary.md")

    # Nix version is free-text; extract semver and bucket rare ones.
    nix_version = extract_first_semver(r.nix_version)

    # Free-text Yes/No questions
    workplace_uses_nix = normalize_yes_no(r.workplace_uses_nix)
    workplace_decision = normalize_yes_no(r.workplace_decision)

    def q(qid: str) -> str:
        return r[qid].question.prompt

    _skill_x_exp_ct = crosstab(
        r.years_using_nix, r.skill_level,
        normalize="y",
        x_order=YEARS_USING_NIX_ORDER, y_order=SKILL_ORDER,
        x_exclude=["I don't use Nix", "Prefer not to say", "Skipped"],
        y_exclude=["I have never used Nix", "Prefer not to say", "Skipped"],
    )
    _traits_rate_exp_ct = crosstab_multi(
        r.traits, r.years_using_nix,
        denominator="rate",
        x_order=YEARS_USING_NIX_ORDER,
        x_exclude=["Skipped", "Prefer not to say", "I don't use Nix"],
    )

    su_funnel_nodes, su_funnel_links = sankey_funnel(r.stable_upgrade, as_percent=True)
    su_cross_nodes, su_cross_links = sankey_links(
        r.years_using_nix, r.stable_upgrade,
        x_band=YEARS_USING_NIX_BAND,
        y_map=STABLE_UPGRADE_OUTCOME_MAP,
        exclude=STABLE_UPGRADE_CROSS_EXCLUDE,
        as_percent=True,
    )
    discovery_nodes, discovery_links = sankey_links(
        r.first_heard_which, r.first_heard_how,
        x_band={"I don’t remember": "Don’t recall (Nix vs NixOS)"},
        exclude=["Skipped"],
        as_percent=True,
    )

    page = Page(
        year=2025,
        title="2025 Survey Results",
        intro_meta="3,399 responses · September 1 — December 15, 2025",
        intro_paragraphs=[
            "The 2025 NixOS Community Survey ran from September 1 to December 15, 2025, drawing 3,399 full responses — a 48% increase over the 2,290 received in 2024.",
            "The growth reflects a noticeably newer audience: 28.9% of respondents started using Nix in the past year, and 82.5% have under four years of experience. New questions in this year's survey, and the additional charts that accompany them, were added to surface insights into who that new majority is, what tools they use, and where they look for help.",
        ],
        sections=[
            Section("people", "People", note="Categories with fewer than 5 respondents are not shown.", rows=[
                Row("country", "Country", question=q("country"), commentary=cm["country"],
                    charts=[horizontal_bar(counts_single(r.country, bucket_min_percent=None, bucket_action="drop"))]),
                Row("age", "Age", question=q("age"), commentary=cm["age"],
                    charts=[horizontal_bar(counts_single(r.age, order=AGE_ORDER, bucket_min_percent=None, bucket_action="drop"))]),
                Row("gender_identity", "Gender Identity", question=q("gender_identity"), commentary=cm["gender_identity"],
                    charts=[horizontal_bar(counts_single(r.gender_identity, bucket_min_percent=None, bucket_action="drop"))]),
                Row("transgender", "Transgender Identity", question=q("transgender"), commentary=cm["transgender"],
                    charts=[horizontal_bar(counts_single(r.transgender, bucket_min_percent=None, bucket_action="drop"))]),
                Row("years_programming", "Years Coding", question=q("years_programming"), commentary=cm["years_programming"],
                    charts=[horizontal_bar(counts_single(r.years_programming, order=YEARS_PROGRAMMING_ORDER, bucket_min_percent=None, bucket_action="drop"))]),
                Row("role", "Role", question=q("role"), commentary=cm["role"],
                    charts=[lollipop(counts_single(r.role, bucket_min_percent=None, bucket_action="drop"))]),
                Row("industry", "Industry", question=q("industry"), commentary=cm["industry"],
                    charts=[lollipop(counts_single(r.industry, bucket_min_percent=None, bucket_action="drop"))]),
                Row("domain", "Domain", question=q("domain"), commentary=cm["domain"],
                    charts=[lollipop(counts_single(r.domain, bucket_min_percent=None, bucket_action="drop"))]),
            ]),
            Section("technology", "Technology", rows=[
                Row("operating_systems", "Operating Systems", question=q("operating_systems"), commentary=cm["operating_systems"],
                    charts=[horizontal_bar(counts_multi(r.operating_systems))]),
                Row("nix_on_os", "Operating systems running Nix", question=q("nix_on_os"), commentary=cm["nix_on_os"],
                    charts=[horizontal_bar(counts_multi(r.nix_on_os))]),
                Row("target_triple", "Target Triple", question=q("target_triple"), commentary=cm["target_triple"],
                    charts=[horizontal_bar(counts_multi(r.target_triple))]),
                Row("experimental_features", "Experimental Features", question=q("experimental_features"), commentary=cm["experimental_features"],
                    charts=[lollipop(counts_multi(r.experimental_features))]),
                Row("install_method", "Install Method", question=q("install_method"), commentary=cm["install_method"],
                    charts=[horizontal_bar(counts_multi(r.install_method))]),
                Row("nix_implementations", "Nix Implementations", question=q("nix_implementations"), commentary=cm["nix_implementations"],
                    charts=[horizontal_bar(counts_multi(r.nix_implementations))]),
                Row("infrastructure", "Infrastructure", question=q("infrastructure"), commentary=cm["infrastructure"],
                    charts=[horizontal_bar(counts_multi(r.infrastructure))]),
                Row("nix_version", "Nix Version", question=q("nix_version"), commentary=cm["nix_version"],
                    charts=[lollipop(counts_single(nix_version, bucket_min_percent=0.1))]),
                Row("nixos_releases", "NixOS Release", question=q("nixos_releases"), commentary=cm["nixos_releases"],
                    charts=[horizontal_bar(counts_multi(r.nixos_releases))]),
                Row("hardware_configuration", "Hardware Configuration", question=q("hardware_configuration"), commentary=cm["hardware_configuration"],
                    charts=[horizontal_bar(counts_multi(r.hardware_configuration))]),
                Row("software_ecosystems", "Software Ecosystems", question=q("software_ecosystems"), commentary=cm["software_ecosystems"],
                    charts=[lollipop(counts_multi(r.software_ecosystems))]),
            ]),
            Section("experience", "Experience", rows=[
                Row("stable_upgrade", "Stable Upgrade", question=q("stable_upgrade"), commentary=cm["stable_upgrade"], wide=True,
                    charts=[
                        likert_bar(
                            counts_single(r.stable_upgrade, order=STABLE_UPGRADE_ORDER,
                                          exclude=["Skipped"], bucket_min_percent=None),
                            positive=["I had no issues.", "I had minor issues."],
                            negative=[
                                "I had moderate issues.",
                                "I had severe issues but figured it out after some time.",
                                "I had severe issues and could not make the upgrade.",
                            ],
                            neutral=[
                                "I did not know there was a new stable release.",
                                "I have not upgraded.",
                            ],
                            title="Outcome mix (100%)",
                        ),
                        sankey(su_funnel_nodes, su_funnel_links, title="Decision funnel"),
                        sankey(su_cross_nodes, su_cross_links, title="Upgrade outcome by experience"),
                    ]),
                Row("involvement", "Involvement", question=q("involvement"), commentary=cm["involvement"],
                    charts=[horizontal_bar(counts_multi(r.involvement))]),
                Row("years_using_nix", "Years using Nix", question=q("years_using_nix"), commentary=cm["years_using_nix"],
                    charts=[horizontal_bar(counts_single(r.years_using_nix, order=YEARS_USING_NIX_ORDER, bucket_min_percent=None))]),
                Row("skill_level", "Nix Skill Level", question=q("skill_level"), commentary=cm["skill_level"],
                    charts=[horizontal_bar(counts_single(r.skill_level, order=SKILL_ORDER, bucket_min_percent=None))]),
                Row("first_heard_which", "First heard of: Nix or NixOS", question=q("first_heard_which"), commentary=cm["first_heard_which"],
                    charts=[horizontal_bar(counts_single(r.first_heard_which))]),
                Row("first_heard_how", "First-exposure channel", question=q("first_heard_how"), commentary=cm["first_heard_how"],
                    charts=[horizontal_bar(counts_single(r.first_heard_how))]),
                Row("discovery_flow", "Discovery flow",
                    question=f"{q('first_heard_which')} → {q('first_heard_how')}",
                    commentary=cm["discovery_flow"], wide=True,
                    charts=[sankey(discovery_nodes, discovery_links)]),
                Row("user_types", "User types",
                    question="Which user types do you identify with?",
                    commentary=cm["user_types"], wide=True,
                    charts=[
                        horizontal_bar(counts_multi(r.user_types)),
                        upset(
                            *upset_combinations(r.user_types),
                            height=560,
                            set_labels={
                                c: c.split(".", 1)[0] for c in r.user_types.choices()
                            },
                        ),
                    ]),
                Row("traits", "Self-described skills", question=q("traits"), commentary=cm["traits"],
                    charts=[horizontal_bar(counts_multi(r.traits))]),
                Row("improvements", "Wished-for improvements", question=q("improvements"), commentary=cm["improvements"],
                    charts=[horizontal_bar(counts_multi(r.improvements))]),
                Row("regular_toolset", "Regular toolset", question=q("regular_toolset"), commentary=cm["regular_toolset"],
                    charts=[horizontal_bar(counts_single(r.regular_toolset))]),
                Row("help_success_frequency", "Help-search success rate", question=q("help_success_frequency"), commentary=cm["help_success_frequency"],
                    charts=[horizontal_bar(counts_single(r.help_success_frequency, order=HELP_FREQUENCY_ORDER, bucket_min_percent=None))]),
                Row("involvement_rate_by_experience", "Involvement rate by years using Nix",
                    question=f"{q('involvement')} × {q('years_using_nix')}",
                    commentary=cm["involvement_rate_by_experience"], wide=True,
                    charts=[heatmap(crosstab_multi(
                        r.involvement, r.years_using_nix,
                        denominator="rate",
                        x_order=YEARS_USING_NIX_ORDER,
                        x_exclude=["I don't use Nix", "Prefer not to say", "Skipped"],
                    ), annotate=True, height=480)]),
                Row("involvement_lift_by_experience", "Involvement lift by years using Nix",
                    question=f"{q('involvement')} × {q('years_using_nix')}",
                    commentary=cm["involvement_lift_by_experience"], wide=True,
                    charts=[heatmap(crosstab_multi(
                        r.involvement, r.years_using_nix,
                        denominator="lift",
                        x_order=YEARS_USING_NIX_ORDER,
                        x_exclude=["I don't use Nix", "Prefer not to say", "Skipped"],
                    ), annotate=True, height=480)]),
                Row("skill_x_experience", "Expertise vs Experience",
                    question=f"{q('skill_level')} × {q('years_using_nix')}",
                    commentary=cm["skill_x_experience"], wide=True,
                    charts=[
                        heatmap(_skill_x_exp_ct, annotate=True, height=356, title="Distribution"),
                        line_chart(_skill_x_exp_ct, title="Trend by tenure"),
                    ]),
                Row("experience_x_skill", "Experience vs Expertise",
                    question=f"{q('years_using_nix')} × {q('skill_level')}",
                    commentary=cm["experience_x_skill"], wide=True,
                    charts=[heatmap(crosstab(
                        r.skill_level, r.years_using_nix,
                        normalize="y",
                        x_order=SKILL_ORDER, y_order=YEARS_USING_NIX_ORDER,
                        x_exclude=["I have never used Nix", "Prefer not to say", "Skipped"],
                        y_exclude=["I don't use Nix", "Prefer not to say", "Skipped"],
                    ), annotate=True, height=460)]),
                Row("traits_rate_by_skill", "Trait rate by skill level",
                    question=f"{q('traits')} × {q('skill_level')}",
                    commentary=cm["traits_rate_by_skill"], wide=True,
                    charts=[heatmap(crosstab_multi(
                        r.traits, r.skill_level,
                        denominator="rate",
                        x_order=["Beginner", "Intermediate", "Advanced"],
                        x_exclude=["Skipped", "Prefer not to say", "I have never used Nix"],
                    ), annotate=True, height=588, vm_min=0, vm_max=100)]),
                Row("traits_lift_by_skill", "Trait lift by skill level",
                    question=f"{q('traits')} × {q('skill_level')}",
                    commentary=cm["traits_lift_by_skill"], wide=True,
                    charts=[heatmap(crosstab_multi(
                        r.traits, r.skill_level,
                        denominator="lift",
                        x_order=["Beginner", "Intermediate", "Advanced"],
                        x_exclude=["Skipped", "Prefer not to say", "I have never used Nix"],
                    ), annotate=True, height=588)]),
                Row("traits_rate_by_experience", "Trait rate by years using Nix",
                    question=f"{q('traits')} × {q('years_using_nix')}",
                    commentary=cm["traits_rate_by_experience"], wide=True,
                    charts=[
                        heatmap(_traits_rate_exp_ct, annotate=True, height=540, vm_min=0, vm_max=100),
                    ]),
                Row("traits_lift_by_experience", "Trait lift by years using Nix",
                    question=f"{q('traits')} × {q('years_using_nix')}",
                    commentary=cm["traits_lift_by_experience"], wide=True,
                    charts=[heatmap(crosstab_multi(
                        r.traits, r.years_using_nix,
                        denominator="lift",
                        x_order=YEARS_USING_NIX_ORDER,
                        x_exclude=["Skipped", "Prefer not to say", "I don't use Nix"],
                    ), annotate=True, height=540)]),
            ]),
            Section("workplace", "Workplace", rows=[
                Row("workplace_uses_nix", "Workplace adoption",
                    question=q("workplace_uses_nix"),
                    commentary=cm["workplace_uses_nix"],
                    charts=[horizontal_bar(counts_single(workplace_uses_nix,
                                                       order=["Yes", "No", "Other", "Skipped"],
                                                       bucket_min_percent=None))]),
                Row("workplace_decision", "Workplace decision-maker",
                    question=q("workplace_decision"),
                    commentary=cm["workplace_decision"],
                    charts=[horizontal_bar(counts_single(workplace_decision,
                                                       order=["Yes", "No", "Other", "Skipped"],
                                                       bucket_min_percent=None))]),
            ]),
            Section("contribution", "Contribution", rows=[
                Row("contribution_experience", "Contributor experience",
                    question=q("contribution_experience"),
                    commentary=cm["contribution_experience"], wide=True,
                    charts=[
                        horizontal_bar(counts_multi(r.contribution_experience)),
                        upset(
                            *upset_combinations(r.contribution_experience, max_combos=25),
                            height=760,
                            set_labels={
                                "I don’t plan to contribute.": "No plan",
                                "I would like to contribute, but I don’t know how to get started.": "Start?",
                                "I want to contribute to an existing effort, but don’t know how to join in.": "Join?",
                                "I tried to contribute, but got stuck after I started.": "Stuck",
                                "I received feedback, but it was unhelpful or unclear.": "Unclear",
                                "It took too long to receive feedback.": "Slow",
                                "I can’t contribute because my employer doesn’t allow it.": "Blocked",
                                "Everything I wanted to work on was already being handled by others and I don't feel the need to get involved.": "Covered",
                                "I was able to contribute on my own.": "Solo",
                                "I was able to contribute with help from the community.": "Helped",
                                "I plan to contribute in the future.": "Future",
                            },
                        ),
                    ]),
            ]),
            Section("foundation", "Foundation", rows=[
                Row("donation_incentives", "Donation incentives",
                    question=q("donation_incentives"),
                    commentary=cm["donation_incentives"],
                    charts=[horizontal_bar(counts_multi(r.donation_incentives))]),
                Row("foundation_priorities", "Foundation funding priorities",
                    question=q("foundation_priorities"),
                    commentary=cm["foundation_priorities"],
                    charts=[rank_distribution_bar(
                        rank_distribution(r.foundation_priorities, bands=[(1, 3), (4, 6), (7, 10)]),
                        bands=[(1, 3), (4, 6), (7, 10)],
                    )]),
            ]),
            Section("information_seeking", "Information seeking", rows=[
                Row("objects_interact_with", "Objects you interact with",
                    question=q("objects_interact_with"),
                    commentary=cm["objects_interact_with"],
                    charts=[rank_distribution_bar(
                        rank_distribution(r.objects_interact_with, bands=[(1, 3), (4, 6), (7, 10)]),
                        bands=[(1, 3), (4, 6), (7, 10)],
                    )]),
                Row("help_resources", "Help resources",
                    question=q("help_resources"),
                    commentary=cm["help_resources"],
                    charts=[rank_distribution_bar(
                        rank_distribution(r.help_resources, bands=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]),
                        bands=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)],
                    )]),
            ]),
        ],
    )

    write_page(page, Path(out_path))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
