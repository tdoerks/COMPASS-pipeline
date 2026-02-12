# Manual Validation Genome Download Guide

## Problem

Beocat HPC is blocking all NCBI download methods:
- ❌ NCBI Datasets API - TLS handshake timeout
- ❌ NCBI FTP - Connection stalls
- ❌ NCBI E-utilities (entrez-direct) - HTTP 400 Bad Request

## Solution

Download the 170 validation genomes on your local machine, then transfer to Beocat.

---

## Step 1: Download on Your Local Machine

### Windows (PowerShell)

```powershell
# Create download directory
New-Item -ItemType Directory -Path "$HOME\compass_validation_genomes" -Force
cd "$HOME\compass_validation_genomes"

# Download the validation samplesheet
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tdoerks/COMPASS-pipeline/v1.3-dev/data/validation/validation_samplesheet.csv" -OutFile "validation_samplesheet.csv"

# View first 10 lines to verify
Get-Content validation_samplesheet.csv | Select-Object -First 10
```

### Mac/Linux

```bash
# Create download directory
mkdir -p ~/compass_validation_genomes
cd ~/compass_validation_genomes

# Download the validation samplesheet
curl -O https://raw.githubusercontent.com/tdoerks/COMPASS-pipeline/v1.3-dev/data/validation/validation_samplesheet.csv

# View first 10 lines to verify
head validation_samplesheet.csv
```

---

## Step 2: Create Download Script

Create a file called `download_genomes.sh` (Mac/Linux) or `download_genomes.ps1` (Windows):

### Mac/Linux Script (`download_genomes.sh`)

```bash
#!/bin/bash
# Download validation genomes from NCBI FTP

set -e

echo "Downloading 170 validation genomes from NCBI..."
echo "This will take 1-3 hours depending on your connection"
echo ""

mkdir -p assemblies

total=0
success=0
failed=0

# Skip header, read each line
tail -n +2 validation_samplesheet.csv | while IFS=, read -r sample organism accession; do
    total=$((total + 1))

    echo "[$total/170] Downloading $sample ($accession)..."

    # Remove version for FTP path
    acc_base=$(echo $accession | sed 's/\.[0-9]*$//')

    # Construct FTP URL
    ftp_url="https://ftp.ncbi.nlm.nih.gov/genomes/all/${acc_base:0:3}/${acc_base:4:3}/${acc_base:7:3}/${acc_base:10:3}/${accession}/${accession}_genomic.fna.gz"

    # Download with retry
    if curl -L -s -f "$ftp_url" -o "assemblies/${sample}.fasta.gz"; then
        gunzip "assemblies/${sample}.fasta.gz"
        success=$((success + 1))
        echo "  ✓ Success"
    else
        failed=$((failed + 1))
        echo "  ✗ Failed"
    fi

    # Progress update every 10
    if [ $((total % 10)) -eq 0 ]; then
        echo ""
        echo "Progress: $total/170 ($success succeeded, $failed failed)"
        echo ""
    fi
done

echo ""
echo "=========================================="
echo "Download Complete!"
echo "=========================================="
echo "Total: $total"
echo "Success: $success"
echo "Failed: $failed"
echo ""
echo "Files saved to: assemblies/"
```

Make it executable:
```bash
chmod +x download_genomes.sh
./download_genomes.sh
```

### Windows Script (`download_genomes.ps1`)

```powershell
# Download validation genomes from NCBI FTP

Write-Host "Downloading 170 validation genomes from NCBI..."
Write-Host "This will take 1-3 hours depending on your connection"
Write-Host ""

New-Item -ItemType Directory -Path "assemblies" -Force | Out-Null

$csv = Import-Csv validation_samplesheet.csv
$total = $csv.Count
$success = 0
$failed = 0
$current = 0

foreach ($row in $csv) {
    $current++
    $sample = $row.sample
    $accession = $row.assembly_accession

    Write-Host "[$current/$total] Downloading $sample ($accession)..."

    # Remove version for FTP path
    $acc_base = $accession -replace '\.\d+$', ''

    # Construct FTP URL
    $prefix1 = $acc_base.Substring(0, 3)
    $prefix2 = $acc_base.Substring(4, 3)
    $prefix3 = $acc_base.Substring(7, 3)
    $prefix4 = $acc_base.Substring(10, 3)
    $ftp_url = "https://ftp.ncbi.nlm.nih.gov/genomes/all/$prefix1/$prefix2/$prefix3/$prefix4/$accession/${accession}_genomic.fna.gz"

    try {
        # Download
        Invoke-WebRequest -Uri $ftp_url -OutFile "assemblies\${sample}.fasta.gz" -ErrorAction Stop

        # Decompress (requires 7-Zip or similar)
        & "C:\Program Files\7-Zip\7z.exe" e "assemblies\${sample}.fasta.gz" -o"assemblies" -y | Out-Null
        Remove-Item "assemblies\${sample}.fasta.gz"

        $success++
        Write-Host "  ✓ Success" -ForegroundColor Green
    }
    catch {
        $failed++
        Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }

    # Progress update every 10
    if ($current % 10 -eq 0) {
        Write-Host ""
        Write-Host "Progress: $current/$total ($success succeeded, $failed failed)"
        Write-Host ""
    }
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Download Complete!"
Write-Host "=========================================="
Write-Host "Total: $total"
Write-Host "Success: $success"
Write-Host "Failed: $failed"
Write-Host ""
Write-Host "Files saved to: assemblies\"
```

