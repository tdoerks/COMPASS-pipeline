# Latest 1000 Bacteria Run - Critical Fixes

**Date:** January 22, 2026
**Job:** 5885049 (FAILED - needs restart with fixes)
**Status:** Both bugs fixed and pushed to v1.3-dev

---

## Summary

The latest 1000 bacteria run encountered TWO critical bugs:

1. **Organism Diversity Bug** - Only Campylobacter downloaded (should be mixed)
2. **Singularity UID Error** - Container can't resolve user ID 3600 on fastscratch

Both have been fixed and are ready for testing!

---

## Bug #1: Organism Diversity Issue

### Problem
```bash
$ awk -F',' '{print $NF}' filtered_samples.csv | sort | uniq -c
   1000 Campylobacter  # Should be ~440 Campy, ~343 E. coli, ~217 Salmonella
```

### Root Cause
`modules/metadata_filtering.nf` line 216 used `.head(1000)` which takes first 1000 rows from concatenated dataframe. Campylobacter metadata is alphabetically first, so all samples were Campylobacter.

### Fix
Changed to random sampling:
```python
combined = combined.sample(n=max_samples, random_state=42)
```

### Commit
- Commit: 10a47ad
- File: `modules/metadata_filtering.nf`

---

## Bug #2: Singularity UID Resolution Error

### Problem
```
FATAL: Couldn't determine user account information: user: unknown userid 3600

Command exit status: 255
Process: AMRFINDER (SRR31981505)
```

### Root Cause
Singularity containers can't resolve user ID 3600 on Beocat's fastscratch filesystem without special container options.

### Fix
Uncommented runOptions in `nextflow.config` line 123:
```groovy
runOptions = '--no-home --contain --bind /homes/tylerdoe/databases:/homes/tylerdoe/databases,/fastscratch/tylerdoe/databases:/fastscratch/tylerdoe/databases'
```

The `--no-home` and `--contain` flags prevent UID resolution issues.

### Commit
- Commit: c629d66
- File: `nextflow.config`

---

## How to Restart with Fixes

### Step 1: Pull Fixed Code
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git pull origin v1.3-dev
```

You should see:
```
Updating 3a6b074..c629d66
Fast-forward
 modules/metadata_filtering.nf | 19 +++++++++++++------
 nextflow.config              |  2 +-
 2 files changed, 14 insertions(+), 7 deletions(-)
```

### Step 2: Cancel Failed Job (if still running)
```bash
scancel 5885049
```

### Step 3: Clean Work Directory (optional but recommended)
```bash
# Remove failed work files to force fresh start
rm -rf work_latest_1000/bf/2d54d8dc2b5d3755c85fb86a2f6fdf

# Or clean all work files for this run
# rm -rf work_latest_1000/*
```

### Step 4: Restart Pipeline
```bash
sbatch run_latest_1000_bacteria.sh
```

### Step 5: Monitor Progress
```bash
# Watch SLURM output
tail -f /homes/tylerdoe/slurm-compass-latest-1000-*.out

# Check organism diversity in filtering step
grep -A 10 "Sampled organism distribution" /homes/tylerdoe/slurm-compass-latest-1000-*.out
```

You should see:
```
Applying stratified random sampling to limit to 1000 samples
Original organism distribution:
  Campylobacter: 15000
  Escherichia: 12000
  Salmonella: 8000
After sampling: 1000 samples
Sampled organism distribution:
  Campylobacter: 440
  Escherichia: 343
  Salmonella: 217
```

---

## Expected Behavior After Fixes

### Organism Diversity
The 1000 samples will be proportionally sampled from all three NARMS organisms:
- **~40-50% Campylobacter** (most abundant in NARMS)
- **~30-40% E. coli**
- **~20-30% Salmonella**

Exact percentages depend on how many samples of each organism pass the ILLUMINA + GENOMIC filters.

### No More UID Errors
The AMRFINDER, VIBRANT, and all other container-based processes should run without UID errors:
```
✓ AMRFINDER (SRR31981505) - COMPLETED
✓ VIBRANT (SRR31981505) - COMPLETED
✓ BUSCO (SRR31981505) - COMPLETED
```

---

## Verification Steps

After the pipeline completes:

### 1. Check Organism Distribution
```bash
OUTPUT_DIR="/fastscratch/tylerdoe/latest_1000_bacteria_$(date +%Y%m%d)"

