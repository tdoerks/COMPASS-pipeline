# Beocat Support Ticket: SLURM Cannot Write Output Files to /fastscratch/

## Issue Summary

SLURM batch jobs fail immediately with **exit code 53** when `#SBATCH --output` or `#SBATCH --error` directives point to `/fastscratch/tylerdoe/` directory.

## Reproduction Steps

1. Create a simple test script:
```bash
#!/bin/bash
#SBATCH --job-name=test_fastscratch_output
#SBATCH --output=/fastscratch/tylerdoe/test_slurm_%j.out
#SBATCH --error=/fastscratch/tylerdoe/test_slurm_%j.err
#SBATCH --time=00:02:00
#SBATCH --mem=100M

echo "Test message"
```

2. Submit the job:
```bash
sbatch test_fastscratch_output.sh
```

3. Check job status:
```bash
sacct -j <JOBID> --format=JobID,State,ExitCode,Elapsed
```

## Observed Behavior

- **State**: FAILED
- **ExitCode**: 0:53
- **Elapsed**: 00:00:00
- **Batch step**: CANCELLED
- **No output file created** in `/fastscratch/tylerdoe/`

## Expected Behavior

Job should run successfully and create output files at the specified location.

## Workaround

Writing SLURM output files to `/homes/tylerdoe/` instead works successfully:

```bash
#SBATCH --output=/homes/tylerdoe/slurm-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-%j.err
```

The pipeline can still **run from** `/fastscratch/` (by using `cd /fastscratch/tylerdoe/COMPASS-pipeline` in the script body), and results can still be **written to** `/fastscratch/` by the running job. Only the SLURM controller's initial output file creation fails.

## Test Results

**Test Job ID**: 4271518
- Script attempted to write to: `/fastscratch/tylerdoe/TEST_slurm_4271518.out`
- Result: FAILED, exit code 0:53
- File created: No

## Questions for Beocat Support

1. Is this expected behavior? Is `/fastscratch/` intentionally restricted from SLURM output files?

2. What is the recommended location for SLURM output/error files when running jobs that need `/fastscratch/` for performance?

3. Is there a filesystem or permissions issue with `/fastscratch/` that prevents the SLURM controller from creating files there?

4. Should we use `/homes/` for logs and `/fastscratch/` for active work/results, or is there a better practice?

## Environment Details

- **User**: tylerdoe
- **Partition**: batch.q
- **SLURM Version**: (check with `sinfo --version`)
- **Directory permissions**:
  ```bash
  ls -ld /fastscratch/tylerdoe/
  # Result: drwx------ tylerdoe (full user permissions)
  ```

## Exit Code 53 Reference

According to SLURM documentation, exit code 53 typically indicates:
> "Cannot open SLURM output/error file for writing"

This suggests a filesystem access issue from the SLURM controller's perspective, even though users can write to `/fastscratch/` normally.

## Impact

This requires all SLURM batch scripts to write logs to `/homes/tylerdoe/`, which:
- ✅ Works as a solution
- ⚠️ Uses limited `/homes/` quota for log files
- ⚠️ Requires periodic cleanup of old logs
- ⚠️ Separates logs from working directories

## Request

Please clarify whether this is expected behavior and document the recommended best practice for SLURM output file locations on Beocat, particularly for users working with `/fastscratch/` storage.

---

**Contact**: Tyler Doerks (tdoerks@vet.k-state.edu)
**Date**: November 27, 2025
**Related Jobs**: 4271518, 4246768, 4246521
