#!/bin/bash
# ============================================================
# TEST SCRIPT - Combine just 5 files to diagnose issue
# ============================================================

set -x  # Show each command as it runs

KANSAS_DIR="/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod"

echo "=========================================="
echo "Testing AMR File Combining (5 files only)"
echo "=========================================="
echo "Data directory: ${KANSAS_DIR}"
echo ""

cd "${KANSAS_DIR}" || exit 1

# Test AMR combining
AMR_OUTPUT="test_amr_combined.tsv"
echo "Finding first AMR file..."
first_file=$(find amrfinder -name "*_amr.tsv" 2>/dev/null | sort | head -1)
echo "First file: $first_file"

echo "Creating header..."
echo -ne "sample_id\t" > "${AMR_OUTPUT}"
head -1 "$first_file" >> "${AMR_OUTPUT}"

echo "Processing files..."
count=0
while IFS= read -r amr_file; do
    sample_id=$(basename "$amr_file" | sed 's/_amr\.tsv$//')
    echo "  Processing $count: $sample_id from $amr_file"

    tail -n +2 "$amr_file" | awk -v sid="$sample_id" 'BEGIN{OFS="\t"} {print sid, $0}' >> "${AMR_OUTPUT}"

    ((count++))
    if [ $count -ge 5 ]; then
        echo "  Stopping at 5 files for test"
        break
    fi
done < <(find amrfinder -name "*_amr.tsv" 2>/dev/null | sort)

echo ""
echo "Done! Results:"
wc -l "${AMR_OUTPUT}"
ls -lh "${AMR_OUTPUT}"
echo ""
echo "Preview:"
head -10 "${AMR_OUTPUT}" | cut -f1-5
