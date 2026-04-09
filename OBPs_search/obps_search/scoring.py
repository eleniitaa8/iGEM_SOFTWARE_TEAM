from __future__ import annotations

import math
import random

from .models import OBPEntry, ScoringConfig


def _bounded(score: float) -> float:
    return max(0.0, min(100.0, score))


def _percentile_rank(values: list[float], index: int, reverse: bool = False) -> float:
    if not values:
        return 0.5
    pairs = sorted(enumerate(values), key=lambda item: item[1], reverse=reverse)
    positions = {original_idx: rank for rank, (original_idx, _) in enumerate(pairs)}
    if len(values) == 1:
        return 1.0
    return positions[index] / (len(values) - 1)


def _promiscuity_strength(obp: OBPEntry) -> float:
    """Higher means stronger off-target risk."""
    if not obp.alt_ki_values:
        return 0.0
    strengths = [1.0 / (1.0 + ki) for ki in obp.alt_ki_values]  # strong affinity -> closer to 1
    return sum(strengths) / len(strengths)


def _selectivity_index(obp: OBPEntry) -> float:
    """Best off-target Ki / target Ki; larger is better."""
    if not obp.alt_ki_values:
        return 10.0
    best_off_target = min(obp.alt_ki_values)
    return max(best_off_target / max(obp.ki_for_target, 1e-9), 0.0)


def _confidence_from_studies(studies: int) -> float:
    return _bounded(100.0 * (1.0 - math.exp(-studies / 12.0)))


def _sample_censored_ki(obp: OBPEntry) -> float:
    if obp.target_censor == "exact":
        return obp.ki_for_target
    if obp.target_censor == "right":
        return random.uniform(obp.ki_for_target / 1.5, obp.ki_for_target * 1.4)
    return random.uniform(obp.ki_for_target * 0.8, obp.ki_for_target * 2.0)


def score_and_sort(obps: list[OBPEntry], config: ScoringConfig) -> list[OBPEntry]:
    if not obps:
        return []

    ki_values = [obp.ki_for_target for obp in obps]
    selectivity_values = [_selectivity_index(obp) for obp in obps]
    studies_values = [obp.studies_count for obp in obps]
    promiscuity_values = [_promiscuity_strength(obp) for obp in obps]

    for idx, obp in enumerate(obps):
        affinity_pct = 1.0 - _percentile_rank(ki_values, idx, reverse=False)
        specificity_pct = _percentile_rank(selectivity_values, idx, reverse=False)
        studies_pct = _percentile_rank(studies_values, idx, reverse=False)

        affinity_score = 100.0 * affinity_pct
        specificity_score = 100.0 * specificity_pct
        studies_score = 100.0 * studies_pct

        raw_score = (
            affinity_score * config.affinity_weight
            + specificity_score * config.specificity_weight
            + studies_score * config.studies_weight
        )

        promiscuity_penalty = 35.0 * promiscuity_values[idx]
        final_score = _bounded(raw_score - promiscuity_penalty)

        obp.selectivity_index = selectivity_values[idx]
        obp.confidence_score = _confidence_from_studies(obp.studies_count)
        obp.score = round(final_score, 3)

    if config.bootstrap_iters > 0:
        for obp in obps:
            samples = []
            for _ in range(config.bootstrap_iters):
                sampled = _sample_censored_ki(obp)
                sampled_affinity = _bounded(100.0 * (1.0 - sampled / max(config.max_ki, sampled)))
                sample_score = (
                    sampled_affinity * config.affinity_weight
                    + (obp.selectivity_index / (obp.selectivity_index + 1.0)) * 100.0 * config.specificity_weight
                    + obp.confidence_score * config.studies_weight
                )
                sample_score = _bounded(sample_score - 35.0 * _promiscuity_strength(obp))
                samples.append(sample_score)

            samples.sort()
            lo = samples[int(0.05 * (len(samples) - 1))]
            hi = samples[int(0.95 * (len(samples) - 1))]
            obp.score_ci_low = round(lo, 3)
            obp.score_ci_high = round(hi, 3)

    return sorted(obps, key=lambda item: item.score, reverse=True)
