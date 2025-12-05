#!/bin/bash
# COMPASS Pipeline Validation Script
# Quick syntax and structure checks before running

set -e

echo "🔍 COMPASS Pipeline Validation"
echo "================================"

# Check Nextflow installation
echo -n "✓ Checking Nextflow... "
if command -v nextflow &> /dev/null; then
    NF_VERSION=$(nextflow -version 2>&1 | head -n1)
    echo "$NF_VERSION"
else
    echo "❌ ERROR: Nextflow not found!"
    exit 1
fi

# Check container runtime
echo -n "✓ Checking container runtime... "
if command -v apptainer &> /dev/null; then
    echo "apptainer ($(apptainer --version))"
elif command -v singularity &> /dev/null; then
    echo "singularity ($(singularity --version))"
else
    echo "⚠️  WARNING: No container runtime found (apptainer/singularity)"
fi

# Validate main workflow
echo -n "✓ Validating main workflow... "
if nextflow inspect main.nf &> /dev/null; then
    echo "OK"
else
    echo "❌ ERROR: main.nf validation failed"
    nextflow inspect main.nf
    exit 1
fi

# Check required directories exist
echo "✓ Checking project structure..."
REQUIRED_DIRS=("modules" "subworkflows" "workflows" "conf" "bin")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        COUNT=$(find "$dir" -name "*.nf" 2>/dev/null | wc -l)
        echo "  - $dir/ ($COUNT .nf files)"
    else
        echo "  ❌ Missing: $dir/"
        exit 1
    fi
done

# Check for common issues
echo "✓ Checking for common issues..."

# Check all modules have containers
echo -n "  - Container specifications... "
MISSING_CONTAINERS=$(grep -L "container\s*=" modules/*.nf 2>/dev/null || true)
if [ -z "$MISSING_CONTAINERS" ]; then
    echo "OK (all modules)"
else
    echo "⚠️  WARNING: Missing containers in:"
    echo "$MISSING_CONTAINERS"
fi

# Check for hardcoded paths (excluding database configs)
echo -n "  - Hardcoded paths... "
HARDCODED=$(grep -r "/homes/" modules/ subworkflows/ workflows/ 2>/dev/null | grep -v "^Binary" || true)
if [ -z "$HARDCODED" ]; then
    echo "OK"
else
    echo "⚠️  Found hardcoded paths (check if intentional):"
    echo "$HARDCODED" | head -3
fi

# Check parameter documentation
echo -n "  - Parameter documentation... "
if grep -q "params {" nextflow.config && grep -q "## Parameters" README.md; then
    echo "OK"
else
    echo "⚠️  Check params documentation"
fi

echo ""
echo "✅ Validation complete!"
echo ""
echo "📋 Quick test command:"
echo "   nextflow run main.nf -profile test -resume"
echo ""
