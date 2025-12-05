#!/bin/bash
# Just the VIBRANT combining part with verbose debugging

KANSAS_DIR="/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod"

cd "${KANSAS_DIR}" || exit 1

VIBRANT_OUTPUT="vibrant_combined_NEW.tsv"

# Build array
echo "Finding VIBRANT directories..." >&2
mapfile -t vibrant_dir_array < <(find vibrant -maxdepth 1 -type d -name "*_vibrant" 2>/dev/null | sort)
vibrant_count=${#vibrant_dir_array[@]}
echo "Found ${vibrant_count} directories" >&2

# Create header
echo -e "sample_id\tscaffold\tfragment\tprotein\tkeywords\ttype\tquality\tcompleteness\tcontig_id" > "${VIBRANT_OUTPUT}"

# Process
found_results=0
for i in "${!vibrant_dir_array[@]}"; do
    vdir="${vibrant_dir_array[$i]}"
    sample_id=$(basename "$vdir" | sed 's/_vibrant$//')

    quality_file="${vdir}/VIBRANT_${sample_id}_contigs/VIBRANT_results_${sample_id}_contigs/VIBRANT_genome_quality_${sample_id}_contigs.tsv"

    if [ -f "$quality_file" ]; then
        tail -n +2 "$quality_file" | awk -v sid="$sample_id" 'BEGIN{OFS="\t"} {print sid, $0}' >> "${VIBRANT_OUTPUT}"
        ((found_results++))
    fi

    # Print progress for EVERY directory (for debugging)
    echo "Processed $((i+1)) / $vibrant_count: $sample_id (found_results=$found_results)" >&2
done

echo "" >&2
echo "DONE! Found results in $found_results samples" >&2
wc -l "${VIBRANT_OUTPUT}"
