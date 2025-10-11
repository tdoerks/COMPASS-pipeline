# COMPASS Pipeline - Troubleshooting Guide

## Quick Debugging Commands

### 1. Check Pipeline Syntax
```bash
nextflow run main.nf -help
bin/validate_pipeline.sh  # If validation script is available
```

### 2. Dry Run (Preview Execution)
```bash
nextflow run main.nf --input test.csv --outdir results -preview
```

### 3. Resume Failed Runs
```bash
# Always use -resume to restart from last successful step
nextflow run main.nf --input test.csv --outdir results -resume
```

### 4. Check What Ran
```bash
# View execution log
cat .nextflow.log | tail -100

# Check work directory
ls -lh work/

# Find failed processes
grep ERROR .nextflow.log
```

---

## Common Issues & Solutions

### Issue 1: "Container not found" or "Singularity/Apptainer error"

**Symptoms:**
```
ERROR ~ Error executing process > 'MLST'
Caused by: Container not found...
```

**Solutions:**
1. Check container runtime is installed:
   ```bash
   apptainer --version  # or singularity --version
   ```

2. Check container cache:
   ```bash
   ls -lh ~/.apptainer/cache/  # or ~/.singularity/cache/
   ```

3. Pre-pull containers manually:
   ```bash
   apptainer pull docker://quay.io/biocontainers/mlst:2.23.0--hdfd78af_1
   ```

4. Add to nextflow.config:
   ```groovy
   singularity {
       enabled = true
       autoMounts = true
       cacheDir = '/path/to/cache'
   }
   ```

---

### Issue 2: "Process exceeds available memory"

**Symptoms:**
```
ERROR ~ Process BUSCO terminated for an unknown reason -- Likely insufficient memory
```

**Solutions:**
1. Check available resources:
   ```bash
   free -h  # Check RAM
   df -h    # Check disk space
   ```

2. Reduce parallel processes in nextflow.config:
   ```groovy
   executor {
       queueSize = 5  # Reduce from default
   }
   ```

3. Increase memory for specific process in conf/base.config:
   ```groovy
   withName: BUSCO {
       memory = { check_max( 16.GB * task.attempt, 'memory' ) }
   }
   ```

---

### Issue 3: Database Not Found

**Symptoms:**
```
ERROR ~ Process CHECKV failed
CheckV database not found at: /path/to/checkv-db
```

**Solutions:**
1. Check database paths in nextflow.config:
   ```bash
   grep -A5 "parameters" nextflow.config
   ```

2. Update paths:
   ```groovy
   params {
       checkv_db = "/correct/path/to/checkv-db-v1.5"
       prophage_db = "/correct/path/to/prophage_db.dmnd"
       busco_download_path = "/correct/path/to/busco_downloads"
   }
   ```

3. Download databases if missing:
   ```bash
   # CheckV
   checkv download_database /path/to/checkv-db

   # BUSCO lineages
   busco --download bacteria_odb10
   ```

---

### Issue 4: "No such file or directory" for Input Files

**Symptoms:**
```
ERROR ~ Missing input file: /path/to/assembly.fasta
```

**Solutions:**
1. Check samplesheet format:
   ```csv
   sample,organism,fasta
   Sample1,Salmonella,/absolute/path/to/file.fasta
   ```

2. Use **absolute paths**, not relative:
   ```bash
   # BAD:  assemblies/sample1.fasta
   # GOOD: /full/path/to/assemblies/sample1.fasta
   ```

3. Verify files exist:
   ```bash
   while IFS=, read -r sample organism fasta; do
       [ -f "$fasta" ] && echo "✓ $fasta" || echo "✗ MISSING: $fasta"
   done < samplesheet.csv
   ```

---

### Issue 5: SISTR Not Running (Salmonella Samples)

**Expected Behavior:** SISTR only runs when organism name contains "Salmonella"

**Check:**
```bash
# Verify organism names in samplesheet
cat samplesheet.csv | grep -i salmonella

# Should match case-insensitive: Salmonella, salmonella, SALMONELLA, Salmonella enterica, etc.
```

**If not running when expected:**
- Check organism column spelling
- Look for typos: "Sallmonella", "Salmonela", etc.
- Make sure organism column exists in samplesheet

