#!/bin/bash
# ---------------------------------------------------------------------------
# COMPASS head-job wrapper for Beocat (K-State).
#
# The Nextflow orchestrator runs HERE (inside this batch job, not on the login
# node) and submits one SLURM job per pipeline task via -profile beocat.
#
# Submit:   sbatch run_compass.sbatch
# Watch:    squeue -u $USER ;  tail -f compass.stdout.*
#
# NOTE: compare the #SBATCH lines below with a wrapper you already run
# successfully on your account (e.g. run_arbor.sbatch) and reconcile the
# partition / --gres / account bits — those are cluster/account specific.
# ---------------------------------------------------------------------------
#SBATCH -N 1
#SBATCH -n 2
#SBATCH --mem=8G
#SBATCH -t 7-00:00:00                 # head job must outlive ALL task jobs; adjust to partition max
#SBATCH -p batch.q                    # matches queue in conf/beocat.config; verify with `sinfo`
#SBATCH --gres=killable:0             # non-killable: don't let the orchestrator get preempted
#SBATCH -J compass-campy
#SBATCH -o "compass.stdout.%j.%N"
#SBATCH -e "compass.stderr.%j.%N"
##SBATCH --mail-user=you@ksu.edu      # uncomment + set to get start/end/fail mail
##SBATCH --mail-type=START,END,FAIL

set -euo pipefail

# --- Environment (Beocat lmod) ---------------------------------------------
# If a module name is wrong:  module spider nextflow   /   module spider apptainer
module load apptainer 2>/dev/null || module load Apptainer 2>/dev/null || true
module load nextflow  2>/dev/null || module load Nextflow  2>/dev/null || true

export NXF_OPTS='-Xms1g -Xmx4g'
# Faster, more reliable NCBI assembly downloads (one Entrez call per genome).
# Strongly recommended at this volume — get a key at NCBI > Account > Settings.
# export NCBI_API_KEY=your_key_here

# --- Run parameters (edit these) -------------------------------------------
PIPELINE="$HOME/COMPASS-pipeline/main.nf"
INPUT="$HOME/beocat/mic_campy/by_organism/Campylobacter_jejuni.csv"
PROPHAGE_DB="/homes/tylerdoe/databases/prophage_db.dmnd"
OUTDIR="$HOME/beocat/results_campy"

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
