#!/bin/bash
# COMPASS Pipeline - Beocat Job Status Checker
# Run this on Beocat to diagnose failed/timed-out runs

echo "================================================"
echo "COMPASS Pipeline - Beocat Status Checker"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check current jobs
echo -e "${BLUE}=== Current SLURM Jobs ===${NC}"
squeue -u tylerdoe -o "%.18i %.9P %.30j %.8T %.10M %.9l %.6D %R"
echo ""

# Check recent jobs (last 7 days)
echo -e "${BLUE}=== Recent Jobs (Last 7 Days) ===${NC}"
sacct -u tylerdoe -S $(date -d '7 days ago' +%Y-%m-%d) --format=JobID,JobName%30,State,Elapsed,Timelimit,MaxRSS,ExitCode -X
echo ""

# Find COMPASS-related SLURM output files
echo -e "${BLUE}=== SLURM Output Files ===${NC}"
if ls slurm-*.out 2>/dev/null | head -5; then
    echo ""
    echo "Recent SLURM output files found. Checking for errors..."
    echo ""

    for file in $(ls -t slurm-*.out 2>/dev/null | head -3); do
        echo -e "${YELLOW}--- File: $file ---${NC}"
        echo "Job info:"
        head -20 "$file" | grep -E "(Job ID|Start time|End time|Exit code)"

        echo ""
        echo "Exit status:"
        tail -10 "$file" | grep -E "(Exit code|✅|❌|ERROR|WARN)"

        echo ""
        echo "Last 5 lines:"
        tail -5 "$file"
        echo ""
        echo "---"
        echo ""
    done
else
    echo "No SLURM output files found in current directory"
fi

# Check Nextflow logs
echo -e "${BLUE}=== Nextflow Status ===${NC}"
if [ -f ".nextflow.log" ]; then
    echo "Latest Nextflow log found (.nextflow.log)"
    echo ""

    # Check for errors
    echo "Recent errors:"
    grep -i "error" .nextflow.log | tail -5
    echo ""

    # Check last execution status
    echo "Last execution lines:"
    tail -20 .nextflow.log
    echo ""
else
    echo "No .nextflow.log found in current directory"
fi

# Check Nextflow history
echo -e "${BLUE}=== Nextflow Run History ===${NC}"
if command -v nextflow &> /dev/null; then
    nextflow log | tail -10
    echo ""

    # Get details of last run
    LAST_RUN=$(nextflow log | tail -1 | awk '{print $4}')
    if [ -n "$LAST_RUN" ]; then
        echo "Details of last run ($LAST_RUN):"
        nextflow log "$LAST_RUN" -f hash,name,status,exit,duration | tail -20
    fi
else
    echo "Nextflow command not found. Try: module load Nextflow"
fi
echo ""

# Check work directory
echo -e "${BLUE}=== Work Directory Status ===${NC}"
if [ -d "work" ]; then
    WORK_SIZE=$(du -sh work 2>/dev/null | cut -f1)
    WORK_FILES=$(find work -type f 2>/dev/null | wc -l)
    echo "Work directory size: $WORK_SIZE"
    echo "Total files: $WORK_FILES"
    echo ""

    # Find recent failures
    echo "Recent failed processes (if any):"
    find work -name ".exitcode" -mtime -1 -exec grep -l "[^0]" {} \; 2>/dev/null | while read exitfile; do
        workdir=$(dirname "$exitfile")
        exitcode=$(cat "$exitfile")
        echo -e "${RED}Failed process in: $workdir (exit code: $exitcode)${NC}"

        # Show command log
        if [ -f "$workdir/.command.log" ]; then
            echo "Last 10 lines of log:"
            tail -10 "$workdir/.command.log"
        fi
        echo ""
    done
else
    echo "No work directory found"
fi
echo ""

# Check results directories
echo -e "${BLUE}=== Results Directories ===${NC}"
for dir in results_2025_production results_kansas_2025 results_2025_production_limited; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}Found: $dir${NC}"
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1)
        echo "  Size: $SIZE"

        # Check what completed
        echo "  Completed analyses:"
        [ -d "$dir/assembly" ] && echo "    ✓ Assembly"
        [ -d "$dir/mlst" ] && echo "    ✓ MLST"
        [ -d "$dir/sistr" ] && echo "    ✓ SISTR"
        [ -d "$dir/amrfinder" ] && echo "    ✓ AMRFinder"
        [ -d "$dir/abricate" ] && echo "    ✓ ABRicate"
        [ -d "$dir/mobsuite" ] && echo "    ✓ MOB-suite"
        [ -d "$dir/phage" ] && echo "    ✓ Phage analysis"
        [ -d "$dir/busco" ] && echo "    ✓ BUSCO"
        [ -d "$dir/quast" ] && echo "    ✓ QUAST"
        [ -f "$dir/multiqc/multiqc_report.html" ] && echo "    ✓ MultiQC report"

        echo ""
    fi
done
echo ""

# Quick diagnostics
echo -e "${BLUE}=== Quick Diagnostics ===${NC}"

# Check disk space
echo "Disk space:"
df -h . | tail -1
echo ""

# Check memory
echo "Memory usage:"
free -h
echo ""

# Check if database paths exist
echo "Database availability:"
[ -d "/homes/tylerdoe/databases/checkv-db-v1.5" ] && echo -e "  ${GREEN}✓ CheckV DB${NC}" || echo -e "  ${RED}✗ CheckV DB${NC}"
[ -f "/homes/tylerdoe/databases/prophage_db.dmnd" ] && echo -e "  ${GREEN}✓ Prophage DB${NC}" || echo -e "  ${RED}✗ Prophage DB${NC}"
[ -d "/homes/tylerdoe/databases/busco_downloads" ] && echo -e "  ${GREEN}✓ BUSCO DB${NC}" || echo -e "  ${RED}✗ BUSCO DB${NC}"
echo ""

echo "================================================"
echo "Diagnostic Complete"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Review any errors shown above"
echo "2. Check SLURM output files: cat slurm-<jobid>.out"
echo "3. Review Nextflow log: tail -100 .nextflow.log"
echo "4. For failed processes, check work directories shown above"
echo ""
echo "To resume a failed run:"
echo "  sbatch run_2025_production.sh"
echo "  (The -resume flag is already included)"
