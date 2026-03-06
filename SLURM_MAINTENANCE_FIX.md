# Slurm Script Update for Maintenance Window

## Problem
- Current job (ID: 5681279) is pending with reason: "ReqNodeNotAvail, Reserved for maintenance"
- Maintenance window: **January 13, 2026 at 08:00:00** (in ~4 days, 21 hours from January 8, 2026 11:04:20)
- Maintenance duration: 8 hours affecting 316 nodes
- Need job to complete **before** maintenance starts

## Solution
Created new optimized Slurm script: `run_ecoli_2020.sh`

### Key Changes from Previous Scripts

| Parameter | Previous (24h) | New (3.5 days) | Reason |
|-----------|----------------|----------------|--------|
| `--time` | 24:00:00 | **84:00:00** | 3.5 days = 84 hours to complete before maintenance |
| `--cpus-per-task` | 2 | **8** | Increased parallelism for faster processing |
| `--mem` | 8G | **32G** | More memory for larger 2020 dataset |
| Year filter | 2025 | **2020** | Target year for E. coli analysis |
| Output dir | results_kansas_2025 | **results_ecoli_2020** | Descriptive output directory |

### Resource Justification

**Time (84 hours)**:
- Provides 3.5-day buffer before maintenance window
- Based on pipeline config, critical time-consuming steps:
  - VIBRANT (phage identification): up to 12h per batch
  - ASSEMBLE_SPADES (if needed): up to 12h per batch
  - For full year of 2020 E. coli data, this allows ample time for:
    - Metadata download and filtering
    - SRA downloads (if needed)
    - Assembly (if raw reads)
    - AMR detection
    - Phage analysis
    - Report generation

**CPUs (8)**:
- Matches VIBRANT and ASSEMBLE_SPADES optimal configuration (8 CPUs)
- Enables efficient parallel processing
- Balances throughput with resource availability

**Memory (32GB)**:
- Matches ASSEMBLE_SPADES requirement (32GB per config)
- Handles large assembly graphs for E. coli genomes
- Prevents memory-related failures during peak processing

### NARMS BioProjects
The pipeline automatically targets E. coli NARMS data:
- **E. coli BioProject**: PRJNA292663
- Filters applied: Kansas (KS) samples from 2020

## Usage

### Option 1: Cancel and Resubmit
If current job hasn't started yet:
```bash
# Cancel the pending job
scancel 5681279

# Submit the new optimized script
sbatch run_ecoli_2020.sh
```

### Option 2: Let Current Job Fail and Resubmit
If job fails due to time limit or maintenance:
```bash
# Submit with corrected parameters
sbatch run_ecoli_2020.sh
```

## Expected Timeline

Assuming submission on **January 8, 2026 ~11:00 AM**:
- Job starts: Immediately (or when resources available)
- Maximum runtime: 84 hours (3.5 days)
- Latest completion: **January 11, 2026 ~7:00 PM**
- Maintenance starts: **January 13, 2026 at 8:00 AM**
- **Buffer: ~36.5 hours** before maintenance

This provides comfortable margin for:
- Queue delays
- Unexpected processing time
- File I/O bottlenecks

## Monitoring

Monitor job progress:
```bash
# Check job status
squeue -u $USER

# Watch output log
tail -f ecoli_2020_*.out

# Check error log
tail -f ecoli_2020_*.err

# Monitor Nextflow progress
# (Look for process completion messages in output log)
```

## Output Location
Results will be saved to: `results_ecoli_2020/`

Directory structure:
```
results_ecoli_2020/
├── metadata/                    # NARMS metadata for E. coli
├── filtered_samples/            # Filtered 2020 KS E. coli samples
├── amrfinder/                   # AMR detection results
├── vibrant/                     # Phage identification
├── diamond_prophage/            # Prophage comparisons
├── checkv/                      # Quality assessment
├── phanotate/                   # Gene predictions
└── summary/                     # Integrated reports
    ├── phage_analysis_summary.tsv
    └── phage_analysis_report.html
```

## Troubleshooting

### If job still shows "ReqNodeNotAvail"
- The maintenance reservation might be blocking submission
- Try different partition: `#SBATCH --partition=killable.q`
- Or request specific non-reserved nodes

### If job runs too long
- Monitor at 60-hour mark
- If progress is slow, consider:
  - Reducing year range (split 2020 into quarters)
  - Filtering by source type
  - Running in multiple smaller batches

### If job fails due to resources
- Check error log for "Out of Memory" or "Killed" messages
- Increase memory: `#SBATCH --mem=64G`
- Reduce CPU if memory-bound: `#SBATCH --cpus-per-task=4`

## Notes

- Original pending job (5681279) can be cancelled once new job is running successfully
- This script uses `main_metadata.nf` workflow (metadata filtering → results)
- Nextflow will handle caching - restarting won't re-download completed samples
- All tools run in Apptainer/Singularity containers for reproducibility
