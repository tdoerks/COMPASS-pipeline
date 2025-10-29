# Beocat Run Fixes - October 2025

## Problem Summary

Recent COMPASS pipeline runs on Beocat encountered timeout and failure issues:

### Job History (Last 5 Days)
- **Job 3753351** (Kansas 2025): TIMEOUT after 2 days (48 hours) - **83% complete**
- **Job 3753138** (Kansas 2025): FAILED after 58 minutes
- **Jobs 3755669-3766483** (Kansas 2024): Multiple FAILED runs (1-2 hours)
- **Job 3766588** (Kansas 2023): FAILED after 23 seconds

## Root Causes Identified

### 1. Insufficient Time Allocation
The Kansas 2025 run was making excellent progress but ran out of time:
- Downloaded and processed 189 samples
- Completed FastQC, fastp, and 83% of assemblies
- Hit 48-hour limit before completion

### 2. Progress at Timeout (Job 3753351)
```
✅ Download: 189/189 (100%)
✅ FastQC: 189/189 (100%)
✅ fastp: 189/189 (100%)
⚠️  Assembly: 156/189 (83% - 10 failed)
⚠️  AMRFinder: 130/146 (89%)
⚠️  ABRicate: 505/584 (86%)
⚠️  MLST: 134/146 (92%)
❌ SISTR: 15/24 Salmonella (15 failures)
❌ MOB-suite: 0/146 (blocked)
```

### 3. Potential Issues
- **SISTR failures**: 15/24 Salmonella samples failing (needs investigation)
- **MOB-suite blocked**: Not starting (dependency issue)
- **Slow phage analysis**: VIBRANT, DIAMOND, PHANOTATE taking considerable time
- **Assembly failures**: 10 samples failed assembly

## Solutions Implemented

### 1. Extended Time Limits (48h → 168h = 7 days)

**Updated scripts:**
- `run_kansas_2025.sh`: 48h → **168h (7 days)**
- `run_2025_production.sh`: 120h → **168h (7 days)**
- `run_kansas_2024_fastscratch.sh`: Already 168h ✓
- `run_kansas_2023_fastscratch.sh`: Already 168h ✓

### 2. Added Session Isolation

To prevent Nextflow lock conflicts when running multiple jobs:

**Added to all scripts:**
```bash
-w work_YEAR                      # Separate work directories
-name job_name_${SLURM_JOB_ID}   # Unique session names
```

This ensures:
- Kansas 2023, 2024, and 2025 runs don't interfere with each other
- Can run multiple years in parallel
- Resume works correctly for each job

### 3. Maintained -resume Flag

All scripts keep the `-resume` flag, so:
- Failed jobs can pick up where they left off
- No need to re-download or re-process completed samples
- Saves significant time and resources

## Next Steps

### Immediate Actions
1. **Resubmit Kansas 2025 run** (will resume from 83%):
   ```bash
   cd /homes/tylerdoe/pipelines/compass-pipeline
   sbatch run_kansas_2025.sh
   ```

2. **Check 2024/2023 failure reasons**:
   ```bash
   # Kansas 2024
   tail -100 /fastscratch/tylerdoe/slurm-3766483.out
   cat /fastscratch/tylerdoe/slurm-3766483.err

   # Kansas 2023
   tail -100 /fastscratch/tylerdoe/slurm-3766588.out
   cat /fastscratch/tylerdoe/slurm-3766588.err
   ```

3. **Monitor SISTR failures** (once jobs restart):
   ```bash
   # Find SISTR work directories with errors
   find work_2025 -name "*SISTR*" -name ".exitcode" -exec grep -l "[^0]" {} \;

   # Check logs for specific error
   cat work_2025/xx/xxxx/.command.log | grep -i error
   ```

### Investigation Needed

**SISTR Failures (15/24 Salmonella samples):**
- May be legitimate (not Salmonella despite metadata)
- Could be assembly quality issues
- Might be SISTR database/version issue
- Check logs when job resumes

**MOB-suite Not Starting:**
- Verify dependency requirements
- Check if waiting on upstream processes
- May start once other processes complete

**Assembly Failures (10/189):**
- Common with low-quality samples
- Review failed sample IDs
- Check if consistent organism/source patterns

## Resource Allocation

Current allocation (seems appropriate):
- **CPUs**: 2 per task
- **Memory**: 8 GB for main job
- **Time**: 168 hours (7 days) - NEW

Individual process resources are set in `conf/base.config` and appear adequate based on progress achieved.

## Expected Timeline

With 7-day limit and -resume:
- **Kansas 2025**: Should complete (was 83% done in 2 days)
- **Kansas 2024**: ~150-200 samples expected
- **Kansas 2023**: ~100-150 samples expected

## Monitoring Commands

While jobs are running:
```bash
# Check job status
squeue -u tylerdoe

# Monitor progress
tail -f slurm-JOBID.out

# Check Nextflow progress
tail -f .nextflow.log

# View work directory growth
watch -n 60 'du -sh work_2025'
```

## Files Modified

1. `run_kansas_2025.sh`
   - Time: 48h → 168h
   - Added: `-w work_2025`
   - Added: `-name kansas_2025_${SLURM_JOB_ID}`

2. `run_2025_production.sh`
   - Time: 120h → 168h
   - Added: `-w work_2025_prod`
   - Added: `-name production_2025_${SLURM_JOB_ID}`

3. `run_kansas_2024_fastscratch.sh`
   - Added: `-w work_2024`
   - Added: `-name kansas_2024_${SLURM_JOB_ID}`

4. `run_kansas_2023_fastscratch.sh`
   - Note: Already had `-w work_2023` and `-name kansas_2023`

## Summary

✅ **Main issue identified**: Insufficient time allocation
✅ **Primary fix**: Extended to 7 days (168 hours)
✅ **Bonus improvement**: Session isolation for parallel runs
✅ **Resume capability**: Maintained for all scripts
⚠️  **Additional issues**: SISTR failures and MOB-suite blocking need monitoring

The Kansas 2025 run should complete successfully on resubmission since:
- It was 83% done in 2 days
- Now has 7 days (350% more time)
- Will resume from last successful step
- All downloaded data is cached

---

**Date**: October 29, 2025
**Branch**: v1.0-stable
**Action Required**: Resubmit jobs with updated scripts
