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
    ranking_avg,
    ranking_top_n,
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
    ranking_bar,
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

    page = Page(
        year=2025,
        title="2025 Survey Results",
        sections=[
            Section("people", "People", note="Categories with fewer than 5 respondents are not shown.", rows=[
                Row("country", "Country", question=q("country"), commentary=cm["country"],
                    chart=horizontal_bar(counts_single(r.country, bucket_min_percent=None, bucket_action="drop"))),
                Row("age", "Age", question=q("age"), commentary=cm["age"],
                    chart=horizontal_bar(counts_single(r.age, order=AGE_ORDER, bucket_min_percent=None, bucket_action="drop"))),
                Row("gender_identity", "Gender Identity", question=q("gender_identity"), commentary=cm["gender_identity"],
                    chart=horizontal_bar(counts_single(r.gender_identity, bucket_min_percent=None, bucket_action="drop"))),
                Row("transgender", "Transgender Identity", question=q("transgender"), commentary=cm["transgender"],
                    chart=horizontal_bar(counts_single(r.transgender, bucket_min_percent=None, bucket_action="drop"))),
                Row("years_programming", "Years Coding", question=q("years_programming"), commentary=cm["years_programming"],
                    chart=horizontal_bar(counts_single(r.years_programming, order=YEARS_PROGRAMMING_ORDER, bucket_min_percent=None, bucket_action="drop"))),
                Row("role", "Role", question=q("role"), commentary=cm["role"],
                    chart=horizontal_bar(counts_single(r.role, bucket_min_percent=None, bucket_action="drop"))),
                Row("industry", "Industry", question=q("industry"), commentary=cm["industry"],
                    chart=horizontal_bar(counts_single(r.industry, bucket_min_percent=None, bucket_action="drop"))),
                Row("domain", "Domain", question=q("domain"), commentary=cm["domain"],
                    chart=horizontal_bar(counts_single(r.domain, bucket_min_percent=None, bucket_action="drop"))),
            ]),
            Section("technology", "Technology", rows=[
                Row("operating_systems", "Operating Systems", question=q("operating_systems"), commentary=cm["operating_systems"],
                    chart=horizontal_bar(counts_multi(r.operating_systems))),
                Row("target_triple", "Target Triple", question=q("target_triple"), commentary=cm["target_triple"],
                    chart=horizontal_bar(counts_multi(r.target_triple))),
                Row("experimental_features", "Experimental Features", question=q("experimental_features"), commentary=cm["experimental_features"],
                    chart=horizontal_bar(counts_multi(r.experimental_features))),
                Row("install_method", "Install Method", question=q("install_method"), commentary=cm["install_method"],
                    chart=horizontal_bar(counts_multi(r.install_method))),
                Row("nix_implementations", "Nix Implementations", question=q("nix_implementations"), commentary=cm["nix_implementations"],
                    chart=horizontal_bar(counts_multi(r.nix_implementations))),
                Row("infrastructure", "Infrastructure", question=q("infrastructure"), commentary=cm["infrastructure"],
                    chart=horizontal_bar(counts_multi(r.infrastructure))),
                Row("nix_version", "Nix Version", question=q("nix_version"), commentary=cm["nix_version"],
                    chart=horizontal_bar(counts_single(nix_version, bucket_min_percent=0.1))),
                Row("nixos_releases", "NixOS Release", question=q("nixos_releases"), commentary=cm["nixos_releases"],
                    chart=horizontal_bar(counts_multi(r.nixos_releases))),
                Row("hardware_configuration", "Hardware Configuration", question=q("hardware_configuration"), commentary=cm["hardware_configuration"],
                    chart=horizontal_bar(counts_multi(r.hardware_configuration))),
                Row("software_ecosystems", "Software Ecosystems", question=q("software_ecosystems"), commentary=cm["software_ecosystems"],
                    chart=horizontal_bar(counts_multi(r.software_ecosystems))),
                Row("nix_on_os", "Operating systems running Nix", question=q("nix_on_os"), commentary=cm["nix_on_os"],
                    chart=horizontal_bar(counts_multi(r.nix_on_os))),
            ]),
            Section("experience", "Experience", rows=[
                Row("stable_upgrade", "Stable Upgrade", question=q("stable_upgrade"), commentary=cm["stable_upgrade"],
                    chart=horizontal_bar(counts_single(r.stable_upgrade, order=STABLE_UPGRADE_ORDER, bucket_min_percent=None))),
                Row("involvement", "Involvement", question=q("involvement"), commentary=cm["involvement"],
                    chart=horizontal_bar(counts_multi(r.involvement))),
                Row("years_using_nix", "Years using Nix", question=q("years_using_nix"), commentary=cm["years_using_nix"],
                    chart=horizontal_bar(counts_single(r.years_using_nix, order=YEARS_USING_NIX_ORDER, bucket_min_percent=None))),
                Row("skill_level", "Nix Skill Level", question=q("skill_level"), commentary=cm["skill_level"],
                    chart=horizontal_bar(counts_single(r.skill_level, order=SKILL_ORDER, bucket_min_percent=None))),
                Row("first_heard_which", "First heard of: Nix or NixOS", question=q("first_heard_which"), commentary=cm["first_heard_which"],
                    chart=horizontal_bar(counts_single(r.first_heard_which))),
                Row("first_heard_how", "First-exposure channel", question=q("first_heard_how"), commentary=cm["first_heard_how"],
                    chart=horizontal_bar(counts_single(r.first_heard_how))),
                Row("user_types", "User types",
                    question="Which user types do you identify with?",
                    commentary=cm["user_types"],
                    chart=horizontal_bar(counts_multi(r.user_types))),
                Row("traits", "Self-described skills", question=q("traits"), commentary=cm["traits"],
                    chart=horizontal_bar(counts_multi(r.traits))),
                Row("improvements", "Wished-for improvements", question=q("improvements"), commentary=cm["improvements"],
                    chart=horizontal_bar(counts_multi(r.improvements))),
                Row("regular_toolset", "Regular toolset", question=q("regular_toolset"), commentary=cm["regular_toolset"],
                    chart=horizontal_bar(counts_single(r.regular_toolset))),
                Row("help_success_frequency", "Help-search success rate", question=q("help_success_frequency"), commentary=cm["help_success_frequency"],
                    chart=horizontal_bar(counts_single(r.help_success_frequency, order=HELP_FREQUENCY_ORDER, bucket_min_percent=None))),
                Row("skill_x_experience", "Expertise vs Experience",
                    question=f"{q('skill_level')} × {q('years_using_nix')}",
                    commentary=cm["skill_x_experience"],
                    chart=heatmap(crosstab(
                        r.years_using_nix, r.skill_level,
                        normalize="y",
                        x_order=YEARS_USING_NIX_ORDER, y_order=SKILL_ORDER,
                        x_exclude=["I don't use Nix", "Prefer not to say", "Skipped"],
                        y_exclude=["I have never used Nix", "Prefer not to say", "Skipped"],
                    ), height=356)),
                Row("experience_x_skill", "Experience vs Expertise",
                    question=f"{q('years_using_nix')} × {q('skill_level')}",
                    commentary=cm["experience_x_skill"],
                    chart=heatmap(crosstab(
                        r.skill_level, r.years_using_nix,
                        normalize="y",
                        x_order=SKILL_ORDER, y_order=YEARS_USING_NIX_ORDER,
                        x_exclude=["I have never used Nix", "Prefer not to say", "Skipped"],
                        y_exclude=["I don't use Nix", "Prefer not to say", "Skipped"],
                    ), height=460)),
                Row("traits_rate_by_skill", "Trait rate by skill level",
                    question=f"{q('traits')} × {q('skill_level')}",
                    commentary=cm["traits_rate_by_skill"],
                    chart=heatmap(crosstab_multi(
                        r.traits, r.skill_level,
                        denominator="rate",
                        x_order=["Beginner", "Intermediate", "Advanced"],
                        x_exclude=["Skipped", "Prefer not to say", "I have never used Nix"],
                    ), height=588, vm_min=0, vm_max=100)),
                Row("traits_lift_by_skill", "Trait lift by skill level",
                    question=f"{q('traits')} × {q('skill_level')}",
                    commentary=cm["traits_lift_by_skill"],
                    chart=heatmap(crosstab_multi(
                        r.traits, r.skill_level,
                        denominator="lift",
                        x_order=["Beginner", "Intermediate", "Advanced"],
                        x_exclude=["Skipped", "Prefer not to say", "I have never used Nix"],
                    ), height=588)),
                Row("traits_rate_by_experience", "Trait rate by years using Nix",
                    question=f"{q('traits')} × {q('years_using_nix')}",
                    commentary=cm["traits_rate_by_experience"],
                    chart=heatmap(crosstab_multi(
                        r.traits, r.years_using_nix,
                        denominator="rate",
                        x_order=YEARS_USING_NIX_ORDER,
                        x_exclude=["Skipped", "Prefer not to say", "I don't use Nix"],
                    ), height=540, vm_min=0, vm_max=100)),
                Row("traits_lift_by_experience", "Trait lift by years using Nix",
                    question=f"{q('traits')} × {q('years_using_nix')}",
                    commentary=cm["traits_lift_by_experience"],
                    chart=heatmap(crosstab_multi(
                        r.traits, r.years_using_nix,
                        denominator="lift",
                        x_order=YEARS_USING_NIX_ORDER,
                        x_exclude=["Skipped", "Prefer not to say", "I don't use Nix"],
                    ), height=540)),
            ]),
            Section("workplace", "Workplace", rows=[
                Row("workplace_uses_nix", "Workplace adoption",
                    question=q("workplace_uses_nix"),
                    commentary=cm["workplace_uses_nix"],
                    chart=horizontal_bar(counts_single(workplace_uses_nix,
                                                       order=["Yes", "No", "Other", "Skipped"],
                                                       bucket_min_percent=None))),
                Row("workplace_decision", "Workplace decision-maker",
                    question=q("workplace_decision"),
                    commentary=cm["workplace_decision"],
                    chart=horizontal_bar(counts_single(workplace_decision,
                                                       order=["Yes", "No", "Other", "Skipped"],
                                                       bucket_min_percent=None))),
            ]),
            Section("contribution", "Contribution", rows=[
                Row("contribution_experience", "Contributor experience",
                    question=q("contribution_experience"),
                    commentary=cm["contribution_experience"],
                    chart=horizontal_bar(counts_multi(r.contribution_experience))),
            ]),
            Section("foundation", "Foundation", rows=[
                Row("donation_incentives", "Donation incentives",
                    question=q("donation_incentives"),
                    commentary=cm["donation_incentives"],
                    chart=horizontal_bar(counts_multi(r.donation_incentives))),
                Row("foundation_priorities", "Foundation funding priorities",
                    question=q("foundation_priorities"),
                    commentary=cm["foundation_priorities"],
                    chart=ranking_bar(ranking_avg(r.foundation_priorities))),
            ]),
            Section("information_seeking", "Information seeking", rows=[
                Row("objects_interact_with", "Objects you interact with",
                    question=q("objects_interact_with"),
                    commentary=cm["objects_interact_with"],
                    chart=ranking_bar(ranking_avg(r.objects_interact_with))),
                Row("help_resources", "Help resources (top-5 appearances)",
                    question=q("help_resources"),
                    commentary=cm["help_resources"],
                    chart=ranking_bar(ranking_top_n(r.help_resources, n=5))),
            ]),
        ],
    )

    write_page(page, Path(out_path))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
