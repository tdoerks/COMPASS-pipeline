#!/bin/bash
#SBATCH -N 1
#SBATCH -n 2
#SBATCH --mem=16G
#SBATCH -t 4:00:00
#SBATCH -p batch.q
#SBATCH --gres=killable:0
#SBATCH -J compass-sa4-check
#SBATCH -o "compass_sa4_check.stdout.%j.%N"
#SBATCH -e "compass_sa4_check.stderr.%j.%N"
#SBATCH --mail-user=tylerdoe@ksu.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

module load apptainer 2>/dev/null || module load Apptainer 2>/dev/null || true
module load nextflow  2>/dev/null || module load Nextflow  2>/dev/null || true

export NXF_OPTS='-Xms2g -Xmx8g'

PIPELINE="/fastscratch/tylerdoe/COMPASS-1.1.0/main.nf"
INPUT="/fastscratch/tylerdoe/COMPASS-1.1.0/samplesheet_sa4_check.csv"
OUTDIR="/fastscratch/tylerdoe/COMPASS-1.1.0/results_sa4_check"

nextflow run "$PIPELINE" -profile beocat \
    -c /fastscratch/tylerdoe/COMPASS-1.1.0/extra.config \
    --input_mode fasta \
    --input "$INPUT" \
    --skip_busco false \
    --outdir "$OUTDIR"
