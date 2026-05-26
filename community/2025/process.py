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
    extract_first_mmp_semver_df,
    normalize_yes_no_column,
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
                Man: 78.3%. Woman: 7.2%. Prefer not to say: 6.6%. Non-binary or
                non-conforming: 5.9%.
                """,
        plot_pane=make_simple_bar_chart_pane(df, 7),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Transgender Identity
                No: 81.8%. Yes: 9.8%. Prefer not to say: 7.2%.
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
                Students lead at 24.0%, ahead of full-stack (13.4%), back-end (10.7%), and
                "Other" (10.3%). Sysadmin trails at 4.8%.
                """,
        plot_pane=make_simple_bar_chart_pane(df, 10),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Industry
                "Other" is the largest single category at 21.0%, suggesting the listed
                industries miss common workplaces. Academia or education (17.6%) is the
                largest named category. Telecom (5.9%), Consulting (5.8%), and Financial
                services (4.7%) follow.
                """,
        plot_pane=make_simple_bar_chart_pane(df, 11),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Domain
                "Other" leads at 15.7%, suggesting the listed domains miss common
                categories. Web development (13.8%), open-source software development
                (10.8%), and programming languages / compilers / code analysis (9.2%)
                follow.
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
                Linux: 96.9%. Android: 57.8%. Windows: 35.5%. macOS: 24.4%. iOS: 19.6%.
                The question covers all devices, so Android and iOS counts likely include
                phone use rather than Nix deployments.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 15, 24),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Target Triple
                x86_64-linux-gnu: 94.5%. ARM combined (aarch64-linux-gnu 17.4% +
                aarch64-apple-darwin 16.2%) reaches 33.6%. RISC-V: 2.0%.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 24, 33),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Experimental Features
                Flakes (78.9%) and the new `nix` CLI (66.7%) lead. The next-ranked feature
                (pipe operators, 8.0%) trails by 58.7 points. 10.9% report using no
                experimental features; 7.9% are not sure.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 46, 70),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Install Method
                NixOS preinstall: 78.4%. Official install script from nixos.org: 36.0%.
                DeterminateSystems/nix-installer: 15.8%. Other package manager: 9.7%.
                Built from source: 3.9%.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 85, 91),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # (?:D|L|N|S|Tv)ix
                Upstream Nix: 87.5%. Lix: 14.8%. Determinate Nix: 9.8%. None: 4.2%.
                Snix: 1.2%. Tvix: 0.8%.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 91, 97),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Infrastructure
                Personal computer: 90.3%. Workstation: 55.8%. Home server: 52.6%.
                Production server: 21.4% and CI: 20.5% — roughly one-quarter the rate of
                personal-computer use.
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
                25.05 (current stable): 61.6%. Unstable: 56.8%. Sum exceeds 100%, indicating
                many respondents run more than one release across machines. 24.11: 6.6%.
                24.05: 2.2%. 23.11 or older: 1.4%.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 108, 115),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Hardware Configuration
                nixos-generate-config: 68.6%. Manual configuration: 39.0%. nixos-hardware
                repository: 26.7%. nixos-facter: 3.9%.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 115, 120),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Software Ecosystems
                NixOS configurations leads at 81.1% (a meta-result — Nix users using Nix for
                their own systems). Among programming languages: Python 45.8%, Rust 42.9%,
                Bash 36.8%, C 26.7%, JavaScript 23.5%, C++ 22.7%, Go 21.3%.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 120, 174),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # OS where you use Nix
                NixOS: 90.0%. Other GNU/Linux: 26.5%. macOS: 18.1%. Windows (via WSL):
                11.0%. Android: 7.5%. 3.7% do not use Nix.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 77, 85),
    ),
)

experience = (
    pn.pane.Markdown(
        "## Experience",
        styles={"font-size": "18px"},
    ),
    make_plot_row(
        md_text="""
                # Stable Upgrade
                No issues: 37.4%. Minor issues: 19.5%. Moderate: 4.4%. Severe but resolved:
                1.8%. Severe and unresolved: 0.9%. Not upgraded: 12.8%. Did not know about
                the release: 5.5%. Skipped: 17.7%.
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
                I use NixOS: 87.1%. Install software with Nix: 66.7%. Maintain machines
                running NixOS: 58.1%. Develop software with Nix: 48.8%. Contribute packages
                or patches to Nixpkgs: 22.8%. Develop tools or infrastructure: 17.9%.
                Maintain packages in Nixpkgs: 15.5%. Have merge access to Nixpkgs: 2.9%.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 34, 44),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Experience
                Less than 1 year: 28.9%. 1-2 years: 34.0%. 3-4 years: 19.6%. 82.5% of
                respondents have used Nix for under 4 years. 5+ years: 11.7%.
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
                Intermediate 45.6%, Beginner 38.9%, Advanced 10.2%.
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
                NixOS: 70.8%. Nix: 20.0%. Don't remember: 7.6%. The operating system is the
                more common entry point into the ecosystem.
                """,
        plot_pane=make_simple_bar_chart_pane(df, 70),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # How first heard about Nix or NixOS
                YouTube: 28.3%. Friend or colleague: 15.9%. Don't remember: 12.0%. Blog or
                personal website: 7.3%. Search: 6.7%. Reddit: 4.9%. At work: 4.6%.
                """,
        plot_pane=make_simple_bar_chart_pane(df, 71),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # User types
                A "love the idea": 85.3%. C "get things done": 51.2%. B "curious": 44.2%.
                D "want to work on Nix": 31.3%. E "decision-maker": 14.8%. Multi-choice,
                so respondents can identify with several personas at once.

                **Persona definitions** (from the survey prompt):

                **A. Love the idea behind Nix or NixOS.** Maybe you spread the word among
                friends and coworkers. Interested in or enthusiastic about free and open
                source software, Linux, home automation, online communities, or
                distro-hopping.

                **B. Curious about Nix and how it works.** Maybe you enjoy or want to
                learn functional programming, or just want to learn new things. Identify
                as: Nix-curious developer, student of a technical field, educator, or
                academic researcher.

                **C. Use Nix or NixOS to get things done** or boost your team's
                productivity, learn it to grow career opportunities, or use it on the job
                because someone said so. Identify as: system administrator, employee
                developer, DevOps engineer, natural scientist, open source software
                author, or early-career professional.

                **D. Work or want to work on the Nix ecosystem** rather than just with
                it. At least one of: aspiring contributor, novice contributor, drive-by
                contributor, package maintainer, code owner, community team member, or
                sponsor.

                **E. Make strategic decisions** for your team or company: which
                technologies to adopt, which skills to train, which projects to support
                or invest in, which services or products to offer. Examples: entrepreneur,
                team lead, software architect, CTO, sales executive, public service
                administrator.
                """,
        plot_pane=make_multi_bar_chart_pane(
            df, 72, 77, title="Which user types do you identify with?"
        ),
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
                Flakes: 50.3%. Error messages: 47.6%. Improve the reference manual: 41.5%.
                Performance: 39.2%. Language usability: 31.2%. Security: 20.2%. Make other
                features non-experimental: 19.4%. Windows support: 6.4%. FreeBSD: 3.5%.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 186, 198),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Regular toolset
                Yes: 81.1%. No: 15.2%. Skipped: 3.7%.
                """,
        plot_pane=make_simple_bar_chart_pane(df, 199),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Help-success frequency
                Often: 48.8%. Sometimes: 30.4%. Always: 6.7%. Rarely: 4.5%. Never: 0.3%.
                Skipped: 9.3%.
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
                Each row sums to 100%. Beginners are concentrated in <2 years (88.0%);
                Intermediate peaks at 1-2 years (43.3%) and extends through 3-4 years
                (28.0%); Advanced spreads from 3 years onward, peaking at 3-4 years
                (30.3%). Self-described skill and time-spent aren't strictly aligned —
                2.0% of Advanced respondents report <1 year using Nix and 2.3% of Beginners
                report 5+ years.
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

