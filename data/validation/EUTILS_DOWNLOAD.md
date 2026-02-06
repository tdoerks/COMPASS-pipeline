# Assembly Download via E-utilities (Beocat-Compatible)

## Problem

Beocat compute nodes experience TLS handshake timeouts with NCBI Datasets API:

```
Error: POST https://api.ncbi.nlm.nih.gov/datasets/v2/genome/dataset_report
net/http: TLS handshake timeout
```

## Solution

Use `download_assemblies_eutils.py` which downloads assemblies via NCBI E-utilities (same API that works for SRA downloads).

---

## Quick Start

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Download all 171 validation assemblies
python3 data/validation/download_assemblies_eutils.py
```

**Expected Runtime**: 1-2 hours for 171 assemblies (0.5s rate limit per assembly)

---

## How It Works

### Method 1: Direct efetch (Primary)

```python
# Query nuccore database by assembly accession
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?
  db=nuccore&
  id=GCF_000285655.1&
  rettype=fasta&
  retmode=text
```

### Method 2: Search then fetch (Fallback)

If Method 1 fails (HTTP 400):

1. Search assembly database for accession
2. Get assembly UID
3. Fetch using UID

### Features

- **Retries**: 3 attempts with exponential backoff (2, 4, 8 seconds)
- **Rate limiting**: 0.5s between downloads (NCBI policy)
- **Resume support**: Skips already downloaded files
- **Progress tracking**: Real-time status for each sample
- **Error handling**: Detailed error messages for failures

---

## Output

Assemblies saved to: `data/validation/assemblies/`

```
assemblies/
├── EC958.fasta
├── JJ1886.fasta
├── K12_MG1655.fasta
├── FDA_ARGOS_001.fasta
├── DIVERSE_001.fasta
└── ... (171 total)
```

---

## After Download Completes

### Step 1: Update Run Script

Edit `data/validation/run_compass_validation.sh`:

```bash
# Change this line:
--input_mode assembly \

# To:
--input_mode fasta \
```

The pipeline will read FASTA files directly from `assemblies/` instead of downloading them.

### Step 2: Submit Validation Run

```bash
sbatch data/validation/run_compass_validation.sh
```

---

## Monitoring Progress

The script shows real-time progress:

```
[1/171] EC958 (GCF_000285655.1): Downloading... ✓ (4,918,596 bytes)
[2/171] JJ1886 (GCF_000393015.1): Downloading... ✓ (5,277,381 bytes)
[3/171] K12_MG1655 (GCF_000005845.2): Downloading... ✓ (4,641,652 bytes)
...
[171/171] ST167_006 (GCF_022699465.1): Downloading... ✓ (5,102,483 bytes)

======================================================================
DOWNLOAD COMPLETE
======================================================================
Total samples: 171
✓ Successfully downloaded: 171
⊙ Already existed (skipped): 0
✗ Failed: 0

Total time: 85.5 minutes
Average: 30.0 seconds per sample

Assemblies saved to: data/validation/assemblies

✅ All assemblies downloaded successfully!
```

---

## Troubleshooting

### Problem: HTTP 400 Bad Request

**Cause**: Accession not in nuccore database

**Solution**: Script automatically tries alternative method (search assembly db first)

### Problem: Network timeout

**Cause**: Temporary NCBI service issue

**Solution**: Script retries 3 times with backoff. If still fails, re-run script (resumes from where it left off)

### Problem: Invalid FASTA content

**Cause**: Empty or incomplete response from NCBI

**Solution**: Script validates FASTA starts with `>` and is >1000 bytes. Retries if invalid.

### Problem: Script interrupted

**Solution**: Just re-run - it skips already downloaded files

```bash
python3 data/validation/download_assemblies_eutils.py
```

---

## Comparison: Methods

| Method | Speed | Reliability on Beocat | Resume Support |
|--------|-------|----------------------|----------------|
| ncbi-datasets CLI | Fast (parallel) | ❌ TLS timeout | No |
| download_genomes.sh | Fast (parallel) | ❌ TLS timeout | No |
| download_assemblies_eutils.py | Slow (serial) | ✅ Works | Yes |

---

## Why This Works

1. **E-utilities vs Datasets API**:
   - E-utilities: Simple HTTP GET requests
   - Datasets API: Complex HTTPS with strict TLS requirements
   - Beocat allows E-utilities but blocks Datasets API

2. **Same approach as SRA downloads**:
   - SRA downloads use `fasterq-dump` which queries NCBI similarly
   - E-utilities proven to work on Beocat

3. **Graceful degradation**:
   - Tries simple method first
   - Falls back to complex method if needed
   - Retries with backoff on failures

---

## Alternative: Download Locally

If E-utilities also fails on Beocat:

```bash
# On your local machine:
git clone https://github.com/tdoerks/COMPASS-pipeline.git
cd COMPASS-pipeline
bash data/validation/download_genomes.sh

# Transfer to Beocat:
scp -r data/validation/assemblies tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/
```

---

## Contact

Tyler Doerksen - tdoerks@vet.k-state.edu

---

**Version**: 1.0
**Date**: February 2026
**Status**: Ready to use on Beocat
