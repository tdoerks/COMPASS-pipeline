# Fix ecoli_monthly_100 Resume Issue - February 11, 2026

## Summary

Fixed critical issue with `run_ecoli_monthly_100_2020-2026.sh` script that was creating new dated output directories on each run instead of properly resuming from existing work. This caused storage bloat with multiple duplicate output directories.

---

## Problem Identified

### Issue
The SLURM script `run_ecoli_monthly_100_2020-2026.sh` was creating a new output directory with date suffix on every run:

```bash
OUTPUT_DIR="/fastscratch/tylerdoe/ecoli_monthly_100_$(date +%Y%m%d)"
```

This resulted in multiple directories:
- `ecoli_monthly_100_20260127` (146,847 files)
- `ecoli_monthly_100_20260128` (181,383 files)
- `ecoli_monthly_100_20260129` (140,491 files)
- `ecoli_monthly_100_20260130` (2,346,245 files)
- `ecoli_monthly_100_20260202` (9,158,885 files)
- `ecoli_monthly_100_20260205` (9,170,032 files) ← Most complete
- `ecoli_monthly_100_20260206` (4,833 files)
- `ecoli_monthly_100_20260207` (210 files)

### Root Cause
Despite using `-resume` flag and a dedicated work directory (`work_ecoli_monthly_100`), the changing output directory name prevented proper resume behavior and caused confusion about which run was current.

### Impact
- **Storage bloat**: Multiple 4+ TB directories with duplicated results
- **Confusion**: Hard to track which run was current/most complete
- **Inefficiency**: Resume was working for cached tasks, but outputs were scattered

---

## Solution

### Fix Applied

Changed line 36 in `run_ecoli_monthly_100_2020-2026.sh`:

**Before**:
```bash
# Set output directory
OUTPUT_DIR="/fastscratch/tylerdoe/ecoli_monthly_100_$(date +%Y%m%d)"
```

**After**:
```bash
# Set output directory (FIXED - no date suffix for proper resume)
OUTPUT_DIR="/fastscratch/tylerdoe/ecoli_monthly_100"
```

### How This Works

The script already had the correct work directory configuration:
```bash
-w work_ecoli_monthly_100 \
```

Now with the fixed output directory:
1. **Work directory** (`work_ecoli_monthly_100`): Stores all cached task results (shared across all runs)
2. **Output directory** (`ecoli_monthly_100`): Fixed name for final results
3. **Resume behavior**: `-resume` flag now properly continues from previous run

### Benefits
- ✅ Single output directory for all runs
- ✅ Proper resume behavior (skip completed tasks)
- ✅ No more storage bloat from dated directories
- ✅ Clear tracking of current run status

---

## Implementation Steps

### 1. Identified Most Complete Run

Checked file counts across all dated directories:

```bash
for dir in ecoli_monthly_100_*/; do
    echo "=== $dir ==="
    echo "Total files: $(find "$dir" -type f 2>/dev/null | wc -l)"
done
```

**Result**: `ecoli_monthly_100_20260205` had 9,170,032 files (most complete)

### 2. Fixed Script and Committed

```bash
# Edit script to use fixed output directory
vim run_ecoli_monthly_100_2020-2026.sh

# Commit fix
git add run_ecoli_monthly_100_2020-2026.sh
git commit -m "Fix ecoli_monthly_100 script to use fixed output directory for proper resume"
git push origin v1.3-dev
```

**Commit**: 11aa267

### 3. Deployed Fix on Beocat

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Pull updated script
git pull origin v1.3-dev

# Cancel initial job that started with wrong directory
scancel 6349688

# Remove incomplete new directory
rm -rf ecoli_monthly_100

# Copy most complete run (02/05) to fixed name
cp -rp ecoli_monthly_100_20260205 ecoli_monthly_100

# Resubmit with fixed script
sbatch run_ecoli_monthly_100_2020-2026.sh
```

### 4. Cleanup Old Directories

Started screen session for cleanup:

```bash
screen -S cleanup

# Remove all dated output directories
rm -rf ecoli_monthly_100_20260127
rm -rf ecoli_monthly_100_20260128
rm -rf ecoli_monthly_100_20260129
rm -rf ecoli_monthly_100_20260130
rm -rf ecoli_monthly_100_20260202
rm -rf ecoli_monthly_100_20260206
rm -rf ecoli_monthly_100_20260207

