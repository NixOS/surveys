# Translating the Nix Community Survey

Rules for `community/<year>/survey.<lang>.toml`. They are binding on whoever
writes a translation and are what a native-speaker reviewer checks against.

Year-specific facts — which languages shipped, who reviewed each, deadlines —
belong in that year's `CHECKLIST.md`, so this file stays reusable.

2026 ships English, French, Spanish, German and Simplified Chinese.

## Register: informal, in every language

LimeSurvey's locale controls its own chrome — buttons, navigation, validation
messages — and not our question text, which comes from the TOML regardless. So
if the translation is formal, the survey addresses the respondent one way in
its buttons and another way in its questions, inside a single page.

| Language | Second person | Note |
|---|---|---|
| `fr` | **tu** | LimeSurvey ships only `fr`, with no informal variant, so this decision lives entirely in our text. |
| `es-informal` | **tú** | Not `usted`, and not voseo. |
| `de-informal` | **du** | Lower case `du`, as in modern usage. Avoid sentence-initial `Sie` even when it means "it" or "she": it is indistinguishable from formal address at a glance, and `check_translations.py` flags it. Reword. |
| `zh-Hans` | **你** | Not 您. Chinese has no T-V distinction in the European sense; this is the nearest equivalent choice. |

## Terminology: five terms that must stay distinct

This instrument's meaning depends on these not collapsing into each other. A
technical audience resolves an ambiguous term silently and confidently rather
than asking, so a collapsed distinction does not show up as confusion in the
data. It shows up as a wrong answer that looks fine.

| English | What it means |
|---|---|
| Nix, the Nix package manager | The command-line tool and its build system |
| the Nix language | The expression language |
| Nixpkgs | The package collection |
| NixOS | The Linux distribution |
| the Nix ecosystem | All of the above plus the surrounding projects |

**The rule that matters most:** wherever the English says "the Nix package
manager" rather than bare "Nix", the translation carries the same expansion.
Five prompts were reworded in 2026 specifically to add it, at the cost of
breaking five tracked series. Collapsing them back to bare "Nix" undoes that
and wastes the break.

| English | fr | es | de | zh-Hans |
|---|---|---|---|---|
| the Nix package manager | le gestionnaire de paquets Nix | el gestor de paquetes Nix | der Paketmanager Nix | Nix 包管理器 |
| the Nix ecosystem | l'écosystème Nix | el ecosistema Nix | das Nix-Ökosystem | Nix 生态系统 |
| the Nix language | le langage Nix | el lenguaje Nix | die Nix-Sprache | Nix 语言 |

## What stays in English

Project names and Nix-specific jargon keep their English form in every
language, including Chinese, because that is what the documentation and the
community use and a respondent looking for the term will not recognise a
translation of it:

Nix · Nixpkgs · NixOS · Lix · Snix · Tvix · fix · Determinate Nix ·
Home Manager · Hydra · flake, flakes · derivation · overlay · stdenv ·
channel · the Nix store · nixos-generate-config · nixos-hardware · nixos-facter

Also unchanged: version numbers (26.05, 2.31.x), the programming-language
names in `softwareEcosystems`, operating-system names, and URLs.

Where a term has a genuinely settled native rendering that the local community
actually uses, prefer it and record the exception here. Do not invent one.

## Gender terminology

"Non-binary" does not translate uniformly across markets, and `genderIdentity`
and `transgender` are already the two most-complained-about questions in the
survey. Decisions:

| English | fr | es | de | zh-Hans |
|---|---|---|---|---|
| Non-binary/non-conforming | Non-binaire / non conforme | No binario / no conforme | Nicht-binär / nicht konform | 非二元性别／性别不一致 |
| Do you identify as transgender? | T'identifies-tu comme transgenre ? | ¿Te identificas como transgénero? | Identifizierst du dich als transgender? | 你认同自己是跨性别者吗？ |
| Prefer not to say | Je préfère ne pas répondre | Prefiero no decirlo | Keine Angabe | 不想回答 |

Spanish has a live problem here: adjectives agree in gender, so "No binario"
carries a masculine ending on a question about not being in that binary. "No
binarie" exists and is not universally accepted. **"No binario" ships**, as
the most widely understood form, and this is the first thing to put in front
of the Spanish reviewer.

## What must not be touched

- **Choice keys** — everything left of the `=` — stay byte-identical. They
  link a string across language files, and a changed key is a build failure at
  best and a silently mislinked option at worst.
- **The `<p>` tags in `intro`.** It is emitted through `html_text`, so the
  tags reach LimeSurvey and are the only paragraph breaks the welcome page
  has.
- **The generated country names.** All 249 come from CLDR via
  `generate_countries.py`; do not edit them. `preferNotToSay` on that question
  is ours and does need translating.
- **`stableUpgrade`'s labels keep their full stops** in every language. The
  English ones are matched literally by the analysis pipeline. The translated
  ones are not, but a set of options where some end in a full stop and others
  do not is simply wrong, and the next person to touch this will not know
  which rule applied where.

## Ordered sets stay parallel

`stableUpgrade`'s five severity options are a ladder, and so are
`skillLevel`'s four. A ladder whose rungs are phrased differently stops
reading as one. Translate each set as a set.

## Mechanics

A language's `survey.<lang>.toml` and its entry in `[survey] languages` are
**one change**. `load_survey` requires every listed language to cover every
string, and it also refuses a file whose language is not listed, so neither
half can exist without the other. Dropping a language means `git rm`-ing its
file as well as removing the code.

Volume for 2026: roughly 780 strings per language, of which about 250 are
generated country names and about 530 need real translation.

`check_translations.py` in the year's directory catches what the loader
cannot: formal-register pronouns, product names dropped in translation, and a
changed paragraph count in the intro. It runs in the build.

## Review

A native speaker who did not write the translation reads it against the
English before it ships, and a language with no completed review is dropped
rather than shipped unreviewed. The nearest comparable project, the Rust
survey, apologised publicly for translation problems; their failure was
review, not translation.

Tell the reviewer how the translation was produced. It changes what they
should look for: fluent and subtly wrong, rather than obviously broken.
