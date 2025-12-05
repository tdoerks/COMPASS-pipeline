#!/bin/bash
# ============================================================
# CHECK ALL RUNNING COMPASS PIPELINE JOBS
# ============================================================

echo "=========================================="
echo "COMPASS Pipeline Jobs Status"
echo "=========================================="
echo "Checking time: $(date)"
echo ""

# Check running jobs
echo "🔍 RUNNING SLURM JOBS"
echo "----------------------------------------"
squeue -u tylerdoe -o "%.18i %.9P %.50j %.8u %.8T %.10M %.9l %.6D %R" 2>/dev/null || echo "Could not check SLURM queue"
echo ""

# Find recent SLURM log files
echo "📝 RECENT SLURM LOG FILES"
echo "----------------------------------------"
echo "In /homes/tylerdoe:"
ls -lhtr /homes/tylerdoe/slurm-*.out 2>/dev/null | tail -5
echo ""
echo "In /fastscratch/tylerdoe:"
ls -lhtr /fastscratch/tylerdoe/slurm-*.out 2>/dev/null | tail -5
echo ""

# Check for pipeline output directories
echo "📁 PIPELINE OUTPUT DIRECTORIES"
echo "----------------------------------------"

# Kansas 2021-2025
if [ -d "/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod" ]; then
    echo "✅ Kansas 2021-2025 (v1.2-mod):"
    echo "   Path: /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod"
    du -sh /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod 2>/dev/null

    # Check sample counts
    amr_count=$(find /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod/amrfinder* -name "*.tsv" 2>/dev/null | wc -l)
    mlst_count=$(find /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod/mlst -name "*.tsv" 2>/dev/null | wc -l)
    echo "   AMRFinder results: $amr_count files"
    echo "   MLST results: $mlst_count files"
    echo ""
fi

# E. coli 2024
if [ -d "/fastscratch/tylerdoe/results_ecoli_all_2024" ]; then
    echo "✅ E. coli 2024 (All US States):"
    echo "   Path: /fastscratch/tylerdoe/results_ecoli_all_2024"
    du -sh /fastscratch/tylerdoe/results_ecoli_all_2024 2>/dev/null

    # Check sample counts
    amr_count=$(find /fastscratch/tylerdoe/results_ecoli_all_2024/amrfinder* -name "*.tsv" 2>/dev/null | wc -l)
    mlst_count=$(find /fastscratch/tylerdoe/results_ecoli_all_2024/mlst -name "*.tsv" 2>/dev/null | wc -l)
    echo "   AMRFinder results: $amr_count files"
    echo "   MLST results: $mlst_count files"
    echo ""
fi

# Check for work directories
echo "💾 NEXTFLOW WORK DIRECTORIES"
echo "----------------------------------------"
find /fastscratch/tylerdoe -maxdepth 1 -type d -name "work*" -exec sh -c 'echo "{}:"; du -sh {} 2>/dev/null' \; 2>/dev/null
echo ""

# Check for .nextflow cache
echo "🗄️  NEXTFLOW CACHE DIRECTORIES"
echo "----------------------------------------"
find /fastscratch/tylerdoe -maxdepth 1 -type d -name ".nextflow*" -exec sh -c 'echo "{}:"; du -sh {} 2>/dev/null' \; 2>/dev/null
echo ""

# Provide quick links to logs
echo "=========================================="
echo "📊 QUICK MONITORING COMMANDS"
echo "=========================================="
echo ""
echo "Monitor E. coli 2024 job:"
echo "  tail -f /homes/tylerdoe/slurm-4408610.out"
echo ""
echo "Monitor Kansas 2021-2025 job (find latest log):"
echo "  ls -ltr /fastscratch/tylerdoe/slurm-*.out | tail -1"
echo "  tail -f /fastscratch/tylerdoe/slurm-JOBID.out"
echo ""
echo "Check job queue:"
echo "  squeue -u tylerdoe"
echo ""
echo "Check disk usage:"
echo "  bash check_disk_usage.sh"
echo ""
