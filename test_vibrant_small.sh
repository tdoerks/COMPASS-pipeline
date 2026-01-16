#!/bin/bash
# Test VIBRANT combining with just 10 directories

set -x

KANSAS_DIR="/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod"

echo "Testing VIBRANT combining..."
cd "${KANSAS_DIR}" || exit 1

VIBRANT_OUTPUT="test_vibrant_combined.tsv"

# Get first 10 directories
echo "Finding VIBRANT directories..."
mapfile -t vibrant_dir_array < <(find vibrant -maxdepth 1 -type d -name "*_vibrant" 2>/dev/null | sort | head -10)
echo "Found ${#vibrant_dir_array[@]} directories"

# Create header
echo -e "sample_id\tscaffold\tfragment\tprotein\tkeywords\ttype\tquality\tcompleteness\tcontig_id" > "${VIBRANT_OUTPUT}"

# Process each directory
found_results=0
for i in "${!vibrant_dir_array[@]}"; do
    vdir="${vibrant_dir_array[$i]}"
    echo "Processing directory $((i+1)): $vdir"

    sample_id=$(basename "$vdir" | sed 's/_vibrant$//')
    echo "  Sample ID: $sample_id"

    # Find VIBRANT quality file
    echo "  Looking for quality file in $vdir..."
    quality_file=$(find "$vdir" -name "VIBRANT_genome_quality_*.tsv" 2>/dev/null | head -1)

    if [ -n "$quality_file" ] && [ -f "$quality_file" ]; then
        echo "  Found: $quality_file"
        tail -n +2 "$quality_file" | awk -v sid="$sample_id" 'BEGIN{OFS="\t"} {print sid, $0}' >> "${VIBRANT_OUTPUT}"
        ((found_results++))
    else
        echo "  No quality file found"
    fi
done

echo ""
echo "Done! Processed ${#vibrant_dir_array[@]} directories, found results in $found_results"
wc -l "${VIBRANT_OUTPUT}"
ls -lh "${VIBRANT_OUTPUT}"
