## country

European responses increased from 52% to 60%.
North American responses decreased from 27.5% to 21.3%.
The remaining responses changed less than 1% from the previous year.

## age

The curve has flattened and shifted.
The largest age group of 25-34 decreased from 35.6% to 30.7%.
The 35-44 age group also decreased from 22.7% to 19.4%.
Age groups under 25 or over 44 increased between 0.4% and 3.1%.

## gender_identity

Man: 78.3%. Woman: 7.2%. Prefer not to say: 6.6%. Non-binary or
non-conforming: 5.9%.

## transgender

No: 81.8%. Yes: 9.8%. Prefer not to say: 7.2%.

## years_programming

There are more fine grained bins for 10+ years of experience compared to previous years.
The groups with 4 or less years of experience have increased.
The groups with 5 or more years of experience have decreased.

## role

Students lead at 24.0%, ahead of full-stack (13.4%), back-end (10.7%), and
"Other" (10.3%). Sysadmin trails at 4.8%.

## industry

"Other" is the largest single category at 21.0%, suggesting the listed
industries miss common workplaces. Academia or education (17.6%) is the
largest named category. Telecom (5.9%), Consulting (5.8%), and Financial
services (4.7%) follow.

## domain

"Other" leads at 15.7%, suggesting the listed domains miss common
categories. Web development (13.8%), open-source software development
(10.8%), and programming languages / compilers / code analysis (9.2%)
follow.

## operating_systems

Linux: 96.9%. Android: 57.8%. Windows: 35.5%. macOS: 24.4%. iOS: 19.6%.
Categories below 0.5% or with fewer than 5 respondents are combined into the "Other (combined)" bar.

## target_triple

`x86_64-linux-gnu`: 94.5%. ARM combined (`aarch64-linux-gnu` 17.4% +
`aarch64-apple-darwin` 16.2%) reaches 33.6%. RISC-V: 2.0%.

## experimental_features

Flakes (78.9%) and the new `nix` CLI (66.7%) lead. The next-ranked feature
(pipe operators, 8.0%) trails by 58.7 points. 10.9% report using no
experimental features; 7.9% are not sure.

## install_method

NixOS preinstall: 78.4%. Official install script from nixos.org: 36.0%.
`DeterminateSystems/nix-installer`: 15.8%. Other package manager: 9.7%.
Built from source: 3.9%.

## nix_implementations

Upstream Nix: 87.5%. Lix: 14.8%. Determinate Nix: 9.8%. None: 4.2%.
Snix: 1.2%. Tvix: 0.8%.

## infrastructure

Personal computer: 90.3%. Workstation: 55.8%. Home server: 52.6%.
Production server: 21.4% and CI: 20.5%.

## nix_version

A lack of response or a an empty string was replaced with "Skipped".
A SemVer regular expression was used to match against the remaining answers.
Values that did not match were replaced with "No Match".
Categories below 0.1% or with fewer than 5 respondents are combined into the "Other (combined)" bar.

## nixos_releases

25.05 (current stable): 61.6%. Unstable: 56.8%. Sum exceeds 100%, indicating
many respondents run more than one release across machines. 24.11: 6.6%.
24.05: 2.2%. 23.11 or older: 1.4%.

## hardware_configuration

`nixos-generate-config`: 68.6%. Manual configuration: 39.0%. `nixos-hardware`
repository: 26.7%. `nixos-facter`: 3.9%.

## software_ecosystems

NixOS configurations leads at 81.1% (a meta-result — Nix users using Nix for
their own systems). Among programming languages: Python 45.8%, Rust 42.9%,
Bash 36.8%, C 26.7%, JavaScript 23.5%, C++ 22.7%, Go 21.3%.
Categories below 0.5% or with fewer than 5 respondents are combined into the "Other (combined)" bar.

## nix_on_os

NixOS: 90.0%. Other GNU/Linux: 26.5%. macOS: 18.1%. Windows (via WSL):
11.0%. Android: 7.5%. 3.7% do not use Nix.

## stable_upgrade

No issues: 37.4%. Minor issues: 19.5%. Moderate: 4.4%. Severe but resolved:
1.8%. Severe and unresolved: 0.9%. Not upgraded: 12.8%. Did not know about
the release: 5.5%. Skipped: 17.7%.

## involvement

I use NixOS: 87.1%. Install software with Nix: 66.7%. Maintain machines
running NixOS: 58.1%. Develop software with Nix: 48.8%. Contribute packages
or patches to Nixpkgs: 22.8%. Develop tools or infrastructure: 17.9%.
Maintain packages in Nixpkgs: 15.5%. Have merge access to Nixpkgs: 2.9%.

## years_using_nix

Less than 1 year: 28.9%. 1-2 years: 34.0%. 3-4 years: 19.6%. 82.5% of
respondents have used Nix for under 4 years. 5+ years: 11.7%.

## skill_level

Intermediate 45.6%, Beginner 38.9%, Advanced 10.2%.
About the same as last year.

## first_heard_which

NixOS: 70.8%. Nix: 20.0%. Don't remember: 7.6%. The operating system is the
more common entry point into the ecosystem.

## first_heard_how

YouTube: 28.3%. Friend or colleague: 15.9%. Don't remember: 12.0%. Blog or
personal website: 7.3%. Search: 6.7%. Reddit: 4.9%. At work: 4.6%.
Categories below 0.5% or with fewer than 5 respondents are combined into the "Other (combined)" bar.

## user_types

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