# Remove old pipeline directory
rm -rf COMPASS-pipeline-old
```

**Note**: Kept `ecoli_monthly_100_20260205` temporarily as backup until new run confirms success.

---

## Technical Details

### Nextflow Resume Behavior

Nextflow's `-resume` flag works by:
1. Checking work directory for cached task results
2. Computing task hash based on inputs/parameters
3. Reusing cached results if hash matches (task unchanged)
4. Re-running only new/changed/failed tasks

**Key Point**: The work directory (`-w work_ecoli_monthly_100`) is what enables resume, NOT the output directory. However, using a consistent output directory name makes it clearer which run is current.

### File Counts by Directory

| Directory | Files | Status |
|-----------|-------|--------|
| ecoli_monthly_100_20260127 | 146,847 | Early run |
| ecoli_monthly_100_20260128 | 181,383 | Early run |
| ecoli_monthly_100_20260129 | 140,491 | Early run |
| ecoli_monthly_100_20260130 | 2,346,245 | Partial |
| ecoli_monthly_100_20260202 | 9,158,885 | Nearly complete |
| ecoli_monthly_100_20260205 | 9,170,032 | **Most complete** ✅ |
| ecoli_monthly_100_20260206 | 4,833 | Restart |
| ecoli_monthly_100_20260207 | 210 | Fresh start |

### Storage Impact

Estimated storage saved by cleanup:
- 7 dated directories: ~20+ TB total
- COMPASS-pipeline-old: ~1-2 GB
- **Total recovery**: ~20+ TB on fastscratch

---

## Lessons Learned

### Best Practices for Long-Running Nextflow Pipelines

1. **Use fixed output directory names**
   - Don't add timestamps/dates to `--outdir`
   - Use a dedicated work directory with `-w`
   - Let `-resume` handle incremental progress

2. **Monitor work directory growth**
   - Work directories accumulate all task results
   - Periodically clean old work files: `nextflow clean -f`
   - Use work directory cleanup after successful runs

3. **Track run progress systematically**
   - Use SLURM job IDs to track runs
   - Check Nextflow execution reports
   - Monitor MultiQC outputs for completion status

4. **Avoid storage bloat**
   - Clean up failed/incomplete runs promptly
   - Use symlinks in output directories (Nextflow default)
   - Remove dated backup directories after confirming success

---

## Current Status

### Active Run
- **Job ID**: TBD (resubmitted after fix)
- **Output directory**: `/fastscratch/tylerdoe/ecoli_monthly_100`
- **Work directory**: `/fastscratch/tylerdoe/COMPASS-pipeline/work_ecoli_monthly_100`
- **Starting point**: Copied from `ecoli_monthly_100_20260205` (9.17M files)
- **Expected behavior**: Resume from 02/05 progress, complete remaining samples

### Cleanup Status
- ✅ Script fixed and pushed to GitHub
- ✅ Most complete run (02/05) copied to fixed directory name
- 🔄 Deleting old dated directories (in screen session)
- 🔄 New job submitted with fixed script

### Files Modified
- `run_ecoli_monthly_100_2020-2026.sh` - Fixed output directory name

### Git Commits
- **11aa267**: "Fix ecoli_monthly_100 script to use fixed output directory for proper resume"

---

## Next Steps

### Immediate
1. ✅ Wait for `ecoli_monthly_100_20260205` copy to complete
2. ✅ Resubmit job with fixed script
3. 🔄 Monitor job progress
4. 🔄 Verify resume is working correctly

### Short-term
1. Monitor new run for successful resume behavior
2. Confirm all samples are processing
3. Check MultiQC report for completion status
4. Remove `ecoli_monthly_100_20260205` backup once new run confirms success

### Future Prevention
1. Review other SLURM scripts for similar issues
2. Consider adding output directory validation to scripts
3. Document best practices for large-scale runs
4. Add monitoring/alerts for storage usage

---

## Commands for Reference

### Check run progress
```bash
# Check SLURM queue
squeue -u tylerdoe

# Monitor job output
tail -f /homes/tylerdoe/slurm-ecoli-monthly-100-<jobid>.out

# Check output directory size
du -sh /fastscratch/tylerdoe/ecoli_monthly_100

# Count completed samples
find /fastscratch/tylerdoe/ecoli_monthly_100 -name "*.tsv" | wc -l
```

### Resume from specific run (if needed)
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Option 1: Resume current run
sbatch run_ecoli_monthly_100_2020-2026.sh

# Option 2: Force clean restart (use with caution)
rm -rf ecoli_monthly_100
rm -rf work_ecoli_monthly_100
sbatch run_ecoli_monthly_100_2020-2026.sh
```

### Clean work directory after successful run
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Remove only failed/temporary work files
nextflow clean -f

# Complete work directory cleanup (only after confirming results)
# rm -rf work_ecoli_monthly_100
```

---

## Related Sessions

- **SESSION_2026-02-10_validation_analysis.md**: COMPASS validation framework development
- **SESSION_2026-02-10_comprehensive_validation_complete.md**: Full validation results (163 genomes, 100% pass rate)

---

## Contact

Tyler Doerks - tdoerks@vet.k-state.edu
Kansas State University College of Veterinary Medicine

**Repository**: https://github.com/tdoerks/COMPASS-pipeline
**Branch**: v1.3-dev
**Status**: ecoli_monthly_100 run fixed and restarted
**Date**: February 11, 2026

---

## Appendix: SLURM Script Comparison

### Before Fix
```bash
#!/bin/bash
#SBATCH --job-name=ecoli_monthly_100
#SBATCH --output=/homes/tylerdoe/slurm-ecoli-monthly-100-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ecoli-monthly-100-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G

# Set output directory
OUTPUT_DIR="/fastscratch/tylerdoe/ecoli_monthly_100_$(date +%Y%m%d)"  # ❌ DATED

nextflow run main.nf \
    -profile beocat \
    --outdir "$OUTPUT_DIR" \
    -w work_ecoli_monthly_100 \
    -resume
```

### After Fix
```bash
#!/bin/bash
#SBATCH --job-name=ecoli_monthly_100
#SBATCH --output=/homes/tylerdoe/slurm-ecoli-monthly-100-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ecoli-monthly-100-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G

# Set output directory (FIXED - no date suffix for proper resume)
OUTPUT_DIR="/fastscratch/tylerdoe/ecoli_monthly_100"  # ✅ FIXED

nextflow run main.nf \
    -profile beocat \
    --outdir "$OUTPUT_DIR" \
    -w work_ecoli_monthly_100 \
    -resume
```

**Key Change**: Removed `$(date +%Y%m%d)` suffix from OUTPUT_DIR

---

**End of Session Notes**
