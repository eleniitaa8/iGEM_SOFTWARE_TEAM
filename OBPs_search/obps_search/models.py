from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OBPEntry:
    name: str
    ki_for_target: float
    target_censor: str = "exact"  # exact | left | right
    alt_vocs: list[str] = field(default_factory=list)
    alt_ki_values: list[float] = field(default_factory=list)
    studies_count: int = 0
    score: float = 0.0
    score_ci_low: float = 0.0
    score_ci_high: float = 0.0
    selectivity_index: float = 0.0
    confidence_score: float = 0.0

    @property
    def alt_voc_count(self) -> int:
        return len(self.alt_vocs)

    @property
    def ki_is_approximate(self) -> bool:
        return self.target_censor != "exact"


@dataclass(frozen=True)
class ScoringConfig:
    affinity_weight: float
    specificity_weight: float
    studies_weight: float
    max_ki: float
    max_alt_vocs: int
    bootstrap_iters: int = 200

    @classmethod
    def automatic(cls) -> "ScoringConfig":
        return cls(
            affinity_weight=0.50,
            specificity_weight=0.30,
            studies_weight=0.20,
            max_ki=30.0,
            max_alt_vocs=50,
            bootstrap_iters=200,
        )

    @classmethod
    def custom(
        cls,
        affinity_weight: float,
        specificity_weight: float,
        studies_weight: float,
        max_ki: float,
        max_alt_vocs: int,
        bootstrap_iters: int = 200,
    ) -> "ScoringConfig":
        weight_sum = affinity_weight + specificity_weight + studies_weight
        if abs(weight_sum - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0. Got: {weight_sum:.3f}")
        if bootstrap_iters < 0:
            raise ValueError("bootstrap_iters must be >= 0")
        return cls(
            affinity_weight=affinity_weight,
            specificity_weight=specificity_weight,
            studies_weight=studies_weight,
            max_ki=max_ki,
            max_alt_vocs=max_alt_vocs,
            bootstrap_iters=bootstrap_iters,
        )
