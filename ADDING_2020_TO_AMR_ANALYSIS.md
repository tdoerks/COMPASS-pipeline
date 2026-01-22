# Adding E. coli 2020 to AMR-Prophage Analysis

**Date:** January 22, 2026
**Purpose:** Extend AMR-prophage analysis from 4 years (2021-2024) to 5 years (2020-2024)
**Status:** ✅ Scripts ready, awaiting execution

---

## Current Status

**Existing Analysis** (completed Jan 20):
- Years: 2021-2024 (4 years)
- Total AMR genes: 396
- Breakdown:
  - 2021: 74 genes
  - 2022: 108 genes
  - 2023: 94 genes
  - 2024: 120 genes

**E. coli 2020 Data** (available):
- Location: `/bulk/tylerdoe/archives/ecoli_2020_all_narms/`
- COMPASS pipeline completed recently
- Has AMRFinder and VIBRANT results
- Ready for prophage-AMR analysis

---

## What Was Created

### 1. `run_ecoli_2020_prophage_amr_analysis.sh`
**Purpose:** Run Method 3 (gold standard) AMR-prophage analysis on 2020 data

**What it does:**
- Extracts prophage sequences from VIBRANT output
- Runs AMRFinder directly on prophage DNA
- Creates `method3_direct_scan.csv` for 2020

**Resources:**
- Time: 24 hours
- CPUs: 4
- Memory: 16GB

**Expected runtime:** 6-8 hours (similar to 2021 analysis)

**Output:**
- `/homes/tylerdoe/ecoli_2020_prophage_amr_analysis_YYYYMMDD/method3_direct_scan.csv`

### 2. Updated `bin/analyze_amr_prophage_comprehensive.py`
**Changes:**
- Added optional `--csv-2020` and `--vibrant-2020` arguments
- Made year columns dynamic (no longer hardcoded to 2021-2024)
- Updated all analysis functions to handle variable years

**Benefits:**
- Works with 2020-2024 OR 2021-2024
- Future-proof for adding 2025, 2026, etc.
- No code changes needed for additional years

### 3. `run_comprehensive_amr_prophage_analysis_2020-2024.sh`
**Purpose:** Run comprehensive analysis on all 5 years (2020-2024)

**What it does:**
- Auto-detects latest Method 3 CSVs for each year
- Includes 2020 if available, otherwise runs 2021-2024 only
- Generates all publication-ready analyses:
  - Gene frequency (with 5-year breakdown)
  - Drug class temporal trends
  - Top samples
  - Gene co-occurrence
  - Prophage characteristics
  - BLAST-ready sequences (30 samples)
  - Summary statistics

**Resources:**
- Time: 2 hours
- CPUs: 1
- Memory: 8GB

**Expected runtime:** 1-2 hours

**Output:**
- `/homes/tylerdoe/comprehensive_amr_prophage_analysis_2020-2024_YYYYMMDD/`

---

## How to Run (2-Step Process)

### Step 1: Run 2020 AMR Analysis

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git pull origin v1.3-dev
sbatch run_ecoli_2020_prophage_amr_analysis.sh
```

**Monitor progress:**
```bash
tail -f ~/slurm-ecoli-2020-prophage-amr-*.out
```

**Expected output:**
```
E. coli 2020: XXX AMR genes in prophages
```

### Step 2: Run Comprehensive Analysis (After Step 1 Completes)

```bash
sbatch run_comprehensive_amr_prophage_analysis_2020-2024.sh
```

**Check results:**
```bash
cat ~/comprehensive_amr_prophage_analysis_2020-2024_*/summary_statistics.txt
```

---

## Expected Results with 2020 Data

**Current (2021-2024):**
- Total AMR genes: 396
- 4-year trend visible

**With 2020 added:**
- Total AMR genes: ~480-520 (estimated)
- 5-year trend analysis
- Pre/post-COVID comparison possible (2020 vs 2021-2024)
- Better statistical power for all analyses

**Example summary (projected):**
```
OVERALL STATISTICS
Total AMR genes in prophages: 510
Unique AMR genes: 22
Unique samples with AMR prophages: 410
Drug classes represented: 10

BY YEAR
2020:
  AMR genes: 114
  Samples: 97

2021:
  AMR genes: 74
  Samples: 67

2022:
  AMR genes: 108
  Samples: 90

2023:
  AMR genes: 94
  Samples: 78

2024:
  AMR genes: 120
  Samples: 98
```

---

## Why Add 2020?

1. **Complete temporal coverage** - No gap in your dataset
2. **Better trends** - 5 data points instead of 4 for temporal analysis
3. **Pre-COVID baseline** - 2020 can serve as pre-pandemic comparison
4. **More statistical power** - ~100 additional genes and samples
5. **Publication strength** - Reviewers like complete datasets

---

## Files Updated

```
COMPASS-pipeline/
├── bin/
│   └── analyze_amr_prophage_comprehensive.py  (updated - supports 2020)
├── run_ecoli_2020_prophage_amr_analysis.sh    (new)
└── run_comprehensive_amr_prophage_analysis_2020-2024.sh  (new)
```

**Branch:** v1.3-dev
**Commit:** dcda8fc

---

## Troubleshooting

### If 2020 Analysis Fails

**Check data exists:**
```bash
ls -lh /bulk/tylerdoe/archives/ecoli_2020_all_narms/amrfinder/*.tsv | wc -l
ls -lh /bulk/tylerdoe/archives/ecoli_2020_all_narms/vibrant/*_phages.fna | wc -l
```

**Check for errors:**
```bash
tail -100 ~/slurm-ecoli-2020-prophage-amr-*.err
```

### If Comprehensive Analysis Can't Find 2020 CSV

The script auto-detects the latest CSVs. If it can't find 2020:

**Manual check:**
```bash
ls -t ~/ecoli_2020_prophage_amr_analysis_*/method3_direct_scan.csv
```

**If found, the comprehensive script will automatically use it**

---

## Alternative: Run Without 2020

If you decide not to include 2020, the comprehensive analysis script will automatically fall back to 2021-2024 only:

```bash
# Just run this - it will detect what's available
sbatch run_comprehensive_amr_prophage_analysis_2020-2024.sh
```

It will warn:
```
⚠️ Warning: No 2020 data found - running with 2021-2024 only
```

And proceed with the 4-year analysis.

---

## Next Steps After Completion

1. **View summary:**
   ```bash
   cat ~/comprehensive_amr_prophage_analysis_2020-2024_*/summary_statistics.txt
   ```

2. **Send BLAST sequences to collaborator:**
   ```bash
   ls -lh ~/comprehensive_amr_prophage_analysis_2020-2024_*/sequences_for_blast.fasta
   ```

3. **Create publication figures:**
   - Import CSVs into R/Python for plotting
   - 5-year temporal trends
   - Drug class distribution over time

4. **Update phylogeny analyses:**
   - May want to re-run phylogenies with 2020 prophages included
   - Use same scripts, just add 2020 to the dataset definitions

---

**Ready to add 2020 and get the complete 5-year analysis! 🎉**
