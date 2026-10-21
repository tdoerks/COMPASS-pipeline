#!/bin/bash
# COMPASS head job — E. coli AST genomes (~8,488 genomes, defense-expansion branch).
#
# Prerequisites:
#   1. Genomes unzipped: cd /fastscratch/tylerdoe/COMPASS-runs/new_set
#                        for z in chunk_??.zip; do unzip -qo $z -d genomes; done
#   2. Build samplesheet: python3 /fastscratch/tylerdoe/COMPASS-phage-therapy/bin/make_fasta_samplesheet.py \
#                           /fastscratch/tylerdoe/COMPASS-runs/new_set/ecoli_AST_Genomes.tsv \
#                           "/fastscratch/tylerdoe/COMPASS-runs/new_set/genomes/ncbi_dataset/data/*/*.fna" \
#                           /fastscratch/tylerdoe/COMPASS-runs/new_set/samplesheet_ecoli_8k.csv
#   3. Submit from COMPASS-phage-therapy/: sbatch run_compass_ecoli_8k.sbatch
#
# Scale: ~21 tasks/isolate → ~178k tasks → ~13 days (> 7-day limit → resubmit with -resume).
#
#SBATCH -N 1
#SBATCH -n 2
#SBATCH --mem=16G
#SBATCH -t 7-00:00:00
#SBATCH -p batch.q
#SBATCH --gres=killable:0
#SBATCH -J compass-ecoli-8k
#SBATCH -o "compass_8k.stdout.%j.%N"
#SBATCH -e "compass_8k.stderr.%j.%N"
#SBATCH --mail-user=tylerdoe@ksu.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

module load apptainer 2>/dev/null || module load Apptainer 2>/dev/null || true
module load nextflow  2>/dev/null || module load Nextflow  2>/dev/null || true

# 178k tasks needs more heap than the 45k-task 6k run
export NXF_OPTS='-Xms2g -Xmx16g'

# ---- Run parameters --------------------------------------------------------
PIPELINE="/fastscratch/tylerdoe/COMPASS-phage-therapy/main.nf"
INPUT="/fastscratch/tylerdoe/COMPASS-runs/new_set/samplesheet_ecoli_8k.csv"
PROPHAGE_DB="/fastscratch/tylerdoe/databases/prophage_db.dmnd"
OUTDIR="/fastscratch/tylerdoe/COMPASS-runs/new_set/results_ecoli_8k"

# ---- Launch ----------------------------------------------------------------
nextflow run "$PIPELINE" -profile beocat \
    -c /fastscratch/tylerdoe/COMPASS-1.1.0/extra.config \
    --input_mode fasta \
    --input "$INPUT" \
    --database_dir "/fastscratch/tylerdoe/databases" \
    --prophage_db "$PROPHAGE_DB" \
    --padloc_db "/fastscratch/tylerdoe/databases/padloc_db" \
    --skip_busco \
    --outdir "$OUTDIR" \
    -resume \
    "$@"