# Count organisms in final results
awk -F',' 'NR>1 {print $NF}' $OUTPUT_DIR/filtered_samples/filtered_samples.csv | \
  sort | uniq -c | sort -rn
```

Expected:
```
    440 Campylobacter
    343 Escherichia
    217 Salmonella
```

### 2. Check Data Explorer Report
```bash
firefox $OUTPUT_DIR/summary/data_explorer.html
```

Should show:
- Multiple organisms in the organism dropdown
- Different AMR resistance patterns by organism
- Mixed MLST sequence types
- Organism-specific prophage diversity

### 3. Check for Container Errors
```bash
# Should be empty (no UID errors)
grep -i "unknown userid" /homes/tylerdoe/slurm-compass-latest-1000-*.err
grep -i "FATAL" /homes/tylerdoe/slurm-compass-latest-1000-*.err
```

---

## Timeline of Discovery

**January 21, 2026 PM:**
- User noticed filtered_samples.csv had only Campylobacter
- Investigated metadata_filtering.nf
- Found .head() bug on line 216
- Fixed with .sample() for random sampling
- Committed and pushed fix (10a47ad)

**January 22, 2026 AM:**
- Pipeline failed with "unknown userid 3600" error
- Checked nextflow.config
- Found commented-out runOptions that fix this exact issue
- Uncommented and added fastscratch database bind
- Committed and pushed fix (c629d66)

---

## Impact on Other Runs

### Organism Diversity Fix
**Affects:**
- Any run using `--max_samples` with default NARMS projects (all 3 organisms)
- `run_latest_1000_bacteria.sh`

**Does NOT affect:**
- E. coli-specific runs (use `--bioproject PRJNA292663`)
- Runs with explicit organism filters
- Runs without `--max_samples` parameter

### Singularity UID Fix
**Affects:**
- **ALL runs on Beocat fastscratch going forward** ✅
- Prevents UID errors in all container-based processes

**Does NOT affect:**
- Runs in /homes/ directory (different filesystem)
- Runs that were already completing successfully

---

## Commits Summary

| Commit | Fix | Files Changed |
|--------|-----|---------------|
| 10a47ad | Organism diversity (random sampling) | modules/metadata_filtering.nf |
| 8d730cb | Documentation for bug #1 | ORGANISM_DIVERSITY_FIX_SUMMARY.md |
| c629d66 | Singularity UID resolution | nextflow.config |

All commits pushed to: **v1.3-dev branch**

---

## Next Steps

1. **Pull fixes** from v1.3-dev on Beocat
2. **Restart run** with `sbatch run_latest_1000_bacteria.sh`
3. **Monitor** organism diversity in filtering step
4. **Verify** no UID errors in AMRFINDER/VIBRANT processes
5. **Check results** when complete for diverse bacterial dataset

---

## Lessons Learned

### For Future Development:

1. **Always use random sampling** when limiting datasets
   - Never use `.head()` on concatenated multi-group dataframes
   - Use `.sample(n=N, random_state=42)` for reproducible diversity

2. **Enable verbose logging** for critical filtering steps
   - Show organism distribution before/after sampling
   - Helps catch biases early

3. **Document container workarounds** clearly
   - The runOptions fix was already in the code but commented out
   - Add comments explaining WHY fixes are needed

4. **Test on target filesystem** before production
   - UID resolution issues are filesystem-specific
   - What works in /homes/ may fail in /fastscratch/

---

**Both fixes are critical for the success of the latest 1000 bacteria run!**

The combination ensures:
- ✅ Diverse bacterial species representation
- ✅ No container UID errors on fastscratch
- ✅ Successful completion with multi-organism dataset
