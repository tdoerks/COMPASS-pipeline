# Run Notes - COMPASS Comparative Analysis

Quick reference for running the comparative analysis pipeline on Beocat.

## Quick Start (3 commands)

```bash
# 1. Pull latest version
cd /fastscratch/tylerdoe/COMPASS-pipeline && git pull origin v1.2-mod

# 2. Navigate and load Python
cd comparative-analysis && module load Python/3.9

# 3. Run it!
bash run_pipeline.sh
```

## What It Does

**Reads from** (your existing COMPASS results):
- `/bulk/tylerdoe/archives/kansas_2022_ecoli/` - 2,838 E. coli samples
- `/bulk/tylerdoe/archives/results_ecoli_2023/` - 3,864 E. coli samples
- `/bulk/tylerdoe/archives/results_ecoli_all_2024/` - E. coli 2024 samples

**Writes to** (permanent storage):
- `/bulk/tylerdoe/archives/comparative_analysis_results/`

**Processing time:** ~30-60 minutes

## Output Files

Main results in: `/bulk/tylerdoe/archives/comparative_analysis_results/results/`

- **`integrated_summary.csv`** - Master dataset linking all samples
- **`integrated_summary_cooccurrence.csv`** - Plasmid-AMR associations

## Download Results to Local Machine

```bash
# From your local computer
scp tylerdoe@beocat.ksu.edu:/bulk/tylerdoe/archives/comparative_analysis_results/results/*.csv ./
```

## Troubleshooting

**Error: "pandas not found"**
```bash
pip install --user pandas numpy
```

**Want to rerun from scratch?**
```bash
rm -rf /bulk/tylerdoe/archives/comparative_analysis_results/
bash run_pipeline.sh
```

**Check progress:**
```bash
tail -f /bulk/tylerdoe/archives/comparative_analysis_results/logs/integrate_data.log
```

## Next Steps After Pipeline Completes

1. Review the integrated summary
2. Explore plasmid-AMR associations
3. Run statistical analyses (scripts coming soon)
4. Create visualizations (scripts coming soon)

## What Makes This Analysis Novel

- **Integrates 3 data types:** Plasmids + Prophages + AMR (NARMS doesn't do this!)
- **Temporal scale:** Tracks changes 2022 → 2024
- **Large scale:** ~7,000+ E. coli genomes
- **Publication-worthy:** Novel connections between mobile genetic elements

## Research Questions This Answers

1. Which plasmid replicon types carry the most AMR genes?
2. Do prophages co-occur with specific plasmid families?
3. How do mobile element patterns change over time?
4. Can we identify "super-spreader" plasmids?

---

**Last Updated:** December 24, 2025
**Pipeline Version:** v1.2-mod
**Location:** COMPASS-pipeline repository, comparative-analysis/