## traits

## improvements

Flakes: 50.3%. Error messages: 47.6%. Improve the reference manual: 41.5%.
Performance: 39.2%. Language usability: 31.2%. Security: 20.2%. Make other
features non-experimental: 19.4%. Windows support: 6.4%. FreeBSD: 3.5%.

## regular_toolset

Yes: 81.1%. No: 15.2%. Skipped: 3.7%.

## help_success_frequency

Often: 48.8%. Sometimes: 30.4%. Always: 6.7%. Rarely: 4.5%. Never: 0.3%.
Skipped: 9.3%.

## skill_x_experience

Each row sums to 100%. Beginners are concentrated in <2 years (88.0%);
Intermediate peaks at 1-2 years (43.3%) and extends through 3-4 years
(28.0%); Advanced spreads from 3 years onward, peaking at 3-4 years
(30.3%). Self-described skill and time-spent aren't strictly aligned —
2.0% of Advanced respondents report <1 year using Nix and 2.3% of Beginners
report 5+ years.

## experience_x_skill

The complement of the previous chart: each row (a tenure cohort) sums
to 100%, showing how self-described skill distributes within that
cohort. Useful for the dual question — "what does this experience level
look like in skill terms?" rather than "what experience does this skill
level have?"

## traits_rate_by_skill

Each cell: of respondents at this skill level, what percent picked this trait.
Cells in a column do NOT sum to 100% — traits are multi-choice.

Beginners overwhelmingly rely on tutorials (83%); rate drops to 57% at
Intermediate and 18% at Advanced. Writing own NixOS modules, understanding
overlays, and contributing upstream all climb steeply from under 20% at
Beginner to over 70% at Advanced.

## traits_lift_by_skill

Each cell: how over- or under-represented this skill level is among trait-pickers,
relative to the overall skill distribution. 1.0× = baseline, >1.0× = over-represented,
<1.0× = under-represented. Strips out the population-size imbalance.

Only "rely on tutorials" is over-represented among Beginners (1.30×). Every other
trait skews Advanced. Strongest Advanced lifts: "deeper module aspect" (3.34×),
"contribute upstream" (3.24×), "architectural choices" (2.79×).

## traits_rate_by_experience

Each cell: of respondents with this much experience, what percent picked this trait.
Cells in a column do NOT sum to 100% — traits are multi-choice.

Tutorial reliance starts at 76% in the first year and falls to 26% by 11+ years.
Most "advanced" trait rates climb steeply through years 1–6 and largely plateau
after. Group sizes shrink rapidly past 5 years (665 → 225 → 98 → 53 → 42), so
cells in the rightmost columns are noisier.

## traits_lift_by_experience

Each cell: how over- or under-represented this experience bucket is among trait-pickers,
relative to the overall experience distribution. 1.0× = baseline, >1.0× = over-represented,
<1.0× = under-represented. Strips out the population-size imbalance.

Tutorial reliance is the only trait over-represented in year-1 respondents
(1.20×). All other traits skew toward more-experienced respondents, with
strongest lifts at 5+ years for "deeper module aspect" (2.1× → 2.4×) and
"contribute upstream" (2.1× → 2.8×). Group sizes shrink rapidly past 5 years,
so cells in the rightmost columns are noisier.

## objects_interact_with

Mean rank (lower = preferred).

Search dominates: package search (avg 1.87) and NixOS option search (2.68)
are far ahead of every other object. NixOS configuration examples (4.58),
manuals (5.91), command-line interface (6.00), and development environments
(6.05) form the next tier. Peripheral items — job postings, press
information, reviews, paid support — sit at the bottom.

## help_resources

Respondents were asked to rank their top 5 only.
Bar = number of respondents who placed this resource in their top 5.

The official NixOS Wiki leads (2,313 — 68% of respondents put it in their
top 5), followed by reference manuals (1,995 — 59%) and GitHub issues
(1,359 — 40%). LLMs already crack the top 7 (919, 27%), ahead of nix.dev
(711, 21%). Social channels — Reddit, Stack Overflow, Matrix, Discord — sit
well below the official and code-adjacent sources; Mastodon and Twitter/X
are essentially unused for help-seeking.

## donation_incentives

Transparency is the top motivator: 26.7% would be encouraged by better
financial and operational reports — more than any other option. Tax
deductibility (16.1%), a maintained LTS release (15.3%), official support or
services (12.9%), and donor perks (12.4%) cluster as secondary motivators.
Ear-marking donations to specific areas lands last at 5.6%.

## foundation_priorities

Mean rank (lower = preferred).

Documentation is the clear top priority (avg rank 2.28, ranked by 2,182
respondents — more than half). Nixpkgs package maintenance (3.47) and
Security (3.67) follow. Community health, NixOS releases, and Nixpkgs
architecture cluster around rank 4. Marketing (6.87) and community events
(7.89) are the lowest priorities.

## contribution_experience

Onboarding is the dominant theme. 35.8% plan to contribute in the future, and
another 36% want to contribute now but don't know how to get started or how
to join existing efforts. Roughly 31% have actually contributed (combining "on
my own" and "with community help"). Feedback friction shows up at modest rates:
7.0% report slow feedback, 5.8% got stuck after starting, 2.1% found received
feedback unhelpful. Employer policy is rarely a blocker (0.6%).

## workplace_uses_nix

Free-text answers normalized to Yes / No / Other.

## workplace_decision

Free-text answers normalized to Yes / No / Other.
