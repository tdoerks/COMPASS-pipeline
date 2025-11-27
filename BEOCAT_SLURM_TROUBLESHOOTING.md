# Beocat SLURM Troubleshooting Guide

## The Fastscratch Output Issue (Exit Code 53)

### Problem Description

When submitting SLURM jobs on Beocat with output/error files directed to `/fastscratch/tylerdoe/`, jobs immediately fail with:
- **State**: FAILED
- **ExitCode**: 0:53
- **Elapsed**: 00:00:00
- **Batch step**: CANCELLED

### Root Cause

**SLURM cannot write output files to `/fastscratch/` filesystem from the SLURM controller**

Exit code 53 typically means "**can't open output/error file**". While users can manually write to `/fastscratch/`, the SLURM controller (which creates the output files BEFORE the job runs) cannot access this filesystem for output file creation.

### Discovery Process

1. **Initial symptom**: Jobs completed instantly without creating any output files
2. **Test #1**: Simple "hello world" script → Still failed
3. **Test #2**: Write output to `/homes/tylerdoe/` → SUCCESS!
4. **Test #3**: Run from fastscratch, output to homes → SUCCESS!
5. **Conclusion**: Issue is specific to SLURM output file location, not job execution location

### Solution

**Write SLURM log files to `/homes/` but run pipeline from `/fastscratch/`**

```bash
#!/bin/bash
#SBATCH --output=/homes/tylerdoe/slurm-%j.out  # ✅ Write logs to /homes
#SBATCH --error=/homes/tylerdoe/slurm-%j.err    # ✅ Write errors to /homes

# Change to fastscratch for pipeline execution
cd /fastscratch/tylerdoe/COMPASS-pipeline  # ✅ Run from fastscratch for speed

# Pipeline results still go to fastscratch
nextflow run main.nf \
    --outdir /fastscratch/tylerdoe/results  # ✅ Results to fastscratch
```

### Benefits of This Approach

| Aspect | Location | Reason |
|--------|----------|--------|
| SLURM logs | `/homes/tylerdoe/` | SLURM controller can write here |
| Pipeline execution | `/fastscratch/tylerdoe/COMPASS-pipeline` | Faster I/O, more space |
| Pipeline results | `/fastscratch/tylerdoe/results_*` | Faster I/O, more space |
| Nextflow work dir | `/fastscratch/tylerdoe/work_*` | Temporary files, lots of I/O |

### Verification

Test with this minimal script:

```bash
#!/bin/bash
#SBATCH --output=/homes/tylerdoe/test_%j.out
#SBATCH --error=/homes/tylerdoe/test_%j.err
#SBATCH --time=00:05:00

echo "Test successful!"
hostname
date
```

If this works but fails when output points to `/fastscratch/`, you have the same issue.

### Common Exit Codes

| Code | Meaning | Likely Cause |
|------|---------|--------------|
| 0:0 | Success | Job completed normally |
| 0:1 | General error | Script error, command not found |
| 0:53 | **File creation error** | **Cannot write to output location** |
| 1:0 | Job failed | Process terminated with error |

### Applied Fixes

All COMPASS pipeline scripts have been updated:

**Fixed scripts** (11/24/2025):
- `run_kansas_2025.sh`
- `run_kansas_2024_fastscratch.sh`
- `test_v1.2mod_fastscratch_5samples.sh`
- All `run_kansas_*_fastscratch.sh` scripts (2018-2024)
- All test scripts

**Batch fix tool**: `fix_fastscratch_scripts.sh` automatically updates all scripts

### Disk Space Management

Since SLURM logs go to `/homes/` (which has limited space), use the cleanup utility:

```bash
# Interactive cleanup
./cleanup_homes.sh

# What it cleans:
# - Old SLURM logs (slurm-*.out, slurm-*.err)
# - Test output files
# - Nextflow work/ and .nextflow/ cache
# - Large data directories (offers to move to fastscratch)
```

### Best Practices

1. **SLURM Logs**: Always write to `/homes/tylerdoe/slurm-%j.out`
2. **Pipeline Work**: Run from `/fastscratch/tylerdoe/COMPASS-pipeline`
3. **Results**: Output to `/fastscratch/tylerdoe/results_*`
4. **Cleanup**: Run `cleanup_homes.sh` monthly to free space
5. **Monitor**: Check disk usage with `quota -s`

### Related Issues

**Issue #1**: Directory name mismatch
- **Old**: `compass-pipeline` (lowercase)
- **New**: `COMPASS-pipeline` (uppercase)
- **Fix**: All scripts updated to use uppercase version

**Issue #2**: /homes full
- **Symptom**: Can't write SLURM logs even to /homes
- **Solution**: Run `cleanup_homes.sh` to free space

### Debugging Commands

```bash
# Check job accounting info
sacct -j <jobid> --format=JobID,State,ExitCode,Elapsed,Reason

# Check SLURM output files
ls -lrt /homes/tylerdoe/slurm-*.out | tail -5

# Check disk usage
quota -s
df -h /homes/tylerdoe /fastscratch/tylerdoe

# Test SLURM submission
squeue -u tylerdoe
scontrol show job <jobid>

# Check for recent failed jobs
sacct --starttime $(date -d '1 hour ago' '+%Y-%m-%dT%H:%M:%S') \
      --format=JobID,JobName,State,ExitCode -u tylerdoe
```

### References

- SLURM Exit Codes: https://slurm.schedmd.com/job_exit_code.html
- Beocat Documentation: https://www.cis.ksu.edu/beocat
- COMPASS Pipeline: https://github.com/tdoerks/COMPASS-pipeline

---

**Last Updated**: November 26, 2025
**Issue Resolved**: Exit code 53 fastscratch output problem
**Solution**: Write SLURM logs to `/homes/`, run pipeline from `/fastscratch/`
