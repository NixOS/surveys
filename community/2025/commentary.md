## country

European responses climbed to 60.0%, up from 52% a year earlier, while
North America slipped from 27.5% to 21.3%. The remaining regions each
moved by less than a point.

## age

The age curve flattened. The 25-34 cohort, still the largest, fell from
35.6% to 30.7%, and 35-44 dropped from 22.7% to 19.4%. Every group
under 25 or over 44 grew, by between 0.4 and 3.1 points — a modest but
broad-based widening.

## gender_identity

The community is overwhelmingly male: 78.3% of respondents identify
as men. Women account for 7.2% and non-binary respondents 5.9%; a
further 6.6% declined to answer.

## transgender

A majority (81.8%) do not identify as transgender; 9.8% do, and 7.2%
declined to answer.

## years_programming

Reported programming experience leans long: most respondents fall in
the 1–14 year bands. Groups with four or fewer years of experience
grew compared with the prior year, while groups with five or more
years shrank. This year's instrument also splits the 10+ bracket into
finer bins, surfacing more detail at the experienced end.

## role

Students lead at 24.0%, followed by full-stack (13.4%) and back-end
developers (10.7%); system and network administrators trail at 4.8%.
A further 10.3% selected "Other".

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

Nearly all respondents — 96.9% — use Linux on at least one device. Android
(57.8%) and Windows (35.5%) are next, with macOS at 24.4% and iOS at 19.6%.
Categories below 0.5% or with fewer than 5 respondents are combined into the
"Other (combined)" bar.

## target_triple

`x86_64-linux-gnu`: 94.5%. ARM combined (`aarch64-linux-gnu` 17.4% +
`aarch64-apple-darwin` 16.2%) reaches 33.6%. RISC-V: 2.0%.

## experimental_features

Flakes (78.9%) and the new `nix` CLI (66.7%) lead. The next-ranked feature
(pipe operators, 8.0%) trails by 58.7 points. 10.9% report using no
experimental features; 7.9% are not sure.

## install_method

Most respondents (78.4%) first met Nix through a NixOS installation.
The official install script accounts for another 36.0%, followed by
the `DeterminateSystems/nix-installer` at 15.8%. Self-built and
third-party-packaged installations together cover the remaining 13.6%.

## nix_implementations

Upstream Nix remains the default by a wide margin (87.5%). Lix (14.8%)
and Determinate Nix (9.8%) are the most-used alternatives. Tvix (0.8%)
and Snix (1.2%) are still in single digits.

## infrastructure

Personal computers (90.3%) are the dominant target. Workstations
(55.8%) and home servers (52.6%) follow. Production servers (21.4%)
and CI environments (20.5%) are used at roughly a quarter the rate
of personal machines.

## nix_version

The 2.28 series dominates the answers that could be parsed: 2.28.5
alone accounts for 21.7%, with 2.28.4 at 10.5%. Roughly a third of
respondents skipped the question; a further 6.4% gave an unparseable
answer.

Versions are extracted with a SemVer regex against the free-text
response. Unparseable answers are labelled "No Match" and bins below
0.1% or 5 respondents are folded into "Other (combined)".

## nixos_releases

25.05 (the current stable) leads at 61.6%, followed closely by
unstable at 56.8%. The two combined exceed 100%, indicating many
respondents run more than one release across their machines. Older
releases drop off sharply: 24.11 at 6.6%, 24.05 at 2.2%, and 23.11 or
earlier at 1.4%.

## hardware_configuration

`nixos-generate-config` is still the dominant entry point at 68.6%,
with manual configuration cited by 39.0% and the `nixos-hardware`
repository by 26.7%. `nixos-facter` lands at 3.9%.

## software_ecosystems

NixOS configurations leads at 81.1% (a meta-result — Nix users using Nix for
their own systems). Among programming languages: Python 45.8%, Rust 42.9%,
Bash 36.8%, C 26.7%, JavaScript 23.5%, C++ 22.7%, Go 21.3%.
Categories below 0.5% or with fewer than 5 respondents are combined into the "Other (combined)" bar.

## nix_on_os

Among respondents who use Nix, NixOS itself is the primary host
(90.0%). Other GNU/Linux distributions (26.5%), macOS (18.1%), and
Windows via WSL (11.0%) round out the meaningful platforms. 3.7%
report not using Nix at all.

## stable_upgrade

Most respondents who upgraded had a clean experience: 37.4% report no
issues and 19.5% only minor ones, while moderate, severe-resolved, and
severe-unresolved issues together account for 7.1%. A further 12.8%
had not yet upgraded at survey time, and 5.5% were unaware a new
stable release existed.

## involvement

Nearly every respondent uses NixOS (87.1%), and two-thirds (66.7%)
install software with Nix more broadly. Roughly half maintain NixOS
machines (58.1%) or develop software on Nix (48.8%). Direct
contribution to Nixpkgs is much narrower: 22.8% have submitted
packages or patches, 15.5% maintain packages, and 2.9% hold merge
access.

## years_using_nix

