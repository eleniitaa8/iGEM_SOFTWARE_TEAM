#!/usr/bin/env python3
"""Literature crawler for plant-illness VOC biomarker discovery.

This script queries Europe PMC, extracts candidate VOC names from titles/abstracts,
and aggregates evidence into JSON/CSV for downstream OBP ranking workflows.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus
from urllib.request import urlopen
from urllib.error import URLError

EUROPE_PMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# Compact lexicon of frequent plant-pathology VOCs for a practical baseline.
VOC_LEXICON = {
    "1-octen-3-ol": {"family": "alcohol", "biosensor_relevance": "fungal-associated marker"},
    "2-hexanone": {"family": "ketone", "biosensor_relevance": "stress-induced volatile"},
    "2-heptanone": {"family": "ketone", "biosensor_relevance": "infection-related signal in crops"},
    "2-nonanone": {"family": "ketone", "biosensor_relevance": "defense/stress signal"},
    "2-phenylethanol": {"family": "alcohol", "biosensor_relevance": "microbial and floral volatile"},
    "3-methyl-1-butanol": {"family": "alcohol", "biosensor_relevance": "fermentation/microbial marker"},
    "(e)-2-hexenal": {"family": "aldehyde", "biosensor_relevance": "green-leaf volatile"},
    "(z)-3-hexenol": {"family": "alcohol", "biosensor_relevance": "green-leaf volatile"},
    "alpha-pinene": {"family": "terpene", "biosensor_relevance": "plant defense terpene"},
    "beta-caryophyllene": {"family": "sesquiterpene", "biosensor_relevance": "defense-related terpene"},
    "benzaldehyde": {"family": "aldehyde", "biosensor_relevance": "aromatic stress marker"},
    "benzyl alcohol": {"family": "alcohol", "biosensor_relevance": "aromatic microbial/plant volatile"},
    "ethyl acetate": {"family": "ester", "biosensor_relevance": "microbial fermentation marker"},
    "ethyl butanoate": {"family": "ester", "biosensor_relevance": "fruit/plant pathology aroma"},
    "geraniol": {"family": "monoterpene alcohol", "biosensor_relevance": "defense-associated terpene alcohol"},
    "hexanal": {"family": "aldehyde", "biosensor_relevance": "lipid oxidation / GLV marker"},
    "hexanol": {"family": "alcohol", "biosensor_relevance": "green-leaf volatile"},
    "isoprene": {"family": "isoprenoid", "biosensor_relevance": "plant physiological stress marker"},
    "limonene": {"family": "monoterpene", "biosensor_relevance": "defense / fruit aroma volatile"},
    "linalool": {"family": "monoterpene alcohol", "biosensor_relevance": "defense signaling volatile"},
    "methyl jasmonate": {"family": "oxylipin", "biosensor_relevance": "defense signaling hormone volatile"},
    "methyl salicylate": {"family": "benzenoid ester", "biosensor_relevance": "systemic acquired resistance signal"},
    "nonanal": {"family": "aldehyde", "biosensor_relevance": "lipid peroxidation marker"},
    "ocimene": {"family": "monoterpene", "biosensor_relevance": "induced defense volatile"},
    "octanal": {"family": "aldehyde", "biosensor_relevance": "oxidative stress marker"},
    "terpinolene": {"family": "monoterpene", "biosensor_relevance": "defense-related terpene"},
}

CHARACTERIZATION_HINTS = (
    "gc-ms",
    "headspace",
    "sppm",
    "spme",
    "identified",
    "quantified",
    "biomarker",
    "marker",
    "discriminat",
    "disease",
    "infection",
    "powdery mildew",
    "oidium",
)

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Paper:
    paper_id: str
    title: str
    abstract: str
    year: str
    doi: str
    source: str
    authors: str
    url: str

DEMO_PAPERS = [
    {
        "paper_id": "demo-1",
        "title": "Volatilome signatures in grapevine leaves infected with powdery mildew (Erysiphe necator)",
        "abstract": "Headspace SPME-GC-MS identified 1-octen-3-ol, methyl salicylate, hexanal and nonanal as discriminant biomarkers in infected Vitis vinifera leaves.",
        "year": "2022",
        "doi": "10.0000/demo.oidium.1",
        "source": "Demo Plant Pathology",
        "authors": "A. Example et al.",
        "url": "https://example.org/demo-oidium-1",
    },
    {
        "paper_id": "demo-2",
        "title": "Early diagnosis of grapevine oidium using VOC fingerprints",
        "abstract": "GC-MS analysis quantified 2-heptanone, 2-hexanone and benzaldehyde. Methyl salicylate increased in disease progression and was proposed as a marker.",
        "year": "2021",
        "doi": "10.0000/demo.oidium.2",
        "source": "Demo Sensors in Agriculture",
        "authors": "B. Example et al.",
        "url": "https://example.org/demo-oidium-2",
    },
    {
        "paper_id": "demo-3",
        "title": "Volatile biomarkers for fungal infection in Vitis vinifera",
        "abstract": "Infection profiling by headspace GC-MS identified linalool, ocimene, alpha-pinene and 1-octen-3-ol as relevant to pathogen challenge.",
        "year": "2020",
        "doi": "10.0000/demo.oidium.3",
        "source": "Demo Journal of Plant Defense",
        "authors": "C. Example et al.",
        "url": "https://example.org/demo-oidium-3",
    },
]


def demo_papers(limit: int = 30) -> list[Paper]:
    return [Paper(**row) for row in DEMO_PAPERS[:limit]]



def build_query(plant: str, illness: str, extra_terms: str | None) -> str:
    terms = [
        f'("{plant}")',
        f'("{illness}")',
        '("volatile organic compound" OR VOC OR volatilome OR "headspace")',
        '("GC-MS" OR SPME OR biomarker OR diagnosis OR characterization)',
    ]
    if extra_terms:
        terms.append(f"({extra_terms})")
    return " AND ".join(terms)


def europe_pmc_search(query: str, page_size: int = 50, max_results: int = 100) -> list[Paper]:
    papers: list[Paper] = []
    page = 1

    while len(papers) < max_results:
        url = (
            f"{EUROPE_PMC_URL}?query={quote_plus(query)}"
            f"&format=json&pageSize={page_size}&page={page}"
            "&resultType=core"
        )
        with urlopen(url) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        result_list = payload.get("resultList", {}).get("result", [])
        if not result_list:
            break

        for item in result_list:
            title = (item.get("title") or "").strip()
            abstract = (item.get("abstractText") or "").strip()
            if not title and not abstract:
                continue

            source = item.get("journalTitle") or item.get("source") or ""
            year = str(item.get("pubYear") or "")
            doi = (item.get("doi") or "").strip()
            auth = (item.get("authorString") or "").strip()
            pid = (item.get("id") or item.get("pmid") or "").strip() or f"paper-{len(papers)+1}"
            if item.get("pmcid"):
                link = f"https://europepmc.org/article/PMC/{item['pmcid']}"
            elif item.get("pmid"):
                link = f"https://pubmed.ncbi.nlm.nih.gov/{item['pmid']}/"
            elif doi:
                link = f"https://doi.org/{doi}"
            else:
                link = ""

            papers.append(
                Paper(
                    paper_id=pid,
                    title=title,
                    abstract=abstract,
                    year=year,
                    doi=doi,
                    source=source,
                    authors=auth,
                    url=link,
                )
            )
            if len(papers) >= max_results:
                break

        page += 1

    return papers


def normalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = lowered.replace("β", "beta").replace("α", "alpha")
    return lowered


def extract_voc_mentions(text: str) -> list[str]:
    text_n = normalize_text(text)
    found = []
    for voc in VOC_LEXICON:
        if voc in text_n:
            found.append(voc)
    return found


def evidence_sentences(text: str, voc: str) -> list[str]:
    sentences = SENTENCE_SPLIT_RE.split(text)
    voc_n = voc.lower()
    matches = []
    for sentence in sentences:
        s = sentence.strip()
        if not s:
            continue
        s_n = normalize_text(s)
        if voc_n in s_n and any(h in s_n for h in CHARACTERIZATION_HINTS):
            matches.append(s)
    return matches[:3]


def aggregate(papers: Iterable[Paper]) -> tuple[dict[str, dict], list[dict]]:
    stats: dict[str, dict] = defaultdict(lambda: {
        "mentions": 0,
        "papers": set(),
        "evidence": [],
    })
    paper_items: list[dict] = []

    for p in papers:
        combined = f"{p.title}. {p.abstract}".strip()
        vocs = extract_voc_mentions(combined)
        voc_counter = Counter(vocs)

        paper_items.append(
            {
                "paper_id": p.paper_id,
                "title": p.title,
                "year": p.year,
                "source": p.source,
                "doi": p.doi,
                "url": p.url,
                "authors": p.authors,
                "matched_vocs": sorted(voc_counter.keys()),
            }
        )

        for voc, count in voc_counter.items():
            stats[voc]["mentions"] += count
            stats[voc]["papers"].add(p.paper_id)
            for ev in evidence_sentences(combined, voc):
                stats[voc]["evidence"].append({"paper_id": p.paper_id, "sentence": ev})

    return stats, paper_items


def write_csv(voc_items: list[dict], out_csv: Path) -> None:
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "voc",
                "mentions",
                "papers_count",
                "family",
                "biosensor_relevance",
                "example_paper_ids",
            ],
        )
        w.writeheader()
        for row in voc_items:
            w.writerow(
                {
                    "voc": row["name"],
                    "mentions": row["mentions"],
                    "papers_count": row["papers_count"],
                    "family": row["properties"]["family"],
                    "biosensor_relevance": row["properties"]["biosensor_relevance"],
                    "example_paper_ids": ",".join(row["paper_ids"][:5]),
                }
            )


def run(plant: str, illness: str, extra_terms: str | None, max_papers: int, out_json: Path, out_csv: Path, demo_only: bool = False) -> None:
    query = build_query(plant=plant, illness=illness, extra_terms=extra_terms)
    if demo_only:
        papers = demo_papers(limit=max_papers)
        source_note = "Bundled demo dataset"
    else:
        try:
            papers = europe_pmc_search(query=query, max_results=max_papers)
            source_note = "Europe PMC"
        except URLError as exc:
            print(f"Warning: Europe PMC request failed ({exc}). Falling back to bundled demo papers.")
            papers = demo_papers(limit=max_papers)
            source_note = "Bundled demo dataset"
    stats, paper_items = aggregate(papers)

    voc_items = []
    for voc, data in sorted(stats.items(), key=lambda x: (len(x[1]["papers"]), x[1]["mentions"]), reverse=True):
        props = VOC_LEXICON.get(voc, {"family": "unknown", "biosensor_relevance": "candidate"})
        voc_items.append(
            {
                "name": voc,
                "mentions": data["mentions"],
                "papers_count": len(data["papers"]),
                "paper_ids": sorted(data["papers"]),
                "properties": props,
                "evidence": data["evidence"][:8],
            }
        )

    result = {
        "query": {
            "plant": plant,
            "illness": illness,
            "extra_terms": extra_terms,
            "raw_query": query,
            "source": source_note,
            "searched_at_utc": datetime.now(timezone.utc).isoformat(),
            "papers_retrieved": len(papers),
        },
        "vocs": voc_items,
        "papers": paper_items,
        "next_step": "Use the VOC names as input candidates for OBPs_search to rank OBPs.",
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(voc_items, out_csv)

    print(f"Saved JSON: {out_json}")
    print(f"Saved CSV:  {out_csv}")
    print(f"Papers retrieved: {len(papers)}")
    print(f"VOCs extracted:   {len(voc_items)}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Crawler for plant illness VOC literature.")
    p.add_argument("--plant", required=True, help="Plant name (e.g., grapevine)")
    p.add_argument("--illness", required=True, help="Illness/pathogen/common disease name (e.g., oidium)")
    p.add_argument("--extra-terms", default=None, help="Optional additional boolean terms for the query")
    p.add_argument("--max-papers", type=int, default=80, help="Maximum number of papers to retrieve")
    p.add_argument("--out-json", default="results/vocs_results.json", help="Output JSON path")
    p.add_argument("--demo-only", action="store_true", help="Skip API calls and use bundled demo papers")
    p.add_argument("--out-csv", default="results/vocs_results.csv", help="Output CSV path")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    run(
        plant=args.plant,
        illness=args.illness,
        extra_terms=args.extra_terms,
        max_papers=args.max_papers,
        out_json=Path(args.out_json),
        out_csv=Path(args.out_csv),
        demo_only=args.demo_only,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
