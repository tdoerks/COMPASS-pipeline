#!/bin/bash

# Analyze preliminary E. coli 2024 results
# Run this on Beocat while pipeline continues in background

RESULTS_DIR="/fastscratch/tylerdoe/results_ecoli_2024_preliminary"
PIPELINE_DIR="$HOME/pipelines/COMPASS-pipeline"

echo "=========================================="
echo "E. coli 2024 Preliminary Analysis"
echo "=========================================="
echo ""
echo "Results: $RESULTS_DIR"
echo "Scripts: $PIPELINE_DIR/bin"
echo ""

# Check directories exist
if [ ! -d "$RESULTS_DIR" ]; then
    echo "ERROR: Results directory not found!"
    echo "Run copy_preliminary_results.sh first"
    exit 1
fi

if [ ! -d "$PIPELINE_DIR" ]; then
    echo "ERROR: Pipeline directory not found!"
    exit 1
fi

cd "$PIPELINE_DIR"

echo "Starting analyses..."
echo ""

# 1. AMR-Prophage Enrichment Analysis
echo "=========================================="
echo "1. AMR-Prophage Enrichment Analysis"
echo "=========================================="
if [ -d "$RESULTS_DIR/amrfinder" ] && [ -d "$RESULTS_DIR/vibrant" ]; then
    echo "Running analyze_enriched_amr_genes.py..."
    python3 bin/analyze_enriched_amr_genes.py "$RESULTS_DIR"
    echo "✅ Done"
else
    echo "⚠️  Skipping - amrfinder or vibrant directory missing"
fi
echo ""

# 2. Comprehensive AMR Analysis
echo "=========================================="
echo "2. Comprehensive AMR-Prophage Analysis"
echo "=========================================="
if [ -d "$RESULTS_DIR/amrfinder" ] && [ -d "$RESULTS_DIR/vibrant" ]; then
    echo "Running comprehensive_amr_analysis.py..."
    python3 bin/comprehensive_amr_analysis.py "$RESULTS_DIR"
    echo "✅ Done"
else
    echo "⚠️  Skipping - amrfinder or vibrant directory missing"
fi
echo ""

# 3. Species Validation Summary
echo "=========================================="
echo "3. Species Validation (Check for Mislabeling)"
echo "=========================================="
if [ -f "$RESULTS_DIR/species_validation/species_validation_report.txt" ]; then
    echo "Displaying species validation report..."
    cat "$RESULTS_DIR/species_validation/species_validation_report.txt"
    echo ""
    echo "Full results in: $RESULTS_DIR/species_validation/"
elif [ -d "$RESULTS_DIR/mlst" ]; then
    echo "⚠️  Species validation not complete yet (MLST finished but validation pending)"
else
    echo "⚠️  Skipping - MLST/species validation not complete yet"
fi
echo ""

# 4. MLST Summary
echo "=========================================="
echo "4. MLST Summary (Top Sequence Types)"
echo "=========================================="
if [ -d "$RESULTS_DIR/mlst" ]; then
    echo "Top 20 E. coli sequence types:"
    cat "$RESULTS_DIR/mlst"/*.tsv | cut -f2,3 | grep -v "SCHEME" | sort | uniq -c | sort -rn | head -20
else
    echo "⚠️  Skipping - MLST directory missing"
fi
echo ""

# 5. MOB-suite Summary (Plasmid Types)
echo "=========================================="
echo "5. MOB-suite Summary (Plasmid Types)"
echo "=========================================="
if [ -d "$RESULTS_DIR/mobsuite" ]; then
    echo "Counting plasmid replicons..."
    recon_files=$(find "$RESULTS_DIR/mobsuite" -name "*_recon.txt" | wc -l)
    echo "  Samples with MOB-suite results: $recon_files"
    echo ""
    echo "Top 10 plasmid replicon types:"
    find "$RESULTS_DIR/mobsuite" -name "*_recon.txt" -exec grep -h "^plasmid" {} \; | \
        cut -f10 | grep -v "^-$" | sort | uniq -c | sort -rn | head -10 || echo "  No plasmids detected yet"
else
    echo "⚠️  Skipping - mobsuite directory missing"
fi
echo ""

# 6. Quick Stats
echo "=========================================="
echo "6. Overall Progress Summary"
echo "=========================================="
echo "Samples with completed analyses:"
for dir in amrfinder vibrant mlst mobsuite quast; do
    if [ -d "$RESULTS_DIR/$dir" ]; then
        count=$(find "$RESULTS_DIR/$dir" -name "*.tsv" -o -name "*.txt" 2>/dev/null | wc -l)
        printf "  %-15s %5d files\n" "$dir:" "$count"
    fi
done
echo ""

# Summary of outputs
echo "=========================================="
echo "Analysis Outputs"
echo "=========================================="
echo "Generated files in: $RESULTS_DIR"
echo ""
echo "CSV files:"
ls -lh "$RESULTS_DIR"/*.csv 2>/dev/null | awk '{print "  " $9, "(" $5 ")"}'
echo ""
echo "HTML files:"
ls -lh "$RESULTS_DIR"/*.html 2>/dev/null | awk '{print "  " $9, "(" $5 ")"}'

echo ""
echo "=========================================="
echo "✅ Preliminary analysis complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Review CSV/HTML files in: $RESULTS_DIR"
echo "  2. Check species_mismatches.tsv for mislabeled samples"
echo "  3. Wait for full pipeline to complete"
echo "  4. Re-run on final complete dataset"