---

### Issue 6: ABRicate Missing Database

**Symptoms:**
```
ERROR ~ ABRicate database 'ncbi' not found
```

**Solutions:**
1. Check available databases:
   ```bash
   abricate --list
   ```

2. Update database:
   ```bash
   abricate --setupdb
   ```

3. Or modify which databases to use in nextflow.config:
   ```groovy
   params {
       abricate_dbs = "ncbi,card"  # Remove problematic databases
   }
   ```

---

### Issue 7: Pipeline Hangs/Stalls

**Symptoms:**
- No progress for extended time
- Process appears stuck

**Debug Steps:**
1. Find running process:
   ```bash
   tail -f .nextflow.log
   ```

2. Check work directory:
   ```bash
   # Find most recent work directory
   find work/ -type f -name ".command.log" -mmin -60 | head -1
   # Check its log
   cat work/xx/xxxxxxxxxxxx/.command.log
   ```

3. Check system resources:
   ```bash
   top    # Check CPU/memory
   squeue # If using SLURM
   ```

4. Kill and resume:
   ```bash
   Ctrl+C
   nextflow run main.nf ... -resume
   ```

---

### Issue 8: "Too Many Open Files"

**Symptoms:**
```
ERROR ~ java.io.IOException: Too many open files
```

**Solutions:**
1. Increase file descriptor limit:
   ```bash
   ulimit -n 4096
   ```

2. Add to ~/.bashrc:
   ```bash
   echo "ulimit -n 4096" >> ~/.bashrc
   ```

3. Reduce parallel processes in config:
   ```groovy
   executor.queueSize = 10
   ```

---

## Debugging Specific Modules

### Check Individual Process Output

Find the work directory for a specific process:
```bash
# Example: Find MLST work directory for Sample001
find work/ -name "Sample001_mlst.tsv"
# Navigate to parent directory
cd work/xx/xxxxxxxxxxxx/

# Check files
ls -lah
cat .command.sh      # The script that ran
cat .command.log     # stdout
cat .command.err     # stderr
cat .exitcode        # exit status (0 = success)
```

### Manually Test a Process

```bash
# Copy command from .command.sh and run manually
cat work/xx/xxxxx/.command.sh | grep -v "^nxf-"
# Then run in container
apptainer exec docker://quay.io/biocontainers/mlst:2.23.0--hdfd78af_1 \
    mlst assembly.fasta
```

---

## Performance Optimization

### Speed Up Testing
1. Use `-resume` flag always
2. Start with `--max_samples 3` for NARMS mode
3. Use small test assemblies (< 5 MB)
4. Increase parallel execution:
   ```groovy
   executor.queueSize = 20
   ```

### Production Optimization
1. Profile resource usage:
   ```bash
   nextflow run main.nf -with-timeline timeline.html -with-report report.html
   ```

2. Adjust CPU/memory in conf/base.config based on profiling

3. Use appropriate profiles (beocat, ceres, standard)

---

## Getting Help

### Pipeline Logs to Share
When reporting issues, include:
```bash
# Essential files
.nextflow.log              # Execution log
.nextflow/history          # Run history
timeline.html              # If generated with -with-timeline
work/xx/xxxx/.command.err  # Specific process error

# System info
nextflow -version
apptainer --version  # or singularity --version
cat /etc/os-release
free -h
df -h
```

### GitHub Issues
Report at: https://github.com/tdoerks/COMPASS-pipeline/issues

Include:
- Nextflow version
- Command used
- Error message
- Relevant log excerpts
- Sample size (number of samples)

---

## Quick Reference

### Essential Commands
```bash
# Validate pipeline
nextflow run main.nf -help

# Run with resume
nextflow run main.nf --input data.csv --outdir results -resume

# Clean up work directory (frees space)
nextflow clean -f

# Check run history
nextflow log

# Get specific run info
nextflow log <run_name> -f workdir,hash,name,status
```

### Key Files
- **nextflow.config** - Main configuration
- **conf/base.config** - Resource settings
- **conf/beocat.config** - Beocat cluster config
- **conf/ceres.config** - Ceres cluster config
- **.nextflow.log** - Execution log
- **work/** - Intermediate files (can be deleted after success)

---

Last updated: 2025-10-11
