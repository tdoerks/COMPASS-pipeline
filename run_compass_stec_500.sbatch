#!/bin/bash
#SBATCH -N 1
#SBATCH -n 2
#SBATCH --mem=16G
#SBATCH -t 7-00:00:00
#SBATCH -p batch.q
#SBATCH --gres=killable:0
#SBATCH -J compass-stec-500
#SBATCH -o "compass_stec500.stdout.%j.%N"
#SBATCH -e "compass_stec500.stderr.%j.%N"
#SBATCH --mail-user=tylerdoe@ksu.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

module load apptainer 2>/dev/null || module load Apptainer 2>/dev/null || true
module load nextflow  2>/dev/null || module load Nextflow  2>/dev/null || true

export NXF_OPTS='-Xms2g -Xmx8g'

PIPELINE="/fastscratch/tylerdoe/COMPASS-1.1.0/main.nf"
INPUT="/fastscratch/tylerdoe/COMPASS-1.1.0/samplesheet_stec_500_fasta.csv"
PROPHAGE_DB="/fastscratch/tylerdoe/databases/prophage_db.dmnd"
OUTDIR="/fastscratch/tylerdoe/COMPASS-1.1.0/results_stec_500"

nextflow run "$PIPELINE" -profile beocat \
    -c /fastscratch/tylerdoe/COMPASS-1.1.0/extra.config \
    --input_mode fasta \
    --input "$INPUT" \
    --database_dir "/fastscratch/tylerdoe/databases" \
    --prophage_db "$PROPHAGE_DB" \
    --skip_busco \
    --outdir "$OUTDIR" \
    -resume
