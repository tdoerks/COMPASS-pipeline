#!/bin/bash
# COMPASS head job for Beocat (KSU) — full E. coli MIC/AST run (~3,500-6,000 genomes).
#
# Prerequisites:
#   1. Pre-download genomes with datasets CLI (see bin/make_fasta_samplesheet.py)
#   2. Build samplesheet:  python3 bin/make_fasta_samplesheet.py
#   3. Submit from COMPASS-1.1.0/:  sbatch run_compass_ecoli_6k.sbatch
#
# Key differences from the test sbatch (run_compass_fasta.sbatch):
#   * --input_mode fasta  (pre-downloaded genomes; no runtime NCBI calls)
#   * NXF_OPTS bumped to -Xmx12g (orchestrating 45k+ tasks needs more heap)
#   * 7-day walltime (head job must outlive all task jobs; full run ~24-48h)
#   * --database_dir + --prophage_db both point at the real DB dir (required
#     for the Apptainer --contain --bind setup on Beocat — see session notes)
#
#SBATCH -N 1
#SBATCH -n 2
#SBATCH --mem=16G
#SBATCH -t 7-00:00:00
#SBATCH -p batch.q
#SBATCH --gres=killable:0
#SBATCH -J compass-ecoli-6k
#SBATCH -o "compass_6k.stdout.%j.%N"
#SBATCH -e "compass_6k.stderr.%j.%N"
#SBATCH --mail-user=tylerdoe@ksu.edu
#SBATCH --mail-type=END,FAIL

set -euo pipefail

module load apptainer 2>/dev/null || module load Apptainer 2>/dev/null || true
module load nextflow  2>/dev/null || module load Nextflow  2>/dev/null || true

# bumped from 4g: orchestrating 45k+ tasks needs more Nextflow heap
export NXF_OPTS='-Xms2g -Xmx12g'

# NCBI API key speeds up any residual Entrez calls (not needed for fasta mode,
# but harmless and good practice for future runs)
# export NCBI_API_KEY=your_key_here

# ---- Run parameters --------------------------------------------------------
PIPELINE="/fastscratch/tylerdoe/COMPASS-1.1.0/main.nf"
INPUT="/fastscratch/tylerdoe/COMPASS-1.1.0/samplesheet_full_fasta.csv"
PROPHAGE_DB="/fastscratch/tylerdoe/databases/prophage_db.dmnd"
OUTDIR="/fastscratch/tylerdoe/COMPASS-1.1.0/results_mic_ecoli_6k"

# ---- Launch ----------------------------------------------------------------
nextflow run "$PIPELINE" -profile beocat \
    -c /fastscratch/tylerdoe/COMPASS-1.1.0/extra.config \
    --input_mode fasta \
    --input "$INPUT" \
    --database_dir "/fastscratch/tylerdoe/databases" \
    --prophage_db "$PROPHAGE_DB" \
    --skip_busco \
    --outdir "$OUTDIR" \
    -resume
