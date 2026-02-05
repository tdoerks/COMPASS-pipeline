#!/bin/bash

# Download assemblies directly from NCBI FTP using wget
# Works around NCBI Datasets API TLS timeout issues on Beocat

set -e

echo "=================================================="
echo "COMPASS Validation - Assembly Download via FTP"
echo "=================================================="
echo "Start time: $(date)"
echo ""

# Output directory
OUTDIR="data/validation/assemblies"
mkdir -p "$OUTDIR"

# Function to download assembly from NCBI FTP
download_assembly() {
    local sample=$1
    local accession=$2

    echo "Downloading $sample ($accession)..."

    # Remove version suffix for FTP path
    local acc_prefix=$(echo $accession | sed 's/\.[0-9]*$//')

    # Construct FTP path
    local ftp_path="https://ftp.ncbi.nlm.nih.gov/genomes/all/${acc_prefix:0:3}/${acc_prefix:4:3}/${acc_prefix:7:3}/${acc_prefix:10:3}/${accession}/${accession}_genomic.fna.gz"

    # Download with retries
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if wget -q -O "${OUTDIR}/${sample}.fasta.gz" "$ftp_path"; then
            echo "  ✓ Downloaded successfully"
            gunzip "${OUTDIR}/${sample}.fasta.gz"
            return 0
        else
            echo "  ✗ Attempt $attempt failed"
            attempt=$((attempt + 1))
            [ $attempt -le $max_attempts ] && sleep 5
        fi
    done

    echo "  ✗ FAILED after $max_attempts attempts"
    return 1
}

# Read samplesheet and download each assembly
echo "Reading validation_samplesheet.csv..."
echo ""

total=0
success=0
failed=0

while IFS=, read -r sample organism accession; do
    # Skip header
    if [ "$sample" = "sample" ]; then
        continue
    fi

    total=$((total + 1))

    if download_assembly "$sample" "$accession"; then
        success=$((success + 1))
    else
        failed=$((failed + 1))
    fi

    # Progress update every 10 samples
    if [ $((total % 10)) -eq 0 ]; then
        echo ""
        echo "Progress: $total samples processed ($success succeeded, $failed failed)"
        echo ""
    fi

done < data/validation/validation_samplesheet.csv

echo ""
echo "=================================================="
echo "Download Complete"
echo "=================================================="
echo "Total samples: $total"
echo "Successful: $success"
echo "Failed: $failed"
echo "End time: $(date)"
echo ""
echo "Assemblies saved to: $OUTDIR"
echo ""

if [ $failed -gt 0 ]; then
    echo "WARNING: $failed assemblies failed to download"
    echo "Check error messages above for details"
    exit 1
fi

echo "All assemblies downloaded successfully!"
