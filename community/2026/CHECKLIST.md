# Community Survey 2026 checklist

Carried from 2025 and updated for how this year actually ran. See
`community/TRANSLATING.md` for the translation rules and
`community/README.md` for the process.

## Design

- [x] Design the survey questions
  - 47 questions down to 40, in eight groups, five languages.
  - [ ] ~~Ask community teams what information they need~~
    Not done this year. An October 1 launch left no room, so team outreach
    was declared out of scope rather than skipped by accident. For 2027:
    the 2025 round added `industry` and `domain` six weeks before fielding
    without full Steering Committee consultation, and both ended up with the
    two highest "Other" rates in the survey.
  - [x] Refine objectives
    - The gender questions were reconsidered against published guidance
      (NASEM, Stats NZ, Pew, ABS) and kept, with `dontKnow` added to
      `transgender`. This will not satisfy the 24 respondents who asked for
      their removal.
- [x] Every question carries a TOML comment recording the decision it
  supports. No previous year did this.

## Translation

Translations are generated in-repo; the community supplies review. A language
ships complete and reviewed, or it does not ship. Dropping one means removing
its entry from `[survey] languages` and `git rm`-ing its
`survey.<lang>.toml`; the loader refuses a file whose language is not listed.

| Language | Translated | Reviewer | Review due | Shipped |
|---|---|---|---|---|
| `fr` | | | | |
| `es-informal` | | | | |
| `de-informal` | | | | |
| `zh-Hans` | | | | |

- [ ] Set a go/no-go date and a default: ship English plus whatever has a
  completed review, or slip the launch.

## Pretesting

- [ ] Five to eight community members who were not part of the design
  complete the English survey and think aloud.
  - Probe: do the factual escape options read as factual states rather than
    refusals; do the terminology fixes resolve Nix vs Nixpkgs vs NixOS for a
    reader who is not us; do the two barriers lists cover what people want to
    say.
- [ ] Expert review of `genderIdentity` and `transgender` by someone outside
  this design.

`save_timings = false` disables response latency, which is the usual fallback
signal when pretesting is thin, so this is the only comprehension check the
design has.

## For the infrastructure team

From the 2025 free-text feedback. None is fixable by question design.

- [ ] Session timeout loses completed responses (16 reports). Two refused to
  redo the survey; two redid it carelessly, which is measurement error
  rather than nonresponse. Five asked for autosave or draft restore.
  Anonymous surveys can still offer save-and-resume.
- [ ] Ranking drag widget unusable on mobile (15 reports). It blocks page
  scroll. Capping the rankings at five reduces the pain without fixing
  it; four respondents asked to replace the format outright.
- [ ] Colour contrast and accessibility (14 reports): pale blue controls, the
  theme ignoring the device dark-mode setting, no sans-serif fallback.
- [ ] Radio buttons cannot be deselected after a misclick (2 reports).
  LimeSurvey has a setting for this.

## Launch

- [ ] Import `result/survey.txt` and review in the admin UI before activating.
  - [ ] The five privacy settings. These cannot be changed after
    activation.
  - [ ] Eight groups, one page each, in order.
  - [ ] `country` renders as a dropdown and sorts alphabetically in each
    language, not just English. If the French list puts `Égypte`,
    `États-Unis` and the `Îles` entries after Zimbabwe instead of
    interleaving them, PHP has no `intl` extension and the Chinese list
    is sorted by codepoint.
  - [ ] The three rankings cap at five and `improvements` caps at three, in
    the live preview rather than the settings screen.
  - [ ] Take the survey once per language, start to finish.
- [ ] Activate
- [ ] Write announcement (link to participate, closing date)
- [ ] Banner on the front page of the official websites
  - [ ] nixos.org
  - [ ] nix.dev
  - [ ] wiki.nixos.org
  - [ ] discourse.nixos.org
  - [ ] search.nixos.org
- [ ] Social media outreach
  - [ ] Discourse
  - [ ] Reddit
  - [ ] Hacker News
  - [ ] Mailing list
  - [ ] Private/unofficial channels
- [ ] Schedule reminders: 1 week after launch, then 1 month / 2 weeks /
  1 week / 2 days / 1 day before closing.

## Analysis

- [ ] Crosstab suppression must land before any country crosstab is
  published, or the 2026 analysis publishes none.
- [ ] Derive region from country so the 2025 continental series continues.
- [ ] Report select-all results as orderings and shares of selections, not
  "N% of respondents use X".
- [ ] Ranking caps censor data: unranked is not ranked-last.
- [ ] Do not present the 2025 `industry` distribution as a sector estimate,
  or compare 2026 against it.
- [ ] Adding languages changes sample composition. A shift in the geographic
  distribution is partly the translation, not community growth.
- [ ] Make analysis and write up evaluation
- [ ] Post results
- [ ] Write down improvements needed for 2027. The survey is not complete
  until that document exists.
