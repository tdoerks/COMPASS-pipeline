#!/bin/bash
# ---------------------------------------------------------------------------
# COMPASS head-job wrapper for Beocat (K-State).
#
# The Nextflow orchestrator runs HERE (inside this batch job, not on the login
# node) and submits one SLURM job per pipeline task via -profile beocat.
#
# Submit FROM the directory that contains your mic_* samplesheet folder:
#     sbatch run_compass.sbatch
# Watch:    squeue -u $USER ;  tail -f compass.stdout.*
#
# Paths below resolve against $SLURM_SUBMIT_DIR (the dir you submit from), so it
# works whether that's on /fastscratch, /homes, etc. Only PIPELINE + PROPHAGE_DB
# are absolute.
#
# NOTE: reconcile the #SBATCH partition / --gres / account lines with a wrapper
# that already runs on your account (e.g. run_arbor.sbatch).
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

# --- Run parameters --------------------------------------------------------
# Resolve sample paths against the submit dir (falls back to PWD if run interactively).
: "${SLURM_SUBMIT_DIR:=$PWD}"

PIPELINE="$HOME/COMPASS-pipeline/main.nf"
INPUT="${SLURM_SUBMIT_DIR}/mic_campy/by_organism/Campylobacter_jejuni.csv"
PROPHAGE_DB="/homes/tylerdoe/databases/prophage_db.dmnd"
OUTDIR="${SLURM_SUBMIT_DIR}/results_campy"

cd "$SLURM_SUBMIT_DIR"

echo "Pipeline:    $PIPELINE"
echo "Input:       $INPUT"
echo "Prophage DB: $PROPHAGE_DB"
echo "Outdir:      $OUTDIR"
[ -f "$INPUT" ] || { echo "ERROR: samplesheet not found: $INPUT"; exit 1; }
[ -f "$PROPHAGE_DB" ] || { echo "ERROR: prophage db not found: $PROPHAGE_DB"; exit 1; }

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
