from __future__ import annotations

import csv
import re
from pathlib import Path

from .models import OBPEntry

CSV_PATH = Path(__file__).resolve().parent.parent / "Compound_OBP_binding.csv"


def parse_ki(raw_value: object) -> tuple[float, str] | None:
    """Return (estimated_value, censor_type). censor_type: exact|left|right."""
    raw = "" if raw_value is None else str(raw_value).strip()
    if not raw or raw == "-":
        return None

    censor = "exact"
    if raw.startswith(">"):
        censor = "right"
        raw = raw[1:].strip()
    elif raw.startswith("<"):
        censor = "left"
        raw = raw[1:].strip()

    cleaned = re.sub(r"[^0-9.]", "", raw)
    if not cleaned:
        return None

    try:
        base = float(cleaned)
    except ValueError:
        return None

    if censor == "right":
        estimate = base * 1.5  # interval-aware heuristic for >X
    elif censor == "left":
        estimate = base * 0.5  # interval-aware heuristic for <X
    else:
        estimate = base

    return estimate, censor


def _read_table(csv_path: Path = CSV_PATH) -> tuple[list[str], list[list[str]]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    return header, rows


def _match_voc_index(rows: list[list[str]], query: str) -> int:
    query_clean = query.strip().lower()

    # 1) exact match first
    for idx, row in enumerate(rows):
        if len(row) > 1 and row[1].strip().lower() == query_clean:
            return idx

    # 2) fallback: substring
    for idx, row in enumerate(rows):
        if len(row) > 1 and query_clean in row[1].strip().lower():
            return idx

    return -1


def find_vocs(query: str, csv_path: Path = CSV_PATH, limit: int = 20) -> list[str]:
    _, rows = _read_table(csv_path)
    needle = query.lower().strip()
    exact = [row[1] for row in rows if len(row) > 1 and row[1].strip().lower() == needle]
    fuzzy = [row[1] for row in rows if len(row) > 1 and needle in row[1].strip().lower() and row[1] not in exact]
    return (exact + fuzzy)[:limit]


def read_obps_for_voc(voc_name: str, csv_path: Path = CSV_PATH) -> tuple[str, list[OBPEntry]]:
    header, rows = _read_table(csv_path)
    if len(header) < 3:
        return voc_name, []

    obp_columns = header[2:]
    target_idx = _match_voc_index(rows, voc_name)
    if target_idx == -1:
        return voc_name, []

    target_row = rows[target_idx]
    matched_voc = target_row[1]

    studies_per_obp = [0] * len(obp_columns)
    for row in rows:
        for col_idx in range(2, min(len(row), len(header))):
            if parse_ki(row[col_idx]) is not None:
                studies_per_obp[col_idx - 2] += 1

    candidates: list[OBPEntry] = []
    for col_idx, obp_name in enumerate(obp_columns, start=2):
        if col_idx >= len(target_row):
            continue

        target_ki = parse_ki(target_row[col_idx])
        if target_ki is None:
            continue

        ki_value, censor = target_ki
        alt_vocs: list[str] = []
        alt_kis: list[float] = []

        for row_idx, row in enumerate(rows):
            if row_idx == target_idx or col_idx >= len(row):
                continue

            alt_ki = parse_ki(row[col_idx])
            if alt_ki is None or len(row) <= 1:
                continue

            alt_name = row[1]
            if len(alt_name) > 30:
                alt_name = f"{alt_name[:30]}..."
            alt_vocs.append(f"{alt_name} (Ki={alt_ki[0]:.1f})")
            alt_kis.append(alt_ki[0])

        candidates.append(
            OBPEntry(
                name=obp_name,
                ki_for_target=ki_value,
                target_censor=censor,
                alt_vocs=alt_vocs,
                alt_ki_values=alt_kis,
                studies_count=studies_per_obp[col_idx - 2],
            )
        )

    return matched_voc, candidates
