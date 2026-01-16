#!/bin/bash
#SBATCH --job-name=ecoli_2024_FULL
#SBATCH --output=/fastscratch/tylerdoe/ecoli_2024_FULL_%j.out
#SBATCH --error=/fastscratch/tylerdoe/ecoli_2024_FULL_%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS FULL Pipeline - E. coli 2024"
echo "WITH COMPLETE QC AND TRIMMING"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""
echo "Pipeline Features:"
echo "  ✅ FastQC - Raw read quality assessment"
echo "  ✅ Fastp - Quality trimming & adapter removal"
echo "  ✅ SPAdes - Assembly from TRIMMED reads"
echo "  ✅ BUSCO - Completeness & contamination QC"
echo "  ✅ QUAST - Assembly statistics"
echo "  ✅ Assembly QC - N50, contigs, length filtering"
echo "  ✅ BUSCO QC - Contamination detection (>5% duplication)"
echo "  ✅ AMRFinder - AMR gene detection"
echo "  ✅ VIBRANT - Phage identification"
echo "  ✅ DIAMOND - Prophage database comparison"
echo "  ✅ MLST - Multi-locus sequence typing"
echo "  ✅ SISTR - Serotyping (Salmonella)"
echo "  ✅ MOB-suite - Plasmid detection"
echo "  ✅ MultiQC - Aggregate QC report"
echo ""
echo "Queue Management:"
echo "  - Max 500 jobs in queue"
echo "  - Submit rate: 20 jobs/min"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Ensure we're on v1.2-dev branch with latest code
echo "Pulling latest v1.2-dev..."
git fetch origin
git checkout v1.2-dev
git pull origin v1.2-dev

# Show latest commit
echo ""
echo "Current version:"
git log --oneline -1
echo ""

# Load Nextflow
module load Nextflow

# Set unique Nextflow home
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ecoli_2024_FULL

# Run FULL pipeline with main.nf (not main_metadata.nf!)
# This uses COMPLETE_PIPELINE workflow with:
# - DATA_ACQUISITION subworkflow
# - ASSEMBLY subworkflow (includes FastQC + Fastp trimming!)
# - All analysis subworkflows (AMR, Phage, Typing, Mobile Elements)
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
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
    --outdir /fastscratch/tylerdoe/results_ecoli_2024_FULL \
    -w work_ecoli_2024_FULL \
    -name ecoli_2024_FULL_${SLURM_JOB_ID} \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ FULL Pipeline completed successfully!"
    echo ""
    echo "Results Directory: /fastscratch/tylerdoe/results_ecoli_2024_FULL"
    echo ""
    echo "Output Directories:"
    echo "  Read QC:"
    echo "    - fastqc/          Raw read quality reports"
    echo "    - fastp/           Trimming reports & stats"
    echo "    - trimmed_fastq/   Trimmed FASTQ files"
    echo ""
    echo "  Assembly:"
    echo "    - assemblies/      Assembled genomes (from TRIMMED reads)"
    echo "    - busco/           BUSCO completeness results"
    echo "    - quast/           Assembly statistics"
    echo "    - assembly_qc/     Assembly QC metrics"
    echo "    - busco_qc/        Contamination detection results"
    echo ""
    echo "  Analysis:"
    echo "    - amrfinder/       AMR gene detection"
    echo "    - vibrant/         Phage identification"
    echo "    - diamond_prophage/ Prophage database hits"
    echo "    - mlst/            Multi-locus sequence typing"
    echo "    - sistr/           Serotyping"
    echo "    - mobsuite/        Plasmid detection"
    echo ""
    echo "  Reports:"
    echo "    - multiqc/         Aggregated QC report (HTML)"
    echo "    - summary/         COMPASS combined analysis"
    echo "    - pipeline_info/   Execution reports"
    echo ""
    echo "Key Reports to Check:"
    echo "  1. MultiQC Report:"
    echo "     /fastscratch/tylerdoe/results_ecoli_2024_FULL/multiqc/multiqc_report.html"
    echo ""
    echo "  2. Assembly QC Summary:"
    echo "     /fastscratch/tylerdoe/results_ecoli_2024_FULL/pipeline_info/assembly_qc_summary.html"
    echo ""
    echo "  3. BUSCO QC Summary (Contamination):"
    echo "     /fastscratch/tylerdoe/results_ecoli_2024_FULL/pipeline_info/busco_qc_summary.html"
    echo ""
    echo "  4. Pipeline Execution Report:"
    echo "     /fastscratch/tylerdoe/results_ecoli_2024_FULL/pipeline_info/execution_report.html"
    echo ""
    echo "Generate comprehensive AMR-prophage analysis:"
    echo "  python bin/comprehensive_amr_prophage_analysis.py \\"
    echo "    --results-dir /fastscratch/tylerdoe/results_ecoli_2024_FULL \\"
    echo "    --prophage-metadata /homes/tylerdoe/databases/prophage_metadata.xlsx \\"
    echo "    --organism ecoli \\"
    echo "    --output ecoli_2024_comprehensive_analysis.html"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check error log: /fastscratch/tylerdoe/ecoli_2024_FULL_${SLURM_JOB_ID}.err"
    echo "  2. Check nextflow log: /fastscratch/tylerdoe/COMPASS-pipeline/.nextflow.log"
    echo "  3. Check MultiQC report (if generated):"
    echo "     /fastscratch/tylerdoe/results_ecoli_2024_FULL/multiqc/multiqc_report.html"
    echo "  4. Check QC reports:"
    echo "     /fastscratch/tylerdoe/results_ecoli_2024_FULL/assembly_qc/"
    echo "     /fastscratch/tylerdoe/results_ecoli_2024_FULL/busco_qc/"
fi

exit $EXIT_CODE
