# Current Pipeline Run Status & Space Management

## Your Running Job

Based on the Nextflow output, you have a **large pipeline run in progress**:

### Job Details
- **Executor**: SLURM job 4861
- **Dataset**: 3724 total samples (Kansas 2021-2025, all NARMS organisms)
- **Output Location**: `/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod/`
- **Branch**: v1.2-mod

### Progress Summary

✅ **Completed** (167 samples - cached from previous run):
- SRA downloads
- Assembly (SPAdes)
- Quality control (QUAST)
- AMRFinder
- ABRicate (4 databases)
- VIBRANT (prophage detection)
- DIAMOND prophage
- PHANOTATE
- MLST typing
- SISTR (Salmonella)
- MOB-suite (plasmid detection)

🔄 **Currently Processing** (3724 samples):
- FastQC: 784/3724 complete
- fastp (trimming): 783/3724 complete
- Assembly: In progress for newly downloaded samples

⏳ **Waiting**:
- ABRicate summary
- Combine results
- MultiQC final report

❌ **Failed Downloads**: 55 samples (out of 3779 attempted)

## Space Management - IMPORTANT!

### Good News! 🎉
Your pipeline is **already configured correctly** and storing data in **fastscratch**, NOT homes!

```bash
Output: /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod/
Work:   /fastscratch/tylerdoe/work_v12mod_test/ (or similar)
Logs:   /fastscratch/tylerdoe/slurm-*.out/err
```

### Why This Matters

**Fastscratch**:
- ✅ Large storage capacity (TBs)
- ✅ Fast I/O for pipeline operations
- ⚠️  **NOT BACKED UP** - temporary scratch space
- ⚠️  May be subject to auto-cleanup after ~30 days

**Homes**:
- Limited space (typically 50-100 GB quota)
- ✅ Backed up regularly
- Should only store: code, scripts, important final results

### Check Your Space

Run this to see current usage:
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
bash check_disk_usage.sh
```

This will show:
- Homes directory quota and usage
- Fastscratch usage breakdown
- Size of each dataset
- Nextflow work directories (can be cleaned)
- Space-saving recommendations

## Managing Pipeline Data

### What's Taking Up Space

**Large directories** (typical sizes):
1. **fastq/** - Raw FASTQ files: 50-100 GB per 1000 samples
2. **assemblies/** - Assembled genomes: 5-10 GB per 1000 samples
3. **work/** - Nextflow temporary files: Can be very large (100s of GB)
4. **trimmed_fastq/** - Quality-trimmed reads: 30-60 GB per 1000 samples

**Smaller directories**:
- amrfinder/, vibrant/, mlst/, etc: < 1 GB each usually

### Safe Cleanup Options

After your pipeline **completes successfully**:

#### 1. Clean Nextflow work directory
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
nextflow clean -f -k  # Removes unused work files
```

#### 2. Remove intermediate files you don't need
```bash
cd /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod

# If you have assemblies, you can remove raw reads
rm -rf fastq/        # Raw reads (can re-download if needed)
rm -rf trimmed_fastq/  # Trimmed reads (can regenerate)
```

#### 3. Compress large result directories
```bash
# Compress an entire dataset for archival
tar -czf kansas_2021-2025_results.tar.gz kansas_2021-2025_all_narms_v1.2mod/

# Then copy to homes for backup
cp kansas_2021-2025_results.tar.gz /homes/tylerdoe/backups/
```

### ⚠️ DON'T Delete While Running!

**Do NOT** remove these while pipeline is running:
- work/ directory
- Any fastq/ or assembly files currently being processed
- .nextflow/ cache directories

## Monitoring Your Current Job

### Check if still running
```bash
squeue -u tylerdoe
```

### Watch progress
```bash
# Find the log file
ls -ltr /fastscratch/tylerdoe/slurm-*.out | tail -1

# Watch it in real-time
tail -f /fastscratch/tylerdoe/slurm-JOBID.out
```

### Estimate completion time
Based on your current progress:
- 784/3724 samples through FastQC/fastp (~21% of QC)
- With 4861 SLURM tasks, you have good parallelization
- Typical rate: ~50-100 samples/hour (depends on cluster load)
- **Estimated time remaining**: 30-50 hours for full dataset

### Check for errors
```bash
# Check error log
tail -50 /fastscratch/tylerdoe/slurm-JOBID.err

# Check for failed processes
grep -i "error\|fail" /fastscratch/tylerdoe/slurm-JOBID.out
```

## When Pipeline Completes

### 1. Verify Results
```bash
cd /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod

# Check sample counts
find mlst -name "*.tsv" | wc -l
find amrfinderplus -type d -mindepth 1 -maxdepth 1 | wc -l

# Check for summary report
ls -lh summary/compass_summary.tsv
```

### 2. Run Analysis Scripts
Once complete, you can run the AMR-prophage analysis:
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
sbatch run_kansas_2021-2025_analyses.sh
```

### 3. Archive Important Results
```bash
# Create backup of key results
mkdir -p /homes/tylerdoe/kansas_2021-2025_results
cp -r kansas_2021-2025_all_narms_v1.2mod/summary /homes/tylerdoe/kansas_2021-2025_results/
cp -r kansas_2021-2025_all_narms_v1.2mod/multiqc /homes/tylerdoe/kansas_2021-2025_results/
cp -r kansas_2021-2025_all_narms_v1.2mod/*.csv /homes/tylerdoe/kansas_2021-2025_results/
```

## Understanding the 55 Failed Downloads

The output shows **55 failed SRA downloads**. Common reasons:
1. SRA accessions no longer exist/were withdrawn
2. Network timeouts
3. Insufficient permissions
4. Corrupted SRA files

To investigate:
```bash
# Check which samples failed
grep -i "failed\|error" /fastscratch/tylerdoe/slurm-JOBID.out | grep SRR
```

Usually okay to proceed with 55/3779 failures (~1.5% failure rate).

## Quick Reference Commands

```bash
# Check job status
squeue -u tylerdoe

# Check disk usage
bash check_disk_usage.sh

# Monitor pipeline log
tail -f /fastscratch/tylerdoe/slurm-*.out

# Check results so far
ls -lh /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod/

# After completion: run analyses
cd /fastscratch/tylerdoe/COMPASS-pipeline
sbatch run_kansas_2021-2025_analyses.sh
```

## Summary

✅ **Your pipeline is configured correctly** - using fastscratch, not homes
✅ **167 samples already complete** - cached and ready for analysis
🔄 **3724 total samples processing** - will take 30-50 hours
📊 **Analysis scripts ready** - can run once pipeline completes
💾 **Space management tools** - use check_disk_usage.sh to monitor

**Next steps**:
1. Let the current job finish
2. Verify results with the script's built-in checks
3. Run analysis scripts on completed data
4. Archive important results to homes
5. Clean up work directories to free space

---
**Last Updated**: December 2024
