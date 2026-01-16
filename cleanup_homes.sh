#!/bin/bash
# COMPASS Pipeline - /homes Directory Cleanup Utility
# Helps free up space in /homes/tylerdoe by safely removing temporary files

set -e

HOMES_DIR="/homes/tylerdoe"
FASTSCRATCH_DIR="/fastscratch/tylerdoe"

echo "=========================================="
echo "COMPASS /homes Directory Cleanup Utility"
echo "=========================================="
echo ""

# Check current disk usage
echo "Current disk usage:"
quota -s 2>/dev/null || echo "  (quota command not available)"
echo ""

# Function to safely remove with confirmation
safe_remove() {
    local pattern=$1
    local description=$2
    local count=$(find $HOMES_DIR -name "$pattern" 2>/dev/null | wc -l)

    if [ $count -gt 0 ]; then
        echo "Found $count $description"
        read -p "  Remove these? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            find $HOMES_DIR -name "$pattern" -delete 2>/dev/null
            echo "  ✅ Removed $count files"
        else
            echo "  ⏭️  Skipped"
        fi
    else
        echo "No $description found"
    fi
    echo ""
}

# Function to move large directories to fastscratch
move_to_fastscratch() {
    local dir_name=$1
    local description=$2

    if [ -d "$HOMES_DIR/$dir_name" ]; then
        local size=$(du -sh "$HOMES_DIR/$dir_name" 2>/dev/null | cut -f1)
        echo "Found $description: $size"
        read -p "  Move to fastscratch? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p "$FASTSCRATCH_DIR"
            mv "$HOMES_DIR/$dir_name" "$FASTSCRATCH_DIR/" 2>/dev/null
            echo "  ✅ Moved to $FASTSCRATCH_DIR/$dir_name"
        else
            echo "  ⏭️  Skipped"
        fi
    else
        echo "No $description found"
    fi
    echo ""
}

# 1. Remove old SLURM logs
echo "1. Old SLURM Logs"
echo "=================="
safe_remove "slurm-*.out" "SLURM output files (.out)"
safe_remove "slurm-*.err" "SLURM error files (.err)"

# 2. Remove test output files
echo "2. Test Output Files"
echo "===================="
safe_remove "test_*.out" "test output files"
safe_remove "test_*.err" "test error files"

# 3. Remove Nextflow work and cache
echo "3. Nextflow Temporary Files"
echo "==========================="
if [ -d "$HOMES_DIR/work" ]; then
    work_size=$(du -sh "$HOMES_DIR/work" 2>/dev/null | cut -f1)
    echo "Found Nextflow work directory: $work_size"
    read -p "  Remove? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$HOMES_DIR/work"
        echo "  ✅ Removed work directory"
    else
        echo "  ⏭️  Skipped"
    fi
else
    echo "No work directory found"
fi
echo ""

if [ -d "$HOMES_DIR/.nextflow" ]; then
    nextflow_size=$(du -sh "$HOMES_DIR/.nextflow" 2>/dev/null | cut -f1)
    echo "Found Nextflow cache: $nextflow_size"
    read -p "  Remove? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$HOMES_DIR/.nextflow"
        echo "  ✅ Removed .nextflow cache"
    else
        echo "  ⏭️  Skipped"
    fi
else
    echo "No .nextflow cache found"
fi
echo ""

# 4. Remove BALROG files
echo "4. BALROG Files"
echo "==============="
if [ -d "$HOMES_DIR/BALRROG_SHORT_META" ]; then
    balrog_size=$(du -sh "$HOMES_DIR/BALRROG_SHORT_META" 2>/dev/null | cut -f1)
    echo "Found BALROG directory: $balrog_size"
    read -p "  Remove? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$HOMES_DIR/BALRROG_SHORT_META"
        echo "  ✅ Removed BALROG directory"
    else
        echo "  ⏭️  Skipped"
    fi
else
    echo "No BALROG directory found"
fi
echo ""

# 5. Move assemblies to fastscratch
echo "5. Large Data Directories"
echo "========================="
move_to_fastscratch "assemblies" "assemblies directory"
move_to_fastscratch "results" "results directory"

# 6. Remove temp files
echo "6. Temporary Files"
echo "=================="
safe_remove "*.tmp" "temporary files (.tmp)"
safe_remove "core.*" "core dump files"
safe_remove "nohup.out" "nohup output files"

# 7. Clean up weird files
echo "7. Miscellaneous"
echo "================"
if [ -f "$HOMES_DIR/WorkflowStats[succeededCount=0" ]; then
    echo "Found incomplete workflow file"
    read -p "  Remove? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$HOMES_DIR/WorkflowStats"*
        echo "  ✅ Removed incomplete files"
    else
        echo "  ⏭️  Skipped"
    fi
else
    echo "No incomplete files found"
fi
echo ""

# Final report
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "New disk usage:"
quota -s 2>/dev/null || echo "  (quota command not available)"
echo ""
echo "Recommendations:"
echo "  - Old results moved to: $FASTSCRATCH_DIR"
echo "  - Pipeline logs go to: /homes/tylerdoe/slurm-*.out"
echo "  - Pipeline results go to: $FASTSCRATCH_DIR/results_*"
echo "  - Periodically run this script to maintain space"
echo ""
echo "✅ Done!"
