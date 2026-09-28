#!/bin/bash
#SBATCH --job-name=clostridium
#SBATCH --output=/fastscratch/tylerdoe/slurm-clostridium-%j.out
#SBATCH --error=/fastscratch/tylerdoe/slurm-clostridium-%j.err
#SBATCH --time=672:00:00
#SBATCH --partition=batch.q
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G

#
# COMPASS Pipeline - Clostridium difficile Study
#
# Part of oxygen gradient prophage burden analysis
# Obligate anaerobe #3 (after Fusobacterium, Bacteroides)
#

set -e

echo "========================================================================"
echo "COMPASS Pipeline - Clostridium difficile Study"
echo "========================================================================"
echo ""
echo "Study: Oxygen Gradient Prophage Burden Analysis"
echo "Organism: Clostridium difficile (obligate anaerobe)"
echo "Hypothesis: Low prophage burden compared to aerobes"
echo ""
echo "Job ID: ${SLURM_JOB_ID}"
echo "Start time: $(date)"
echo ""

# Pipeline version
PIPELINE_VERSION="1.2.0-candidate"
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline-${PIPELINE_VERSION}"

# Output directory
OUTPUT_DIR="/fastscratch/tylerdoe/clostridium_results"

# Samplesheet
SAMPLESHEET="${PIPELINE_DIR}/clostridium_difficile_study/data/samplesheet_clostridium.txt"

# Nextflow work directory (unique per study)
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_clostridium
mkdir -p $NXF_HOME

echo "Configuration:"
echo "  Pipeline version: ${PIPELINE_VERSION}"
echo "  Pipeline directory: ${PIPELINE_DIR}"
echo "  Samplesheet: ${SAMPLESHEET}"
echo "  Output directory: ${OUTPUT_DIR}"
echo "  Nextflow home: ${NXF_HOME}"
echo ""

# Check samplesheet exists
if [ ! -f "${SAMPLESHEET}" ]; then
    echo "ERROR: Samplesheet not found: ${SAMPLESHEET}"
    exit 1
fi

# Count samples
n_samples=$(wc -l < "${SAMPLESHEET}")
echo "Total samples: ${n_samples}"
echo ""

# Load modules
echo "Loading modules..."
module load Nextflow || {
    echo "ERROR: Failed to load Nextflow module"
    exit 1
}

echo ""
echo "========================================================================"
echo "Starting COMPASS Pipeline"
echo "========================================================================"
echo ""

# Run pipeline
cd ${PIPELINE_DIR}

nextflow run main.nf \
    -profile beocat \
    --input_mode sra_list \
    --input "${SAMPLESHEET}" \
    --skip_busco false \
    --busco_download_path /fastscratch/tylerdoe/databases/busco_downloads \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --outdir "${OUTPUT_DIR}" \
    -w work_clostridium \
    -resume

echo ""
echo "========================================================================"
echo "Pipeline Complete"
echo "========================================================================"
echo ""
echo "End time: $(date)"
echo "Results: ${OUTPUT_DIR}"
echo ""
echo "Next steps:"
echo "  1. Analyze prophage counts: VIBRANT results"
echo "  2. Compare to Fusobacterium and Bacteroides"
echo "  3. Test oxygen gradient hypothesis"
echo ""
