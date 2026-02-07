# Session Notes - February 5, 2026
## E. coli Monthly 100 Sample Recovery & Validation Attempts

---

## Summary

Worked on recovering the ecoli_monthly_100 pipeline run that was interrupted, and attempted to set up validation run with reference genomes. Created tools for filling gaps in monthly sampling datasets.

---

## Key Accomplishments

### 1. Sample List Recovery (6,600 samples recovered)

**Problem**: Lost the original `sra_accessions_ecoli_monthly_100_2020-2026.txt` file when cleaning up corrupted git directories.

**Solution**: Extracted sample IDs from partial output directories.

```bash
# Recovered samples from fastq directories across multiple runs
ls /fastscratch/tylerdoe/ecoli_monthly_100_*/fastq/ | grep -oP 'SRR\d+' | sort -u > sra_accessions_ecoli_monthly_100_2020-2026.txt

# Result: 6,600 samples recovered (92% of expected 7,142)
```

**Files created**:
- `/fastscratch/tylerdoe/COMPASS-pipeline/sra_accessions_ecoli_monthly_100_2020-2026.txt` (6,600 lines)

---

### 2. Gap Analysis Tools Created

Created Python scripts to analyze and fill gaps in monthly sampling datasets.

#### Script 1: `analyze_sample_distribution.py`

**Purpose**: Bins recovered samples by month/year, identifies incomplete months

**Features**:
- Queries NCBI E-utilities for each SRR accession's release date
- Bins samples by year-month (2020-01 through 2026-01)
- Identifies months with <100 samples
- Generates detailed gap report

**Usage**:
```bash
python3 analyze_sample_distribution.py [input_file] [output_report]
# Default: sra_accessions_ecoli_monthly_100_2020-2026.txt → sample_distribution_report.txt
```

**Expected Runtime**: ~20-30 minutes for 6,600 samples (0.35s per NCBI query with rate limiting)

**Output**:
```
Monthly Distribution:
✓ 2020-01: 100 samples
✗ 2020-03:  87 samples (missing 13)
✓ 2020-04: 100 samples
...

Summary:
  Complete months: 58/73
  Incomplete months: 15
  Total missing: ~542 samples
```

#### Script 2: `fill_missing_samples.py`

**Purpose**: Fetches exactly the missing samples for each incomplete month

**Features**:
- Parses gap report from analyze script
- For each incomplete month:
  - Queries NCBI for E. coli samples from that specific month
  - Filters out samples already in list (no duplicates)
  - Randomly samples exactly the number needed
- Appends new samples to existing file

**Usage**:
```bash
python3 fill_missing_samples.py [input_file] [report_file]
# Appends to input file
```

**Expected Runtime**: ~5-10 minutes (depends on number of gaps)

**Output**: Complete ~7,142 sample list with balanced monthly distribution

#### Documentation: `FILL_MISSING_SAMPLES_GUIDE.md`

Complete guide with:
- When to use these tools vs built-in filtering
- Step-by-step instructions
- Troubleshooting tips
- Expected vs suspicious results

**Git Commits**:
```
8445cac - Add tools to analyze and fill gaps in monthly sampling
```

---

### 3. Validation Run Setup Attempts

#### Initial Setup (Success)

**Validation Dataset**: 171 E. coli reference genomes
- 14 core references (K-12 MG1655, EC958, JJ1886, ETEC strains, controls)
- 50 FDA-ARGOS (curated AMR profiles)
- 100 diverse genomes
- 7 sequence type representatives

**Files**:
- `data/validation/validation_samplesheet.csv` (171 genomes)
- `data/validation/run_compass_validation.sh` (SLURM script)
- `VALIDATION_QUICKSTART.md` (user guide)

#### Problem 1: Partition Permission Error

**Error**:
```
uid 3600 not in group permitted to use this partition (ksu-gen-highmem.q)
```

**Fix**: Removed `--partition=ksu-gen-highmem.q` line from sbatch script to use default partition

**Git Commit**:
```
c96d482 - Fix validation script partition - use default partition
```

#### Problem 2: Assembly Download Failures

**Attempt 1: wget + FTP path construction** (FAILED)

Error: NCBI FTP directory naming doesn't match accession
```
Expected: /genomes/all/GCF/000/285/655/GCF_000285655.1/
Actual:   /genomes/all/GCF/000/285/655/GCF_000285655.3_EC958.v1/
```

Substring extraction logic also had errors for constructing paths.

