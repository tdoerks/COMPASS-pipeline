#!/bin/bash
#SBATCH --job-name=ecoli_2024_qc
#SBATCH --output=/fastscratch/tylerdoe/ecoli_2024_qc_%j.out
#SBATCH --error=/fastscratch/tylerdoe/ecoli_2024_qc_%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline v1.2-dev - E. coli 2024"
echo "WITH COMPREHENSIVE QC SYSTEM"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""
echo "QC Features:"
echo "  - Assembly QC (N50, contigs, length)"
echo "  - BUSCO contamination detection (>5% duplication)"
echo "  - Automatic filtering of failed samples"
echo "  - Comprehensive QC reports (HTML/CSV/TXT)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Ensure we're on v1.2-dev branch with latest QC system
echo "Pulling latest v1.2-dev with QC system..."
git fetch origin
git checkout v1.2-dev
git pull origin v1.2-dev

# Show latest commit to verify QC system is present
echo ""
echo "Current version:"
git log --oneline -1
echo ""

# Load Nextflow
module load Nextflow

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ecoli_2024_qc

# Run pipeline for E. coli 2024 with comprehensive QC
# - Assembly QC: Checks N50, contigs, length, N content
# - BUSCO QC: Detects contamination via duplication
# - Only clean samples proceed to AMR/phage analysis
nextflow run main_metadata.nf \
    -profile beocat \
    --filter_state null \
    --filter_organism "Escherichia" \
    --filter_year_start 2024 \
    --filter_year_end 2024 \
    --skip_busco false \
    --skip_assembly_qc false \
    --skip_busco_qc false \
    --assembly_error_strategy ignore \
    --busco_error_strategy ignore \
    --busco_qc_max_duplicated 5.0 \
    --busco_qc_min_complete 80.0 \
    --assembly_qc_min_n50 10000 \
    --assembly_qc_min_length 1000000 \
    --outdir /fastscratch/tylerdoe/results_ecoli_2024_with_qc \
    -w work_ecoli_2024_qc \
    -name ecoli_2024_qc_${SLURM_JOB_ID} \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Pipeline completed successfully!"
    echo ""
    echo "QC Reports Generated:"
    echo "  Assembly QC Summary:"
    echo "    - /fastscratch/tylerdoe/results_ecoli_2024_with_qc/pipeline_info/assembly_qc_summary.html"
    echo "    - /fastscratch/tylerdoe/results_ecoli_2024_with_qc/pipeline_info/assembly_qc_summary.csv"
    echo ""
    echo "  BUSCO QC Summary (Contamination):"
    echo "    - /fastscratch/tylerdoe/results_ecoli_2024_with_qc/pipeline_info/busco_qc_summary.html"
    echo "    - /fastscratch/tylerdoe/results_ecoli_2024_with_qc/pipeline_info/busco_qc_summary.csv"
    echo ""
    echo "  Individual QC Reports:"
    echo "    - /fastscratch/tylerdoe/results_ecoli_2024_with_qc/assembly_qc/"
    echo "    - /fastscratch/tylerdoe/results_ecoli_2024_with_qc/busco_qc/"
    echo ""
    echo "Generate comprehensive AMR-prophage analysis:"
    echo "  python bin/comprehensive_amr_prophage_analysis.py \\"
    echo "    --results-dir /fastscratch/tylerdoe/results_ecoli_2024_with_qc \\"
    echo "    --prophage-metadata /homes/tylerdoe/databases/prophage_metadata.xlsx \\"
    echo "    --organism ecoli \\"
    echo "    --output ecoli_2024_comprehensive_analysis.html"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check error log: /fastscratch/tylerdoe/ecoli_2024_qc_${SLURM_JOB_ID}.err"
    echo "  2. Check nextflow log: /fastscratch/tylerdoe/COMPASS-pipeline/.nextflow.log"
    echo "  3. Check QC reports for failed samples:"
    echo "     - /fastscratch/tylerdoe/results_ecoli_2024_with_qc/assembly_qc/*.qc_failed.txt"
    echo "     - /fastscratch/tylerdoe/results_ecoli_2024_with_qc/busco_qc/*.busco_qc_failed.txt"
    echo "  4. Check assembly failures:"
    echo "     - /fastscratch/tylerdoe/results_ecoli_2024_with_qc/assemblies/failed/*.failed.log"
fi

exit $EXIT_CODE
