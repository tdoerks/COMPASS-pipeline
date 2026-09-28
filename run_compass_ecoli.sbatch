#!/bin/bash
# ---------------------------------------------------------------------------
# COMPASS head-job wrapper for Beocat (K-State) — E. coli MIC/AST assembly batch.
#
# Assembly input mode: the samplesheet lists NCBI GCA/GCF accessions and COMPASS
# downloads each FASTA itself (modules/download_assembly.nf). No pre-staging.
#
# Build the samplesheet first (from an NCBI Isolates Browser export):
#   python3 bin/make_samplesheet.py isolates.csv -o samplesheet.csv
#   head -n 21 samplesheet.csv > samplesheet_test.csv     # header + 20 (test batch)
#
# Submit:   sbatch run_compass_ecoli.sbatch
# Watch:    squeue -u $USER ;  tail -f compass.stdout.*
#
# Reconcile the #SBATCH partition / account / --gres lines with a wrapper you
# already run successfully on your account.
# ---------------------------------------------------------------------------
#SBATCH -N 1
#SBATCH -n 2
#SBATCH --mem=8G
#SBATCH -t 7-00:00:00                 # head job must outlive ALL task jobs
#SBATCH -p batch.q                    # verify with `sinfo`
#SBATCH --gres=killable:0             # don't let the orchestrator get preempted
#SBATCH -J compass-ecoli
#SBATCH -o "compass.stdout.%j.%N"
#SBATCH -e "compass.stderr.%j.%N"
##SBATCH --mail-user=you@ksu.edu
##SBATCH --mail-type=START,END,FAIL

set -euo pipefail

module load apptainer 2>/dev/null || module load Apptainer 2>/dev/null || true
module load nextflow  2>/dev/null || module load Nextflow  2>/dev/null || true

export NXF_OPTS='-Xms1g -Xmx4g'
# STRONGLY recommended for the full ~6k run (one Entrez download per genome):
# export NCBI_API_KEY=your_key_here

# --- Run parameters (EDIT these) -------------------------------------------
PIPELINE="/fastscratch/tylerdoe/COMPASS-1.1.0/main.nf"                # verified 1.1.0 checkout
INPUT="/fastscratch/tylerdoe/COMPASS-1.1.0/samplesheet_test.csv"      # test batch first; swap to samplesheet.csv for full run
PROPHAGE_DB="/homes/tylerdoe/databases/prophage_db.dmnd"             # proven path
OUTDIR="/fastscratch/tylerdoe/COMPASS-1.1.0/results_mic_ecoli_test"  # fresh; won't collide with mic_campy

# --- Launch -----------------------------------------------------------------
# --skip_busco to start fast; to enable BUSCO, drop it and add
#   --busco_download_path /homes/tylerdoe/databases/busco_downloads
nextflow run "$PIPELINE" -profile beocat \
    --input_mode assembly \
    --input "$INPUT" \
    --prophage_db "$PROPHAGE_DB" \
    --skip_busco \
    --outdir "$OUTDIR" \
    -resume
