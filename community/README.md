# Nix Community Survey

## Introduction

The Nix Community Survey, or "Nix Survey" for short, is a public survey organized by the Nix community in order to collect information from all Nix users, contributors and maintainers.

Its goals are to

- Describe the evolution of the Nix community over the years;
- Support Nix teams' strategies and operations by seeking to provide concrete data to validate or invalidate their assumptions.

This document describes the process of preparing and running the Nix Community Survey.

Please improve this document according to your experience.
Just edit and commit fearlessly.

## Wording

A _survey_ is made up of _questions_.

A _question_ is made up of a _prompt_ and _choices_.

The _prompt_ is a short text presented to the participant to ask the question.

_Choices_ can be either:

- _multiple choices_: the user can select as many choices as they want from a list of proposed choices, and input free text in a "other" choice field
- _single choice_: the user can only select one choice from a list of proposed choices, or input free text in a "other" choice field
- _ranking_: the user can pick and rank items from a list, they can't input free text in a "other" field
- _free text_: the user can input any text

## Organization

### Phases

#### Preparation

> We keep improving the survey every year.
> Great change can be brought from one survey to another, but we need to strive for an incremental approach.
> When preparing a survey, you should start from the last survey as well as the document of key improvements that had been noted at the end of the previous survey.
> On this note, a survey should not be considered completed until a document describing key improvements for the next survey has been committed.

Write down a checklist of all foreseen steps.

Talk to all Nix teams to understand the kind of data that they need.

Write questions and their choices in this repository, one file per year.

> It is hard to make anything from free-text answers.
>
> You should only ask questions with a quantitative answer or categorical answers (single or multiple).
> Even if it means having many categories or missing possible answers.
> Note that we can still put a "Other" choice, but they question should be designed
>
> Imagine 2k participants, 20 free-text answers with a response rate of 50%, each response being 20 words on average.
> That's too much to read with an objective approach.
> We play a long-term game and burn-out from reading 2000\*40 answers every year is not the way to go.
>
> With that in mind, feedback such as "this question was missing what I wanted to answer" is precious as it will help make our survey more and more complete.

You may make a RFC (Request for Comment) when needed, from selected people or a broad audience, as you see fit.

Write the survey as TOML in the year's directory (see `community/2025/`):

- `survey.toml` holds the structure: survey id, languages, privacy flags,
  groups, and questions with their type, flags, and choice keys. No text.
- `survey.<lang>.toml` holds every human-readable string for one language:
  title, intro, the optional end text, group titles and their optional
  descriptions, prompts, help, and one line per choice key. Every language
  listed in `survey.toml` needs one of these files.

Question ids become LimeSurvey question codes, so they must start with a
letter, contain only letters and digits, and be at most 20 characters.
Loading fails with a message naming the file and id when a rule is broken.

The `id` under `[survey]` is only a preference. LimeSurvey uses it when it is
free and assigns a random one when it is already taken, so pick something
memorable such as the survey year rather than the id of a survey already on
the server.

Prompts are emitted as a single line of plain text, so a prompt written as a
bulleted list in TOML arrives in LimeSurvey flattened; put lists or
instructions in `help`, or accept the flat text.

Build the LimeSurvey import file and upload it:

```
nix build .#nixos-surveys-community-2025-limesurvey
```

Then in LimeSurvey go to Surveys > Create > Import, choose `result/survey.txt`,
and import. Review the new survey in the admin UI before activating it; the
privacy settings from `survey.toml` are already applied and cannot be changed
after activation.

Prepare announcement to open survey for participation.
The announcement must at least contain

- a link to allow people to participate.
- the closing date of participation

Prepare posts for social medias.
Ideally, each post should have a tag to allow analytics to source sessions' channel, e.g. `https://survey.nixos.org/?utm_channel=twitter`.

#### Participation

Allow participation to the survey on the survey tool.

Publish announcement on Discourse.
Post on social medias: Reddit, Hacker News, Twitter/X, LinkedIn.

Activate banner on the `nixos.org` website.

Schedule reminders on social medias.
For instance

- 1 week after launch,
- 1 month before closing,
- 2 weeks before closing,
- 1 week before closing,
- 2 days before closing.
- 1 days before closing.

Wait for the closing date.

#### Analysis

Produce aggregates and charts for each question of this survey.

**TODO**

#### Feedback and improvements

Collect feedback.

Write down a document of improvements that will be needed for the next survey.

### Schedule

The Nix Survey is run every year, usually in spring.

The survey is open to participants for about a month.

It is preferred to publish unidentifiable data (e.g. aggregates) at most one month after the survey closure.

Due to the uncertain nature of data analysis, there is no expected date of publication of its analysis.