**Attempt 2: entrez-direct (esearch + efetch)** (FAILED)

Errors:
1. Missing Perl module: `Can't locate Time/HiRes.pm in @INC`
2. HTTP 400 Bad Request from NCBI
3. Empty results

```
ERROR:  wget command failed with: 8
HTTP/1.1 400 Bad Request
EMPTY RESULT
ERROR: Failed to download GCF_000010245.1
```

**Root Cause**: The `quay.io/biocontainers/entrez-direct:16.2--he881be0_1` container is missing Perl dependencies and NCBI rejects the efetch requests for assembly database with rettype=fasta.

**Git Commit** (attempted fix, didn't work):
```
aad0324 - Fix assembly download - revert to entrez-direct
```

**Status**: Validation run blocked on assembly download issues

**Alternative Solutions Not Yet Tried**:
1. Manual download using `download_genomes.sh` script + ncbi-datasets CLI
2. Different entrez-direct container
3. Use nucleotide database instead of assembly database
4. Skip validation for now

---

## Issues Encountered

### Issue 1: Lost Original Sample List

**Problem**: Original `sra_accessions_ecoli_monthly_100_2020-2026.txt` file lost during git directory cleanup

**Impact**: Can't resume pipeline with exact same samples

**Workaround**: Extracted 6,600 samples from partial output directories (92% recovery)

**Remaining Issue**: 542 samples missing, distribution may not be perfectly balanced (100/month)

---

### Issue 2: Pipeline Restart Downloaded New Samples

**Problem**: Job 6293627 restarted but appeared to download new samples instead of using cached work

**Evidence**:
```
[b7/e9978a] DOWNLOAD_SRA (SRR12902475) | 834 of 6600, failed: 14
```

No "cached" indicators in grep of slurm output

**Possible Causes**:
1. Recovered sample list doesn't match originally processed samples
2. Work directory hash changed
3. Nextflow resume not recognizing cached downloads

**Status**: Job was canceled (scancel 6293627) before investigating further

**Action Needed**: Determine if recovered sample list matches cached work samples

---

### Issue 3: Assembly Download Module Broken

**Problem**: Neither wget FTP nor entrez-direct approaches work for downloading assemblies

**Symptoms**:
- wget: Can't construct correct FTP paths
- entrez-direct: Missing Perl modules, HTTP 400 errors

**Impact**: Cannot run validation pipeline with auto-download feature

**Next Steps**:
- Try manual download with ncbi-datasets CLI
- Or use different download approach (nucleotide database)
- Or pre-download assemblies locally

---

## Git Activity

### Commits Pushed to v1.3-dev

```
8445cac - Add tools to analyze and fill gaps in monthly sampling
  - analyze_sample_distribution.py
  - fill_missing_samples.py
  - FILL_MISSING_SAMPLES_GUIDE.md

becf407 - Add validation quickstart guide
  - VALIDATION_QUICKSTART.md

c96d482 - Fix validation script partition - use default partition
  - data/validation/run_compass_validation.sh

aad0324 - Fix assembly download - revert to entrez-direct (didn't work)
  - modules/download_assembly.nf
```

---

## Jobs Run

### Job 6293627 - E. coli Monthly 100 (Canceled)

**Status**: Canceled after ~1.5 hours
**Reason**: Appeared to be downloading new samples instead of using cache

**Progress at cancellation**:
- Downloaded: 834 of 6,600
- Failed: 14 downloads
- No cached tasks detected

**Work directory preserved**: `/fastscratch/tylerdoe/COMPASS-pipeline/work_ecoli_monthly_100/`

---

### Job 6294749 - Validation Run Attempt 1 (Failed - Partition Error)

**Status**: Failed immediately
**Error**: Permission denied for ksu-gen-highmem.q partition
**Fix**: Removed partition specification
**Duration**: <1 minute

---

### Job 6294759 - Validation Run Attempt 2 (Failed - Download Errors)

**Status**: Failed - all assembly downloads failed
**Error**: entrez-direct missing Perl modules + HTTP 400
**Failed samples**: K12_W3110, ETEC_E24377A, CFT073, ETEC_TW11681, ETEC_TW10722, FDA_ARGOS_002, etc.
**Duration**: ~3 minutes before all downloads failed
**Action**: Canceled (scancel 6294759)

---

## Current State

### E. coli Monthly 100 Run

**Sample List**: 6,600 samples recovered (sra_accessions_ecoli_monthly_100_2020-2026.txt)
**Missing**: ~542 samples (can fill with fill_missing_samples.py)
**Work Directory**: Preserved at `/fastscratch/tylerdoe/COMPASS-pipeline/work_ecoli_monthly_100/`
**Status**: Ready to restart, but need to verify cache usage

**Commands to restart**:
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
sbatch run_ecoli_monthly_100_2020-2026.sh
```

**Recommendation**:
1. First, run analyze_sample_distribution.py to see actual monthly distribution
2. Optionally fill gaps with fill_missing_samples.py
3. Then restart pipeline

---

### Validation Run

**Dataset**: 171 genomes ready (validation_samplesheet.csv)
**Status**: Blocked on assembly download module
**Work Directory**: `/fastscratch/tylerdoe/COMPASS-pipeline/work/` (clean, can delete)

**Next Steps**:
1. Try manual assembly download approach
2. Or fix entrez-direct container issues
3. Or use alternative download method

---

## Tools Created

### Python Scripts

1. **analyze_sample_distribution.py** (NEW)
   - Analyzes monthly distribution of SRA samples
   - Queries NCBI for release dates
   - Identifies gaps in sampling
   - ~300 lines

2. **fill_missing_samples.py** (NEW)
   - Fills gaps identified by analyze script
   - Fetches missing samples month-by-month
   - Avoids duplicates
   - ~250 lines

### Documentation

1. **FILL_MISSING_SAMPLES_GUIDE.md** (NEW)
   - Complete usage guide
   - Troubleshooting tips
   - Expected results
   - ~300 lines

2. **VALIDATION_QUICKSTART.md** (NEW)
   - Quick start for validation run
   - Dataset description
   - Validation checks
   - Troubleshooting
   - ~300 lines

---

## Recommendations for Next Session

### Immediate Priority: Fix Validation Download

**Option 1: Manual Download** (Most Reliable)
```bash
# Install ncbi-datasets if not available
conda install -c conda-forge ncbi-datasets-cli

# Run manual download script
cd /fastscratch/tylerdoe/COMPASS-pipeline
bash data/validation/download_genomes.sh

# Then run pipeline in fasta mode instead of assembly mode
# Edit run_compass_validation.sh: --input_mode assembly → --input_mode fasta
```

**Option 2: Fix entrez-direct**
- Try different entrez-direct container version
- Or use nucleotide database instead of assembly database
- Or add Perl Time::HiRes to container

**Option 3: Alternative Download Method**
- Use curl + NCBI Datasets API
- Use SRA toolkit (but it's for reads, not assemblies)

---

### Secondary Priority: Complete Monthly Run

**Before restarting**:
1. Run analyze_sample_distribution.py on recovered list
2. Review monthly distribution gaps
3. Decide: use 6,600 as-is or fill gaps to 7,142?
4. Verify: Do recovered samples match cached work?

**To check cache match**:
```bash
# Extract sample IDs from work directory metadata
find /fastscratch/tylerdoe/COMPASS-pipeline/work_ecoli_monthly_100 -name "SRR*" -type d | head -100

# Compare to recovered list
head -100 sra_accessions_ecoli_monthly_100_2020-2026.txt

# If they match: cache will work
# If they don't: cache won't help
```

---

## Known Issues to Address

1. **Assembly download module broken**
   - Need working download solution for validation
   - entrez-direct container has bugs
   - wget FTP approach has path construction errors

2. **Gap analysis script not run yet**
   - Created but not executed on recovered samples
   - Need to verify monthly distribution
   - May have biases from partial recovery

3. **Cache usage uncertain**
   - Not clear if recovered sample list matches cached work
   - Need to verify before restarting

4. **Validation approach unclear**
   - Multiple download methods all failed
   - Need to pick reliable approach and commit to it

---

## Contact

Tyler Doerksen - tdoerks@vet.k-state.edu
Kansas State University College of Veterinary Medicine

---

## Session End

**Date**: February 5, 2026
**Duration**: ~2 hours
**Branch**: v1.3-dev
**Status**:
- ✅ Sample recovery tools created and documented
- ✅ 6,600 samples recovered from partial outputs
- ❌ Validation run blocked on assembly downloads
- ⏸️ Monthly run paused, ready to restart

**Next Actions**:
1. User to decide: manual validation download or skip for now?
2. Analyze recovered samples with new tools
3. Restart monthly run with verified sample list
