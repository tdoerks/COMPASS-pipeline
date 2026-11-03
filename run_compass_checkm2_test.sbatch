#!/bin/bash
#SBATCH -N 1
#SBATCH -n 2
#SBATCH --mem=16G
#SBATCH -t 2-00:00:00
#SBATCH -p batch.q
#SBATCH --gres=killable:0
#SBATCH -J compass-checkm2-test
#SBATCH -o "compass_checkm2_test.stdout.%j.%N"
#SBATCH -e "compass_checkm2_test.stderr.%j.%N"
#SBATCH --mail-user=tylerdoe@ksu.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

module load apptainer 2>/dev/null || module load Apptainer 2>/dev/null || true
module load nextflow  2>/dev/null || module load Nextflow  2>/dev/null || true

export NXF_OPTS='-Xms2g -Xmx8g'

PIPELINE="/fastscratch/tylerdoe/COMPASS-phage-therapy/main.nf"
INPUT="/fastscratch/tylerdoe/COMPASS-phage-therapy/samplesheet_checkm2_test.csv"
PROPHAGE_DB="/fastscratch/tylerdoe/databases/prophage_db.dmnd"
CHECKM2_DB="/fastscratch/tylerdoe/databases/checkm2_db/CheckM2_database/uniref100.KO.1.dmnd"
OUTDIR="/fastscratch/tylerdoe/COMPASS-phage-therapy/results_checkm2_test"

nextflow run "$PIPELINE" -profile beocat \
    --input_mode fasta \
    --input "$INPUT" \
    --prophage_db "$PROPHAGE_DB" \
    --checkm2_db "$CHECKM2_DB" \
    --outdir "$OUTDIR" \
    "$@"
