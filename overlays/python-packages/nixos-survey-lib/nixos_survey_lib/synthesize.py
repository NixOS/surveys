"""Generate a synthetic survey-response CSV from a SurveySchema.

Everything is fabricated; no real survey rows are involved anywhere.
Output is byte-identical for a fixed (schema, rows, seed, text_pools) —
Nix builds require determinism — so all randomness flows from one
``random.Random(seed)`` whose consumption order follows schema question
order.

Distributions are deliberately skewed (not uniform) so downstream charts
have realistic shape, but the skew ratio is bounded: unbounded draws let a
single choice swallow ~90% of a small-choice question, and in crosstab
charts (sankey/heatmap) a low-weight choice crossed with many categories
loses every cell to min-count suppression, silently deleting whole nodes.
Choice weights are additionally floored so that at the default row count
every choice comfortably clears the pipeline's min-count privacy
suppression in single-column charts (floor * rows = 12 expected >>
DEFAULT_BUCKET_MIN_COUNT).
"""

import csv
import random
from pathlib import Path

from .loader import normalize_prompt
from .types import SurveySchema

_PLACEHOLDER_TEXT = "Synthetic placeholder response."
_WEIGHT_FLOOR = 0.02
_SKIP_RANGE = (0.02, 0.15)
_MULTI_RATE_RANGE = (0.05, 0.7)


def _choice_str(choice: object) -> str:
    """YAML 1.1 parses bare Yes/No choices as booleans; the survey
    platform's CSV holds the strings."""
    if isinstance(choice, bool):
        return "Yes" if choice else "No"
    return str(choice)


def _skewed_weights(rng: random.Random, n: int) -> list[float]:
    floor = min(_WEIGHT_FLOOR, 1.0 / n)
    raw = [rng.uniform(1.0, 5.0) ** 2 for _ in range(n)]
    total = sum(raw)
    scale = 1.0 - floor * n
    return [floor + scale * r / total for r in raw]


def _weighted_permutation(rng: random.Random, items: list[str], weights: list[float]) -> list[str]:
    """Plackett-Luce draw: pick without replacement proportional to weight,
    so high-weight items cluster at the top ranks while every permutation
    stays possible. An unweighted permutation would make rank charts
    converge to flat as rows grow."""
    remaining = list(items)
    remaining_w = list(weights)
    out: list[str] = []
    while remaining:
        i = rng.choices(range(len(remaining)), weights=remaining_w)[0]
        out.append(remaining.pop(i))
        remaining_w.pop(i)
    return out


def synthesize_csv(
    schema: SurveySchema,
    out_path: Path,
    *,
    rows: int = 600,
    seed: int = 2025,
    text_pools: dict[str, list[str]] | None = None,
) -> None:
    """Write a fake responses CSV whose columns match ``schema`` exactly
    (one column per single/text question, one per choice for multiple,
    ``Rank 1..N`` for ranking), so ``load_responses`` accepts it."""
    rng = random.Random(seed)
    pools = text_pools or {}

    headers: list[str] = []
    columns: list[list[str]] = []

    for q in schema.questions:
        prompt = normalize_prompt(q.prompt)
        skip_rate = rng.uniform(*_SKIP_RANGE)

        if q.type == "single":
            choices = [_choice_str(c) for c in q.choices]
            weights = _skewed_weights(rng, len(choices))
            col = [
                "" if rng.random() < skip_rate else rng.choices(choices, weights=weights)[0]
                for _ in range(rows)
            ]
            headers.append(prompt)
            columns.append(col)

        elif q.type == "multiple":
            choices = [_choice_str(c) for c in q.choices]
            include_rates = [rng.uniform(*_MULTI_RATE_RANGE) for _ in choices]
            cols: list[list[str]] = [[] for _ in choices]
            for _ in range(rows):
                for i, rate in enumerate(include_rates):
                    cols[i].append("Yes" if rng.random() < rate else "No")
            for choice, col in zip(choices, cols):
                headers.append(f"{prompt} [{choice}]")
                columns.append(col)

        elif q.type == "ranking":
            choices = [_choice_str(c) for c in q.choices]
            n = len(choices)
            weights = _skewed_weights(rng, n)
            cols = [[] for _ in range(n)]
            for _ in range(rows):
                if rng.random() < skip_rate:
                    for c in cols:
                        c.append("")
                else:
                    for c, v in zip(cols, _weighted_permutation(rng, choices, weights)):
                        c.append(v)
            for i, col in enumerate(cols, start=1):
                headers.append(f"{prompt} [Rank {i}]")
                columns.append(col)

        elif q.type == "text":
            pool = pools.get(q.id, [_PLACEHOLDER_TEXT])
            col = ["" if rng.random() < skip_rate else rng.choice(pool) for _ in range(rows)]
            headers.append(prompt)
            columns.append(col)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for i in range(rows):
            writer.writerow([col[i] for col in columns])
