#!/bin/bash
#SBATCH --job-name=prophage_amr_analysis
#SBATCH --output=/homes/tylerdoe/slurm-prophage-amr-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-prophage-amr-%j.err
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Complete Prophage-AMR Analysis"
echo "All 3 Methods on Kansas 2021-2025 Dataset"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
RESULTS_DIR="/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod"
OUTPUT_DIR="/homes/tylerdoe/prophage_amr_analysis_$(date +%Y%m%d)"

# Create output directory
mkdir -p "$OUTPUT_DIR"

cd "$PIPELINE_DIR" || {
    echo "ERROR: Could not cd to $PIPELINE_DIR"
    exit 1
}

echo "Pipeline directory: $PIPELINE_DIR"
echo "Results directory: $RESULTS_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Count samples
SAMPLE_COUNT=$(find "$RESULTS_DIR/amrfinder" -name "*_amr.tsv" | wc -l)
PROPHAGE_COUNT=$(find "$RESULTS_DIR/vibrant" -name "*_phages.fna" | wc -l)

echo "Dataset Summary:"
echo "  Samples with AMR results: $SAMPLE_COUNT"
echo "  Samples with prophage data: $PROPHAGE_COUNT"
echo ""

# ============================================================================
# METHOD 1: Coordinate-Based Analysis (FAST - seconds)
# ============================================================================

echo "=========================================="
echo "METHOD 1: Coordinate-Based Analysis"
echo "=========================================="
echo "Status: Running..."
echo "Speed: Fast (seconds for all samples)"
echo "Description: Check if AMR gene coordinates overlap prophage boundaries"
echo ""

START_TIME=$(date +%s)

./bin/analyze_true_amr_prophage_colocation.py \
    "$RESULTS_DIR" \
    "$OUTPUT_DIR/method1_coordinate_based.csv"

METHOD1_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
if [ $METHOD1_EXIT -eq 0 ]; then
    echo "✅ Method 1 completed successfully in ${ELAPSED}s"
    echo "   Output: $OUTPUT_DIR/method1_coordinate_based.csv"
    echo "   HTML Report: $OUTPUT_DIR/method1_coordinate_based.html"

    # Show quick summary
    if [ -f "$OUTPUT_DIR/method1_coordinate_based.csv" ]; then
        COLOCATION_COUNT=$(tail -n +2 "$OUTPUT_DIR/method1_coordinate_based.csv" | \
            awk -F',' '$NF == "within_prophage"' | wc -l)
        echo "   AMR genes in prophages: $COLOCATION_COUNT"
    fi
else
    echo "❌ Method 1 failed with exit code $METHOD1_EXIT"
fi
echo ""

# ============================================================================
# METHOD 2: Annotation Search (FAST - seconds)
# ============================================================================

echo "=========================================="
echo "METHOD 2: Annotation-Based Search"
echo "=========================================="
echo "Status: Running..."
echo "Speed: Fast (seconds for all samples)"
echo "Description: Search VIBRANT annotations for AMR gene names"
echo ""

START_TIME=$(date +%s)

./bin/search_amr_in_vibrant_annotations.py \
    "$RESULTS_DIR" \
    > "$OUTPUT_DIR/method2_annotation_search.log" 2>&1

METHOD2_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# Move CSV output to our directory
if [ -f "$HOME/amr_in_vibrant_annotations.csv" ]; then
    mv "$HOME/amr_in_vibrant_annotations.csv" "$OUTPUT_DIR/method2_annotation_search.csv"
fi

echo ""
if [ $METHOD2_EXIT -eq 0 ]; then
    echo "✅ Method 2 completed successfully in ${ELAPSED}s"
    echo "   Output: $OUTPUT_DIR/method2_annotation_search.csv"
    echo "   Log: $OUTPUT_DIR/method2_annotation_search.log"

    # Show quick summary
    if [ -f "$OUTPUT_DIR/method2_annotation_search.csv" ]; then
        MATCH_COUNT=$(tail -n +2 "$OUTPUT_DIR/method2_annotation_search.csv" | wc -l)
        echo "   Matches found: $MATCH_COUNT"
    fi
else
    echo "❌ Method 2 failed with exit code $METHOD2_EXIT"
fi
echo ""

# ============================================================================
# METHOD 3: Direct AMRFinder Scan (SLOW - hours)
# ============================================================================

echo "=========================================="
echo "METHOD 3: Direct AMRFinder Scan"
echo "=========================================="
echo "Status: Running..."
echo "Speed: SLOW (~1-2 min per sample, expect hours)"
echo "Description: Run AMRFinderPlus directly on prophage DNA sequences"
echo ""
echo "⚠️  This will take a LONG time for $PROPHAGE_COUNT samples!"
echo "   Estimated time: $(($PROPHAGE_COUNT * 2 / 60)) - $(($PROPHAGE_COUNT * 2 / 60 * 2)) hours"
echo ""

START_TIME=$(date +%s)

