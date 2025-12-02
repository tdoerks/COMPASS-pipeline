#!/bin/bash

# check_kansas_results.sh
# Inventory script to assess existing Kansas NARMS results (2021-2025)
#
# This script checks:
# - What analysis modules exist for each year
# - Sample counts per module (MLST, AMRFinderPlus, Prokka, QUAST, MOB-suite, etc.)
# - Whether summary reports exist
# - Whether sample counts are consistent across modules
#
# Usage: bash check_kansas_results.sh

echo "=========================================="
echo "KANSAS NARMS RESULTS INVENTORY"
echo "Checking: 2021-2025"
echo "Location: /homes/tylerdoe/archives/compass_kansas_results/"
echo "=========================================="
echo ""

RESULTS_BASE="/homes/tylerdoe/archives/compass_kansas_results"

for year in 2021 2022 2023 2024 2025; do
    echo "========================================="
    echo "KANSAS $year RESULTS"
    echo "========================================="

    RESULTS_DIR="${RESULTS_BASE}/results_kansas_${year}"

    if [ ! -d "$RESULTS_DIR" ]; then
        echo "❌ Directory not found: $RESULTS_DIR"
        echo ""
        continue
    fi

    echo "📁 Directory: $RESULTS_DIR"
    echo ""

    # List all top-level directories (analysis modules)
    echo "Available analysis modules:"
    ls -d $RESULTS_DIR/*/ 2>/dev/null | sed "s|$RESULTS_DIR/||" | sed 's|/$||' | sed 's/^/  • /'
    echo ""

    echo "Sample counts per module:"

    # MLST
    mlst_count=$(find $RESULTS_DIR/mlst -name "*.tsv" 2>/dev/null | wc -l)
    printf "  %-20s %3d samples\n" "MLST:" "$mlst_count"

    # AMRFinderPlus
    amr_count=$(find $RESULTS_DIR/amrfinderplus -type d -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)
    printf "  %-20s %3d samples\n" "AMRFinderPlus:" "$amr_count"

    # Prokka
    prokka_count=$(find $RESULTS_DIR/prokka -type d -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)
    printf "  %-20s %3d samples\n" "Prokka:" "$prokka_count"

    # QUAST
    quast_count=$(find $RESULTS_DIR/quast -name "*.tsv" 2>/dev/null | wc -l)
    printf "  %-20s %3d samples\n" "QUAST:" "$quast_count"

    # BUSCO
    busco_count=$(find $RESULTS_DIR/busco -type d -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)
    printf "  %-20s %3d samples\n" "BUSCO:" "$busco_count"

    # MOB-suite
    mobsuite_count=$(find $RESULTS_DIR/mobsuite -type d -name "*_mobsuite" 2>/dev/null | wc -l)
    printf "  %-20s %3d samples" "MOB-suite:" "$mobsuite_count"
    if [ $mobsuite_count -eq 0 ]; then
        echo "  ❌ MISSING"
    elif [ $mobsuite_count -lt $mlst_count ]; then
        echo "  ⚠️  INCOMPLETE"
    else
        echo "  ✅"
    fi

    # SISTR (Salmonella only)
    sistr_count=$(find $RESULTS_DIR/sistr -name "*.tsv" 2>/dev/null | wc -l)
    if [ $sistr_count -gt 0 ]; then
        printf "  %-20s %3d samples\n" "SISTR:" "$sistr_count"
    fi

    # Assemblies
    assembly_count=$(find $RESULTS_DIR/assemblies -name "*.fasta" -o -name "*.fa" 2>/dev/null | wc -l)
    printf "  %-20s %3d samples\n" "Assemblies:" "$assembly_count"

    echo ""

    # Check for summary report
    echo "Summary report:"
    if [ -f "$RESULTS_DIR/summary/compass_summary.tsv" ]; then
        lines=$(wc -l < "$RESULTS_DIR/summary/compass_summary.tsv")
        samples=$((lines - 1))  # Subtract header
        echo "  ✅ EXISTS ($samples samples in report)"
    else
        echo "  ❌ MISSING"
    fi

    echo ""

    # Check for pipeline completion
    if [ -f "$RESULTS_DIR/pipeline_info/execution_report.html" ]; then
        echo "Pipeline status: ✅ COMPLETED"

        # Try to extract completion time
        if [ -f "$RESULTS_DIR/pipeline_info/execution_trace.txt" ]; then
            # Count successful processes
            success_count=$(grep -c "COMPLETED" "$RESULTS_DIR/pipeline_info/execution_trace.txt" 2>/dev/null || echo "0")
            failed_count=$(grep -c "FAILED" "$RESULTS_DIR/pipeline_info/execution_trace.txt" 2>/dev/null || echo "0")

            if [ $failed_count -gt 0 ]; then
                echo "  ⚠️  $failed_count failed processes detected"
            fi
            echo "  $success_count processes completed successfully"
        fi
    else
        echo "Pipeline status: ⚠️  INCOMPLETE or OLD FORMAT"
    fi

    echo ""

    # Consistency check
    if [ $mlst_count -ne $amr_count ] || [ $mlst_count -ne $prokka_count ]; then
        echo "⚠️  WARNING: Sample counts inconsistent across modules!"
        echo "   This may indicate incomplete run or failures."
    else
        echo "✅ Sample counts consistent across core modules"
    fi

    echo ""
    echo ""
done

# Summary table
echo "========================================="
echo "SUMMARY TABLE"
echo "========================================="
printf "%-6s | %-6s | %-6s | %-10s | %-10s\n" "Year" "MLST" "AMR" "MOB-suite" "Summary"
echo "-------|--------|--------|------------|------------"

for year in 2021 2022 2023 2024 2025; do
    RESULTS_DIR="${RESULTS_BASE}/results_kansas_${year}"

    if [ -d "$RESULTS_DIR" ]; then
        mlst=$(find $RESULTS_DIR/mlst -name "*.tsv" 2>/dev/null | wc -l)
        amr=$(find $RESULTS_DIR/amrfinderplus -type d -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)
        mob=$(find $RESULTS_DIR/mobsuite -type d -name "*_mobsuite" 2>/dev/null | wc -l)

        if [ $mob -eq 0 ]; then
            mob_status="❌ Missing"
        elif [ $mob -lt $mlst ]; then
            mob_status="⚠️  $mob (partial)"
        else
            mob_status="✅ $mob"
        fi

        if [ -f "$RESULTS_DIR/summary/compass_summary.tsv" ]; then
            sum_status="✅ Exists"
        else
            sum_status="❌ Missing"
        fi

        printf "%-6s | %6d | %6d | %-10s | %-10s\n" "$year" "$mlst" "$amr" "$mob_status" "$sum_status"
    else
        printf "%-6s | %-6s | %-6s | %-10s | %-10s\n" "$year" "N/A" "N/A" "N/A" "N/A"
    fi
done

echo ""
echo "========================================="
echo "RECOMMENDATIONS"
echo "========================================="

# Check which years need MOB-suite
missing_mob=""
for year in 2021 2022 2023 2024 2025; do
    RESULTS_DIR="${RESULTS_BASE}/results_kansas_${year}"
    if [ -d "$RESULTS_DIR" ]; then
        mob=$(find $RESULTS_DIR/mobsuite -type d -name "*_mobsuite" 2>/dev/null | wc -l)
        if [ $mob -eq 0 ]; then
            missing_mob="$missing_mob $year"
        fi
    fi
done

if [ -n "$missing_mob" ]; then
    echo "Years missing MOB-suite:$missing_mob"
    echo "  → Re-run these years with current pipeline to get MOB-suite results"
else
    echo "✅ All years have MOB-suite results!"
fi

# Check which years need summary
missing_sum=""
for year in 2021 2022 2023 2024 2025; do
    RESULTS_DIR="${RESULTS_BASE}/results_kansas_${year}"
    if [ -d "$RESULTS_DIR" ]; then
        if [ ! -f "$RESULTS_DIR/summary/compass_summary.tsv" ]; then
            missing_sum="$missing_sum $year"
        fi
    fi
done

if [ -n "$missing_sum" ]; then
    echo ""
    echo "Years missing summary reports:$missing_sum"
    echo "  → Run COMPASS_SUMMARY module (once fixed) or generate manually"
fi

echo ""
echo "========================================="
echo "Inventory complete!"
echo "========================================="