information_seeking = (
    pn.pane.Markdown(
        "## Information seeking",
        styles={"font-size": "18px"},
    ),
    make_plot_row(
        md_text="""
                # Objects you interact with
                Mean rank (lower = preferred).

                Search dominates: package search (avg 1.87) and NixOS option search (2.68)
                are far ahead of every other object. NixOS configuration examples (4.58),
                manuals (5.91), command-line interface (6.00), and development environments
                (6.05) form the next tier. Peripheral items — job postings, press
                information, reviews, paid support — sit at the bottom.
                """,
        plot_pane=make_ranking_chart(df, 208, 238, method="avg_rank"),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Help resources (top-5 appearances)
                Respondents were asked to rank their top 5 only.
                Bar = number of respondents who placed this resource in their top 5.

                The official NixOS Wiki leads (2,313 — 68% of respondents put it in their
                top 5), followed by reference manuals (1,995 — 59%) and GitHub issues
                (1,359 — 40%). LLMs already crack the top 7 (919, 27%), ahead of nix.dev
                (711, 21%). Social channels — Reddit, Stack Overflow, Matrix, Discord — sit
                well below the official and code-adjacent sources; Mastodon and Twitter/X
                are essentially unused for help-seeking.
                """,
        plot_pane=make_ranking_chart(df, 238, 255, method="top_n_count", top_n=5),
    ),
)

foundation = (
    pn.pane.Markdown(
        "## Foundation",
        styles={"font-size": "18px"},
    ),
    make_plot_row(
        md_text="""
                # Donation incentives

                Transparency is the top motivator: 26.7% would be encouraged by better
                financial and operational reports — more than any other option. Tax
                deductibility (16.1%), a maintained LTS release (15.3%), official support or
                services (12.9%), and donor perks (12.4%) cluster as secondary motivators.
                Ear-marking donations to specific areas lands last at 5.6%.
                """,
        plot_pane=make_multi_bar_chart_pane(df, 267, 273),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Foundation funding priorities
                Mean rank (lower = preferred).

                Documentation is the clear top priority (avg rank 2.28, ranked by 2,182
                respondents — more than half). Nixpkgs package maintenance (3.47) and
                Security (3.67) follow. Community health, NixOS releases, and Nixpkgs
                architecture cluster around rank 4. Marketing (6.87) and community events
                (7.89) are the lowest priorities.
                """,
        plot_pane=make_ranking_chart(df, 273, 287, method="avg_rank"),
    ),
)

contribution = (
    pn.pane.Markdown(
        "## Contribution",
        styles={"font-size": "18px"},
    ),
    make_plot_row(
        md_text="""
                # Contribution experience

                Onboarding is the dominant theme. 35.8% plan to contribute in the future, and
                another 36% want to contribute now but don't know how to get started or how
                to join existing efforts. Roughly 31% have actually contributed (combining "on
                my own" and "with community help"). Feedback friction shows up at modest rates:
                7.0% report slow feedback, 5.8% got stuck after starting, 2.1% found received
                feedback unhelpful. Employer policy is rarely a blocker (0.6%).
                """,
        plot_pane=make_multi_bar_chart_pane(df, 255, 266),
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
    *contribution,
    *foundation,
    *information_seeking,
    sizing_mode="stretch_width",
    margin=20,
)
app.servable()