./bin/run_amrfinder_on_prophages.py \
    "$RESULTS_DIR" \
    > "$OUTPUT_DIR/method3_direct_scan.log" 2>&1 <<EOF
y
EOF

METHOD3_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))

# Move CSV output to our directory
if [ -f "$HOME/prophage_amr_direct_scan.csv" ]; then
    mv "$HOME/prophage_amr_direct_scan.csv" "$OUTPUT_DIR/method3_direct_scan.csv"
fi

echo ""
if [ $METHOD3_EXIT -eq 0 ]; then
    echo "✅ Method 3 completed successfully in ${HOURS}h ${MINUTES}m"
    echo "   Output: $OUTPUT_DIR/method3_direct_scan.csv"
    echo "   Log: $OUTPUT_DIR/method3_direct_scan.log"

    # Show quick summary
    if [ -f "$OUTPUT_DIR/method3_direct_scan.csv" ]; then
        GENES_IN_PROPHAGE=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
            awk -F',' '$2 != "None"' | wc -l)
        echo "   Samples with AMR in prophages: $GENES_IN_PROPHAGE"
    fi
else
    echo "❌ Method 3 failed with exit code $METHOD3_EXIT"
fi
echo ""

# ============================================================================
# GENERATE COMPARISON REPORT
# ============================================================================

echo "=========================================="
echo "Generating Comparison Report"
echo "=========================================="

REPORT_FILE="$OUTPUT_DIR/analysis_comparison_report.txt"

cat > "$REPORT_FILE" <<REPORT
================================================================================
PROPHAGE-AMR ANALYSIS COMPARISON REPORT
================================================================================
Dataset: Kansas 2021-2025 NARMS
Samples analyzed: $SAMPLE_COUNT
Analysis date: $(date)
Job ID: $SLURM_JOB_ID

================================================================================
METHOD 1: Coordinate-Based Analysis
================================================================================
Status: $([ $METHOD1_EXIT -eq 0 ] && echo "✅ Success" || echo "❌ Failed")
Runtime: ${ELAPSED}s
Output: method1_coordinate_based.csv, method1_coordinate_based.html

Description:
  Parses AMRFinderPlus coordinates (contig, start, end) and VIBRANT prophage
  coordinates, then checks if AMR gene coordinates fall within prophage boundaries.

Results:
REPORT

if [ -f "$OUTPUT_DIR/method1_coordinate_based.csv" ]; then
    TOTAL_AMR=$(tail -n +2 "$OUTPUT_DIR/method1_coordinate_based.csv" | wc -l)
    IN_PROPHAGE=$(tail -n +2 "$OUTPUT_DIR/method1_coordinate_based.csv" | \
        awk -F',' '$NF == "within_prophage"' | wc -l)
    SAMPLES_WITH_COLOC=$(tail -n +2 "$OUTPUT_DIR/method1_coordinate_based.csv" | \
        awk -F',' '$NF == "within_prophage" {print $1}' | sort -u | wc -l)

    cat >> "$REPORT_FILE" <<REPORT
  Total AMR genes analyzed: $TOTAL_AMR
  AMR genes inside prophages: $IN_PROPHAGE
  Samples with prophage-carried AMR: $SAMPLES_WITH_COLOC
  Percentage in prophages: $(awk "BEGIN {printf \"%.2f\", ($IN_PROPHAGE/$TOTAL_AMR)*100}")%
REPORT
else
    echo "  No output file generated" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" <<REPORT

================================================================================
METHOD 2: Annotation-Based Search
================================================================================
Status: $([ $METHOD2_EXIT -eq 0 ] && echo "✅ Success" || echo "❌ Failed")
Output: method2_annotation_search.csv

Description:
  Searches VIBRANT annotation files for AMR gene names from AMRFinderPlus.
  Note: VIBRANT uses VOG/KEGG IDs, not AMR-specific gene names, so this
  typically finds 0 matches.

Results:
REPORT

if [ -f "$OUTPUT_DIR/method2_annotation_search.csv" ]; then
    MATCH_COUNT=$(tail -n +2 "$OUTPUT_DIR/method2_annotation_search.csv" | wc -l)
    echo "  Total matches found: $MATCH_COUNT" >> "$REPORT_FILE"
else
    echo "  No output file generated" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" <<REPORT

================================================================================
METHOD 3: Direct AMRFinder Scan (DEFINITIVE)
================================================================================
Status: $([ $METHOD3_EXIT -eq 0 ] && echo "✅ Success" || echo "❌ Failed")
Runtime: ${HOURS}h ${MINUTES}m
Output: method3_direct_scan.csv

Description:
  Extracts prophage sequences from VIBRANT output and runs AMRFinderPlus
  directly on those sequences. This is the most definitive approach.

Results:
REPORT

