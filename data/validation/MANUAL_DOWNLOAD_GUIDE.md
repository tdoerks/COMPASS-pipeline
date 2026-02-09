# Manual Genome Download Guide

Complete guide for manually downloading reference genomes from NCBI and uploading to Beocat HPC.

---

## Table of Contents

1. [When to Use Manual Download](#when-to-use-manual-download)
2. [Prerequisites](#prerequisites)
3. [Method 1: NCBI Website (Most Reliable)](#method-1-ncbi-website-most-reliable)
4. [Method 2: NCBI Datasets CLI (If Available)](#method-2-ncbi-datasets-cli-if-available)
5. [Method 3: Direct FTP Download](#method-3-direct-ftp-download)
6. [Uploading to Beocat](#uploading-to-beocat)
7. [Batch Processing Multiple Genomes](#batch-processing-multiple-genomes)
8. [Troubleshooting](#troubleshooting)

---

## When to Use Manual Download

Use manual download when:

- ✅ Automated download scripts fail (E-utilities timeout, network restrictions)
- ✅ You need a small number of specific reference genomes
- ✅ NCBI Datasets CLI is not available on HPC
- ✅ You want to verify genome quality before upload
- ✅ You're downloading from non-NCBI sources (ENA, local databases)

**Don't use manual download if:**
- You have >20 genomes to download → Use E-utilities script or NCBI Datasets CLI
- The genome is available via SRA → Use COMPASS `--input_mode sra_list`

---

## Prerequisites

### On Your Local Computer

**Windows:**
- PowerShell or Command Prompt
- Web browser (Chrome, Firefox, Edge)
- SCP client (built into Windows 10+ PowerShell, or use WinSCP GUI)

**Mac/Linux:**
- Terminal
- Web browser
- SCP (pre-installed)

### On Beocat

- SSH access: `ssh USERNAME@beocat.ksu.edu`
- Directory for assemblies (usually `/fastscratch/$USER/COMPASS-pipeline/data/validation/assemblies/`)

---

## Method 1: NCBI Website (Most Reliable)

### Step 1: Find the Genome on NCBI

**Option A: Search by Strain Name**
1. Go to [NCBI Genome](https://www.ncbi.nlm.nih.gov/genome/)
2. Search for strain (e.g., "Escherichia coli EC958")
3. Click on the genome result
4. Find the **RefSeq** or **GenBank** accession (e.g., `GCF_000285655.3`)

**Option B: Direct Accession Lookup**
1. If you have the accession: `GCF_000285655.3`
2. Go to: `https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000285655.3/`

### Step 2: Download via NCBI Datasets

On the genome page:

1. Click **"Download"** button (top right)
2. Select **"Genome sequences (FASTA)"**
3. Click **"Download"**
4. File will be saved as `ncbi_dataset.zip` in your Downloads folder

**Alternative**: Use the direct download link:
```
https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/GCF_000285655.3/download
```

### Step 3: Extract the FASTA File

**Windows (PowerShell):**
```powershell
cd ~/Downloads
Expand-Archive -Path ncbi_dataset.zip -DestinationPath ncbi_dataset
dir ncbi_dataset\ncbi_dataset\data\GCF_*\*.fna
```

**Mac/Linux:**
```bash
cd ~/Downloads
unzip ncbi_dataset.zip
ls ncbi_dataset/data/GCF_*/*.fna
```

**Expected file**: `GCF_000285655.3_ASM28565v2_genomic.fna`

### Step 4: Rename to Sample Name

```powershell
# Windows
Copy-Item ncbi_dataset\ncbi_dataset\data\GCF_000285655.3\GCF_000285655.3_ASM28565v2_genomic.fna -Destination EC958.fasta
```

```bash
# Mac/Linux
cp ncbi_dataset/data/GCF_000285655.3/GCF_000285655.3_ASM28565v2_genomic.fna EC958.fasta
```

### Step 5: Verify File

```bash
# Check file size (should be >1 MB for bacterial genome)
ls -lh EC958.fasta

# Check format (should start with >)
head -1 EC958.fasta
# Expected: >NZ_HG941718.1 Escherichia coli EC958 chromosome, complete genome
```

**Proceed to**: [Uploading to Beocat](#uploading-to-beocat)

---

## Method 2: NCBI Datasets CLI (If Available)

### Installation

**Mac/Linux:**
```bash
curl -o datasets 'https://ftp.ncbi.nlm.nih.gov/pub/datasets/command-line/v2/linux-amd64/datasets'
chmod +x datasets
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://ftp.ncbi.nlm.nih.gov/pub/datasets/command-line/v2/win-amd64/datasets.exe" -OutFile "datasets.exe"
```

### Download Genome

```bash
# Download single genome
./datasets download genome accession GCF_000285655.3

# Unzip
unzip ncbi_dataset.zip

# Extract and rename
cp ncbi_dataset/data/GCF_000285655.3/*.fna EC958.fasta
```

### Batch Download Multiple Genomes

```bash
# Create file with accessions (one per line)
cat > accessions.txt <<'EOF'
GCF_000285655.3
GCF_000005845.2
GCF_000008865.2
EOF

# Download all
./datasets download genome accession --inputfile accessions.txt

# Extract all
unzip ncbi_dataset.zip
for dir in ncbi_dataset/data/GCF_*; do
    acc=$(basename "$dir")
    # You'll need a mapping file to convert accession → sample name
    echo "Extracted: $acc"
done
```

**Note**: On Beocat, NCBI Datasets CLI often fails with TLS timeout errors. Use Method 1 or 3 instead.

---

## Method 3: Direct FTP Download

### Step 1: Find FTP Path

From NCBI genome page:
1. Look for **"FTP directory for RefSeq assembly"**
2. Example: `https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/285/655/GCF_000285655.3_ASM28565v2/`

### Step 2: Download via wget or curl

**Using wget:**
```bash
wget https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/285/655/GCF_000285655.3_ASM28565v2/GCF_000285655.3_ASM28565v2_genomic.fna.gz

# Decompress
gunzip GCF_000285655.3_ASM28565v2_genomic.fna.gz

# Rename
mv GCF_000285655.3_ASM28565v2_genomic.fna EC958.fasta
```

**Using curl:**
```bash
curl -o EC958.fna.gz https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/285/655/GCF_000285655.3_ASM28565v2/GCF_000285655.3_ASM28565v2_genomic.fna.gz

gunzip EC958.fna.gz
mv EC958.fna EC958.fasta
```

**Note**: FTP downloads on Beocat often fail due to network restrictions. Prefer downloading on local machine then uploading.

---

## Uploading to Beocat

### Method A: SCP from Command Line

**Windows (PowerShell):**
```powershell
# Upload single file
scp EC958.fasta tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/assemblies/

# Upload multiple files
scp *.fasta tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/assemblies/
```

**Mac/Linux:**
```bash
# Upload single file
scp EC958.fasta USERNAME@beocat.ksu.edu:/fastscratch/$USER/COMPASS-pipeline/data/validation/assemblies/

# Upload multiple files
scp *.fasta USERNAME@beocat.ksu.edu:/fastscratch/$USER/COMPASS-pipeline/data/validation/assemblies/
```

### Method B: WinSCP (Windows GUI)

1. Download [WinSCP](https://winscp.net/)
2. **Host**: `beocat.ksu.edu`
3. **Username**: Your K-State eID
4. **Password**: Your K-State password
5. Navigate to `/fastscratch/USERNAME/COMPASS-pipeline/data/validation/assemblies/`
6. Drag and drop `.fasta` files

### Method C: rsync (Mac/Linux)

```bash
# Upload with progress
rsync -avP *.fasta USERNAME@beocat.ksu.edu:/fastscratch/$USER/COMPASS-pipeline/data/validation/assemblies/

# Resume interrupted transfer
rsync -avP --partial *.fasta USERNAME@beocat.ksu.edu:/fastscratch/$USER/COMPASS-pipeline/data/validation/assemblies/
```

### Verify Upload

```bash
# SSH to Beocat
ssh USERNAME@beocat.ksu.edu

# Check files
ls -lh /fastscratch/$USER/COMPASS-pipeline/data/validation/assemblies/*.fasta

# Verify file integrity (check file size, should be >1 MB)
du -h /fastscratch/$USER/COMPASS-pipeline/data/validation/assemblies/EC958.fasta
```

---

## Batch Processing Multiple Genomes

### Example: Download 10 Reference Genomes

**Step 1: Create Mapping File**

`genome_mapping.csv`:
```csv
sample,accession
K12_MG1655,GCF_000005845.2
EC958,GCF_000285655.3
JJ1886,GCF_000492015.1
CFT073,GCF_000007445.1
ATCC_25922,GCF_000648355.1
```

**Step 2: Download Script**

`download_genomes.sh`:
```bash
#!/bin/bash
# Download multiple genomes from NCBI

MAPPING_FILE="genome_mapping.csv"
OUTPUT_DIR="assemblies"

mkdir -p "$OUTPUT_DIR"

while IFS=, read -r sample accession; do
    if [ "$sample" != "sample" ]; then
        echo "Downloading: $sample ($accession)"

        # Extract accession path components
        acc_prefix=$(echo "$accession" | cut -d_ -f1)
        acc_suffix=$(echo "$accession" | cut -d_ -f2 | sed 's/\(...\)\(...\)\(...\).*/\1\/\2\/\3/')

        # Construct FTP URL
        ftp_url="https://ftp.ncbi.nlm.nih.gov/genomes/all/${acc_prefix}/${acc_suffix}/${accession}_*/${accession}_*_genomic.fna.gz"

        # Download
        wget -q -O "${OUTPUT_DIR}/${sample}.fna.gz" "$ftp_url"

        # Decompress
        gunzip "${OUTPUT_DIR}/${sample}.fna.gz"

        # Rename
        mv "${OUTPUT_DIR}/${sample}.fna" "${OUTPUT_DIR}/${sample}.fasta"

        echo "✓ $sample complete"
    fi
done < "$MAPPING_FILE"

echo ""
echo "Download complete. Files in: $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/*.fasta
```

**Usage:**
```bash
chmod +x download_genomes.sh
./download_genomes.sh
```

**Step 3: Upload All to Beocat**

```bash
# Upload entire directory
scp assemblies/*.fasta USERNAME@beocat.ksu.edu:/fastscratch/$USER/COMPASS-pipeline/data/validation/assemblies/
```

---

## Troubleshooting

### Issue 1: "Host key verification failed"

**Error**: SSH/SCP fails with host key error

**Solution**:
```bash
# Accept host key
ssh USERNAME@beocat.ksu.edu
# Type "yes" when prompted
```

### Issue 2: "Permission denied (publickey)"

**Error**: SCP authentication fails

**Solutions**:
1. Make sure you're using correct K-State eID
2. Reset K-State password if needed
3. Use password authentication: `scp -o PreferredAuthentications=password file.fasta ...`

### Issue 3: Wrong hostname

**Error**: `ssh: Could not resolve hostname beocat.cis.ksu.edu`

**Solution**: Use correct hostname: `beocat.ksu.edu` (not `beocat.cis.ksu.edu`)

### Issue 4: File not found after upload

**Error**: File exists on Beocat but COMPASS can't find it

**Diagnosis**:
```bash
# Check file exists
ls -lh /fastscratch/$USER/COMPASS-pipeline/data/validation/assemblies/EC958.fasta

# Check permissions
ls -l /fastscratch/$USER/COMPASS-pipeline/data/validation/assemblies/EC958.fasta
# Should be: -rw-r--r--
```

**Solution**: Verify absolute path in samplesheet:
```csv
sample,organism,fasta
EC958,Escherichia,/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/assemblies/EC958.fasta
```

### Issue 5: Corrupted download

**Symptom**: File is too small (<1 MB) or truncated

**Diagnosis**:
```bash
# Check file size
ls -lh EC958.fasta

# Check if valid FASTA
head -1 EC958.fasta
# Should start with >

# Count contigs
grep -c "^>" EC958.fasta
# Should be >0
```

**Solution**: Re-download from NCBI

### Issue 6: .fna vs .fasta extension

**Problem**: Downloaded file is `.fna` but pipeline expects `.fasta`

**Solution**: Just rename
```bash
mv EC958.fna EC958.fasta
```

Both are identical formats (FASTA), just different naming conventions.

---

## Quality Control Checklist

Before using downloaded assemblies in COMPASS:

- ✅ **File size**: Should be >1 MB for bacterial genome (typically 3-6 MB)
- ✅ **Format**: File starts with `>` (FASTA header)
- ✅ **Contigs**: Has at least one contig (`grep -c "^>" file.fasta`)
- ✅ **Correct organism**: FASTA header matches expected species
- ✅ **Completeness**: Compare size to expected genome size (E. coli ~5 Mbp)
- ✅ **File naming**: Matches sample name in samplesheet
- ✅ **Absolute path**: Samplesheet uses full path to file

**Quick QC Script**:
```bash
#!/bin/bash
# qc_fasta.sh - Validate FASTA file

FASTA=$1

echo "File: $FASTA"
echo "Size: $(du -h "$FASTA" | cut -f1)"
echo "Contigs: $(grep -c "^>" "$FASTA")"
echo "First header:"
head -1 "$FASTA"
echo ""
```

**Usage**: `./qc_fasta.sh EC958.fasta`

---

## Example Workflow: Adding EC958 to Validation

Real example from February 2026 validation run:

### Problem
- Validation run failed because EC958 assembly was missing from Beocat
- Needed to manually download and add to 162-sample dataset

### Solution

**Step 1: Download from NCBI (on Windows laptop)**
1. Went to: https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000285655.3/
2. Clicked "Download" → "Genome sequences (FASTA)"
3. Downloaded `ncbi_dataset.zip` to Downloads folder
4. Extracted: `ncbi_dataset\data\GCF_000285655.3\GCF_000285655.3_ASM28565v2_genomic.fna`
5. Renamed to `EC958.fasta`

**Step 2: Upload to Beocat (PowerShell)**
```powershell
cd ~/Downloads
scp EC958.fasta tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/assemblies/
```

**Step 3: Update Samplesheet (on Beocat)**
```bash
# Add EC958 to samplesheet
echo "EC958,Escherichia,/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/assemblies/EC958.fasta" >> data/validation/validation_samplesheet_163.csv

# Verify
grep EC958 data/validation/validation_samplesheet_163.csv
```

**Step 4: Restart Validation Run**
```bash
rm -rf .nextflow/
rm -rf data/validation/results/
sbatch data/validation/run_compass_validation.sh
```

**Result**: ✅ Validation run launched successfully with 163 samples

---

## See Also

- [FASTA_INPUT_MODE.md](../docs/FASTA_INPUT_MODE.md) - Complete guide for FASTA input mode
- [VALIDATION_QUICKSTART.md](../docs/VALIDATION_QUICKSTART.md) - Validation workflow
- [SESSION_2026-02-09_validation_run.md](../docs/presentations/SESSION_2026-02-09_validation_run.md) - Troubleshooting session notes

---

## Contact

For questions about manual downloads:
- Tyler Doerksen - tdoerks@vet.k-state.edu
- GitHub Issues: https://github.com/tdoerks/COMPASS-pipeline/issues

---

**Last Updated**: February 2026
**Pipeline Version**: COMPASS v1.3-dev
