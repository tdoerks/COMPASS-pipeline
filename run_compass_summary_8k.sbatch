#!/bin/bash
# Generate COMPASS summary + phage therapy viewer for the 8k E. coli AST run.
# Joins NCBI Pathogen Isolates metadata (AST/MIC phenotypic data) via --metadata.
# Submit from: /fastscratch/tylerdoe/COMPASS-phage-therapy/
#
#SBATCH -N 1
#SBATCH -n 4
#SBATCH --mem=32G
#SBATCH -t 2:00:00
#SBATCH -p batch.q
#SBATCH --gres=killable:0
#SBATCH -J compass-summary-8k
#SBATCH -o "compass_summary_8k.stdout.%j.%N"
#SBATCH -e "compass_summary_8k.stderr.%j.%N"
#SBATCH --mail-user=tylerdoe@ksu.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-phage-therapy"
OUTDIR="/fastscratch/tylerdoe/COMPASS-runs/new_set/results_ecoli_8k"
METADATA="/fastscratch/tylerdoe/COMPASS-runs/new_set/ecoli_AST_genomes.tsv"
SUMMARY_TSV="compass_summary_8k.tsv"
VIEWER_HTML="phage_therapy_viewer_8k.html"

cd "$PIPELINE_DIR"

echo "=== Step 1: Generate summary TSV ==="
python3 bin/generate_compass_summary.py \
    --outdir "$OUTDIR" \
    --output_tsv "$SUMMARY_TSV" \
    --metadata "$METADATA"

echo ""
echo "=== AST column check ==="
head -1 "$SUMMARY_TSV" | tr '\t' '\n' | grep -i "ampicillin\|ciprofloxacin\|ceftriaxone\|tetracycline\|gentamicin" || echo "  (no AST columns found — check metadata join)"

echo ""
echo "=== Step 2: Build phage therapy viewer ==="
python3 bin/build_phage_therapy_viewer.py \
    --compass "$SUMMARY_TSV" \
    --resolve-names \
    --out "$VIEWER_HTML"

echo ""
echo "Done: $PIPELINE_DIR/$VIEWER_HTML"