if [ -f "$OUTPUT_DIR/method3_direct_scan.csv" ]; then
    SAMPLES_ANALYZED=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
        awk -F',' '{print $1}' | sort -u | wc -l)
    SAMPLES_WITH_AMR=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
        awk -F',' '$2 != "None" && $2 != ""' | wc -l)
    TOTAL_AMR_IN_PROPHAGE=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
        awk -F',' '$2 != "None" && $2 != ""' | wc -l)

    cat >> "$REPORT_FILE" <<REPORT
  Samples analyzed: $SAMPLES_ANALYZED
  Samples with AMR in prophages: $SAMPLES_WITH_AMR
  Total AMR genes in prophages: $TOTAL_AMR_IN_PROPHAGE
REPORT
else
    echo "  No output file generated" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" <<REPORT

================================================================================
COMPARISON & INTERPRETATION
================================================================================

Method Agreement:
REPORT

if [ -f "$OUTPUT_DIR/method1_coordinate_based.csv" ] && [ -f "$OUTPUT_DIR/method3_direct_scan.csv" ]; then
    M1_COUNT=$(tail -n +2 "$OUTPUT_DIR/method1_coordinate_based.csv" | \
        awk -F',' '$NF == "within_prophage"' | wc -l)
    M3_COUNT=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
        awk -F',' '$2 != "None" && $2 != ""' | wc -l)

    cat >> "$REPORT_FILE" <<REPORT
  Method 1 (Coordinate): $M1_COUNT AMR genes in prophages
  Method 3 (Direct Scan): $M3_COUNT AMR genes in prophages

  Agreement: $([ "$M1_COUNT" = "$M3_COUNT" ] && echo "✅ Yes" || echo "⚠️  No - investigate discrepancy")
REPORT
fi

cat >> "$REPORT_FILE" <<REPORT

Biological Interpretation:
REPORT

if [ -f "$OUTPUT_DIR/method3_direct_scan.csv" ]; then
    M3_COUNT=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
        awk -F',' '$2 != "None" && $2 != ""' | wc -l)

    if [ "$M3_COUNT" -eq 0 ]; then
        cat >> "$REPORT_FILE" <<REPORT

  ✅ DEFINITIVE RESULT: No AMR genes found in prophages

  This means:
  - AMR genes in this dataset are chromosomal, not prophage-mediated
  - Resistance spread likely occurs via plasmids or direct conjugation
  - Prophage transduction is NOT a major mechanism for AMR transmission
  - This is a scientifically valuable finding!
REPORT
    else
        cat >> "$REPORT_FILE" <<REPORT

  ⚠️  AMR GENES FOUND IN PROPHAGES!

  This means:
  - Prophages DO carry resistance genes in this dataset
  - Prophage-mediated transduction may contribute to AMR spread
  - These genes are potentially mobile with prophage infection
  - Important finding for understanding resistance transmission!

  Recommended follow-up:
  - Identify which AMR genes are most common in prophages
  - Analyze temporal trends (increasing over time?)
  - Examine geographic distribution
  - Consider drug classes affected
REPORT
    fi
fi

cat >> "$REPORT_FILE" <<REPORT

================================================================================
OUTPUT FILES
================================================================================

All results saved to: $OUTPUT_DIR

Files:
  - method1_coordinate_based.csv      : Coordinate-based results
  - method1_coordinate_based.html     : Interactive HTML report
  - method2_annotation_search.csv     : Annotation search results
  - method2_annotation_search.log     : Search log
  - method3_direct_scan.csv           : Direct AMRFinder scan results
  - method3_direct_scan.log           : Scan log
  - analysis_comparison_report.txt    : This report

To view HTML report:
  scp tylerdoe@beocat.ksu.edu:$OUTPUT_DIR/method1_coordinate_based.html .

================================================================================
End of Report
================================================================================
REPORT

echo ""
echo "✅ Comparison report generated: $REPORT_FILE"
echo ""

# ============================================================================
# FINAL SUMMARY
# ============================================================================

echo "=========================================="
echo "Analysis Complete!"
echo "=========================================="
echo "End time: $(date)"
echo ""
echo "Results Directory: $OUTPUT_DIR"
echo ""
echo "Method Results:"
echo "  Method 1 (Coordinate): $([ $METHOD1_EXIT -eq 0 ] && echo "✅ Success" || echo "❌ Failed")"
echo "  Method 2 (Annotation): $([ $METHOD2_EXIT -eq 0 ] && echo "✅ Success" || echo "❌ Failed")"
echo "  Method 3 (Direct Scan): $([ $METHOD3_EXIT -eq 0 ] && echo "✅ Success" || echo "❌ Failed")"
echo ""
echo "Next Steps:"
echo "  1. Review comparison report: cat $OUTPUT_DIR/analysis_comparison_report.txt"
echo "  2. View HTML report: scp tylerdoe@beocat.ksu.edu:$OUTPUT_DIR/method1_coordinate_based.html ."
echo "  3. Analyze CSV files for detailed results"
echo ""
echo "=========================================="

# Display the report to console
cat "$REPORT_FILE"

exit 0
