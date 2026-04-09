# OBPs Search (Python)

Python tool to rank candidate OBPs for a target VOC using `Compound_OBP_binding.csv`.

## What are VOCs and OBPs (quickly)

- **VOCs (Volatile Organic Compounds):** small molecules that evaporate easily and can be used as scent/chemical signals.
- **OBPs (Odorant-Binding Proteins):** proteins (often in insect olfaction) that bind odor molecules and help transport/present them to receptors.

## Run

```bash
cd OBPs_search
python3 -m pip install -e .
obps-search --voc benzaldehyde --top 10
```

Interactive mode:

```bash
cd OBPs_search
python3 main.py
```

## Inputs

- `--voc` (string): target VOC name (exact match first, fallback fuzzy contains).
- `--top` (int): number of OBPs to display.
- Weights:
  - `--w-aff` affinity weight
  - `--w-spec` specificity/selectivity weight
  - `--w-studies` studies/confidence weight
- Uncertainty:
  - `--bootstrap-iters` bootstrap iterations for confidence interval

## Outputs

The table includes:

- `Ki (uM)`: estimated target Ki
- `Cens`: censor type (`exact`, `right` for `>X`, `left` for `<X`)
- `Alt`: number of alternative VOC hits
- `SelIdx`: selectivity index = best off-target Ki / target Ki
- `Conf`: confidence score from number of studies
- `Score`: final rank score
- `CI90`: bootstrap 90% interval for score

## Example inputs and output

### Example 1

Input:

```bash
obps-search --voc benzaldehyde --top 5
```

Output (example):

```text
Matched VOC: benzaldehyde
#   OBP                         Ki (uM)   Cens    Alt   SelIdx    Conf    Score   CI90
1   McinNPC2                    0.81      exact   5     1.85      39.3    83.21   [78.1,87.0]
2   BmorCSP4                    3.20      exact   4     3.40      34.1    82.77   [79.0,86.2]
...
```

### Example 2

Input (custom weights + uncertainty):

```bash
obps-search --voc "ionone (beta)" --top 8 --w-aff 0.6 --w-spec 0.3 --w-studies 0.1 --bootstrap-iters 400
```

## Scoring approach (improved)

1. **Exact-first VOC matching**, then fuzzy fallback.
2. **Censored Ki handling**:
   - `>X` and `<X` are treated as interval-censored proxies (not fixed penalty).
3. **Quantile/rank normalization**:
   - affinity, selectivity, and studies are percentile-scaled (more robust to outliers than max scaling).
4. **Target-centric specificity**:
   - uses selectivity index (`best off-target Ki / target Ki`).
5. **Promiscuity by strength**:
   - off-target penalty uses off-target binding strength, not just count.
6. **Uncertainty output**:
   - bootstrap CI90 for each OBP score.

## Project layout

- Python implementation: `obps_search/`
- Legacy Java prototype preserved in: `java_legacy/`

## Can machine learning be done?

Yes, but only if you have richer labeled data (e.g., validated true-positive OBP-VOC detection outcomes, assay metadata, replicates). If labels are limited, this ranking system is a strong baseline and easier to interpret. A practical path:

1. Keep this scorer as baseline.
2. Add curated features (phylogeny, structure embeddings, physicochemical descriptors).
3. Train a probabilistic model with calibration and compare against baseline by cross-validation.