The community skews new: 28.9% have used Nix for less than a year,
34.0% for one to two years, and 19.6% for three to four. Combined,
82.5% of respondents have under four years of Nix experience. Only
12.3% have used Nix for five or more years.

## skill_level

Self-described skill remains roughly stable year over year:
Intermediate (45.6%) is the largest group, followed by Beginner
(38.9%) and Advanced (10.2%).

## first_heard_which

NixOS is the more common entry point into the ecosystem: 70.8% of
respondents heard about it first, against 20.0% who heard of Nix
first. 7.6% no longer remember.

## first_heard_how

YouTube is the single largest channel (28.3%), well ahead of
word-of-mouth from a friend or colleague (15.9%). 12.0% no longer
remember. Blogs (7.3%), search (6.7%), Reddit (4.9%), and work
introductions (4.6%) make up the next tier. Categories below 0.5% or
fewer than 5 respondents are folded into "Other (combined)".

## user_types

"Love the idea" (A) is by far the most-claimed identity, picked by
85.3% of respondents. Roughly half (51.2%) also identify as "get
things done" pragmatists (C), and 44.2% as curious learners (B).
Aspiring or active contributors (D) account for 31.3%, and strategic
decision-makers (E) for 14.8%. Because the question allows multiple
selections, respondents often combine personas — e.g., enthusiast and
pragmatist.

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

Respondents pick the traits that describe their relationship with Nix
across a 12-item checklist. Tutorial reliance leads at 62.5%, followed
by using the module system for one's own configuration (56.3%) and
having used overlays (53.7%). The share that feels comfortable
contributing upstream (23.3%), reads the Nix source (19.4%), or
claims to understand every error message (4.0%) drops sharply.

## improvements

Asked to pick about three areas they would improve, respondents
prioritise flakes (50.3%) — the most-cited single area — alongside
error messages (47.6%) and the reference manual (41.5%). Performance
(39.2%) and language usability (31.2%) form the next tier. Platform
expansion (Windows 6.4%, FreeBSD 3.5%) ranks low.

## regular_toolset

A clear majority — 81.1% — consider Nix part of their regular toolset.
15.2% do not, and 3.7% skipped the question.

## help_success_frequency

Respondents largely find what they need: 48.8% say they reach a useful
answer "often" and another 6.7% "always". 30.4% land on "sometimes",
while only a small minority report rare success (4.5%) or none at all
(0.3%).

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

Each bar shows how respondents distributed their ranks across grouped positions
(1-3, 4-6, 7-10), with the remainder left unranked. Search objects dominate the
top band: package search and NixOS option search are placed in the top three far
more often than anything else. Configuration examples, manuals, the command-line
interface, and development environments form the middle tier. Peripheral
objects — job postings, press information, reviews, paid support — are mostly
left unranked.

## help_resources

Each bar shows the share of respondents who placed a resource at each of their
top five positions, with the remainder unranked. The official NixOS Wiki and the
reference manuals are placed in the top five most often, followed by GitHub
issues and discussions. LLMs already appear in many top-five lists, ahead of
nix.dev. Social channels — Reddit, Stack Overflow, Matrix, Discord — trail the
official and code-adjacent sources; Mastodon and Twitter/X are rarely chosen for
help-seeking.

## donation_incentives

Transparency is the top motivator: 26.7% would be encouraged by better
financial and operational reports — more than any other option. Tax
deductibility (16.1%), a maintained LTS release (15.3%), official support or
services (12.9%), and donor perks (12.4%) cluster as secondary motivators.
Ear-marking donations to specific areas lands last at 5.6%.

## foundation_priorities

Each bar shows how respondents distributed their ranks across positions, with the
remainder unranked. Documentation is placed first far more often than any other
area. Nixpkgs package maintenance and security follow closely. Community health,
NixOS releases, and Nixpkgs architecture cluster in the middle. Marketing and
community events are the priorities most often ranked low or left unranked.

## contribution_experience

Onboarding is the dominant theme. 35.8% plan to contribute in the future, and
another 36% want to contribute now but don't know how to get started or how
to join existing efforts. Roughly 31% have actually contributed (combining "on
my own" and "with community help"). Feedback friction shows up at modest rates:
7.0% report slow feedback, 5.8% got stuck after starting, 2.1% found received
feedback unhelpful. Employer policy is rarely a blocker (0.6%).

## involvement_x_experience

Two views of how involvement roles vary with experience. The Rate heatmap shows
the rate — among respondents in each experience band, the share reporting each
involvement role. The Lift heatmap shows lift — how much more (or less) likely
each role is within a band relative to the overall baseline (1.0× = no
difference). Bands exclude non-users and undisclosed experience.

## workplace_uses_nix

Among respondents whose free-text answers could be normalised, 12.8%
reported their workplace uses Nix and 29.2% said it does not. A
majority — 57.9% — gave answers that fell into the "Other" category.

Free-text answers normalised to Yes / No / Other.

## workplace_decision

Of respondents in a Nix-using workplace, 15.7% report having made the
adoption decision themselves; 23.9% did not. The largest share
(60.4%) again falls into "Other".

Free-text answers normalised to Yes / No / Other.
