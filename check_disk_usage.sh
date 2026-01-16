#!/bin/bash
# ============================================================
# CHECK DISK USAGE FOR COMPASS PIPELINE
# ============================================================
# This script checks space usage in both homes and fastscratch
#

echo "=========================================="
echo "Disk Usage Report"
echo "=========================================="
echo "Report time: $(date)"
echo ""

# Check homes directory quota
echo "📁 HOMES DIRECTORY (~)"
echo "----------------------------------------"
if command -v quota &> /dev/null; then
    quota -s
else
    echo "Quota command not available, showing disk usage:"
    df -h /homes/tylerdoe 2>/dev/null || echo "Could not check /homes/tylerdoe"
fi
echo ""

# Check homes directory usage
echo "Your homes directory usage:"
du -sh /homes/tylerdoe 2>/dev/null || echo "Could not access /homes/tylerdoe"
echo ""

# Top directories in homes
echo "Top 10 largest directories in homes:"
du -h /homes/tylerdoe/* 2>/dev/null | sort -rh | head -10
echo ""

# Check fastscratch
echo "📁 FASTSCRATCH DIRECTORY"
echo "----------------------------------------"
df -h /fastscratch 2>/dev/null || echo "Could not check /fastscratch"
echo ""

# Check fastscratch/tylerdoe usage
echo "Your fastscratch directory usage:"
du -sh /fastscratch/tylerdoe 2>/dev/null || echo "Could not access /fastscratch/tylerdoe"
echo ""

# Top directories in fastscratch
echo "Top directories in fastscratch/tylerdoe:"
du -h --max-depth=1 /fastscratch/tylerdoe 2>/dev/null | sort -rh | head -15
echo ""

# Check specific pipeline directories
echo "📊 COMPASS PIPELINE DATA"
echo "----------------------------------------"

if [ -d "/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod" ]; then
    echo "Kansas 2021-2025 dataset:"
    du -sh /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod
    echo ""
    echo "  Subdirectories:"
    du -h --max-depth=1 /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod 2>/dev/null | sort -rh | head -10
    echo ""
fi

if [ -d "/fastscratch/tylerdoe/results_ecoli_all_2024" ]; then
    echo "E. coli 2024 dataset:"
    du -sh /fastscratch/tylerdoe/results_ecoli_all_2024
    echo ""
fi

if [ -d "/fastscratch/tylerdoe/work_v12mod_test" ]; then
    echo "Work directory (Nextflow temp):"
    du -sh /fastscratch/tylerdoe/work_v12mod_test
    echo ""
fi

# Check for Nextflow work directories (can be cleaned up)
echo "🧹 CLEANABLE NEXTFLOW WORK DIRECTORIES"
echo "----------------------------------------"
find /fastscratch/tylerdoe -maxdepth 1 -type d -name "work*" -exec du -sh {} \; 2>/dev/null
echo ""

# Check .nextflow directories (caches)
echo "💾 NEXTFLOW CACHE DIRECTORIES"
echo "----------------------------------------"
find /fastscratch/tylerdoe -maxdepth 1 -type d -name ".nextflow*" -exec du -sh {} \; 2>/dev/null
find /homes/tylerdoe -maxdepth 1 -type d -name ".nextflow*" -exec du -sh {} \; 2>/dev/null
echo ""

# Recommendations
echo "=========================================="
echo "💡 SPACE MANAGEMENT RECOMMENDATIONS"
echo "=========================================="
echo ""
echo "To free up space, you can:"
echo "  1. Clean up old Nextflow work directories:"
echo "     rm -rf /fastscratch/tylerdoe/work_OLD_NAME"
echo ""
echo "  2. Clean up Nextflow caches (safe after jobs complete):"
echo "     nextflow clean -f"
echo ""
echo "  3. Remove intermediate files you don't need:"
echo "     - fastq/ (raw reads, if you have assemblies)"
echo "     - trimmed_fastq/ (if you have assemblies)"
echo ""
echo "  4. Compress large result directories:"
echo "     tar -czf backup.tar.gz results_directory/"
echo ""
echo "⚠️  WARNING: fastscratch is NOT backed up!"
echo "   Important results should be copied to homes or archived."
echo ""