Run it:
```powershell
powershell -ExecutionPolicy Bypass -File download_genomes.ps1
```

**Note**: Windows PowerShell doesn't have built-in gzip decompression. You'll need:
- Install 7-Zip: https://www.7-zip.org/download.html
- Or manually decompress the .gz files after download

---

## Step 3: Verify Downloads

Check that you have 170 FASTA files:

**Mac/Linux**:
```bash
ls assemblies/ | wc -l
ls -lh assemblies/ | head -10
```

**Windows**:
```powershell
(Get-ChildItem assemblies).Count
Get-ChildItem assemblies | Select-Object -First 10
```

Expected:
- 170 `.fasta` files
- Each 3-6 MB uncompressed
- Total ~500 MB - 1 GB

---

## Step 4: Transfer to Beocat

### Create Tar Archive (Recommended)

**Mac/Linux**:
```bash
tar -czf validation_genomes.tar.gz assemblies/
ls -lh validation_genomes.tar.gz
```

**Windows** (with 7-Zip):
```powershell
& "C:\Program Files\7-Zip\7z.exe" a -ttar validation_genomes.tar assemblies\
& "C:\Program Files\7-Zip\7z.exe" a -tgzip validation_genomes.tar.gz validation_genomes.tar
```

### Transfer to Beocat

**Using SCP** (Mac/Linux/Windows 10+):
```bash
scp validation_genomes.tar.gz tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/
```

**Using WinSCP** (Windows GUI):
1. Download WinSCP: https://winscp.net/
2. Connect to `beocat.ksu.edu` with your credentials
3. Navigate to `/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/`
4. Upload `validation_genomes.tar.gz`

---

## Step 5: Extract on Beocat

```bash
# SSH to Beocat
ssh tylerdoe@beocat.ksu.edu

# Navigate to validation directory
cd /fastscratch/tylerdoe/COMPASS-pipeline/data/validation

# Extract genomes
tar -xzf validation_genomes.tar.gz

# Verify
ls assemblies/ | wc -l  # Should show 170
ls -lh assemblies/ | head -10
```

---

## Step 6: Update SLURM Script to Use FASTA Mode

Edit `run_compass_validation.sh`:

```bash
# Change this line:
--input_mode assembly \

# To this:
--input_mode fasta \
```

And update the samplesheet path check:

```bash
# Change:
SAMPLESHEET="data/validation/validation_samplesheet.csv"

# To:
SAMPLESHEET="data/validation/validation_samplesheet_fasta.csv"
```

---

## Step 7: Create FASTA Samplesheet

On Beocat, create a new samplesheet with local paths:

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline/data/validation

# Create FASTA samplesheet
echo "sample,organism,fasta" > validation_samplesheet_fasta.csv

# Add all genomes
for fasta in assemblies/*.fasta; do
    sample=$(basename "$fasta" .fasta)
    echo "$sample,Escherichia,$PWD/$fasta" >> validation_samplesheet_fasta.csv
done

# Verify
head validation_samplesheet_fasta.csv
wc -l validation_samplesheet_fasta.csv  # Should show 171 (170 + header)
```

---

## Step 8: Submit Validation Job

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Edit the SLURM script to use fasta mode
sed -i 's/--input_mode assembly/--input_mode fasta/' data/validation/run_compass_validation.sh
sed -i 's/validation_samplesheet.csv/validation_samplesheet_fasta.csv/' data/validation/run_compass_validation.sh

# Submit job
sbatch data/validation/run_compass_validation.sh
```

---

## Expected Timeline

- **Step 1-2**: 5 minutes (setup)
- **Step 2**: 1-3 hours (download 170 genomes)
- **Step 3**: 2 minutes (verify)
- **Step 4**: 10-30 minutes (transfer ~500 MB to Beocat)
- **Step 5**: 2 minutes (extract on Beocat)
- **Step 6-8**: 5 minutes (setup and submit)
- **Pipeline run**: 24-48 hours

**Total prep time**: 2-4 hours (mostly waiting for downloads/transfer)

---

## Troubleshooting

### Download Fails

**Problem**: Some genomes fail to download

**Solution**: Re-run the script - it will skip existing files and only download missing ones

### Transfer Fails

**Problem**: SCP times out or connection drops

**Solution**:
- Split into smaller chunks (transfer 50 genomes at a time)
- Use `rsync` instead: `rsync -avz --progress assemblies/ tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/assemblies/`

### Wrong Paths in Samplesheet

**Problem**: Pipeline can't find FASTA files

**Solution**: Use absolute paths in samplesheet:
```bash
# Make sure paths start with /fastscratch/...
grep "^[^s]" validation_samplesheet_fasta.csv | head -3
```

### Out of Space

**Problem**: Not enough space in fastscratch

**Solution**: Check quota and clean up:
```bash
df -h /fastscratch/tylerdoe
du -sh /fastscratch/tylerdoe/*
```

---

## Alternative: Download Incrementally

If you want to start the pipeline sooner, download and transfer in batches:

```bash
# Download first 50 genomes
head -51 validation_samplesheet.csv > batch1.csv  # 50 + header
./download_genomes.sh batch1.csv

# Transfer and start pipeline
scp assemblies/* tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline/data/validation/assemblies/

# Continue downloading remaining 120 while pipeline runs on first 50
```

---

## Contact

Tyler Doerks - tdoerks@vet.k-state.edu

**Status**: Ready to download manually
**Date**: February 7, 2026
**Branch**: v1.3-dev
