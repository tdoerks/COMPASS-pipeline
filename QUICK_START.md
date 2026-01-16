# COMPASS Pipeline Quick Start Guide

## TL;DR - I Just Want to Run Kansas 2025

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git checkout v1.2-mod
git pull origin v1.2-mod
sbatch run_kansas_2025.sh
```

Monitor:
```bash
squeue -u tylerdoe
tail -f /homes/tylerdoe/slurm-*.out
```

## Common Commands

### Check Job Status
```bash
squeue -u tylerdoe           # Currently running jobs
sacct -u tylerdoe | tail     # Recent job history
```

### Check Logs
```bash
# SLURM logs (in /homes now!)
ls -lrt /homes/tylerdoe/slurm-*.out | tail -5
tail -100 /homes/tylerdoe/slurm-<jobid>.out

# Nextflow log
tail -100 .nextflow.log
```

### Check Results
```bash
ls -lh /fastscratch/tylerdoe/results_kansas_2025/
ls -lh /fastscratch/tylerdoe/results_kansas_2025/summary/
```

### Clean Up Disk Space
```bash
# If /homes is full:
./cleanup_homes.sh

# Quick manual cleanup:
rm /homes/tylerdoe/slurm-*.out
rm /homes/tylerdoe/slurm-*.err
```

## Available Scripts

### Production Runs
```bash
sbatch run_kansas_2025.sh                    # Full 2025 dataset
sbatch run_kansas_2024_fastscratch.sh        # 2024 dataset
```

### Quick Tests
```bash
sbatch test_v1.2mod_fastscratch_5samples.sh  # 5 samples (~2 hours)
```

### Year-Specific Runs
```bash
sbatch run_kansas_2023_fastscratch.sh
sbatch run_kansas_2022_fastscratch.sh
sbatch run_kansas_2021_fastscratch.sh
sbatch run_kansas_2020_fastscratch.sh
```

## Troubleshooting

### Job Fails Instantly (Exit Code 53)
**Problem:** SLURM can't write to output location

**Solution:** Scripts fixed! Logs now go to `/homes/`. Pull latest code:
```bash
git pull origin v1.2-mod
```

### Disk Space Full
```bash
quota -s
df -h /homes/tylerdoe /fastscratch/tylerdoe
./cleanup_homes.sh
```

### Pipeline Fails Partway Through
```bash
# Check the SLURM log for errors
tail -100 /homes/tylerdoe/slurm-<jobid>.out

# Check Nextflow log
tail -100 .nextflow.log

# Resume from checkpoint
sbatch run_kansas_2025.sh  # -resume flag already included
```

### Can't Find Results
Results are in **fastscratch**, logs are in **homes**:
```bash
ls /fastscratch/tylerdoe/results_kansas_2025/  # Results here
ls /homes/tylerdoe/slurm-*.out                  # Logs here
```

## File Locations

### Where Things Are
```
/fastscratch/tylerdoe/
├── COMPASS-pipeline/          # Working directory (run from here)
├── databases/
│   └── prophage_db.dmnd       # Database
├── results_kansas_2025/       # Output (created by pipeline)
└── work_2025/                 # Nextflow temp files

/homes/tylerdoe/
├── slurm-*.out                # SLURM logs (NEW!)
└── slurm-*.err                # SLURM errors (NEW!)
```

### Important: Logs Moved!
**Old (broken):** `/fastscratch/tylerdoe/slurm-*.out`
**New (working):** `/homes/tylerdoe/slurm-*.out`

## Resume After Failure

Pipeline automatically resumes with `-resume` flag.

Just resubmit:
```bash
sbatch run_kansas_2025.sh
```

Nextflow will skip completed tasks!

## Check Progress

```bash
# Real-time log
tail -f /homes/tylerdoe/slurm-<jobid>.out

# Count completed assemblies
ls /fastscratch/tylerdoe/results_kansas_2025/assemblies/ | wc -l

# Check summary (when done)
cat /fastscratch/tylerdoe/results_kansas_2025/summary/combined_summary.tsv
```

## Generate Report

After pipeline completes:
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
./bin/generate_report_v3.py /fastscratch/tylerdoe/results_kansas_2025 -o compass_report_ks_2025.html
```

Download report:
```bash
scp tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/compass_report_ks_2025.html ~/Downloads/
```

## Getting Help

1. **Check SLURM log:** `/homes/tylerdoe/slurm-<jobid>.out`
2. **Check Nextflow log:** `.nextflow.log`
3. **Read troubleshooting guide:** `BEOCAT_SLURM_TROUBLESHOOTING.md`
4. **Check job details:** `sacct -j <jobid> --format=JobID,State,ExitCode,Elapsed`

## Pro Tips

✅ **DO:**
- Run from `/fastscratch/tylerdoe/COMPASS-pipeline`
- Check disk space before long runs
- Use `-resume` for failed jobs (already in scripts)
- Clean up `/homes/` regularly

❌ **DON'T:**
- Submit from `/homes` (slower)
- Delete `work_2025/` before pipeline finishes
- Modify scripts while job is running

---

**Need more details?** See `BEOCAT_SLURM_TROUBLESHOOTING.md`
