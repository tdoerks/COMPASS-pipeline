# Error Handling in COMPASS Pipeline

The COMPASS pipeline is designed to be robust and continue running even when individual samples fail. This document explains the error handling strategy and how to interpret failure reports.

## Philosophy

**Key principle**: One bad sample should not crash the entire pipeline.

In large-scale genomic analyses, it's common for a small percentage of samples to fail due to:
- Poor data quality
- Corrupted downloads
- Assembly failures
- Timeout issues
- Resource exhaustion

The COMPASS pipeline handles these gracefully by:
1. Retrying failed tasks (with increased resources)
2. Ignoring samples that repeatedly fail
3. Continuing with successful samples
4. Generating detailed failure reports

## Error Strategies by Process

### Critical Processes (Retry then Ignore)
These processes are retried up to 2-3 times before being ignored:

- **DOWNLOAD_SRA**: 3 retries (network issues are common)
- **ASSEMBLE_SPADES**: 1 retry (assembly failures often consistent)
- **AMRFINDER**: 1 retry
- **VIBRANT**: 1 retry

### Optional Processes (Always Ignore)
These processes fail gracefully without retrying:

- **DIAMOND_PROPHAGE**: Prophage analysis is supplementary
- **CHECKV**: Quality assessment is optional
- **PHANOTATE**: Gene prediction can timeout on large sequences

## Exit Codes and Retry Logic

### Automatic Retry Exit Codes
The pipeline automatically retries these common failures:
- **143**: SIGTERM (timeout)
- **137**: SIGKILL (out of memory)
- **104**: Connection reset
- **134, 139, 140**: Segmentation faults

### Other Failures
- First attempt: Retry with 2x memory
- Second attempt: Retry with 4x memory
- Third attempt: Ignore and continue

## Configuration

### Enable Error Handling
```groovy
// In nextflow.config or custom config
includeConfig 'conf/error_handling.config'
```

### Customize Error Strategies
```groovy
process {
    withName: 'MY_PROCESS' {
        errorStrategy = { task.attempt < 3 ? 'retry' : 'ignore' }
        maxRetries = 2
    }
}
```

### Disable Error Handling (Strict Mode)
```groovy
process {
    errorStrategy = 'terminate'  // Stop on first error
    maxErrors = 0
}
```

## Failure Reports

### Location
Failed sample reports are generated in:
```
results/pipeline_info/
├── failed_samples_report.txt  # Human-readable summary
├── failed_samples.csv          # Machine-readable data
├── execution_trace.txt         # Full execution log
└── execution_report.html       # Interactive report
```

### Failed Samples Report Format

**Example `failed_samples_report.txt`:**
```
COMPASS Pipeline - Failed Samples Report
============================================================

Total failed tasks: 5
Unique processes with failures: 2
Unique samples affected: 3

Failures by Process:
------------------------------------------------------------

ASSEMBLE_SPADES: 2 failures
  - Sample: SRR12345678
    Exit code: 137
    Action: IGNORED
  - Sample: SRR12345679
    Exit code: 1
    Action: IGNORED

VIBRANT: 3 failures
  - Sample: SRR12345680
    Exit code: 143
    Action: IGNORED

Failures by Sample:
------------------------------------------------------------

SRR12345678:
  - ASSEMBLE_SPADES (exit: 137)

SRR12345679:
  - ASSEMBLE_SPADES (exit: 1)

SRR12345680:
  - VIBRANT (exit: 143)
```

### CSV Format
```csv
sample_id,process,exit_code,error
SRR12345678,ASSEMBLE_SPADES,137,IGNORED
SRR12345679,ASSEMBLE_SPADES,1,IGNORED
SRR12345680,VIBRANT,143,IGNORED
```

## Interpreting Failures

### Common Failure Scenarios

#### 1. Assembly Failures (ASSEMBLE_SPADES)
**Exit codes**: 1, 137
**Causes**:
- Low coverage data
- Contaminated samples
- Insufficient memory

**Action**: Review sample quality, check read counts

#### 2. Timeout Failures (VIBRANT, PHANOTATE)
**Exit code**: 143
**Causes**:
- Very large genomes
- Complex phage sequences
- Insufficient time allocation

**Action**: Increase time limits or skip problematic samples

#### 3. Out of Memory (OOM)
**Exit code**: 137
**Causes**:
- Large assemblies
- Memory-intensive processes

**Action**: Increase memory allocation or use high-memory nodes

#### 4. Download Failures (DOWNLOAD_SRA)
**Exit codes**: 104, 1
**Causes**:
- Network issues
- Missing/restricted SRA accessions
- SRA server downtime

**Action**: Retry manually or check SRA availability

## Best Practices

### 1. Always Review Failure Reports
After pipeline completion:
```bash
cat results/pipeline_info/failed_samples_report.txt
```

### 2. Rerun Failed Samples
Extract failed sample IDs:
```bash
# Get failed sample IDs
cut -d',' -f1 results/pipeline_info/failed_samples.csv | tail -n +2 > failed_ids.txt

# Create new samplesheet with only failed samples
# Then rerun with increased resources
nextflow run main.nf \
    -profile beocat \
    --input failed_samples.csv \
    --max_memory 512.GB \
    --max_time 48.h
```

### 3. Monitor During Execution
```bash
# Watch for failures in real-time
tail -f .nextflow.log | grep -i "error\\|fail"

# Check SLURM queue
squeue -u $USER | grep FAILED
```

### 4. Use Execution Reports
Open the HTML report for interactive visualization:
```bash
firefox results/pipeline_info/execution_report_*.html
```

## Troubleshooting

### Too Many Failures
If >10% of samples fail:
1. Check input data quality
2. Review resource allocations
3. Check cluster/network status
4. Consider using smaller batches

### Pipeline Won't Continue
If pipeline stops despite error handling:
```bash
# Check error strategy is loaded
nextflow run main.nf -profile beocat --help | grep -i error

# Verify config
nextflow config -profile beocat | grep errorStrategy
```

### Want Strict Mode
To fail immediately on any error:
```bash
nextflow run main.nf -profile beocat -with-dag pipeline.dot
# Remove error_handling.config include
# Or set: process.errorStrategy = 'terminate'
```

## Exit Code Reference

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Continue |
| 1 | General error | Retry then ignore |
| 104 | Connection reset | Retry |
| 134 | SIGABRT | Retry |
| 137 | SIGKILL (OOM) | Retry with more memory |
| 139 | SIGSEGV (segfault) | Retry |
| 140 | SIGPIPE | Retry |
| 143 | SIGTERM (timeout) | Retry with more time |

## Contact

If you encounter unexpected failures or need help interpreting failure reports:
- Open an issue: https://github.com/tdoerks/COMPASS-pipeline/issues
- Include: `failed_samples_report.txt` and `execution_trace.txt`
