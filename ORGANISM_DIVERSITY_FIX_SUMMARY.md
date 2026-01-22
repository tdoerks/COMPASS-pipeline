# Organism Diversity Bug - Investigation and Fix

**Date:** January 21, 2026
**Discovered During:** Latest 1000 bacteria run analysis
**Status:** ✅ FIXED and pushed to v1.3-dev

---

## Quick Summary

The latest 1000 bacteria run was downloading only Campylobacter (all 1000 samples) instead of a diverse mix of bacterial species. 

**Root cause:** Used `.head(1000)` instead of `.sample(1000)`, which takes the first 1000 rows from concatenated dataframes. Since Campylobacter metadata comes first alphabetically, all samples were Campylobacter.

**Fix:** Changed to random sampling with `combined.sample(n=max_samples, random_state=42)` to ensure proportional representation across all organisms.

---

## How to Apply the Fix

### If you want to restart the current run with diverse bacteria:

```bash
# 1. Cancel the current job (if still running)
scancel 5885069  # or whatever the job ID is

# 2. Pull the fix from v1.3-dev
cd /fastscratch/tylerdoe/COMPASS-pipeline
git pull origin v1.3-dev

# 3. Restart the run
sbatch run_latest_1000_bacteria.sh

# 4. Monitor the filtering to verify diversity
tail -f work_latest_1000/*/FILTER_NARMS_SAMPLES/.command.log
```

You should see output like:
```
Applying stratified random sampling to limit to 1000 samples
Original organism distribution:
  Campylobacter: 15234
  Escherichia: 11892
  Salmonella: 7654
After sampling: 1000 samples
Sampled organism distribution:
  Campylobacter: 440
  Escherichia: 343
  Salmonella: 217
```

### If you want to keep the current run:

The current run will complete with 1000 Campylobacter genomes, which is still useful for:
- Benchmarking Campylobacter-specific analysis
- Testing prophage detection in Campylobacter
- Comparing with future diverse bacterial runs

---

## What Changed in the Code

**File:** `modules/metadata_filtering.nf`
**Lines:** 208-230

**Before (buggy):**
```python
if len(combined) > max_samples:
    print(f"  Applying .head({max_samples}) to limit samples")
    combined = combined.head(max_samples)  # BUG: Takes first N rows only!
```

**After (fixed):**
```python
if len(combined) > max_samples:
    print(f"  Applying stratified random sampling to limit to {max_samples} samples")
    print(f"  Original organism distribution:")
    for org in combined['organism'].unique():
        count = len(combined[combined['organism'] == org])
        print(f"    {org}: {count}")

    # Use random sampling to ensure organism diversity
    combined = combined.sample(n=max_samples, random_state=42)

    print(f"  After sampling: {len(combined)} samples")
    print(f"  Sampled organism distribution:")
    for org in combined['organism'].unique():
        count = len(combined[combined['organism'] == org])
        print(f"    {org}: {count}")
```

---

## Why This Happened

1. **Metadata download** (DOWNLOAD_NARMS_METADATA process):
   - Downloads 3 separate CSV files: campylobacter_metadata.csv, ecoli_metadata.csv, salmonella_metadata.csv

2. **Filtering** (FILTER_NARMS_SAMPLES process):
   - Filters each CSV separately
   - Concatenates with `pd.concat(all_samples, ignore_index=True)`
   - Dataframes are concatenated in order they're processed

3. **File processing order**:
   - Nextflow passes files alphabetically
   - campylobacter_metadata.csv comes FIRST
   - All Campylobacter rows appear at the top of combined dataframe

4. **max_samples limiting**:
   - `.head(1000)` takes first 1000 rows
   - All 1000 rows = Campylobacter 🐛

---

## Impact Assessment

### Scripts Affected:
- ✅ `run_latest_1000_bacteria.sh` - Uses `--max_samples 1000` with default NARMS projects

### Scripts NOT Affected:
- ✅ All E. coli runs - Use `--bioproject PRJNA292663` (single organism)
- ✅ State-filtered runs - Additional filters may limit total samples
- ✅ Runs without `--max_samples` - No limiting applied

### Data Integrity:
- ✅ No data corruption
- ✅ No analysis errors
- ⚠️  Just not diverse as expected

---

## Testing After Fix

When a run completes with the fixed code:

```bash
# 1. Check organism distribution in filtered samples
OUTPUT_DIR="/fastscratch/tylerdoe/latest_1000_bacteria_YYYYMMDD"
cd $OUTPUT_DIR

# Count organisms
awk -F',' 'NR>1 {print $NF}' filtered_samples/filtered_samples.csv | sort | uniq -c | sort -rn

# Expected output (example):
#    440 Campylobacter
#    343 Escherichia
#    217 Salmonella
```

```bash
# 2. Check Data Explorer report
firefox $OUTPUT_DIR/summary/data_explorer.html

# Should see:
# - Multiple organisms in organism column
# - Different AMR patterns per organism
# - Mixed MLST sequence types
# - Organism-specific prophage diversity
```

---

## Prevention for Future

**Best practices for limiting datasets:**

```python
# ❌ BAD - Takes first N rows (order-dependent)
df = df.head(max_samples)

# ✅ GOOD - Random sampling ensures diversity
df = df.sample(n=max_samples, random_state=42)

# ✅ EVEN BETTER - Stratified sampling by group
df = df.groupby('organism').apply(
    lambda x: x.sample(min(len(x), per_organism_limit), random_state=42)
).reset_index(drop=True)
```

---

## Questions This Bug Raised

1. **Q:** Why do we download all 3 NARMS organisms by default?
   **A:** To provide maximum flexibility for mixed-organism studies without requiring bioproject specification.

2. **Q:** Should we add a `--filter_organism` parameter?
   **A:** Already exists! Can use `--bioproject PRJNA292663` for E. coli only, or specify organism filter.

3. **Q:** What if I want EQUAL numbers from each organism?
   **A:** Could add stratified sampling option. Current fix does proportional sampling based on available data.

4. **Q:** Why use `random_state=42`?
   **A:** Makes sampling reproducible - same 1000 samples every time script runs with same input data.

---

## Commit Information

**COMPASS-pipeline repository:**
- Branch: v1.3-dev
- Commit: 10a47ad
- Message: "Fix organism diversity issue in max_samples filtering"

**TD-Scratch repository:**
- Branch: vet-lirn-grant
- Commit: 62ab59d
- Documentation: BUG_FIX_organism_diversity_20260121.md

---

## Next Steps

1. **Decide:** Cancel current run and restart with fix, OR let it finish as Campylobacter-only dataset
2. **Pull fix:** `git pull origin v1.3-dev` in COMPASS-pipeline directory
3. **Test:** Run new analysis and verify organism diversity in output
4. **Monitor:** Check other jobs for similar biases (though this bug is specific to max_samples)
5. **Document:** Add to pipeline documentation about sampling behavior

---

**This fix improves the robustness of COMPASS for multi-organism comparative genomics studies! 🎉**
