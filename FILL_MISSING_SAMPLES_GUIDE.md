# Guide: Filling Missing Samples in Monthly Dataset

## Overview

When recovering samples from partial pipeline runs, you may have gaps in your monthly sampling strategy. These tools help you identify which months are incomplete and fetch exactly the missing samples.

## Quick Start

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Step 1: Analyze current distribution (takes ~20-30 minutes for 6,600 samples)
python3 analyze_sample_distribution.py

# Step 2: Review the gap report
cat sample_distribution_report.txt

# Step 3: Fill in the missing samples (takes ~5-10 minutes)
python3 fill_missing_samples.py

# Step 4: Verify final count
wc -l sra_accessions_ecoli_monthly_100_2020-2026.txt
```

## Step-by-Step Instructions

### Step 1: Analyze Sample Distribution

This script queries NCBI for each recovered sample's release date and bins them by month.

```bash
python3 analyze_sample_distribution.py [input_file] [output_report]
```

**Default files:**
- Input: `sra_accessions_ecoli_monthly_100_2020-2026.txt`
- Output: `sample_distribution_report.txt`

**What it does:**
- Queries NCBI E-utilities API for each SRR accession
- Extracts the release date (year-month)
- Counts samples per month from Jan 2020 to Jan 2026
- Identifies months with <100 samples
- Generates detailed report

**Time:** ~20-30 minutes for 6,600 samples (0.35 sec per query with rate limiting)

**Example output:**
```
Progress: 100/6600 (1.5%)
Progress: 200/6600 (3.0%)
...

Summary:
  Complete months: 58/73
  Incomplete months: 15
  Total missing: 542 samples

Top 10 months needing samples:
  2025-12: 100 samples
  2025-11: 87 samples
  2024-08: 45 samples
  ...
```

### Step 2: Review the Gap Report

Open `sample_distribution_report.txt` to see:

```
======================================================================
E. coli Sample Distribution Report
Generated: 2026-02-05 16:00:00
======================================================================

Total samples analyzed: 6600
Failed queries: 0
Successfully dated: 6600

======================================================================
Monthly Distribution
======================================================================

✓ 2020-01: 100 samples
✓ 2020-02: 100 samples
✗ 2020-03:  87 samples (missing 13)
✓ 2020-04: 100 samples
...
✗ 2025-12:   0 samples (missing 100)
✓ 2026-01: 100 samples

======================================================================
Summary
======================================================================

Complete months (≥100 samples): 58/73
Incomplete months: 15/73
Total missing samples: 542

Months needing samples:
  2020-03: 13 samples needed
  2020-07: 8 samples needed
  ...
  2025-12: 100 samples needed
```

### Step 3: Fill Missing Samples

This script reads the gap report and fetches exactly the missing samples for each incomplete month.

```bash
python3 fill_missing_samples.py [input_file] [report_file]
```

**Default files:**
- Input: `sra_accessions_ecoli_monthly_100_2020-2026.txt`
- Report: `sample_distribution_report.txt`
- Output: Appends to input file

**What it does:**
- Parses the gap report to find incomplete months
- For each incomplete month:
  - Queries NCBI for E. coli samples from that specific month
  - Filters out samples already in your list (no duplicates)
  - Randomly samples exactly the number needed
- Appends new samples to the existing file
- Reports final count

**Time:** ~5-10 minutes (depends on number of incomplete months)

**Example output:**
```
Existing samples: 6600

Found 15 incomplete months

Fetching 13 samples for 2020-03...
Querying 2020-03... Found 450 total → Got 450 accessions
  ✓ Selected 13 new samples

Fetching 8 samples for 2020-07...
Querying 2020-07... Found 520 total → Got 520 accessions
  ✓ Selected 8 new samples

...

======================================================================
Complete!
======================================================================
Original samples: 6600
New samples added: 542
Final total: 7142
Target: ~7,142 (73 months × 100 samples)
Completion: 100.0%
```

### Step 4: Verify and Use

```bash
# Check final count
wc -l sra_accessions_ecoli_monthly_100_2020-2026.txt
# Should be ~7,142

# Optional: Re-analyze to verify all months are complete
python3 analyze_sample_distribution.py

# Use the complete list in your pipeline
sbatch run_ecoli_monthly_100_2020-2026.sh
```

## Important Notes

### Rate Limiting
Both scripts include NCBI API rate limiting:
- `analyze_sample_distribution.py`: 0.35 seconds per query
- `fill_missing_samples.py`: 0.4-1.0 seconds per query

**Do not remove the `time.sleep()` calls** - NCBI will block your IP if you query too fast.

### Handling Failures

**If analyze script fails partway through:**
- The script will show which samples failed
- Most common cause: Network timeout or NCBI API issues
- Solution: Re-run the script (it will re-query all samples)

**If fill script can't find enough samples:**
- Some months may have fewer than 100 E. coli samples available
- The script will warn you: "Only X new samples available (needed Y)"
- This is normal for recent months or months with limited submissions

### Running in Background

Both scripts can take 20-30 minutes. Run in background:

```bash
# Analyze in background
nohup python3 analyze_sample_distribution.py > analyze.log 2>&1 &

# Check progress
tail -f analyze.log

# When done, fill gaps in background
nohup python3 fill_missing_samples.py > fill.log 2>&1 &
tail -f fill.log
```

## Troubleshooting

### Error: "Input file not found"
Make sure you're in the directory with `sra_accessions_ecoli_monthly_100_2020-2026.txt`

### Error: "No gaps found in report"
If the analyze script shows all months are complete, you don't need to run the fill script!

### Script hangs on a specific sample
Occasionally NCBI API times out. Press Ctrl+C and re-run. The script will continue.

### Final count is less than 7,142
Some months genuinely have fewer than 100 E. coli samples in NCBI. This is expected, especially for recent months.

## Advanced Usage

### Analyze a different file

```bash
python3 analyze_sample_distribution.py my_samples.txt my_report.txt
```

### Fill from a specific report

```bash
python3 fill_missing_samples.py my_samples.txt my_report.txt
```

### Check distribution without filling

Just run Step 1 and review the report. You don't have to fill gaps if the current set is sufficient.

## What to Do After Filling

1. **Cancel current job** (if running with incomplete list):
   ```bash
   scancel <job_id>
   ```

2. **Restart with complete list**:
   ```bash
   cd /fastscratch/tylerdoe/COMPASS-pipeline
   sbatch run_ecoli_monthly_100_2020-2026.sh
   ```

3. **Or keep current job running** and use the complete list for future runs

## Contact

Questions? Check COMPASS pipeline documentation or session notes.

---

**Version:** 1.0
**Date:** February 2026
**Pipeline:** COMPASS v1.3-dev
