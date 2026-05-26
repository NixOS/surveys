from pathlib import Path

import panel as pn
import polars as pl
from altplot import (
    heatmap_from_col_indices,
    make_multi_bar_chart_pane,
    make_multi_vs_single_heatmap,
    make_plot_row,
    make_ranking_chart,
    make_simple_bar_chart_pane,
)
from dfhelpers import (
    bucket_rare_categories_df,
    extract_first_mmp_semver_df,
    normalize_yes_no_column,
    reduce_multi_choice_to_single_column,
)

csv_data = Path(__file__).parent / "nix-community-survey-2025-completed-responses.csv"
df = pl.read_csv(csv_data)

pn.extension("vega")

people = (
    pn.pane.Markdown(
        "## People",
        styles={"font-size": "18px"},
    ),
    make_plot_row(
        md_text="""
                # Country
                European responses increased from 52% to 60%.
                North American responses decreased from 27.5% to 21.3%.
                The remaining responses changed less than 1% from the previous year.
                """,
        plot_pane=make_simple_bar_chart_pane(df, 5),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Age
                The curve has flattened and shifted.
                The largest age group of 25-34 decreased from 35.6% to 30.7%.
                The 35-44 age group also decreased from 22.7% to 19.4%.
                Age groups under 25 or over 44 increased between 0.4% and 3.1%.
                """,
        plot_pane=make_simple_bar_chart_pane(
            df,
            6,
            label_order=[
                "Under 18",
                "18-24",
                "25-34",
                "35-44",
                "45-54",
                "55-64",
                "65 or older",
                "Prefer not to say",
                "Skipped",
            ],
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Gender Identity
                """,
        plot_pane=make_simple_bar_chart_pane(df, 7),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Transgender Identity
                """,
        plot_pane=make_simple_bar_chart_pane(df, 8),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Years Coding
                There are more fine grained bins for 10+ years of experience compared to previous years.
                The groups with 4 or less years of experience have increased.
                The groups with 5 or more years of experience have decreased.
                """,
        plot_pane=make_simple_bar_chart_pane(
            df,
            9,
            label_order=[
                "I have never programmed",
                "Less than 1 year",
                "1 to 4 years",
                "5 to 9 years",
                "10 to 14 years",
                "15 to 19 years",
                "20 to 24 years",
                "25 to 29 years",
                "30 to 34 years",
                "35 to 39 years",
                "40 to 44 years",
                "45 to 49 years",
                "More than 50 years",
                "Prefer not to say",
                "Skipped",
            ],
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Role
                """,
        plot_pane=make_simple_bar_chart_pane(df, 10),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Industry
                """,
        plot_pane=make_simple_bar_chart_pane(df, 11),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Domain
                """,
        plot_pane=make_simple_bar_chart_pane(df, 12),
    ),
)


technology = (
    pn.pane.Markdown(
        "## Technology",
        styles={"font-size": "18px"},
    ),
    make_plot_row(
        md_text="""
                # Operating Systems
                """,
        plot_pane=make_multi_bar_chart_pane(df, 15, 24),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Target Triple
                """,
        plot_pane=make_multi_bar_chart_pane(df, 24, 33),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Experimental Features
                """,
        plot_pane=make_multi_bar_chart_pane(df, 46, 70),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Install Method
                """,
        plot_pane=make_multi_bar_chart_pane(df, 85, 91),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # (?:D|L|N|S|Tv)ix
                """,
        plot_pane=make_multi_bar_chart_pane(df, 91, 97),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Infrastructure
                """,
        plot_pane=make_multi_bar_chart_pane(df, 97, 107),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Nix Version
                A lack of response or a an empty string was replaced with "Skipped".
                A SemVer regular expression was used to match against the remaining answers.
                Values that did not match were replaced with "No Match".
                Finally, responses that comprised less that 0.5% were combined and replaced with "Other".
                """,
        plot_pane=make_simple_bar_chart_pane(
            extract_first_mmp_semver_df(df, 107, min_percent=0.5),
            0,
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # NixOS Release
                """,
        plot_pane=make_multi_bar_chart_pane(df, 108, 115),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Hardware Configuration
                """,
        plot_pane=make_multi_bar_chart_pane(df, 115, 120),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Software Ecosystems
                """,
        plot_pane=make_multi_bar_chart_pane(df, 120, 174),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # OS where you use Nix
                """,
        plot_pane=make_multi_bar_chart_pane(df, 77, 85),
    ),
)

print(reduce_multi_choice_to_single_column(df, 120, 174)[0])
print(bucket_rare_categories_df(reduce_multi_choice_to_single_column(df, 120, 174)[0], 0, min_percent=1))

experience = (
    pn.pane.Markdown(
        "## Experience",
        styles={"font-size": "18px"},
    ),
    make_plot_row(
        md_text="""
                # Stable Upgrade
                """,
        plot_pane=make_simple_bar_chart_pane(
            df,
            33,
            label_order=[
                "I did not know there was a new stable release.",
                "I have not upgraded.",
                "I had no issues.",
                "I had minor issues.",
                "I had moderate issues.",
                "I had severe issues but figured it out after some time.",
                "I had severe issues and could not make the upgrade.",
                "Skipped",
            ],
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Involvement
                """,
        plot_pane=make_multi_bar_chart_pane(df, 34, 44),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Experience
                """,
        plot_pane=make_simple_bar_chart_pane(
            df,
            44,
            label_order=[
                "I don't use Nix",
                "Less than 1 year",
                "1 to 2 years",
                "3 to 4 years",
                "5 to 6 years",
                "7 to 8 years",
                "9 to 10 years",
                "11 or more years",
                "Prefer not to say",
                "Skipped",
            ],
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Expertise
                About the same as last year.
                """,
        plot_pane=make_simple_bar_chart_pane(
            df,
            45,
            label_order=[
                "I have never used Nix",
                "Beginner",
                "Intermediate",
                "Advanced",
                "Prefer not to say",
                "Skipped",
            ],
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # First heard: Nix vs NixOS
                """,
        plot_pane=make_simple_bar_chart_pane(df, 70),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # How first heard about Nix or NixOS
                """,
        plot_pane=make_simple_bar_chart_pane(df, 71),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # User types
                """,
        plot_pane=make_multi_bar_chart_pane(df, 72, 77),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Which of these describe you?
                """,
        plot_pane=make_multi_bar_chart_pane(df, 174, 186),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Three improvements
                """,
        plot_pane=make_multi_bar_chart_pane(df, 186, 198),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Regular toolset
                """,
        plot_pane=make_simple_bar_chart_pane(df, 199),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Help-success frequency
                """,
        plot_pane=make_simple_bar_chart_pane(
            df,
            266,
            label_order=[
                "Always",
                "Often",
                "Sometimes",
                "Rarely",
                "Never",
                "Skipped",
            ],
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Expertise vs Experience
                """,
        plot_pane=heatmap_from_col_indices(
            df,
            44,
            45,
            value="percent",
            normalize="y",
            height=240,
            title="Percent of self-evaluated skill level normalized by skill level.",
            x_order=[
                "Less than 1 year",
                "1 to 2 years",
                "3 to 4 years",
                "5 to 6 years",
                "7 to 8 years",
                "9 to 10 years",
                "11 or more years",
            ],
            y_order=[
                "Beginner",
                "Intermediate",
                "Advanced",
            ],
            x_exclude=[
                "I don't use Nix",
                "Prefer not to say",
                "Skipped",
            ],
            y_exclude=[
                "I have never used Nix",
                "Prefer not to say",
                "Skipped",
            ],
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Trait rate by skill level
                Each cell: of respondents at this skill level, what percent picked this trait.
                Cells in a column do NOT sum to 100% — traits are multi-choice.

                Beginners overwhelmingly rely on tutorials (83%); rate drops to 57% at
                Intermediate and 18% at Advanced. Writing own NixOS modules, understanding
                overlays, and contributing upstream all climb steeply from under 20% at
                Beginner to over 70% at Advanced.
                """,
        plot_pane=make_multi_vs_single_heatmap(
            df, 174, 186, 45,
            denominator="single",
            x_order=["Beginner", "Intermediate", "Advanced"],
            x_exclude=["Skipped", "Prefer not to say", "I have never used Nix"],
            title="Trait rate by skill level",
            height=360,
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Trait lift by skill level
                Each cell: how over- or under-represented this skill level is among trait-pickers,
                relative to the overall skill distribution. 1.0× = baseline, >1.0× = over-represented,
                <1.0× = under-represented. Strips out the population-size imbalance.

                Only "rely on tutorials" is over-represented among Beginners (1.30×). Every other
                trait skews Advanced. Strongest Advanced lifts: "deeper module aspect" (3.34×),
                "contribute upstream" (3.24×), "architectural choices" (2.79×).
                """,
        plot_pane=make_multi_vs_single_heatmap(
            df, 174, 186, 45,
            denominator="lift",
            x_order=["Beginner", "Intermediate", "Advanced"],
            x_exclude=["Skipped", "Prefer not to say", "I have never used Nix"],
            title="Trait lift by skill level",
            height=360,
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Trait rate by years using Nix
                Each cell: of respondents with this much experience, what percent picked this trait.
                Cells in a column do NOT sum to 100% — traits are multi-choice.

                Tutorial reliance starts at 76% in the first year and falls to 26% by 11+ years.
                Most "advanced" trait rates climb steeply through years 1–6 and largely plateau
                after. Group sizes shrink rapidly past 5 years (665 → 225 → 98 → 53 → 42), so
                cells in the rightmost columns are noisier.
                """,
        plot_pane=make_multi_vs_single_heatmap(
            df, 174, 186, 44,
            denominator="single",
            x_order=[
                "Less than 1 year",
                "1 to 2 years",
                "3 to 4 years",
                "5 to 6 years",
                "7 to 8 years",
                "9 to 10 years",
                "11 or more years",
            ],
            x_exclude=["Skipped", "Prefer not to say", "I don't use Nix"],
            title="Trait rate by years using Nix",
            height=360,
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Trait lift by years using Nix
                Each cell: how over- or under-represented this experience bucket is among trait-pickers,
                relative to the overall experience distribution. 1.0× = baseline, >1.0× = over-represented,
                <1.0× = under-represented. Strips out the population-size imbalance.

                Tutorial reliance is the only trait over-represented in year-1 respondents
                (1.20×). All other traits skew toward more-experienced respondents, with
                strongest lifts at 5+ years for "deeper module aspect" (2.1× → 2.4×) and
                "contribute upstream" (2.1× → 2.8×). Group sizes shrink rapidly past 5 years,
                so cells in the rightmost columns are noisier.
                """,
        plot_pane=make_multi_vs_single_heatmap(
            df, 174, 186, 44,
            denominator="lift",
            x_order=[
                "Less than 1 year",
                "1 to 2 years",
                "3 to 4 years",
                "5 to 6 years",
                "7 to 8 years",
                "9 to 10 years",
                "11 or more years",
            ],
            x_exclude=["Skipped", "Prefer not to say", "I don't use Nix"],
            title="Trait lift by years using Nix",
            height=360,
        ),
    ),
)

workplace = (
    pn.pane.Markdown(
        "## Workplace",
        styles={"font-size": "18px"},
    ),
    make_plot_row(
        md_text="""
                # Does your workplace use Nix?
                Free-text answers normalized to Yes / No / Other / Skipped.
                """,
        plot_pane=make_simple_bar_chart_pane(
            normalize_yes_no_column(df, 200),
            0,
            label_order=["Yes", "No", "Other", "Skipped"],
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Did you make the workplace decision?
                Free-text answers normalized to Yes / No / Other / Skipped.
                """,
        plot_pane=make_simple_bar_chart_pane(
            normalize_yes_no_column(df, 201),
            0,
            label_order=["Yes", "No", "Other", "Skipped"],
        ),
    ),
)

app = pn.Column(
    pn.pane.Markdown(
        "# NixOS Community Survey 2025 Results",
        styles={"font-size": "18px"},
    ),
    *people,
    *technology,
    *experience,
    *workplace,
    sizing_mode="stretch_width",
    margin=20,
)
app.servable()
