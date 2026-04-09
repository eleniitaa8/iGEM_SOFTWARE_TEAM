from __future__ import annotations

import argparse

from .models import ScoringConfig
from .reader import find_vocs, read_obps_for_voc
from .scoring import score_and_sort


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rank OBPs for a target VOC.")
    parser.add_argument("--voc", help="Target VOC name (exact-first, then fuzzy match).")
    parser.add_argument("--top", type=int, default=20, help="How many ranked OBPs to print.")
    parser.add_argument("--w-aff", type=float, default=0.5, help="Affinity weight.")
    parser.add_argument("--w-spec", type=float, default=0.3, help="Specificity/selectivity weight.")
    parser.add_argument("--w-studies", type=float, default=0.2, help="Studies/confidence weight.")
    parser.add_argument("--max-ki", type=float, default=30.0, help="Reference max Ki for bootstrap sampling.")
    parser.add_argument("--max-alt-vocs", type=int, default=50, help="Compatibility parameter from legacy scorer.")
    parser.add_argument("--bootstrap-iters", type=int, default=200, help="Bootstrap iterations for score intervals.")
    return parser


def _config_from_args(args: argparse.Namespace) -> ScoringConfig:
    return ScoringConfig.custom(
        affinity_weight=args.w_aff,
        specificity_weight=args.w_spec,
        studies_weight=args.w_studies,
        max_ki=args.max_ki,
        max_alt_vocs=args.max_alt_vocs,
        bootstrap_iters=args.bootstrap_iters,
    )


def _print_results(voc: str, ranked, top: int) -> None:
    print(f"\nMatched VOC: {voc}")
    print(
        f"{'#':<4}{'OBP':<28}{'Ki (uM)':<10}{'Cens':<8}{'Alt':<6}{'SelIdx':<10}"
        f"{'Conf':<8}{'Score':<8}{'CI90':<16}"
    )

    for idx, obp in enumerate(ranked[:top], start=1):
        ci = f"[{obp.score_ci_low:.1f},{obp.score_ci_high:.1f}]"
        print(
            f"{idx:<4}{obp.name:<28}{obp.ki_for_target:<10.2f}{obp.target_censor:<8}{obp.alt_voc_count:<6}"
            f"{obp.selectivity_index:<10.2f}{obp.confidence_score:<8.1f}{obp.score:<8.2f}{ci:<16}"
        )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    target_voc = args.voc or input("Enter VOC to detect: ").strip()
    if not target_voc:
        print("VOC is required.")
        return

    try:
        config = _config_from_args(args)
    except ValueError as err:
        print(f"Invalid scoring configuration: {err}")
        return

    matched_voc, candidates = read_obps_for_voc(target_voc)
    if not candidates:
        print(f"No OBPs found for '{target_voc}'.")
        suggestions = find_vocs(target_voc)
        if suggestions:
            print("Closest VOC matches in dataset:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        return

    ranked = score_and_sort(candidates, config)
    _print_results(matched_voc, ranked, top=max(1, args.top))


if __name__ == "__main__":
    main()
