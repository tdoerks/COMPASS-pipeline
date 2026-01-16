#!/bin/bash
# COMPASS Pipeline - Quick Test Script
# Performs basic validation and suggests test commands

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🧬 COMPASS Pipeline - Quick Test Helper"
echo "========================================"
echo ""

# 1. Run validation
if [ -x "bin/validate_pipeline.sh" ]; then
    echo "Running pipeline validation..."
    ./bin/validate_pipeline.sh
    echo ""
else
    echo "⚠️  Validation script not found, skipping..."
fi

# 2. Check for test data
echo "📁 Checking for test data..."
if [ -f "test_data/example_samplesheet.csv" ]; then
    echo "✓ Found: test_data/example_samplesheet.csv"
    HAS_TEST_DATA=true
else
    echo "⚠️  No test data found"
    HAS_TEST_DATA=false
fi
echo ""

# 3. Suggest test commands
echo "🚀 Suggested Test Commands:"
echo ""

if [ "$HAS_TEST_DATA" = true ]; then
    echo "A) Test with Example Samplesheet (edit paths first):"
    echo "   nextflow run main.nf \\"
    echo "       --input test_data/example_samplesheet.csv \\"
    echo "       --outdir test_results \\"
    echo "       -resume"
    echo ""
fi

echo "B) Test with NARMS Metadata (5 samples from Kansas 2023):"
echo "   nextflow run main.nf \\"
echo "       --input_mode metadata \\"
echo "       --filter_state \"KS\" \\"
echo "       --filter_year_start 2023 \\"
echo "       --filter_year_end 2023 \\"
echo "       --max_samples 5 \\"
echo "       --outdir test_results_narms \\"
echo "       -resume"
echo ""

echo "C) Test with Custom SRA List:"
echo "   echo 'SRR12345678' > test_srr.txt"
echo "   nextflow run main.nf \\"
echo "       --input_mode sra_list \\"
echo "       --input test_srr.txt \\"
echo "       --outdir test_results_sra \\"
echo "       -resume"
echo ""

# 4. Check profiles
echo "📋 Available Profiles:"
if grep -q "profiles {" nextflow.config; then
    grep -A20 "profiles {" nextflow.config | grep -E "^\s+\w+\s*{" | sed 's/{//g' | sed 's/^/   - /'
else
    echo "   - standard (default)"
fi
echo ""

# 5. Environment check
echo "🔧 Environment Check:"
command -v nextflow >/dev/null && echo "   ✓ nextflow" || echo "   ✗ nextflow (NOT FOUND)"
command -v apptainer >/dev/null && echo "   ✓ apptainer" || \
    (command -v singularity >/dev/null && echo "   ✓ singularity" || echo "   ⚠️  No container runtime found")
command -v git >/dev/null && echo "   ✓ git" || echo "   ⚠️  git (not found)"
echo ""

# 6. Tips
echo "💡 Tips:"
echo "   - Always use -resume to restart from last successful step"
echo "   - Use -with-timeline timeline.html for performance profiling"
echo "   - Use -with-report report.html for execution report"
echo "   - Check TROUBLESHOOTING.md if you encounter issues"
echo "   - Start with small datasets (3-5 samples) for testing"
echo ""

echo "✅ Ready to test! Choose a command above and run it."
echo ""
