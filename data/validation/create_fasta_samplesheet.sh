#!/bin/bash
# Create FASTA samplesheet for validation genomes
# This script generates a CSV with sample,organism,fasta columns
# pointing to locally downloaded FASTA files

set -e

VALIDATION_DIR="/fastscratch/tylerdoe/COMPASS-pipeline/data/validation"
ASSEMBLIES_DIR="${VALIDATION_DIR}/assemblies"
OUTPUT_CSV="${VALIDATION_DIR}/validation_samplesheet_fasta.csv"

echo "Creating FASTA samplesheet..."
echo "Input directory: ${ASSEMBLIES_DIR}"
echo "Output file: ${OUTPUT_CSV}"
echo ""

# Check assemblies directory exists
if [ ! -d "$ASSEMBLIES_DIR" ]; then
    echo "ERROR: Assemblies directory not found: $ASSEMBLIES_DIR"
    exit 1
fi

# Count FASTA files
FASTA_COUNT=$(ls ${ASSEMBLIES_DIR}/*.fasta 2>/dev/null | wc -l)
echo "Found ${FASTA_COUNT} FASTA files"
echo ""

if [ "$FASTA_COUNT" -eq 0 ]; then
    echo "ERROR: No FASTA files found in $ASSEMBLIES_DIR"
    exit 1
fi

# Create CSV header
echo "sample,organism,fasta" > "$OUTPUT_CSV"

# Add each FASTA file
for fasta in ${ASSEMBLIES_DIR}/*.fasta; do
    sample=$(basename "$fasta" .fasta)
    echo "${sample},Escherichia,${fasta}" >> "$OUTPUT_CSV"
done

# Report results
TOTAL_LINES=$(wc -l < "$OUTPUT_CSV")
SAMPLE_COUNT=$((TOTAL_LINES - 1))  # Subtract header

echo "=========================================="
echo "FASTA Samplesheet Created Successfully!"
echo "=========================================="
echo "Output: ${OUTPUT_CSV}"
echo "Total samples: ${SAMPLE_COUNT}"
echo ""
echo "First 10 entries:"
head -11 "$OUTPUT_CSV"
echo ""
echo "Last 5 entries:"
tail -5 "$OUTPUT_CSV"
echo ""
echo "Next steps:"
echo "  1. Review samplesheet: cat ${OUTPUT_CSV}"
echo "  2. Update run_compass_validation.sh to use fasta mode"
echo "  3. Submit job: sbatch data/validation/run_compass_validation.sh"
