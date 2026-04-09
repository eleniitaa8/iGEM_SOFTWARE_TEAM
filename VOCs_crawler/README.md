# VOCs_crawler

Base crawler to discover **VOCs reported in literature for a plant illness** and export structured outputs (`JSON` + `CSV`) for your OBP workflow.

## What this does

1. Builds a literature query from:
   - plant (e.g., `grapevine`)
   - illness/pathogen (e.g., `oidium`, `powdery mildew`, `Erysiphe necator`)
2. Searches literature (Europe PMC API).
3. Parses titles/abstracts and detects candidate VOC names from a VOC lexicon.
4. Collects evidence snippets (sentences with characterization hints such as `GC-MS`, `SPME`, `identified`, `biomarker`).
5. Exports:
   - `JSON` with papers + ranked VOC findings
   - `CSV` summary for quick filtering
6. Next step: feed VOC names into `OBPs_search`.

## Files

- `vocs_crawler.py` → CLI crawler script.
- `results/oidium_grapevine.json` → example output for grapevine oidium.
- `results/oidium_grapevine.csv` → tabular version of the same example.

## Run

```bash
python3 VOCs_crawler/vocs_crawler.py \
  --plant grapevine \
  --illness oidium \
  --extra-terms "Vitis vinifera OR powdery mildew OR Erysiphe necator" \
  --max-papers 80 \
  --out-json VOCs_crawler/results/oidium_grapevine.json \
  --out-csv VOCs_crawler/results/oidium_grapevine.csv
```

### Demo mode (works without internet/API access)

```bash
python3 VOCs_crawler/vocs_crawler.py \
  --plant grapevine \
  --illness oidium \
  --demo-only \
  --out-json VOCs_crawler/results/oidium_grapevine.json \
  --out-csv VOCs_crawler/results/oidium_grapevine.csv
```

## Output structure (`JSON`)

```json
{
  "query": {
    "plant": "grapevine",
    "illness": "oidium",
    "source": "Europe PMC or Bundled demo dataset"
  },
  "vocs": [
    {
      "name": "methyl salicylate",
      "mentions": 2,
      "papers_count": 2,
      "properties": {
        "family": "benzenoid ester",
        "biosensor_relevance": "systemic acquired resistance signal"
      },
      "evidence": ["..."]
    }
  ],
  "papers": ["..."],
  "next_step": "Use VOC names as input candidates for OBPs_search"
}
```

## Workflow you described (implemented)

- Search papers by **plant + illness**.
- Extract disease-associated **VOCs** and their characterization context.
- Save all findings in **JSON/CSV**.
- Reuse VOC names in the **OBPs_search** tool to prioritize OBPs for biosensor design.

## Notes

- The current VOC extraction is lexicon-based (fast baseline).
- You can expand `VOC_LEXICON` in `vocs_crawler.py` to include more compounds/metadata.
- If Europe PMC is blocked from your environment, the script automatically falls back to bundled demo papers.
